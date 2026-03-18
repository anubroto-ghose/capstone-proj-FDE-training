from typing import Optional
from ..utils.database import AsyncSessionLocal
from ..models.models import AgentMessage


async def store_assistant_message(session_id: str, content: str) -> Optional[int]:
    async with AsyncSessionLocal() as db:
        msg = AgentMessage(session_id=session_id, role="assistant", content=content)
        db.add(msg)
        await db.commit()
        await db.refresh(msg)
        return msg.id

