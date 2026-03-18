import pytest
from types import SimpleNamespace
from app.routes import dashboard_routes


class FakeQuery:
    def __init__(self, first_result=None, all_result=None):
        self._first = first_result
        self._all = all_result or []

    def filter(self, *args, **kwargs):
        return self

    def outerjoin(self, *args, **kwargs):
        return self

    def group_by(self, *args, **kwargs):
        return self

    def order_by(self, *args, **kwargs):
        return self

    def first(self):
        return self._first

    def all(self):
        return self._all


class FakeDB:
    def __init__(self, queries):
        self._queries = list(queries)

    def query(self, *args, **kwargs):
        if not self._queries:
            raise RuntimeError("No fake query configured for this call")
        return self._queries.pop(0)


@pytest.mark.asyncio
async def test_get_profile_success():
    user = SimpleNamespace(
        id="u-1",
        first_name="Jane",
        last_name="Doe",
        email="jane@example.com",
        role="user",
    )
    db = FakeDB([FakeQuery(first_result=user)])

    result = await dashboard_routes.get_profile(
        current_user={"email": "jane@example.com"},
        db=db,
    )
    assert result.email == "jane@example.com"


@pytest.mark.asyncio
async def test_list_sessions_returns_session_name_and_counts():
    user = SimpleNamespace(id="u-1", email="jane@example.com")
    sessions = [
        SimpleNamespace(
            session_id="s-1",
            session_name="Slow API",
            created_at="2026-01-01T00:00:00",
            message_count=5,
        ),
        SimpleNamespace(
            session_id="s-2",
            session_name="DB Timeout",
            created_at="2026-01-02T00:00:00",
            message_count=2,
        ),
    ]
    db = FakeDB([
        FakeQuery(first_result=user),
        FakeQuery(all_result=sessions),
    ])

    result = await dashboard_routes.list_sessions(
        current_user={"email": "jane@example.com"},
        db=db,
    )
    assert len(result) == 2
    assert result[0].session_name == "Slow API"
    assert result[1].message_count == 2


@pytest.mark.asyncio
async def test_get_chat_history_read_only():
    user = SimpleNamespace(id="u-1", email="jane@example.com")
    session = SimpleNamespace(session_id="s-1", user_id="u-1")
    messages = [
        SimpleNamespace(id=1, role="user", content="Issue details", created_at="2026-01-01T00:00:00"),
        SimpleNamespace(id=2, role="assistant", content="Suggested fix", created_at="2026-01-01T00:00:10"),
    ]
    db = FakeDB([
        FakeQuery(first_result=user),
        FakeQuery(first_result=session),
        FakeQuery(all_result=messages),
    ])

    result = await dashboard_routes.get_chat_history(
        session_id="s-1",
        current_user={"email": "jane@example.com"},
        db=db,
    )
    assert result.session_id == "s-1"
    assert len(result.messages) == 2
    assert result.messages[1].role == "assistant"

