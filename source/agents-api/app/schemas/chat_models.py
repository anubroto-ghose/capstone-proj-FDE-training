from pydantic import BaseModel, Field, field_validator
from typing import Optional

class ChatRequest(BaseModel):
    session_id: Optional[str] = None
    message: str = Field(..., min_length=2, max_length=4000)

    @field_validator("message")
    @classmethod
    def validate_message(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("message cannot be empty")
        return normalized

class ChatResponse(BaseModel):
    response: str
    session_id: str
    message_id: Optional[int] = None
    category: Optional[str] = None
    agent_tier: Optional[str] = None
