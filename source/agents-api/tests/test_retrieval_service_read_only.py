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
async def test_hybrid_search_uses_bm25_when_semantic_empty_and_category_filter_applies():
    service = RetrievalService.__new__(RetrievalService)
    service.bm25 = DummyBM25([1.0, 0.8, 0.3])
    service.incident_ids = ["IM0001", "IM0002", "IM0003"]
    service.collection = DummyCollection()
    service.incident_lookup = {
        "IM0001": {
            "category_raw": "Application",
            "media_asset": "MediaServer01",
            "ticket_id": "TKT-1001",
            "incident_details": "Disk Space Alert",
            "description": "Storage exceeded threshold causing upload failures",
            "solution": "Archive old media files and expand storage volume",
            "resolution_summary": "Description: Storage exceeded threshold causing upload failures; Solution: Archive old media files and expand storage volume",
        },
        "IM0002": {
            "category_raw": "Application",
            "media_asset": "MediaServer02",
            "ticket_id": "TKT-1002",
            "incident_details": "Slow Delivery",
            "description": "Media loading slowly due to cache miss",
            "solution": "Refresh CDN cache and optimize media compression",
            "resolution_summary": "Description: Media loading slowly due to cache miss; Solution: Refresh CDN cache and optimize media compression",
        },
        "IM0003": {
            "category_raw": "Network",
            "media_asset": "MediaServer07",
            "ticket_id": "TKT-1007",
            "incident_details": "Streaming Failure",
            "description": "Video stream stopped responding for live broadcast",
            "solution": "Restart streaming service and reset network interface",
            "resolution_summary": "Description: Video stream stopped responding for live broadcast; Solution: Restart streaming service and reset network interface",
        },
    }

    async def _mock_embedding(_text):
        return [0.01, 0.02, 0.03]

    service.get_embeddings = _mock_embedding

    results = await service.hybrid_search(
        query="system slowdown intermittent timeout",
        category="Application",
        top_k=5,
    )

    # Category filter should keep only Application incidents and exclude Network.
    assert len(results) == 2
    assert {r["incident_id"] for r in results} == {"IM0001", "IM0002"}
    assert "resolution_summary" in results[0]
    # Category filter expression should be generated for Milvus.
    assert 'category == "Application"' in service.collection.last_search_kwargs.get("expr", "")


def test_search_output_includes_textual_resolution_fields():
    service = RetrievalService.__new__(RetrievalService)
    service.incident_lookup = {}
    effective_meta = service._effective_meta(
        "INC-5001",
        {
            "media_asset": "MediaServer01",
            "category": "Storage",
            "ticket_id": "TKT-1001",
            "incident_details": "Disk Space Alert",
            "description": "Storage exceeded threshold causing upload failures",
            "solution": "Archive old media files and expand storage volume",
        },
    )
    assert effective_meta["incident_details"] == "Disk Space Alert"
    assert effective_meta["description"] == "Storage exceeded threshold causing upload failures"
    assert effective_meta["solution"] == "Archive old media files and expand storage volume"
