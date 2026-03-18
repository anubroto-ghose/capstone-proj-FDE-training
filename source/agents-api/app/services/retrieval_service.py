import os
import pickle
from rank_bm25 import BM25Okapi
from pymilvus import connections, Collection
from pathlib import Path
from typing import List, Dict, Any, Optional
import re
from datetime import datetime, timezone
import pandas as pd
import psycopg2
from dotenv import load_dotenv
from langsmith import traceable
from ..utils.telemetry import traced_client

load_dotenv()

# ── Milvus schema reference ────────────────────────────────────────────────────
# Fields in `incident_vectors` collection:
#   id (INT64, PK), incident_id (VARCHAR), priority (INT64),
#   impact (INT64), category (VARCHAR), resolved (BOOL),
#   incident_date (VARCHAR), embedding (FLOAT_VECTOR)
# ───────────────────────────────────────────────────────────────────────────────

PRIORITY_MAP = {
    "p1": 1, "critical": 1, "1": 1,
    "p2": 2, "high": 2, "2": 2,
    "p3": 3, "medium": 3, "3": 3,
    "p4": 4, "low": 4, "4": 4,
}
IMPACT_MAP = {
    "1": 1, "extensive": 1, "high": 1,
    "2": 2, "significant": 2, "medium": 2,
    "3": 3, "moderate": 3, "low": 3,
    "4": 4, "minor": 4,
}


