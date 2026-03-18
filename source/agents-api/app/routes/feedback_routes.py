from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from ..utils.auth import get_current_user
from ..utils.database import AsyncSessionLocal
from ..models.feedback import IncidentFeedback
from ..utils.logger import logger
from sqlalchemy.future import select
from sqlalchemy import func

router = APIRouter(tags=["feedback"])


class FeedbackRequest(BaseModel):
    session_id: str
    message_id: Optional[int] = None       # ID of the agent message being rated
    helpful: bool                           # True = positive, False = negative
    comment: Optional[str] = None          # Optional free text
    agent_tier: Optional[str] = None       # e.g. "L1", "L2", "L3"
    incident_category: Optional[str] = None


class FeedbackSummary(BaseModel):
    total: int
    positive: int
    negative: int
    positive_rate: float


@router.post("/feedback", status_code=201)
async def submit_feedback(
    payload: FeedbackRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    POST /api/v1/agents/feedback

    Submit thumbs-up or thumbs-down feedback on an agent response.
    Used to drive the continuous-improvement feedback loop.
    """
    try:
        async with AsyncSessionLocal() as db:
            fb = IncidentFeedback(
                session_id=payload.session_id,
                message_id=payload.message_id,
                helpful=payload.helpful,
                comment=payload.comment,
                agent_tier=payload.agent_tier,
                incident_category=payload.incident_category,
            )
            db.add(fb)
            await db.commit()

        logger.info(
            f"Feedback received | session={payload.session_id} | "
            f"helpful={payload.helpful} | tier={payload.agent_tier}"
        )
        return {"status": "ok", "message": "Feedback recorded"}

    except Exception as e:
        logger.error(f"Feedback error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to store feedback")


@router.get("/feedback/summary", response_model=FeedbackSummary)
async def get_feedback_summary(
    session_id: Optional[str] = None,
    agent_tier: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
):
    """
    GET /api/v1/agents/feedback/summary

    Aggregated feedback stats. Filter by session or agent tier.
    """
    try:
        async with AsyncSessionLocal() as db:
            stmt = select(IncidentFeedback)
            if session_id:
                stmt = stmt.where(IncidentFeedback.session_id == session_id)
            if agent_tier:
                stmt = stmt.where(IncidentFeedback.agent_tier == agent_tier)

            res = await db.execute(stmt)
            rows = res.scalars().all()

        total = len(rows)
        positive = sum(1 for r in rows if r.helpful)
        negative = total - positive
        rate = round(positive / total, 2) if total > 0 else 0.0

        return FeedbackSummary(total=total, positive=positive, negative=negative, positive_rate=rate)

    except Exception as e:
        logger.error(f"Feedback summary error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve feedback summary")
