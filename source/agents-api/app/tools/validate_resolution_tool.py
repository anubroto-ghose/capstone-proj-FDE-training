from ..utils.telemetry import traced_client as _client
from langsmith import traceable
from agents import function_tool

@traceable(run_type="llm", name="llm_as_judge_validation", project_name="IT-Incident-Assistant")
def _call_judge_llm(judge_prompt: str) -> str:
    """Inner function traced as an LLM call so tokens and cost appear in LangSmith."""
    response = _client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": judge_prompt}],
        response_format={"type": "json_object"},
        temperature=0.1,
    )
    return response.choices[0].message.content

@function_tool
async def validate_resolution_tool(incident_description: str, proposed_resolution: str) -> str:
    """
    LLM-as-judge: Evaluates whether a proposed resolution is appropriate, complete,
    and safe for the given IT incident. Returns a structured verdict with score and reasoning.
    
    Use this tool BEFORE presenting a final resolution to the user to validate its quality.
    """
    judge_prompt = f"""You are an expert IT operations judge. Your task is to rigorously evaluate if the proposed resolution is:
1. Technically accurate and correct for the described incident
2. Complete (does not omit critical steps)
3. Safe (does not introduce security or stability risks)
4. Clear and actionable for an IT technician

Incident Description:
{incident_description}

Proposed Resolution:
{proposed_resolution}

Important constraints:
- Be concise and practical.
- Do NOT restate the whole incident.
- Keep total response short (under 90 words).

Respond with a JSON object using exactly this schema:
{{
  "verdict": "APPROVED" | "NEEDS_IMPROVEMENT" | "REJECTED",
  "confidence_score": <0.0 to 1.0>,
  "summary": "<max 22 words>",
  "top_gaps": ["<max 10 words>", "<max 10 words>"],
  "suggested_fix": "<max 18 words or 'None'>"
}}
"""
    return _call_judge_llm(judge_prompt)
