from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class priorAuthUserAction(BaseModel):
    id: str = Field(..., description="Unique identifier for the prior authorization user action")
    requestId: str = Field(..., description="ID of the prior authorization request associated with this action")
    userId: str = Field(..., description="ID of the user performing the action")
    actionType: str = Field(..., description="Type of action performed by the user")
    actionStatus: str = Field(..., description="Status of the action performed by the user")
    requestedAt: datetime = Field(..., description="Timestamp when the action was requested")
    actionedAt: datetime = Field(..., description="Timestamp when the action was performed")
    metadata: str = Field(None, description="url of the screenshot stored in the blob storages")