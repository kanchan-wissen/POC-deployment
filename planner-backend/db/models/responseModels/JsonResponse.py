from typing import Optional

from pydantic import BaseModel, Field

from db.models.dbmodels.utility.httpResponseEnum import HttpResponseEnum
class JsonResponse(BaseModel):
    json_data: dict = Field(..., description="The JSON data to be returned")
    http_status: HttpResponseEnum = Field(..., description="The HTTP status of the response")
    error_message: Optional[str] = Field(None, description="Error message if any")