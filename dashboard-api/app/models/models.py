from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text, JSON
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from ..utils.database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(UUID(as_uuid=True), primary_key=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    role = Column(String, default="user")
    created_at = Column(DateTime)

class AgentSession(Base):
    __tablename__ = "agent_sessions"
    session_id = Column(String, primary_key=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    session_name = Column(String, nullable=True)
    created_at = Column(DateTime)

class AgentMessage(Base):
    __tablename__ = "agent_messages"
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String, ForeignKey("agent_sessions.session_id"))
    role = Column(String, nullable=False)
    content = Column(Text)
    created_at = Column(DateTime)

class TurnUsage(Base):
    __tablename__ = "turn_usage"
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String, ForeignKey("agent_sessions.session_id"))
    total_tokens = Column(Integer, default=0)
    created_at = Column(DateTime)