class RetrievalService:
    def __init__(self):
        self.client = traced_client
        self.milvus_url = os.getenv("MILVUS_URL", "http://localhost:19530")

        # Paths
        PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
        self.index_path = PROJECT_ROOT / "vector_db" / "bm25_index.pkl"
        self.csv_path = PROJECT_ROOT / "data" / "ITSM_data.csv"

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
        self.collection = Collection("incident_vectors")
        self.collection.load()

    def _safe_str(self, value: Any) -> str:
        if value is None or (isinstance(value, float) and pd.isna(value)):
            return ""
        text = str(value).strip()
        return "" if text.lower() == "nan" else text

    def _safe_int(self, value: Any) -> Optional[int]:
        text = self._safe_str(value)
        if not text:
            return None
        try:
            return int(float(text))
        except Exception:
            return None

    def _status_is_resolved(self, status: str) -> bool:
        s = (status or "").strip().lower()
        return s in {"closed", "resolved", "complete"}

    def _build_resolution_summary(
        self,
        status: str,
        closure_code: str,
        related_change: str,
        resolved_time: str,
        ci_cat: str,
        ci_subcat: str,
    ) -> str:
        parts: List[str] = []
        if closure_code:
            parts.append(f"Closure code: {closure_code}")
        if related_change:
            parts.append(f"Related change: {related_change}")
        if status:
            parts.append(f"Status: {status}")
        if resolved_time:
            parts.append(f"Resolved at: {resolved_time}")
        if ci_cat or ci_subcat:
            scope = " / ".join([x for x in [ci_cat, ci_subcat] if x])
            parts.append(f"Affected area: {scope}")

        if not parts:
            return "No explicit resolution notes available in dataset for this incident."
        return "; ".join(parts)

    def _to_lookup_record(
        self,
        status: str,
        closure_code: str,
        related_change: str,
        resolved_time: str,
        ci_cat: str,
        ci_subcat: str,
        category: str,
        priority: Optional[int],
        impact: Optional[int],
    ) -> Dict[str, str]:
        return {
            "status": status,
            "closure_code": closure_code,
            "related_change": related_change,
            "resolved_time": resolved_time,
            "category_raw": category,
            "priority_raw": priority,
            "impact_raw": impact,
            "resolved_raw": self._status_is_resolved(status),
            "resolution_summary": self._build_resolution_summary(
                status=status,
                closure_code=closure_code,
                related_change=related_change,
                resolved_time=resolved_time,
                ci_cat=ci_cat,
                ci_subcat=ci_subcat,
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
                            status,
                            closure_code,
                            related_change,
                            resolved_time,
                            ci_cat,
                            ci_subcat,
                            category,
                            priority,
                            impact
                        FROM incidents
                        """
                    )
                    for row in cursor.fetchall():
                        incident_id = self._safe_str(row[0])
                        if not incident_id:
                            continue

                        lookup[incident_id] = self._to_lookup_record(
                            status=self._safe_str(row[1]),
                            closure_code=self._safe_str(row[2]),
                            related_change=self._safe_str(row[3]),
                            resolved_time=self._safe_str(row[4]),
                            ci_cat=self._safe_str(row[5]),
                            ci_subcat=self._safe_str(row[6]),
                            category=self._safe_str(row[7]),
                            priority=self._safe_int(row[8]),
                            impact=self._safe_int(row[9]),
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
                incident_id = self._safe_str(row.get("Incident_ID"))
                if not incident_id:
                    continue

                status = self._safe_str(row.get("Status"))
                closure_code = self._safe_str(row.get("Closure_Code"))
                related_change = self._safe_str(row.get("Related_Change"))
                resolved_time = self._safe_str(row.get("Resolved_Time"))
                ci_cat = self._safe_str(row.get("CI_Cat"))
                ci_subcat = self._safe_str(row.get("CI_Subcat"))
                category = self._safe_str(row.get("Category"))

                lookup[incident_id] = self._to_lookup_record(
                    status=status,
                    closure_code=closure_code,
                    related_change=related_change,
                    resolved_time=resolved_time,
                    ci_cat=ci_cat,
                    ci_subcat=ci_subcat,
                    category=category,
                    priority=self._safe_int(row.get("Priority")),
                    impact=self._safe_int(row.get("Impact")),
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

    def _to_int_filter(self, label_map: dict, value: Optional[str]) -> Optional[int]:
        if not value:
            return None
        return label_map.get(value.lower().strip())

    def _to_int_filters(self, label_map: dict, value: Optional[str]) -> List[int]:
        if not value:
            return []
        normalized = (
            value.lower()
            .replace(" or ", ",")
            .replace("/", ",")
            .replace("|", ",")
            .replace(";", ",")
        )
        parts = [p.strip() for p in normalized.split(",") if p.strip()]
        values: List[int] = []
        for p in parts:
            v = label_map.get(p)
            if v is not None and v not in values:
                values.append(v)
        return values

    def _effective_meta(self, inc_id: str, meta: Dict[str, Any]) -> Dict[str, Any]:
        lookup = self.incident_lookup.get(inc_id, {})
        return {
            "priority": meta.get("priority") if meta.get("priority") is not None else lookup.get("priority_raw"),
            "impact": meta.get("impact") if meta.get("impact") is not None else lookup.get("impact_raw"),
            "category": meta.get("category") or lookup.get("category_raw"),
            "resolved": meta.get("resolved") if meta.get("resolved") is not None else lookup.get("resolved_raw"),
            "incident_date": meta.get("incident_date"),
            "status": lookup.get("status"),
            "closure_code": lookup.get("closure_code"),
            "related_change": lookup.get("related_change"),
            "resolved_time": lookup.get("resolved_time"),
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
        if priority_filters and effective_meta.get("priority") not in priority_filters:
            return False
        if impact_filters and effective_meta.get("impact") not in impact_filters:
            return False
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
        priority_filters = self._to_int_filters(PRIORITY_MAP, priority)
        if len(priority_filters) == 1:
            filter_parts.append(f'priority == {priority_filters[0]}')
        elif len(priority_filters) > 1:
            ints = ", ".join(str(v) for v in priority_filters)
            filter_parts.append(f"priority in [{ints}]")
        
        impact_filters = self._to_int_filters(IMPACT_MAP, impact)
        if len(impact_filters) == 1:
            filter_parts.append(f'impact == {impact_filters[0]}')
        elif len(impact_filters) > 1:
            ints = ", ".join(str(v) for v in impact_filters)
            filter_parts.append(f"impact in [{ints}]")

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
            output_fields=["incident_id", "priority", "impact", "category", "resolved", "incident_date"],
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
                    "priority": hit.entity.get("priority"),
                    "impact": hit.entity.get("impact"),
                    "category": hit.entity.get("category"),
                    "resolved": hit.entity.get("resolved"),
                    "incident_date": hit.entity.get("incident_date"),
                }
                if inc_id in combined:
                    combined[inc_id]["score"] += sem_score * semantic_weight
                    combined[inc_id]["meta"] = meta
                else:
                    combined[inc_id] = {"score": sem_score * semantic_weight, "meta": meta}

        # ── 5. Reranking ───────────────────────────────────────────────────────
        now = datetime.now(timezone.utc)
        for inc_id, entry in combined.items():
            meta = entry["meta"]
            if not meta: continue

            # Recency boost
            recency_boost = 0.0
            date_str = meta.get("incident_date")
            if date_str:
                try:
                    # CSV dates are often MM/DD/YYYY or similar. Milvus has them as strings.
                    # We'll try a flexible parse or fallback.
                    dt = datetime.fromisoformat(date_str) if "T" in date_str else datetime.strptime(date_str, "%m/%d/%Y %H:%M")
                    if dt.tzinfo is None: dt = dt.replace(tzinfo=timezone.utc)
                    age_days = (now - dt).days
                    recency_boost = max(0.0, 1.0 - (age_days / 730)) # Decays over 2 years
                except:
                    pass

            # Resolution boost
            resolution_boost = 1.0 if meta.get("resolved") else 0.0

            entry["score"] += (recency_boost * recency_weight) + (resolution_boost * resolution_weight)

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
                    "priority": effective_meta.get("priority"),
                    "category": effective_meta.get("category"),
                    "impact": effective_meta.get("impact"),
                    "resolved": effective_meta.get("resolved"),
                    "status": effective_meta.get("status"),
                    "closure_code": effective_meta.get("closure_code"),
                    "related_change": effective_meta.get("related_change"),
                    "resolved_time": effective_meta.get("resolved_time"),
                    "resolution_summary": effective_meta.get("resolution_summary"),
                }
            )

        return results[:top_k]

retrieval_service = RetrievalService()
