from fastapi import APIRouter, Depends, HTTPException
import re
from ..services.agent_session import get_session
from ..utils.auth import get_current_user
from ..utils.guardrails import guardrails
from ..utils.fallback_llm import generate_max_turns_fallback
from ..utils.chat_helpers import generate_default_session_name, build_static_max_turns_fallback
from ..utils.logger import logger
from ..utils.runtime_context import set_current_session_id, reset_current_session_id
from ..schemas.chat_models import ChatRequest, ChatResponse
from ..utils.database import AsyncSessionLocal
from ..models.models import AgentMessage
from ..services.agent_execution_service import run_agent_with_tracing
from ..services.message_service import store_assistant_message
from sqlalchemy.future import select
from agents.exceptions import MaxTurnsExceeded

router = APIRouter(tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
async def chat_with_agent(request: ChatRequest, current_user: dict = Depends(get_current_user)):
    try:
        user_id = current_user.get("user_id")
        user_email = current_user.get("email", "unknown")
        default_session_name = generate_default_session_name(request.message)

        # Get or create session
        session = await get_session(
            request.session_id,
            user_id=user_id,
            session_name=default_session_name if request.session_id is None else None
        )
        actual_session_id = session.session_id

        logger.info(f"Chat request | user={user_email} | session={actual_session_id}")

        # ── DYNAMIC AGENT LOADING: Retrieve current agent from session ──
        current_agent_name = await session.get_current_agent_name()
        
        # Import agents here to avoid circular dependencies
        from ..agents.l1_agent import l1_agent
        from ..agents.l2_agent import l2_agent
        from ..agents.rca_agent import rca_agent
        
        agent_map = {
            "L1 Support Specialist": l1_agent,
            "L2 Technical Specialist": l2_agent,
            "RCA Specialist": rca_agent
        }
        starting_agent = agent_map.get(current_agent_name, l1_agent)
        logger.info(f"Starting turn with agent: {current_agent_name}")

        # ── TOKEN OPTIMIZATION ──
        try:
            from ..utils.token_optimizer import compress_history_for_bulk_analysis
            history = await session.get_items()
            if len(history) > 10:
                compress_history_for_bulk_analysis(history)
                logger.info(f"Token optimization triggered for session {actual_session_id}")
        except Exception as opt_err:
            logger.warning(f"Token optimization failed: {opt_err}")

        # ── INPUT GUARDRAIL ──
        sanitized_input = guardrails.mask_pii(request.message)

        # Deterministic escalation fallback for explicit user consent.
        lower_msg = sanitized_input.lower()
        wants_l2 = bool(re.search(r"(hand\s*(it\s*)?over|escalat|transfer).*(l2|technical specialist)", lower_msg))
        wants_rca = bool(re.search(r"(hand\s*(it\s*)?over|escalat|transfer).*(rca|root cause)", lower_msg))
        if current_agent_name == "L1 Support Specialist" and wants_l2:
            starting_agent = l2_agent
            await session.set_current_agent_name("L2 Technical Specialist")
            logger.info(f"Explicit escalation detected | session={actual_session_id} | switched_to=L2")
        elif current_agent_name in {"L1 Support Specialist", "L2 Technical Specialist"} and wants_rca:
            starting_agent = rca_agent
            await session.set_current_agent_name("RCA Specialist")
            logger.info(f"Explicit escalation detected | session={actual_session_id} | switched_to=RCA")

        # ── Run the agent ──
        session_token = set_current_session_id(actual_session_id)
        try:
            try:
                result = await run_agent_with_tracing(sanitized_input, session, actual_session_id, starting_agent)
            except MaxTurnsExceeded:
                logger.warning(f"Max turns exceeded | session={actual_session_id}")
                try:
                    fallback_text = await generate_max_turns_fallback(request.message)
                except Exception as fallback_err:
                    logger.warning(f"Fallback LLM failed, using static fallback | error={fallback_err}")
                    fallback_text = build_static_max_turns_fallback(request.message)
                sanitized_fallback = guardrails.mask_pii(fallback_text)
                fallback_msg_id = await store_assistant_message(actual_session_id, sanitized_fallback)
                return ChatResponse(
                    response=sanitized_fallback,
                    session_id=actual_session_id,
                    message_id=fallback_msg_id,
                    category="General",
                    agent_tier="L1"
                )
        finally:
            reset_current_session_id(session_token)

        agent_output = result.final_output
        
        # Safely detect the new agent name (SDK uses last_agent)
        new_agent = getattr(result, "last_agent", starting_agent)
        new_agent_name = getattr(new_agent, "name", starting_agent.name)
        
        # Persist the new agent state if it changed
        if new_agent_name != current_agent_name:
            await session.set_current_agent_name(new_agent_name)
            logger.info(f"Handoff detected! New agent: {new_agent_name}")

        # ── OUTPUT GUARDRAIL ──
        sanitized_output = guardrails.mask_pii(agent_output)

        # ── Store usage and metadata ──
        try:
            await session.store_run_usage(result)
        except Exception as usage_err:
            logger.warning(f"Error storing usage: {usage_err}")

        assistant_msg_id = None
        category = "General"
        
        async with AsyncSessionLocal() as db:
            stmt = select(AgentMessage.id).where(
                AgentMessage.session_id == actual_session_id,
                AgentMessage.role == "assistant"
            ).order_by(AgentMessage.created_at.desc()).limit(1)
            res = await db.execute(stmt)
            assistant_msg_id = res.scalar_one_or_none()

            from ..services.a2a_context import a2a_store
            contexts = await a2a_store.get_context(actual_session_id, "L2 Technical Specialist")
            for ctx in contexts:
                if ctx.get("context_type") == "triage_summary":
                    content = ctx.get("content", "")
                    if "Category:" in content:
                        try:
                            category = content.split("Category:")[1].split("\n")[0].strip()
                        except: pass
                    break

        tier_map = {
            "L1 Support Specialist": "L1",
            "L2 Technical Specialist": "L2",
            "RCA Specialist": "RCA"
        }
        agent_tier = tier_map.get(new_agent_name, "L1")

        return ChatResponse(
            response=sanitized_output,
            session_id=actual_session_id,
            message_id=assistant_msg_id,
            category=category,
            agent_tier=agent_tier
        )
    except Exception as e:
        logger.error(f"Chat error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
