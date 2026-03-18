from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List
from ..utils.database import get_db
from ..utils.auth import get_current_user
from ..models import models
from ..schemas import schemas
from sqlalchemy import func

router = APIRouter(prefix="/api/v1/dashboard", tags=["dashboard"])

@router.get("/profile", response_model=schemas.UserProfile)
async def get_profile(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == current_user.get("email")).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.get("/sessions", response_model=List[schemas.SessionResponse])
async def list_sessions(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == current_user.get("email")).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    sessions = db.query(
        models.AgentSession.session_id, 
        models.AgentSession.session_name,
        models.AgentSession.created_at,
        func.count(models.AgentMessage.id).label("message_count")
    ).outerjoin(
        models.AgentMessage, models.AgentSession.session_id == models.AgentMessage.session_id
    ).filter(
        or_(models.AgentSession.user_id == user.id, models.AgentSession.user_id == None)
    ).group_by(
        models.AgentSession.session_id
    ).order_by(
        models.AgentSession.created_at.desc()
    ).all()
    
    return [
        schemas.SessionResponse(
            session_id=s.session_id,
            session_name=s.session_name,
            created_at=s.created_at,
            message_count=s.message_count
        )
        for s in sessions
    ]

@router.get("/sessions/{session_id}/history", response_model=schemas.ChatHistoryResponse)
async def get_chat_history(session_id: str, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == current_user.get("email")).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    # Allow access to sessions owned by the user OR unlinked sessions (legacy)
    session = db.query(models.AgentSession).filter(
        models.AgentSession.session_id == session_id,
        or_(models.AgentSession.user_id == user.id, models.AgentSession.user_id == None)
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found or inaccessible")
        
    messages = db.query(models.AgentMessage).filter(
        models.AgentMessage.session_id == session_id
    ).order_by(models.AgentMessage.id).all()
    
    return schemas.ChatHistoryResponse(
        session_id=session_id,
        messages=[schemas.MessageResponse(
            id=m.id, 
            role=m.role, 
            content=m.content, 
            created_at=m.created_at,
            category="General", # Default for history
            agent_tier="L1" if m.role == "assistant" else None
        ) for m in messages]
    )

@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == current_user.get("email")).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    session = db.query(models.AgentSession).filter(
        models.AgentSession.session_id == session_id,
        or_(models.AgentSession.user_id == user.id, models.AgentSession.user_id == None)
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found or inaccessible")
        
    # Delete associated messages first
    db.query(models.AgentMessage).filter(models.AgentMessage.session_id == session_id).delete(synchronize_session=False)
    # Delete the session itself
    db.query(models.AgentSession).filter(models.AgentSession.session_id == session_id).delete(synchronize_session=False)
    db.commit()
    
    return {"status": "success", "message": "Session deleted"}

@router.put("/sessions/{session_id}/name")
async def rename_session(
    session_id: str,
    payload: schemas.RenameSessionRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    user = db.query(models.User).filter(models.User.email == current_user.get("email")).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    session = db.query(models.AgentSession).filter(
        models.AgentSession.session_id == session_id,
        or_(models.AgentSession.user_id == user.id, models.AgentSession.user_id == None)
    ).first()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found or inaccessible")

    session_name = (payload.session_name or "").strip()
    if not session_name:
        raise HTTPException(status_code=400, detail="Session name cannot be empty")
    if len(session_name) > 120:
        raise HTTPException(status_code=400, detail="Session name too long (max 120 chars)")

    session.session_name = session_name
    db.commit()

    return {"status": "success", "session_id": session_id, "session_name": session_name}
