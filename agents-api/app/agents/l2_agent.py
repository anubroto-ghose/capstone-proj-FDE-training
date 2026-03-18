from agents import Agent
from ..tools.hybrid_search_tool import hybrid_search_tool
from ..tools.filtered_search_tool import filtered_search_tool
from ..tools.validate_resolution_tool import validate_resolution_tool
from ..tools.handoff_context_tool import share_handoff_context, get_shared_context
from ..tools.metrics_tool import predict_resolution_time, assess_fix_accuracy
from ..prompts.l2_prompts import L2_SYSTEM_PROMPT
from .rca_agent import rca_agent

l2_agent = Agent(
    name="L2 Technical Specialist",
    instructions=L2_SYSTEM_PROMPT,
    tools=[
        hybrid_search_tool, 
        filtered_search_tool, 
        validate_resolution_tool, 
        share_handoff_context, 
        get_shared_context,
        predict_resolution_time,
        assess_fix_accuracy
    ],
    handoffs=[rca_agent],
    model="gpt-4o-mini"
)
