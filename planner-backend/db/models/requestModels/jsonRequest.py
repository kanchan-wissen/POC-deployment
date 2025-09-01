from pydantic import BaseModel, Field

class JsonRequest(BaseModel):
    payer_id: str = Field(..., description="The ID of the payer")
    patient_id: int = Field(..., description="The ID of the patient")