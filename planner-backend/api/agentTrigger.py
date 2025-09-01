import os
from datetime import datetime

import httpx
from fastapi import APIRouter

from db.models.dbmodels.requestProgress import RequestProgress, RequestStatus
from db.models.dbmodels.utility.httpResponseEnum import HttpResponseEnum
from db.models.requestModels.taskRequest import TaskRequest
from db.config.connection import get_db
from db.models.responseModels.ErrorHandler import ErrorHandler
from db.models.responseModels.taskResponse import  TaskReponse
import uuid

router = APIRouter()

@router.get("/planner-agent")

async def planner_agent(req:TaskRequest):
    """
    Endpoint to trigger the planner agent with a specific task.
    """
    db = await get_db()
    client = httpx.AsyncClient()
    request_id = uuid.uuid4().hex
    try:
        prompt  = req.task

        request_save =RequestProgress(
            requestId=request_id,
            status = RequestStatus.CREATED,
            lastUpdatedAt=datetime.now(),

        )
        await db.collection("requestProgress").insert_one(request_save.dict())
        await client.post(f"{os.getenv('AGENT_URL')}",json=prompt)
        return TaskReponse(
            request_id=request_id,
            http_status=HttpResponseEnum.CREATED
        )

    except Exception as e:
        request_save = RequestProgress(
            requestId=request_id,
            status=RequestStatus.FAILED,
            lastUpdatedAt=datetime.now(),
            remarks=str(e),

        )
        await db.collection("requestProgress").insert_one(request_save.dict())
        return ErrorHandler(
            http_status=HttpResponseEnum.INTERNAL_SERVER_ERROR,
            error=str(e),
        )


    