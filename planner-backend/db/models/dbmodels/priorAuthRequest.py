from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class priorAuthRequest(BaseModel):
    requestId: str = Field(..., description="Unique identifier for the prior authorization request")
    userId: str = Field(..., description="ID of the user making the request")
    patientId: str = Field(..., description="ID of the patient for whom the request is made")
    patientName: str = Field(..., description="Name of the patient")
    payerId: str = Field(..., description="ID of the payer associated with the request")
    createdAt: datetime = Field(..., description="Timestamp when the request was created")
    lastUpdatedAt: datetime = Field(..., description="Timestamp when the request was last updated")