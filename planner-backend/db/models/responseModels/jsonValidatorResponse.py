from typing import Optional
from pydantic import BaseModel, Field
from db.models.dbmodels.utility.httpResponseEnum import HttpResponseEnum

class JsonValidatorResponse(BaseModel):
    is_valid: bool = Field(..., description="Indicates if the JSON data is valid")
    http_status: HttpResponseEnum = Field(..., description="The HTTP status of the response")
    error_message: Optional[str] = Field(None, description="Error message if any")