def generate_default_session_name(user_message: str) -> str:
    text = (user_message or "").strip()
    # Keep it readable: collapse whitespace and remove symbol-only noise.
    text = " ".join(text.split())
    cleaned = "".join(ch for ch in text if ch.isalnum() or ch.isspace()).strip()
    if not cleaned:
        return "Untitled Session"
    return cleaned[:20]


def build_static_max_turns_fallback(user_message: str) -> str:
    return (
        "I could not complete the full multi-agent workflow within the turn limit, "
        "but here is an immediate triage plan you can execute now:\n\n"
        "1. Check application and database latency/error metrics for the same time window.\n"
        "2. Verify CPU, memory, thread pool, and DB connection pool saturation.\n"
        "3. Review recent deploy/config changes and rollback suspicious changes if needed.\n"
        "4. Inspect network path health (timeouts, packet drops, DNS, gateway errors).\n"
        "5. Collect top related incident IDs and compare closure codes for proven fixes.\n\n"
        f"Original query: \"{user_message.strip()}\"\n\n"
        "If you resend with a narrower scope (for example: only DB timeout or only network timeout), "
        "I can provide a more targeted resolution."
    )

