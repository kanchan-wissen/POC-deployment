from pydantic import BaseModel
from typing import Optional

class TaskRequest(BaseModel):
    task: str
    session_id: Optional[str] = None

class SessionStatusRequest(BaseModel):
    session_id: str
