from app.utils.guardrails import guardrails

test_cases = [
    "The issue needs immediate attention (P1, Critical).",
    "I can hand this over to our L2 Technical Specialist.",
    "Estimated Resolution Time: Approximately 4 to 6 hours.",
    "My email is john.doe@example.com and phone is 555-0199.",
    "Incident ID: IM0024023 has been resolved via load balancing.",
    "See ticket INC0024032 for details on traffic patterns.",
    "This is an L1 Support Specialist response for a High priority incident."
]

print("--- Guardrail Test Results ---")
for case in test_cases:
    sanitized = guardrails.mask_pii(case)
    print(f"Original: {case}")
    print(f"Sanitized: {sanitized}")
    print("-" * 30)
