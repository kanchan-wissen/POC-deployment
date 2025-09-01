"""
id
requestId
userId
senderType
message
timestamp
"""
from pydantic import BaseModel, Field
from typing import Optional 
from datetime import datetime
from enum import Enum
class SenderType(str, Enum):
    """Enumeration for sender types in conversation history."""
    HUMAN = "human"
    AGENT = "agent"
class conversationStatus(str, Enum):
    OPEN = "open"
    CLOSED = "closed"
class ConversationHistory(BaseModel):
    """Model representing a conversation history entry."""
    id: str = Field(..., description="Unique identifier for the conversation history entry")
    requestId: str = Field(..., description="ID of the prior authorization request associated with this conversation")
    userId: str = Field(..., description="ID of the user involved in the conversation")
    senderType: SenderType = Field(..., description="Type of sender in the conversation (user/system/bot)")
    message: str = Field(..., description="Message content of the conversation entry")
    timestamp: datetime = Field(..., description="Timestamp when the message was sent or received")
    status: conversationStatus = Field(..., description="Current status of the conversation (open/closed)")