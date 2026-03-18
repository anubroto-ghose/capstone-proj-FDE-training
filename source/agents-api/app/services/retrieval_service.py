import os
import pickle
from rank_bm25 import BM25Okapi
from pymilvus import connections, Collection
from pathlib import Path
from typing import List, Dict, Any, Optional
import re
import pandas as pd
import psycopg2
from dotenv import load_dotenv
from langsmith import traceable
from ..utils.telemetry import traced_client

load_dotenv()

# ── Milvus schema reference ────────────────────────────────────────────────────
# Fields in `incident_response_vectors` collection:
#   id (INT64, PK), incident_id (VARCHAR), media_asset (VARCHAR),
#   category (VARCHAR), ticket_id (VARCHAR), incident_details (VARCHAR),
#   description (VARCHAR), solution (VARCHAR), embedding (FLOAT_VECTOR)
# ───────────────────────────────────────────────────────────────────────────────


class RetrievalService:
    def __init__(self):
        self.client = traced_client
        self.milvus_url = os.getenv("MILVUS_URL", "http://localhost:19530")

        # Paths
        PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
        self.index_path = PROJECT_ROOT / "vector_db" / "bm25_index_incident_response_v2.pkl"
        self.csv_path = PROJECT_ROOT / "data" / "incident_response_dataset_150_rows.xlsx - Incident Data.csv"

        # Load BM25 Index
        with open(self.index_path, "rb") as f:
            data = pickle.load(f)
            self.bm25 = data["bm25"]
            self.incident_ids = data["incident_ids"]

        # Load incident lookup from canonical PostgreSQL incidents table.
        # Fall back to CSV only if DB is unavailable.
        self.incident_lookup = self._load_incident_lookup_from_db()
        if not self.incident_lookup:
            self.incident_lookup = self._load_incident_lookup_from_csv()

        # Connect Milvus
        connections.connect(host="localhost", port="19530")
        self.collection = Collection("incident_response_vectors")
        self.collection.load()

    def _safe_str(self, value: Any) -> str:
        if value is None or (isinstance(value, float) and pd.isna(value)):
            return ""
        text = str(value).strip()
        return "" if text.lower() == "nan" else text

    def _build_resolution_summary(self, description: str, solution: str) -> str:
        parts: List[str] = []
        if description:
            parts.append(f"Description: {description}")
        if solution:
            parts.append(f"Solution: {solution}")

        if not parts:
            return "No explicit resolution notes available in dataset for this incident."
        return "; ".join(parts)

    def _to_lookup_record(
        self,
        media_asset: str,
        category: str,
        ticket_id: str,
        incident_details: str,
        description: str,
        solution: str,
    ) -> Dict[str, str]:
        return {
            "media_asset": media_asset,
            "category_raw": category,
            "ticket_id": ticket_id,
            "incident_details": incident_details,
            "description": description,
            "solution": solution,
            "resolution_summary": self._build_resolution_summary(
                description=description,
                solution=solution,
            ),
        }

    def _load_incident_lookup_from_db(self) -> Dict[str, Dict[str, str]]:
        conn_str = os.getenv("DB_CONNECTION_STRING", "").strip()
        if not conn_str:
            return {}

        lookup: Dict[str, Dict[str, str]] = {}
        try:
            with psycopg2.connect(conn_str) as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        """
                        SELECT
                            incident_id,
                            media_asset,
                            category,
                            ticket_id,
                            incident_details,
                            description,
                            solution
                        FROM incidents
                        """
                    )
                    for row in cursor.fetchall():
                        incident_id = self._safe_str(row[0])
                        if not incident_id:
                            continue

                        lookup[incident_id] = self._to_lookup_record(
                            media_asset=self._safe_str(row[1]),
                            category=self._safe_str(row[2]),
                            ticket_id=self._safe_str(row[3]),
                            incident_details=self._safe_str(row[4]),
                            description=self._safe_str(row[5]),
                            solution=self._safe_str(row[6]),
                        )
            return lookup
        except Exception:
            return {}

    def _load_incident_lookup_from_csv(self) -> Dict[str, Dict[str, str]]:
        if not self.csv_path.exists():
            return {}

        try:
            df = pd.read_csv(self.csv_path, low_memory=False)
            lookup: Dict[str, Dict[str, str]] = {}
            for _, row in df.iterrows():
                incident_id = self._safe_str(row.get("Incident ID"))
                if not incident_id:
                    continue

                category = self._safe_str(row.get("Category"))
                media_asset = self._safe_str(row.get("Media Asset"))
                ticket_id = self._safe_str(row.get("Ticket ID"))
                incident_details = self._safe_str(row.get("Incident Details"))
                description = self._safe_str(row.get("Description"))
                solution = self._safe_str(row.get("Solution"))

                lookup[incident_id] = self._to_lookup_record(
                    media_asset=media_asset,
                    category=category,
                    ticket_id=ticket_id,
                    incident_details=incident_details,
                    description=description,
                    solution=solution,
                )
            return lookup
        except Exception:
            return {}

    def normalize_text(self, text: str) -> str:
        text = text.lower()
        text = re.sub(r"[^a-z0-9\s]", " ", text)
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    @traceable(run_type="llm", name="embedding_generation", project_name="IT-Incident-Assistant")
    async def get_embeddings(self, text: str) -> List[float]:
        response = self.client.embeddings.create(
            model="text-embedding-3-small",
            input=text
        )
        return response.data[0].embedding

    def _effective_meta(self, inc_id: str, meta: Dict[str, Any]) -> Dict[str, Any]:
        lookup = self.incident_lookup.get(inc_id, {})
        return {
            "category": meta.get("category") or lookup.get("category_raw"),
            "media_asset": meta.get("media_asset") or lookup.get("media_asset"),
            "ticket_id": meta.get("ticket_id") or lookup.get("ticket_id"),
            "incident_details": meta.get("incident_details") or lookup.get("incident_details"),
            "description": meta.get("description") or lookup.get("description"),
            "solution": meta.get("solution") or lookup.get("solution"),
            "resolution_summary": lookup.get(
                "resolution_summary",
                "No explicit resolution notes available in dataset for this incident.",
            ),
        }

    def _passes_filters(
        self,
        effective_meta: Dict[str, Any],
        priority_filters: List[int],
        impact_filters: List[int],
        category_filter: Optional[str],
    ) -> bool:
        # Priority and impact are not present in the current dataset schema.
        # Ignore those filters rather than forcing synthetic metadata.
        if category_filter:
            category_value = (effective_meta.get("category") or "").strip().lower()
            if category_value != category_filter:
                return False
        return True

    @traceable(run_type="tool", name="hybrid_search", project_name="IT-Incident-Assistant")
    async def hybrid_search(
        self,
        query: str,
        top_k: int = 5,
        semantic_weight: float = 0.7,
        # ── Metadata filters ──────────────────────────────────────────────────
        priority: Optional[str] = None,
        category: Optional[str] = None,
        impact: Optional[str] = None,
        # ── Reranking weights ─────────────────────────────────────────────────
        recency_weight: float = 0.1,      # boost for newer incidents
        resolution_weight: float = 0.1,   # boost for resolved incidents
    ) -> List[Dict[str, Any]]:
        """
        Hybrid search combining BM25 keyword scoring and Milvus semantic search,
        augmented with:
        - Metadata filtering (priority / category / impact)
        - Reranking by recency and resolution status
        """
        # ── 1. Build Milvus filter expression ─────────────────────────────────
        filter_parts = []
        priority_filters: List[int] = []
        impact_filters: List[int] = []

        category_filter = category.strip().lower() if category else None
        if category_filter:
            filter_parts.append(f'category == "{category}"')
        
        milvus_expr = " && ".join(filter_parts) if filter_parts else None

        # ── 2. Semantic Search (Milvus) ────────────────────────────────────────
        query_vector = await self.get_embeddings(query)
        search_params = {"metric_type": "COSINE", "params": {"ef": 64}}
        search_kwargs: Dict[str, Any] = dict(
            data=[query_vector],
            anns_field="embedding",
            param=search_params,
            limit=top_k * 3,
            output_fields=[
                "incident_id",
                "media_asset",
                "category",
                "ticket_id",
                "incident_details",
                "description",
                "solution",
            ],
        )
        if milvus_expr:
            search_kwargs["expr"] = milvus_expr

        milvus_results = self.collection.search(**search_kwargs)

        # ── 3. Keyword Search (BM25) ───────────────────────────────────────────
        tokenized_query = self.normalize_text(query).split()
        bm25_scores = self.bm25.get_scores(tokenized_query)
        max_bm25 = max(bm25_scores) if max(bm25_scores) > 0 else 1.0

        # ── 4. Combine scores ─────────────────────────────────────────────────
        combined: Dict[str, Dict[str, Any]] = {}

        for idx, score in enumerate(bm25_scores):
            inc_id = self.incident_ids[idx]
            combined[inc_id] = {"score": (float(score) / max_bm25) * (1 - semantic_weight), "meta": {}}

        for hits in milvus_results:
            for hit in hits:
                inc_id = hit.entity.get("incident_id")
                sem_score = float(hit.distance)
                meta = {
                    "media_asset": hit.entity.get("media_asset"),
                    "category": hit.entity.get("category"),
                    "ticket_id": hit.entity.get("ticket_id"),
                    "incident_details": hit.entity.get("incident_details"),
                    "description": hit.entity.get("description"),
                    "solution": hit.entity.get("solution"),
                }
                if inc_id in combined:
                    combined[inc_id]["score"] += sem_score * semantic_weight
                    combined[inc_id]["meta"] = meta
                else:
                    combined[inc_id] = {"score": sem_score * semantic_weight, "meta": meta}

        # ── 5. Reranking ───────────────────────────────────────────────────────
        # No recency/resolution metadata exists in the current dataset schema.
        # Keep score as hybrid(BM25 + semantic) without synthetic boosts.

        # ── 6. Sort and return top_k ───────────────────────────────────────────
        sorted_results = sorted(combined.items(), key=lambda x: x[1]["score"], reverse=True)[:top_k]

        results: List[Dict[str, Any]] = []
        for inc_id, entry in sorted_results:
            effective_meta = self._effective_meta(inc_id, entry["meta"])
            if not self._passes_filters(effective_meta, priority_filters, impact_filters, category_filter):
                continue

            results.append(
                {
                    "incident_id": inc_id,
                    "score": round(entry["score"], 4),
                    "priority": None,
                    "category": effective_meta.get("category"),
                    "impact": None,
                    "resolved": None,
                    "media_asset": effective_meta.get("media_asset"),
                    "ticket_id": effective_meta.get("ticket_id"),
                    "incident_details": effective_meta.get("incident_details"),
                    "description": effective_meta.get("description"),
                    "solution": effective_meta.get("solution"),
                    "resolution_summary": effective_meta.get("resolution_summary"),
                }
            )

        return results[:top_k]

retrieval_service = RetrievalService()
