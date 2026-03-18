from agents import Agent
from ..tools.hybrid_search_tool import hybrid_search_tool
from ..tools.filtered_search_tool import filtered_search_tool
from ..tools.validate_resolution_tool import validate_resolution_tool
from ..prompts.rca_prompts import RCA_SYSTEM_PROMPT

rca_agent = Agent(
    name="RCA Specialist",
    instructions=RCA_SYSTEM_PROMPT,
    tools=[hybrid_search_tool, filtered_search_tool, validate_resolution_tool],
    model="gpt-4o-mini"
)
