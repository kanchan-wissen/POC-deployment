from pydantic import BaseModel, Field
from typing import Optional, Any, Dict

class CustomerInquiryRequest(BaseModel):
    customer_inquiry: Dict

class PreAuthRequest(BaseModel):
    requestId: str = Field(..., description="ID of the pre-authorization request")
    # payerId: str = Field(..., description="ID of the payer")
    jsonData: Dict[str, Any] = Field(..., description="JSON data to validate")


class PreAuthResponse(BaseModel):
    req_id: str
    status: str
    message: str