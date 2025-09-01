from pydantic import BaseModel, Field

class TaskRequest(BaseModel):
    task : str = Field(..., description="The task to be performed")

    