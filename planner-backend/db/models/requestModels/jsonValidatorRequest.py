from pydantic import BaseModel, Field

class JsonValidatorRequest(BaseModel):
    json_data : dict = Field(..., description="The JSON dict to be validated")