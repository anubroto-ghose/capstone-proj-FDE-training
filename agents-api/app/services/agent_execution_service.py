from agents import Runner
from langsmith import get_current_run_tree, traceable
from ..utils.telemetry import track_cost
from ..utils.logger import logger


@traceable(
    run_type="llm",  # Enables token/cost visibility in LangSmith columns
    name="agent_chat_run",
    project_name="IT-Incident-Assistant",
)
async def run_agent_with_tracing(sanitized_input: str, session, session_id: str, starting_agent, max_turns: int = 20):
    """
    Runs the OpenAI Agents workflow with LangSmith tracing and usage metadata attachment.
    """
    result = await Runner.run(
        starting_agent,
        sanitized_input,
        session=session,
        max_turns=max_turns,
    )

    total_input_tokens = 0
    total_output_tokens = 0
    for raw_resp in getattr(result, "raw_responses", []):
        usage = getattr(raw_resp, "usage", None)
        if usage:
            total_input_tokens += getattr(usage, "input_tokens", 0) or 0
            total_output_tokens += getattr(usage, "output_tokens", 0) or 0

    cost = track_cost("gpt-4o-mini", total_input_tokens, total_output_tokens)
    logger.info(
        f"Usage | session={session_id} | "
        f"in={total_input_tokens} out={total_output_tokens} | "
        f"cost=${cost:.6f}"
    )

    run = get_current_run_tree()
    if run:
        run.add_metadata({
            "ls_provider": "openai",
            "ls_model_name": "gpt-4o-mini",
            "total_tokens": total_input_tokens + total_output_tokens,
            "total_cost": cost,
        })
        run.add_outputs({
            "token_usage": {
                "total_tokens": total_input_tokens + total_output_tokens,
                "prompt_tokens": total_input_tokens,
                "completion_tokens": total_output_tokens,
            }
        })

    return result

