import json
from datetime import datetime
from typing import Dict, Any, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from db.config.connection import get_db
from db.models.dbmodels.requestProgress import RequestStatus
from db.models.dbmodels.priorAuthUserAction import priorAuthUserAction
from db.models.dbmodels.utility.httpResponseEnum import HttpResponseEnum
import uuid

router = APIRouter()

class N8NCallbackRequest(BaseModel):
    request_id: str = Field(..., description="Request ID from the original preauth request")
    status: str = Field(..., description="Status update from N8N workflow")
    action_type: Optional[str] = Field(None, description="Type of action required from user")
    message: str = Field(..., description="Message or description of the update")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata from N8N")
    screenshot_url: Optional[str] = Field(None, description="URL of screenshot if available")
    user_action_required: bool = Field(False, description="Whether user action is required")
    workflow_step: Optional[str] = Field(None, description="Current workflow step")

class N8NCallbackResponse(BaseModel):
    success: bool = Field(..., description="Whether the callback was processed successfully")
    message: str = Field(..., description="Response message")
    http_status: HttpResponseEnum

@router.post("/n8n/callback", response_model=N8NCallbackResponse)
async def n8n_callback(req: N8NCallbackRequest):
    """
    Callback endpoint for N8N to send updates back to the system.
    This endpoint handles various status updates and user action requests from N8N workflow.
    """
    db = get_db()
    
    try:
        # Map N8N status to internal request status
        status_mapping = {
            "in_progress": RequestStatus.IN_PROGRESS,
            "waiting_for_user": RequestStatus.USER_ACTION_REQUIRED,
            "completed": RequestStatus.COMPLETED,
            "failed": RequestStatus.FAILED,
            "paused": RequestStatus.USER_ACTION_REQUIRED,
            "success": RequestStatus.COMPLETED,
            "error": RequestStatus.FAILED
        }
        
        internal_status = status_mapping.get(req.status.lower(), RequestStatus.IN_PROGRESS)
        
        # Update request progress
        await db["requestProgress"].update_one(
            {"requestId": req.request_id},
            {
                "$set": {
                    "status": internal_status,
                    "lastUpdatedAt": datetime.now(),
                    "remarks": f"N8N Update: {req.message}",
                    "workflowStep": req.workflow_step,
                    "metadata": req.metadata or {}
                }
            }
        )
        
        # If user action is required, create a user action record
        if req.user_action_required and req.action_type:
            # Get the original request to find user_id
            original_request = await db["priorAuthRequest"].find_one({"requestId": req.request_id})
            if original_request:
                user_action = priorAuthUserAction(
                    id=uuid.uuid4().hex,
                    requestId=req.request_id,
                    userId=original_request["userId"],
                    actionType=req.action_type,
                    actionStatus="PENDING",
                    requestedAt=datetime.now(),
                    actionedAt=datetime.now(),
                    metadata=req.screenshot_url or json.dumps(req.metadata or {})
                )
                await db["priorAuthUserAction"].insert_one(user_action.dict())
        
        return N8NCallbackResponse(
            success=True,
            message="Callback processed successfully",
            http_status=HttpResponseEnum.OK
        )
        
    except Exception as e:
        # Update request with error status
        try:
            await db["requestProgress"].update_one(
                {"requestId": req.request_id},
                {
                    "$set": {
                        "status": RequestStatus.FAILED,
                        "lastUpdatedAt": datetime.now(),
                        "remarks": f"Callback processing error: {str(e)}"
                    }
                }
            )
        except:
            pass  # Don't fail if we can't update the status
            
        return N8NCallbackResponse(
            success=False,
            message=f"Error processing callback: {str(e)}",
            http_status=HttpResponseEnum.INTERNAL_SERVER_ERROR
        )

