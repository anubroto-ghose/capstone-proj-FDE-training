from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from uuid import UUID

class UserProfile(BaseModel):
    id: UUID
    first_name: str
    last_name: str
    email: str
    role: str

class SessionResponse(BaseModel):
    session_id: str
    session_name: Optional[str] = None
    created_at: datetime
    message_count: int

class RenameSessionRequest(BaseModel):
    session_name: str

class MessageResponse(BaseModel):
    id: int
    role: str
    content: Optional[str] = None
    created_at: datetime
    category: Optional[str] = None
    agent_tier: Optional[str] = None

class ChatHistoryResponse(BaseModel):
    session_id: str
    messages: List[MessageResponse]
