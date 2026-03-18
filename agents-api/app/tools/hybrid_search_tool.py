from agents import function_tool
from ..services.retrieval_service import retrieval_service

@function_tool
async def hybrid_search_tool(query: str):
    """
    Search historical incident records using a combination of keyword and semantic search.
    Returns the most relevant incidents and their resolutions.
    """
    results = await retrieval_service.hybrid_search(query)
    # Further processing here to return full text/resolutions
    return results
