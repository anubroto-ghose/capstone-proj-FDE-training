from agents import Agent
from ..tools.hybrid_search_tool import hybrid_search_tool
from ..tools.filtered_search_tool import filtered_search_tool
from ..tools.validate_resolution_tool import validate_resolution_tool
from ..tools.handoff_context_tool import share_handoff_context
from ..tools.metrics_tool import predict_resolution_time, assess_fix_accuracy
from ..prompts.l1_prompts import L1_SYSTEM_PROMPT
from .l2_agent import l2_agent

l1_agent = Agent(
    name="L1 Support Specialist",
    instructions=L1_SYSTEM_PROMPT,
    tools=[
        hybrid_search_tool, 
        filtered_search_tool, 
        validate_resolution_tool, 
        share_handoff_context,
        predict_resolution_time,
        assess_fix_accuracy
    ],
    handoffs=[l2_agent],
    model="gpt-4o-mini"
)
