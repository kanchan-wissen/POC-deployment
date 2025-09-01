from pydantic import BaseModel, Field
from typing import Optional, List, Any
from datetime import datetime
from enum import Enum

class TaskStatus(str, Enum):
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ERROR = "error"

class SessionStatus(str, Enum):
    ACTIVE = "active"
    DELETED = "deleted"
    INITIALIZING = "initializing"  # Fixed typo: was "INTIALIZING"


class TaskDocument(BaseModel):
    task_id: str = Field(..., alias="_id")
    name: str
    status: TaskStatus
    prompt: str
    result: Optional[str] = None  # Made optional since it might not exist initially
    session_id: str
    created_at: Optional[datetime] = Field(default_factory=datetime.now)
    updated_at: Optional[datetime] = Field(default_factory=datetime.now)

    class Config:
        allow_population_by_field_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        arbitrary_types_allowed = True


class SessionDocument(BaseModel):
    session_id: str = Field(..., alias="_id")
    workflow_id: Optional[str] = None
    agent_id: Optional[str] = None  # Made optional since it might not be set initially
    user_id: Optional[str] = None
    task: List[TaskDocument] = Field(default_factory=list)
    status: SessionStatus = SessionStatus.INITIALIZING  # Fixed typo
    is_active: bool = False  # Added default value
    vnc_url: Optional[str] = None  # Made optional since it might not be set initially
    last_error: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }


class ScreenshotDocument(BaseModel):
     # Added optional ID field
    session_id: str
    step_number: int
    url: str
    title: str
    screenshot_base64: str
    created_at: datetime = Field(default_factory=datetime.now)
    agent_id: str
    tabs: Optional[List[Any]] = Field(default_factory=list)
    interacted_element: Optional[Any] = None

    class Config:
        allow_population_by_field_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        arbitrary_types_allowed = True