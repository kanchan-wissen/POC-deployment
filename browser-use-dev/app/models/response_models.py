
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from app.models.db_models import TaskDocument, SessionStatus

class SessionResponse(BaseModel):
    session_id: str = Field(..., alias="_id")
    workflow_id: Optional[str] = None
    agent_id: Optional[str] = None
    user_id: Optional[str] = None
    task: List[TaskDocument] = Field(default_factory=list)
    status: SessionStatus
    is_active: bool = False
    vnc_url: Optional[str] = None
    last_error: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        allow_population_by_field_name = True
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }
