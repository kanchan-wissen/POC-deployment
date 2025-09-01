import datetime
import os
import uuid

from fastapi import APIRouter, HTTPException, Query

from app.core.config import SESSION_DIR
from app.db.mongo import get_db

from app.models.db_models import SessionDocument, SessionStatus
from app.models.response_models import SessionResponse
from app.utility.display_allocation import get_next_display_port, start_vnc_session, start_novnc_proxy,  VNC_PORTS, VNC_DISPLAYS

router =APIRouter()
@router.post("/")
async def create_session():
    """
    Endpoint to retrieve session information.
    """
    try:
        session_id = f"{uuid.uuid4().hex[:4]}-{uuid.uuid4().hex[:4]}-{uuid.uuid4().hex[:4]}-{uuid.uuid4().hex[:4]}"
        session_path = os.path.join(SESSION_DIR,session_id)
        os.makedirs(session_path, exist_ok=True)
        display_num,web_port = get_next_display_port()
        vnc_port = 5900 +display_num-100
        start_vnc_session(display_num,vnc_port)
        start_novnc_proxy(vnc_port,web_port)
        VNC_PORTS[session_id] = web_port
        VNC_DISPLAYS[session_id] = display_num


        vnc_url = f"{os.getenv('BASE_URL','http://localhost')}:{web_port}/vnc.html?autoconnect=1"

        now = datetime.datetime.now()
        db = get_db()
        doc = SessionDocument(
            _id=session_id,

            status=SessionStatus.INITIALIZING,
            is_active=True,
            vnc_url=vnc_url,
            created_at=now,
            updated_at=now,

        )
        await db["sessions"].insert_one(doc.model_dump(by_alias=True))



        return {"session_id": session_id, "vnc_url": vnc_url}
    except Exception as e :
        return {"error": str(e), "message": "Failed to retrieve session information."}
    
from typing import List, Dict, Any
@router.get("/")
async def get_all_sessions():
    try:
        db = get_db()
        sessions = await db["sessions"].find({}).sort("created_at", -1).to_list(length=1000)

        # Get all session IDs
        session_ids = [s["_id"] for s in sessions]

        # Get all tasks for these sessions
        tasks_by_session = {}
        cursor = db["tasks"].find({"session_id": {"$in": session_ids}})
        async for task in cursor:
            tasks_by_session.setdefault(task["session_id"], []).append(task)

        # Merge tasks into sessions
        for session in sessions:
            session["task"] = tasks_by_session.get(session["_id"], [])

        return sessions

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch sessions: {str(e)}")

@router.get("/{session_id}", response_model=SessionResponse)
async def get_session_details(session_id: str):
    try:
        db = get_db()
        session = await db["sessions"].find_one({"_id": session_id})
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        # Fetch and attach tasks
        tasks = await db["tasks"].find({"session_id": session_id}).to_list(length=1000)
        session["task"] = tasks

        return session

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch session details: {str(e)}")
