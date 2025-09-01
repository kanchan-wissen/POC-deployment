from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum

class RequestStatus(str, Enum):
    """Enumeration for request statuses."""
    CREATED = "created"
    VALIDATED = "validated"
    PROCESSING = "processing"
    IN_PROGRESS = "in_progress"
    ACTION_NEEDED = "action_needed"
    USER_ACTION_REQUIRED = "user_action_required"
    COMPLETED = "completed"
    SUCCEEDED = "succeeded"
    FAILED = "failed"

class RequestProgress(BaseModel):
    requestId: str = Field(..., description="Unique identifier for the request")
    status: RequestStatus = Field(..., description="Current status of the request")
    lastUpdatedAt: datetime = Field(..., description="Timestamp when the request was last updated")
    remarks: Optional[str] = Field(None, description="Remarks or comments related to the request")  
    
    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }
