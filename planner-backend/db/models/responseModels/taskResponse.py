from pydantic import BaseModel, Field,Optional
from dbmodels.utility import httpResponseEnum
class TaskReponse(BaseModel):
    request_id: str = Field(..., description="The ID of the request")
    http_status: httpResponseEnum = Field(..., description="The HTTP status of the response")
    error_message:Optional[str] = Field(None, description="Error message if any")