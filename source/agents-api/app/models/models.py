from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text, Float, JSON
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
import uuid
from ..utils.database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, default="user")
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

class AgentSession(Base):
    __tablename__ = "agent_sessions"
    session_id = Column(String, primary_key=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    session_name = Column(String, nullable=True)
    current_agent = Column(String, default="L1 Support Specialist")
    created_at = Column(DateTime, server_default=func.now())

class AgentMessage(Base):
    __tablename__ = "agent_messages"
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String, ForeignKey("agent_sessions.session_id", ondelete="CASCADE"), nullable=False)
    role = Column(String, nullable=False)
    content = Column(Text)
    created_at = Column(DateTime, server_default=func.now())

class MessageStructure(Base):
    __tablename__ = "message_structure"
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String, ForeignKey("agent_sessions.session_id", ondelete="CASCADE"), nullable=False)
    message_id = Column(Integer, ForeignKey("agent_messages.id", ondelete="CASCADE"), nullable=False)
    branch_id = Column(String, default="main")
    message_type = Column(String, nullable=False)
    sequence_number = Column(Integer, nullable=False)
    user_turn_number = Column(Integer)
    branch_turn_number = Column(Integer)
    tool_name = Column(String)
    created_at = Column(DateTime, server_default=func.now())

class TurnUsage(Base):
    __tablename__ = "turn_usage"
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String, ForeignKey("agent_sessions.session_id", ondelete="CASCADE"), nullable=False)
    branch_id = Column(String, default="main")
    user_turn_number = Column(Integer, nullable=False)
    requests = Column(Integer, default=0)
    input_tokens = Column(Integer, default=0)
    output_tokens = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)
    input_tokens_details = Column(JSONB)
    output_tokens_details = Column(JSONB)
    created_at = Column(DateTime, server_default=func.now())

class A2AContext(Base):
    __tablename__ = "a2a_context"
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String, ForeignKey("agent_sessions.session_id", ondelete="CASCADE"), nullable=False)
    from_agent = Column(String, nullable=False)
    to_agent = Column(String, nullable=False)
    context_type = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