@router.post("/n8n/workflow-status/{request_id}")
async def update_workflow_status(request_id: str, status_data: Dict[str, Any]):
    """
    Endpoint for N8N to update workflow status with detailed information
    """ 
    db = get_db()
    
    try:
        # Update the request progress with workflow-specific data
        update_data = {
            "lastUpdatedAt": datetime.now(),
            "workflowData": status_data
        }
        
        if "status" in status_data:
            status_mapping = {
                "running": RequestStatus.IN_PROGRESS,
                "paused": RequestStatus.USER_ACTION_REQUIRED,
                "completed": RequestStatus.COMPLETED,
                "failed": RequestStatus.FAILED,
                "cancelled": RequestStatus.FAILED
            }
            update_data["status"] = status_mapping.get(status_data["status"], RequestStatus.IN_PROGRESS)
        
        if "message" in status_data:
            update_data["remarks"] = f"Workflow: {status_data['message']}"
        
        await db["requestProgress"].update_one(
            {"requestId": request_id},
            {"$set": update_data}
        )
        
        return {
            "success": True,
            "message": "Workflow status updated successfully",
            "http_status": HttpResponseEnum.OK
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/n8n/screenshot/{request_id}")
async def save_screenshot(request_id: str, screenshot_data: Dict[str, Any]):
    """
    Endpoint for N8N to save screenshot URLs or data
    """
    db = get_db()
    
    try:
        # Get the original request to find user_id
        original_request = await db["priorAuthRequest"].find_one({"requestId": request_id})
        if not original_request:
            raise HTTPException(status_code=404, detail="Request not found")
        
        # Create a user action record with screenshot metadata
        user_action = priorAuthUserAction(
            id=uuid.uuid4().hex,
            requestId=request_id,
            userId=original_request["userId"],
            actionType="SCREENSHOT_CAPTURE",
            actionStatus="COMPLETED",
            requestedAt=datetime.now(),
            actionedAt=datetime.now(),
            metadata=screenshot_data.get("screenshot_url", json.dumps(screenshot_data))
        )
        await db["priorAuthUserAction"].insert_one(user_action.dict())
        
        # Also update the request progress
        await db["requestProgress"].update_one(
            {"requestId": request_id},
            {
                "$set": {
                    "lastUpdatedAt": datetime.now(),
                    "remarks": "Screenshot captured",
                    "latestScreenshot": screenshot_data.get("screenshot_url")
                }
            }
        )
        
        return {
            "success": True,
            "message": "Screenshot saved successfully",
            "http_status": HttpResponseEnum.OK
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/n8n/workflow-info/{request_id}")
async def get_workflow_info(request_id: str):
    """
    Endpoint for N8N to get information about a specific workflow/request
    """    
    db = get_db()
    
    try:
        # Get request progress
        request_progress = await db["requestProgress"].find_one({"requestId": request_id})
        if not request_progress:
            raise HTTPException(status_code=404, detail="Request not found")
        
        # Get original request details
        original_request = await db["priorAuthRequest"].find_one({"requestId": request_id})
        
        # Get user actions
        user_actions = await db["priorAuthUserAction"].find({"requestId": request_id}).to_list(None)
        
        return {
            "request_id": request_id,
            "status": request_progress.get("status"),
            "workflow_step": request_progress.get("workflowStep"),
            "last_updated": request_progress.get("lastUpdatedAt"),
            "remarks": request_progress.get("remarks"),
            "original_request": original_request,
            "user_actions": user_actions,
            "metadata": request_progress.get("metadata", {}),
            "http_status": HttpResponseEnum.OK
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/n8n/complete/{request_id}")
async def complete_workflow(request_id: str, completion_data: Dict[str, Any]):
    """
    Endpoint for N8N to mark a workflow as completed
    """    
    db = get_db()
    
    try:
        # Update request progress to completed
        await db["requestProgress"].update_one(
            {"requestId": request_id},
            {
                "$set": {
                    "status": RequestStatus.COMPLETED,
                    "lastUpdatedAt": datetime.now(),
                    "remarks": f"Workflow completed: {completion_data.get('message', 'Success')}",
                    "completionData": completion_data,
                    "completedAt": datetime.now()
                }
            }
        )
        
        # Create a completion user action record
        original_request = await db["priorAuthRequest"].find_one({"requestId": request_id})
        if original_request:
            user_action = priorAuthUserAction(
                id=uuid.uuid4().hex,
                requestId=request_id,
                userId=original_request["userId"],
                actionType="WORKFLOW_COMPLETED",
                actionStatus="COMPLETED",
                requestedAt=datetime.now(),
                actionedAt=datetime.now(),
                metadata=json.dumps(completion_data)
            )
            await db["priorAuthUserAction"].insert_one(user_action.dict())
        
        return {
            "success": True,
            "message": "Workflow marked as completed",
            "completion_data": completion_data,
            "http_status": HttpResponseEnum.OK
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
