from sqlalchemy import Column, String, Integer, DateTime, Boolean, Text
from sqlalchemy.sql import func
from ..utils.database import Base

class IncidentFeedback(Base):
    """
    Stores user feedback on agent responses to drive the feedback loop.
    Each row corresponds to one message/response pair in a session.
    """
    __tablename__ = "incident_feedback"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String, nullable=False, index=True)
    message_id = Column(Integer, nullable=True)          # FK to agent_messages.id (optional)
    helpful = Column(Boolean, nullable=False)             # True = thumbs up, False = thumbs down
    comment = Column(Text, nullable=True)                 # Optional free-text comment
    agent_tier = Column(String, nullable=True)            # 'L1', 'L2', 'L3'
    incident_category = Column(String, nullable=True)    # category tag for aggregation
    created_at = Column(DateTime, server_default=func.now())
