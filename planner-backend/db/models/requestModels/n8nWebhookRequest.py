import json
from pydantic import BaseModel, Field

class n8nWebhookRequest(BaseModel):
    payerId: str = Field(..., description="The ID of the payer")
    task: str = Field(..., description="The task to be performed")
    requestId: str = Field(..., description="The ID of the request")
    json_data: dict = Field(..., description="The JSON data to be processed")
    userId :str = Field(..., description="The ID of the user making the request")
    patientId: str = Field(..., description="The ID of the patient associated with the request")
    patientName: str = Field(..., description="The name of the patient associated with the request")