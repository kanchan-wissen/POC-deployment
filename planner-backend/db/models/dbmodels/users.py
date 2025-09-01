from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum
class Status(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
   
class UserRole(str, Enum):
    ADMIN = "admin"
    USER = "operator"

class User(BaseModel):
    id: str = Field(..., description="Unique identifier for the user")
    firstName: str = Field(..., description="First name of the user")
    middleName: Optional[str] = Field(None, description="Middle name of the user, if any")
    lastName: str = Field(..., description="Last name of the user")
    userName: str = Field(..., description="Username for the user")
    emailId: str = Field(..., description="Email address of the user")
    password: str = Field(..., description="Password for the user account")
    status: Status = Field(..., description="Status of the user account")
    createdBy: str = Field(..., description="User who created this account")
    createdAt: datetime = Field(..., description="Timestamp when the account was created")
    updatedBy: str = Field(..., description="User who last updated this account")
    lastUpdatedAt: datetime = Field(..., description="Timestamp when the account was last updated")
    role: UserRole = Field(..., description="Role of the user in the system")