import datetime
import logging
import os
import uuid

from browser_use.agent.views import AgentHistory
from fastapi import HTTPException, APIRouter
from datetime import timezone

from app.db.mongo import get_db
from app.models.db_models import TaskDocument, SessionStatus, TaskStatus, ScreenshotDocument
from app.models.request_models import TaskRequest
from app.services.browser_manager import run_task, AGENTS
from app.utility.local_storage import save_agent_history_to_local
from app.utility.display_allocation import VNC_DISPLAYS, VNC_PORTS

router = APIRouter()


async def store_unique_screenshots(agent, session_id, db):
    """Store only new/unique screenshots to avoid duplicates"""
    if not agent:
        print("\033[1;31m🚨 WARNING: No agent provided! 🚨\033[0m")
        return {"status": "no_agent"}

    screenshots = agent.state.history.screenshots(return_none_if_not_screenshot=False)

    if not screenshots:
        print("\033[1;31m🚨 WARNING: No screenshots were captured by the agent! 🚨\033[0m")
        return {"status": "no_screenshots"}

    collection = db.screenshots
    existing_count = await collection.count_documents({"session_id": session_id})
    new_screenshots = screenshots[existing_count:]

    if not new_screenshots:
        print(f"\033[1;33m⚠️ No new screenshots to store. Already have {existing_count} screenshots.\033[0m")
        return {"status": "no_new_screenshots"}

    print(f"\033[1;32m✅ Processing {len(new_screenshots)} new screenshots (total: {len(screenshots)})\033[0m")

    documents = []
    for i, s in enumerate(new_screenshots, existing_count + 1):
        if not s:
            continue
        try:
            history_item = agent.state.history.history[i - 1]
            state = history_item.state

            doc = ScreenshotDocument(
                session_id=session_id,
                step_number=i,
                url=state.url,
                title=state.title,
                screenshot_base64=s,
                created_at=datetime.datetime.now(timezone.utc),
                agent_id=session_id,
                tabs=getattr(state, "tabs", []),
                interacted_element=getattr(state, "interacted_element", None)
            ).model_dump(by_alias=True)

            documents.append(doc)
        except Exception as screenshot_error:
            logging.warning(f"⚠️ Failed to process screenshot step {i}: {screenshot_error}")

    if documents:
        result = await collection.insert_many(documents)
        print(f"\033[1;32m✅ Stored {len(result.inserted_ids)} new screenshots to MongoDB.\033[0m")
        return {"status": "success", "new_screenshots": len(documents)}
    else:
        return {"status": "no_valid_screenshots"}


@router.post("/execute")
async def create_task(request: TaskRequest):
    """
    Endpoint to create a new task and wait for completion.
    """
    db = get_db()
    session_id = request.session_id
    task_id = str(uuid.uuid4())
    try:
        task = request.task
        if not session_id or not task:
            return {"error": "Session ID and task are required.", "message": "Invalid request."}

        session = await db.sessions.find_one({"_id": session_id})
        if not session:
            return {"error": "Session not found.", "message": "Invalid session ID."}

        # Create and store task document
        task_doc = TaskDocument(
            _id=task_id,
            name=task,
            status=TaskStatus.IN_PROGRESS,
            prompt=task,
            session_id=session_id,
            created_at=datetime.datetime.now(),
            updated_at=datetime.datetime.now(),
        )
        await db["tasks"].insert_one(task_doc.model_dump(by_alias=True))

        await db["sessions"].update_one(
            {"_id": session_id},
            {
                "$set": {
                    "status": SessionStatus.ACTIVE,
                    "updated_at": datetime.datetime.now(),
                    "is_active": True
                }
            }
        )

        display = f":{VNC_DISPLAYS[session_id]}"

        try:
            agent = None

            # Check if an agent already exists for this session
            if session_id in AGENTS:
                agent = AGENTS[session_id]
                agent.add_new_task(task)
                result = await agent.run()
                save_agent_history_to_local(agent, session_id)
            else:
                result_data = await run_task(task, session_id, display)
                result = result_data["result"]
                agent = AGENTS.get(session_id)

            # Store unique screenshots for both paths
            await store_unique_screenshots(agent, session_id, db)

            # Mark session completed
            await db["sessions"].update_one(
                {"_id": session_id},
                {
                    "$set": {
                        "status": SessionStatus.ACTIVE,
                        "updated_at": datetime.datetime.now(),
                        "is_active": True,
                        "agent_id": agent.state.agent_id if hasattr(agent, 'state') else None
                    }
                }
            )

            last_item: AgentHistory = result.history[-1] if result.history else None

            if last_item and last_item.result:
                status_flag: bool = last_item.result[0].is_done
                success_flag: bool = last_item.result[0].success
                model_output = last_item.model_output
                result_send = last_item.result
                metadata = last_item.metadata
            else:
                status_flag = success_flag = False
                model_output = None
                result_send = []
                metadata = {}

            await db["tasks"].update_one(
                {"_id": task_id},
                {
                    "$set": {
                        "status": TaskStatus.COMPLETED,
                        "updated_at": datetime.datetime.now(),
                        "result": result_send[0].extracted_content if result_send else None,
                    }
                }
            )

            return {
                "status": "completed" if status_flag and success_flag else "in_progress",
                "model_output": model_output,
                "session_id": session_id,
                "metadata": metadata,
                "result": result_send
            }

        except Exception as task_error:
            # Handle task failure
            await db["sessions"].update_one(
                {"_id": session_id},
                {
                    "$set": {
                        "status": SessionStatus.ACTIVE,
                        "error": str(task_error),
                        "is_active": True,
                        "updated_at": datetime.datetime.now()
                    }
                }
            )
            await db["tasks"].update_one(
                {"_id": task_id},
                {
                    "$set": {
                        "status": TaskStatus.ERROR,
                        "updated_at": datetime.datetime.now(),
                        "error": str(task_error)
                    }
                }
            )

            return {
                "status": "error",
                "message": "Task failed",
                "error": str(task_error),
                "session_id": session_id,
                "vnc_url": f"{os.getenv('BASE_URL', 'http://localhost')}:{VNC_PORTS[session_id]}/vnc.html"
            }

    except Exception as e:
        # Critical error
        await db["tasks"].update_one(
            {"_id": task_id},
            {
                "$set": {
                    "status": TaskStatus.ERROR,
                    "updated_at": datetime.datetime.now(),
                    "error": str(e)
                }
            }
        )
        raise HTTPException(status_code=500, detail=str(e))