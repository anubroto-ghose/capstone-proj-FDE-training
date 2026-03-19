# A2A (Agent-to-Agent) context sharing
# Durable PostgreSQL-backed implementation.

from typing import Any, Dict, List, Optional
import json
from sqlalchemy import select, delete, distinct
from ..utils.database import AsyncSessionLocal
from ..models.models import A2AContext, AgentSession

class A2AContextStore:
    """
    Durable A2A context store backed by PostgreSQL.
    Context remains available across service restarts and replicas.
    """
    def _serialize_content(self, content: Any) -> str:
        if isinstance(content, str):
            return content
        try:
            return json.dumps(content)
        except Exception:
            return str(content)

    def _deserialize_content(self, raw: str) -> Any:
        if not raw:
            return raw
        try:
            return json.loads(raw)
        except Exception:
            return raw

    async def post_context(
        self,
        session_id: str,
        from_agent: str,
        to_agent: str,
        context_type: str,
        content: Any,
    ) -> None:
        """
        Called by an agent to share information with another agent.
        
        Args:
            session_id: Shared session identifier.
            from_agent: Name of the sending agent (e.g. 'L1 Support Specialist').
            to_agent: Name of the target agent (e.g. 'L2 Technical Specialist').
            context_type: Semantic type of the context (e.g. 'triage_result', 'search_findings', 'rca_detail').
            content: The payload to share (string, dict, or list).
        """
        async with AsyncSessionLocal() as db:
            existing = await db.scalar(
                select(AgentSession.session_id).where(AgentSession.session_id == session_id)
            )
            if existing is None:
                db.add(AgentSession(session_id=session_id))
                await db.flush()

            row = A2AContext(
                session_id=session_id,
                from_agent=from_agent,
                to_agent=to_agent,
                context_type=context_type,
                content=self._serialize_content(content),
            )
            db.add(row)
            await db.commit()

    async def get_context(
        self,
        session_id: str,
        to_agent: Optional[str] = None,
        context_type: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Retrieves shared context entries for a given session.
        
        Args:
            session_id: Shared session identifier.
            to_agent: If provided, filter entries intended for this agent.
            context_type: If provided, filter by context type.
        
        Returns:
            List of matching context entries.
        """
        async with AsyncSessionLocal() as db:
            stmt = select(A2AContext).where(A2AContext.session_id == session_id)
            if to_agent:
                stmt = stmt.where(A2AContext.to_agent == to_agent)
            if context_type:
                stmt = stmt.where(A2AContext.context_type == context_type)
            stmt = stmt.order_by(A2AContext.id.asc())

            res = await db.execute(stmt)
            rows = res.scalars().all()

            return [
                {
                    "from_agent": r.from_agent,
                    "to_agent": r.to_agent,
                    "context_type": r.context_type,
                    "content": self._deserialize_content(r.content),
                }
                for r in rows
            ]

    async def clear_context(self, session_id: str) -> None:
        """Clears all stored context for a session (e.g. after completion)."""
        async with AsyncSessionLocal() as db:
            await db.execute(delete(A2AContext).where(A2AContext.session_id == session_id))
            await db.commit()

    async def get_all_sessions(self) -> List[str]:
        async with AsyncSessionLocal() as db:
            stmt = select(distinct(A2AContext.session_id))
            res = await db.execute(stmt)
            return [row[0] for row in res.all()]


# Singleton instance used across the application
a2a_store = A2AContextStore()
