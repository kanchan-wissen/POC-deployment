from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from app.db.mongo import get_db
import logging

router = APIRouter()


@router.get("/{session_id}")
async def get_session_screenshots(
        session_id: str,
        step_number: Optional[int] = Query(None, description="Get specific step screenshot"),
        limit: Optional[int] = Query(None, description="Limit number of screenshots"),
        skip: Optional[int] = Query(0, description="Skip number of screenshots")
) -> List[dict]:
    """Get screenshots for a session."""
    try:
        db = get_db()
        collection = db.screenshots

        # Build query
        query = {"session_id": session_id}
        if step_number is not None:
            query["step_number"] = step_number

        # Build cursor with sorting
        cursor = collection.find(query, {"_id": 0}).sort("step_number", 1)

        # Apply skip and limit
        if skip:
            cursor = cursor.skip(skip)
        if limit:
            cursor = cursor.limit(limit)

        # Convert async cursor to list
        screenshots = await cursor.to_list(length=None)
        return screenshots

    except Exception as e:
        logging.error(f"Failed to retrieve screenshots for session {session_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve screenshots: {str(e)}")


@router.get("/{session_id}/count")
async def get_session_screenshots_count(session_id: str) -> dict:
    """Get count of screenshots for a session."""
    try:
        db = get_db()
        collection = db.screenshots
        count = await collection.count_documents({"session_id": session_id})
        return {"session_id": session_id, "screenshot_count": count}

    except Exception as e:
        logging.error(f"Failed to get screenshot count for session {session_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get screenshot count: {str(e)}")

