from agents import function_tool
from langsmith import traceable
from ..services.retrieval_service import retrieval_service

@traceable(run_type="tool", name="filtered_search", project_name="IT-Incident-Assistant")
async def _filtered_search_impl(query: str, priority: str, category: str, impact: str) -> list:
    return await retrieval_service.hybrid_search(
        query=query,
        priority=priority or None,
        category=category or None,
        impact=impact or None,
    )

@function_tool
async def filtered_search_tool(query: str, priority: str = "", category: str = "", impact: str = "") -> list:
    """
    Search historical incident records with optional metadata filters.
    Use this when the user specifies a priority level (e.g. 'P1', 'Critical'),
    category (e.g. 'Network', 'Database', 'Hardware'), or impact level (e.g. 'High', 'Medium').

    Leave filter fields empty to search without filtering.
    """
    return await _filtered_search_impl(query, priority, category, impact)
