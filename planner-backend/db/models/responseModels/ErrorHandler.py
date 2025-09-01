
from pydantic import BaseModel, Field
from db.models.dbmodels.utility.httpResponseEnum import HttpResponseEnum
class ErrorHandler(BaseModel):
    error: str = Field(..., description="error Message")
    http_status: HttpResponseEnum = Field(..., description="Http Status")
