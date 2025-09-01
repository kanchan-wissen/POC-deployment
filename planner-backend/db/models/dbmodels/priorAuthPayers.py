from enum import Enum

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class PayerStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"

class PriorAuthPayers(BaseModel):
    id: str = Field(..., description="Unique identifier for the prior authorization pair")
    name: str = Field(..., description="Name of the payer associated with the prior authorization")
    url: str = Field(..., description="URL for the payer's prior authorization portal")
    serviceAccName: str = Field(..., description="Service account name for accessing the payer's prior authorization system")
    payerStatus: PayerStatus = Field(..., description="Status of the payer's prior authorization system")
    createdBy: str = Field(..., description="User who created this prior authorization pair")
    createdAt: datetime = Field(..., description="Timestamp when the prior authorization pair was created")
    lastUpdatedBy: str = Field(..., description="User who last updated this prior authorization pair")
    lastUpdatedAt: datetime = Field(..., description="Timestamp when the prior authorization pair was last updated")
    