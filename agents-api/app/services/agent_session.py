from typing import Any, List, Dict, Optional
from agents.extensions.memory import SQLAlchemySession
from ..models.models import AgentSession, AgentMessage, MessageStructure, TurnUsage
from sqlalchemy.future import select
from ..utils.database import AsyncSessionLocal, engine
import logging

class PostgresAdvancedSession(SQLAlchemySession):
    """
    Extensions to SQLAlchemySession to support the 'Advanced' schema 
    (message_structure, turn_usage) provided in setup/postgres_sql_setup.py.
    """
    def __init__(self, session_id: str, **kwargs):
        # SQLAlchemySession requires an AsyncEngine.
        super().__init__(session_id=session_id, engine=engine, **kwargs)
        self.logger = logging.getLogger("PostgresAdvancedSession")

    async def add_items(self, items: List[Dict[str, Any]]) -> None:
        """
        Overrides the base add_items to map to the user's AgentMessage table
        (role, content) instead of the default SDK schema (message_data).
        Handles the SDK's complex content formats (lists of content blocks).
        """
        if not items:
            return
        
        import json
        
        async with AsyncSessionLocal() as db:
            for item in items:
                role = item.get("role", "user")
                raw_content = item.get("content", "")
                
                # The SDK sends assistant content as a list of content blocks
                # e.g. [{'text': '...', 'type': 'output_text'}]
                # We need to extract the text
                if isinstance(raw_content, list):
                    text_parts = []
                    for block in raw_content:
                        if isinstance(block, dict) and "text" in block:
                            text_parts.append(block["text"])
                        elif isinstance(block, str):
                            text_parts.append(block)
                    content = "\n".join(text_parts)
                elif isinstance(raw_content, dict):
                    content = raw_content.get("text", json.dumps(raw_content))
                else:
                    content = str(raw_content) if raw_content else ""
                
                # Skip empty messages (e.g. tool call placeholders)
                if not content.strip():
                    continue
                
                msg = AgentMessage(
                    session_id=self.session_id,
                    role=role,
                    content=content
                )
                db.add(msg)
            await db.commit()

    async def get_items(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Overrides the base get_items to retrieve message history from 
        the user's AgentMessage table.
        """
        async with AsyncSessionLocal() as db:
            stmt = select(AgentMessage).where(AgentMessage.session_id == self.session_id).order_by(AgentMessage.created_at.asc())
            if limit:
                stmt = stmt.limit(limit)
            
            res = await db.execute(stmt)
            messages = res.scalars().all()
            
            return [{"role": m.role, "content": m.content} for m in messages]

    # In a real implementation with the SDK, we would override methods like 
    # store_run_usage and add_message to populate the advanced tables.
    # For the purpose of this demo, we'll implement the logic that matches the user's setup.

    async def store_run_usage(self, result: Any):
        """
        Extracts token usage from the SDK's RunResult.raw_responses
        and inserts a row into the turn_usage table.
        """
        try:
            total_input = 0
            total_output = 0
            request_count = 0
            
            # Additional dicts for detailed breakdowns (JSONB columns)
            input_details = {}
            output_details = {}

            for raw_resp in getattr(result, "raw_responses", []):
                usage = getattr(raw_resp, "usage", None)
                if usage:
                    total_input += getattr(usage, "input_tokens", getattr(usage, "prompt_tokens", 0)) or 0
                    total_output += getattr(usage, "output_tokens", getattr(usage, "completion_tokens", 0)) or 0
                    
                    # Extract advanced details from OpenAI usage if available
                    if hasattr(usage, "prompt_tokens_details") and usage.prompt_tokens_details:
                        try:
                            input_details = usage.prompt_tokens_details.model_dump()
                        except:
                            input_details = usage.prompt_tokens_details.__dict__
                    
                    if hasattr(usage, "completion_tokens_details") and usage.completion_tokens_details:
                        try:
                            output_details = usage.completion_tokens_details.model_dump()
                        except:
                            output_details = usage.completion_tokens_details.__dict__

                    request_count += 1

            if request_count == 0:
                self.logger.info(f"No usage data in result for session {self.session_id}")
                return

            # Determine the current turn number from message count
            async with AsyncSessionLocal() as db:
                stmt = select(AgentMessage).where(
                    AgentMessage.session_id == self.session_id,
                    AgentMessage.role == "user"
                )
                res = await db.execute(stmt)
                turn_number = len(res.scalars().all())

                usage_row = TurnUsage(
                    session_id=self.session_id,
                    branch_id="main",
                    user_turn_number=turn_number,
                    requests=request_count,
                    input_tokens=total_input,
                    output_tokens=total_output,
                    total_tokens=total_input + total_output,
                    input_tokens_details=input_details if input_details else None,
                    output_tokens_details=output_details if output_details else None,
                )
                db.add(usage_row)
                await db.commit()

            self.logger.info(
                f"Usage stored | session={self.session_id} | turn={turn_number} | "
                f"in={total_input} out={total_output} total={total_input + total_output}"
            )
        except Exception as e:
            self.logger.warning(f"Failed to store usage for session {self.session_id}: {e}")

    async def track_message_structure(self, message_id: int, message_type: str, seq: int, turn: int):
        """
        Tracks the specific structure of a message (tool usage, sequence, etc.)
        """
        async with AsyncSessionLocal() as db:
            struct = MessageStructure(
                session_id=self.session_id,
                message_id=message_id,
                message_type=message_type,
                sequence_number=seq,
                user_turn_number=turn
            )
            db.add(struct)
            await db.commit()

    async def get_current_agent_name(self) -> str:
        """
        Retrieves the name of the currently active agent for this session.
        """
        async with AsyncSessionLocal() as db:
            stmt = select(AgentSession.current_agent).where(AgentSession.session_id == self.session_id)
            res = await db.execute(stmt)
            return res.scalar_one_or_none() or "L1 Support Specialist"

    async def set_current_agent_name(self, agent_name: str) -> None:
        """
        Updates the currently active agent for this session.
        """
        async with AsyncSessionLocal() as db:
            stmt = select(AgentSession).where(AgentSession.session_id == self.session_id)
            res = await db.execute(stmt)
            session = res.scalar_one_or_none()
            if session:
                session.current_agent = agent_name
                await db.commit()

    async def get_session_name(self) -> Optional[str]:
        async with AsyncSessionLocal() as db:
            stmt = select(AgentSession.session_name).where(AgentSession.session_id == self.session_id)
            res = await db.execute(stmt)
            return res.scalar_one_or_none()

    async def set_session_name(self, session_name: str) -> None:
        async with AsyncSessionLocal() as db:
            stmt = select(AgentSession).where(AgentSession.session_id == self.session_id)
            res = await db.execute(stmt)
            session = res.scalar_one_or_none()
            if session:
                session.session_name = session_name
                await db.commit()

import uuid

# Factory function to create or retrieve a session
async def get_session(
    session_id: Optional[str] = None,
    user_id: Optional[str] = None,
    session_name: Optional[str] = None
) -> PostgresAdvancedSession:
    if not session_id:
        session_id = str(uuid.uuid4())
        
    # Logic to ensure session exists in agent_sessions table
    async with AsyncSessionLocal() as db:
        stmt = select(AgentSession).where(AgentSession.session_id == session_id)
        res = await db.execute(stmt)
        existing = res.scalar_one_or_none()
        if not existing:
            new_session = AgentSession(session_id=session_id, user_id=user_id, session_name=session_name)
            db.add(new_session)
            await db.commit()
        elif existing and user_id and not existing.user_id:
            # Link an existing unowned session to this user
            existing.user_id = user_id
            await db.commit()
        elif existing and session_name and not existing.session_name:
            existing.session_name = session_name
            await db.commit()
    
    return PostgresAdvancedSession(session_id=session_id)
