from agents import function_tool
from langsmith import traceable
from ..services.a2a_context import a2a_store
from ..utils.logger import logger

@traceable(run_type="tool", name="share_handoff_context", project_name="IT-Incident-Assistant")
async def _share_context_impl(session_id: str, to_agent: str, context_type: str, content: str) -> str:
    await a2a_store.post_context(
        session_id=session_id,
        from_agent="Current Agent",
        to_agent=to_agent,
        context_type=context_type,
        content=content
    )
    logger.info(f"A2A context shared: {context_type} for {to_agent} in session {session_id}")
    return "Context shared successfully."

@traceable(run_type="tool", name="get_shared_context", project_name="IT-Incident-Assistant")
async def _get_context_impl(session_id: str, agent_name: str) -> list:
    return await a2a_store.get_context(session_id=session_id, to_agent=agent_name)

@function_tool
async def share_handoff_context(session_id: str, to_agent: str, context_type: str, content: str) -> str:
    """
    Share structured context or findings with another agent during a handoff.
    This enables A2A (Agent-to-Agent) communication and knowledge sharing.
    
    Args:
        session_id: The current chat session ID.
        to_agent: The name of the agent you are handing off to (e.g. 'L2 Technical Specialist').
        context_type: The type of information (e.g. 'triage_summary', 'initial_diagnosis').
        content: The detailed information to share.
    """
    return await _share_context_impl(session_id, to_agent, context_type, content)

@function_tool
async def get_shared_context(session_id: str, agent_name: str) -> list:
    """
    Retrieve any context shared by previous agents for this session.
    Use this at the start of your turn if you were handed a complex ticket.
    """
    return await _get_context_impl(session_id, agent_name)
