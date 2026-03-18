from agents import function_tool
from langsmith import traceable
import os
import json
from ..utils.telemetry import traced_client as _client

@traceable(run_type="llm", name="predict_resolution_time_llm", project_name="IT-Incident-Assistant")
def _call_predict_llm(category: str, priority: str) -> str:
    prompt = f"""As an IT operations manager, predict the resolution time for this incident.
Category: {category}
Priority: {priority}

Provide a realistic estimate in hours and a brief justification.
Respond in plain text.
"""
    response = _client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
    )
    return response.choices[0].message.content

@traceable(run_type="llm", name="assess_fix_accuracy_llm", project_name="IT-Incident-Assistant")
def _call_accuracy_llm(resolution_steps: str) -> str:
    prompt = f"""Evaluate the following proposed resolution steps for an IT incident.
Estimate the 'Fix Accuracy Score' (0-100%) based on how likely this is to be the final, successful fix.

Steps:
{resolution_steps}

Respond with just the score and a 1-sentence note.
"""
    response = _client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
    )
    return response.choices[0].message.content

@function_tool
def predict_resolution_time(category: str, priority: str) -> str:
    """
    Predicts the expected time to resolve an incident based on its category and priority.
    """
    return _call_predict_llm(category, priority)

@function_tool
def assess_fix_accuracy(resolution_steps: str) -> str:
    """
    Analyzes proposed resolution steps and predicts the likelihood of it being the final fix.
    """
    return _call_accuracy_llm(resolution_steps)
