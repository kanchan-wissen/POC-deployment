from pydantic import BaseModel, Field

class ValidationRequest(BaseModel):
    payer_id: str = Field(..., description="The ID of the payer")
    request_id: str = Field(..., description="The ID of the request")