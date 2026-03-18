from langsmith import traceable
from .telemetry import traced_async_client


@traceable(run_type="llm", name="max_turns_fallback_llm", project_name="IT-Incident-Assistant")
async def generate_max_turns_fallback(user_message: str) -> str:
    prompt = f"""You are an IT support fallback assistant.
The primary multi-agent workflow exceeded its turn limit.

User query:
{user_message}

Generate a concise, practical response that includes:
1) A brief explanation that the system hit an internal turn limit.
2) An immediate triage checklist (3-5 action items).
3) A request to retry with a narrowed scope.

Keep it under 180 words. Use plain text with numbered steps.
"""

    response = await traced_async_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
    )
    content = response.choices[0].message.content or ""
    return content.strip()

