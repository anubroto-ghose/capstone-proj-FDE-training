from contextvars import ContextVar
from typing import Optional


_current_session_id: ContextVar[Optional[str]] = ContextVar("current_session_id", default=None)


def set_current_session_id(session_id: str):
    return _current_session_id.set(session_id)


def get_current_session_id() -> Optional[str]:
    return _current_session_id.get()


def reset_current_session_id(token) -> None:
    _current_session_id.reset(token)

