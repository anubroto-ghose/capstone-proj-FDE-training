import pytest
from app.services.retrieval_service import RetrievalService


class DummyBM25:
    def __init__(self, scores):
        self._scores = scores

    def get_scores(self, tokenized_query):
        return self._scores


class DummyCollection:
    def __init__(self):
        self.last_search_kwargs = None

    def search(self, **kwargs):
        self.last_search_kwargs = kwargs
        # No semantic hits to force BM25 fallback path
        return [[]]


@pytest.mark.asyncio
async def test_hybrid_search_uses_bm25_when_semantic_empty_and_filters_apply():
    service = RetrievalService.__new__(RetrievalService)
    service.bm25 = DummyBM25([1.0, 0.8, 0.3])
    service.incident_ids = ["IM0001", "IM0002", "IM0003"]
    service.collection = DummyCollection()
    service.incident_lookup = {
        "IM0001": {
            "priority_raw": 1,
            "impact_raw": 1,
            "category_raw": "Application",
            "resolved_raw": True,
            "status": "Closed",
            "closure_code": "Solved",
            "related_change": "",
            "resolved_time": "2026-01-01 10:00",
            "resolution_summary": "Closed with application tuning.",
        },
        "IM0002": {
            "priority_raw": 2,
            "impact_raw": 2,
            "category_raw": "Application",
            "resolved_raw": True,
            "status": "Closed",
            "closure_code": "Solved",
            "related_change": "",
            "resolved_time": "2026-01-02 10:00",
            "resolution_summary": "Closed after DB config change.",
        },
        "IM0003": {
            "priority_raw": 4,
            "impact_raw": 3,
            "category_raw": "Network",
            "resolved_raw": False,
            "status": "Open",
            "closure_code": "",
            "related_change": "",
            "resolved_time": "",
            "resolution_summary": "No resolution yet.",
        },
    }

    async def _mock_embedding(_text):
        return [0.01, 0.02, 0.03]

    service.get_embeddings = _mock_embedding

    results = await service.hybrid_search(
        query="system slowdown intermittent timeout",
        priority="P1,P2",
        impact="high",
        top_k=5,
    )

    # Filter should keep IM0001 (priority=1, impact=1), and exclude others.
    assert len(results) == 1
    assert results[0]["incident_id"] == "IM0001"
    assert "resolution_summary" in results[0]
    # Multi-value filter expression should be generated for Milvus.
    assert "priority in [1, 2]" in service.collection.last_search_kwargs.get("expr", "")


def test_priority_filter_parsing_supports_or_and_commas():
    service = RetrievalService.__new__(RetrievalService)
    values = service._to_int_filters({"p1": 1, "p2": 2, "critical": 1}, "P1 or P2, critical")
    assert values == [1, 2]

