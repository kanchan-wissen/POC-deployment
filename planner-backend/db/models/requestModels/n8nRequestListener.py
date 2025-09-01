from typing import Optional

from pydantic import BaseModel

class N8nRequestListener(BaseModel):
    requestId: str
    payerId: str
    error: Optional[str]
    message: Optional[str]