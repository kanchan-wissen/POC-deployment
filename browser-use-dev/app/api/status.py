import datetime
import os
import logging
from fastapi import APIRouter
from app.db.mongo import get_db
from app.services.browser_manager import USER_DATA_DIR_BASE

from app.models.db_models import SessionStatus
from app.services.browser_manager import AGENTS, get_status, SESSION_PAGES, BROWSERS, CONTEXTS
from app.utility.display_allocation import USED_PORTS, VNC_PORTS, VNC_DISPLAYS, USED_DISPLAY
import shutil
router = APIRouter(prefix="/sessions/{session_id}/agent", tags=["Agent"])

@router.get("/status")
async def get_agent_status(session_id: str):
    """
    Endpoint to retrieve the status of the agent.
    """

    try:
        agent = AGENTS.get(session_id)
        if agent:
            status = get_status(session_id=session_id)
            return {"status": status}
        else:
            return {"error": "Agent not found.", "message": "Invalid session ID."}
    except Exception as e:
        return {"error": str(e), "message": "Failed to retrieve agent status."}


@router.get("/stop")
async def stop_agent(session_id: str):
    """
    Endpoint to stop the agent and clean up all resources.
    """
    db = get_db()
    try:
        agent = AGENTS.get(session_id)
        if agent:
            page = SESSION_PAGES.pop(session_id, None)
            if page:
                await page.close()
            context = CONTEXTS.pop(session_id, None)
            if context:
                await context.close()
            browser = BROWSERS.pop(session_id, None)
            if browser:
                await browser.close()
            web_port = VNC_PORTS.pop(session_id, None)
            display_num = VNC_DISPLAYS.pop(session_id, None)
            if web_port:
                USED_PORTS.discard(web_port)
            if display_num:
                USED_DISPLAY.discard(display_num)
                from app.utility.display_allocation import cleanup_session_processes
                cleanup_session_processes(display_num)
            profile_dir = os.path.join(USER_DATA_DIR_BASE, session_id)
            if os.path.exists(profile_dir):
                shutil.rmtree(profile_dir)
                logging.info(f"Deleted browser profile directory: {profile_dir}")

            await db["sessions"].update_one(
                {"_id": session_id},
                {
                    "$set": {
                        "status": SessionStatus.DELETED,
                        "is_active": False,
                        "updated_at": datetime.datetime.now()
                    }
                }
            )
            agent.stop()
            AGENTS.pop(session_id, None)
            return {"status": "stopped"}
        else:
            return {"error": "Agent not found.", "message": "Invalid session ID."}
    except Exception as e:
        return {"error": str(e), "message": "Failed to stop the agent."}
@router.get("/pause")
async def pause_agent(session_id: str):
    """
    Endpoint to pause the agent.
    """
    db = get_db()
    try:
        agent = AGENTS.get(session_id)
        if agent:
            agent.pause()
            await db["sessions"].update_one(
                {"_id": session_id},
                {
                    "$set": {
                        "status": SessionStatus.ACTIVE,
                        "is_active": True,

                        "updated_at": datetime.datetime.now()
                    }
                }
            )
            return {"status": "paused"}
        else:
            return {"error": "Agent not found.", "message": "Invalid session ID."}
    except Exception as e:
        return {"error": str(e), "message": "Failed to pause the agent."}


@router.get("/resume")
async def resume_agent(session_id: str):
    """
    Endpoint to resume the agent.
    """
    db = get_db()
    try:
        agent = AGENTS.get(session_id)
        if agent:
            try:
                agent.resume()
            except AttributeError as e:
                if "_init" not in str(e):
                    raise
            await db["sessions"].update_one(
                {"_id": session_id},
                {
                    "$set": {
                        "status": SessionStatus.ACTIVE,
                        "is_active": True,

                        "updated_at": datetime.datetime.now()
                    }
                }
            )
            return {"status": "running"}
        else:
            return {"error": "Agent not found.", "message": "Invalid session ID."}
    except Exception as e:
        return {"error": str(e), "message": "Failed to resume the agent."}
