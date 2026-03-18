import pandas as pd
import pickle
from pathlib import Path
from rank_bm25 import BM25Okapi
import re
from tqdm import tqdm


# ==============================
# PATHS
# ==============================

BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent

CSV_PATH = PROJECT_ROOT / "data" / "ITSM_data.csv"
INDEX_PATH = PROJECT_ROOT / "vector_db" / "bm25_index.pkl"


# ==============================
# TEXT NORMALIZATION
# ==============================

def normalize_text(text: str):

    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text)

    return text.strip()


# ==============================
# LOAD DATASET
# ==============================

print("Loading dataset...")

df = pd.read_csv(CSV_PATH)

print(f"Loaded {len(df)} incidents")


# ==============================
# BUILD DOCUMENTS
# ==============================

documents = []
incident_ids = []

print("Building BM25 documents...")

for _, row in tqdm(df.iterrows(), total=len(df)):

    text = f"""
    incident category {row.get("Category","")}
    configuration item {row.get("CI_Cat","")}
    subcategory {row.get("CI_Subcat","")}
    priority {row.get("Priority","")}
    impact {row.get("Impact","")}
    urgency {row.get("Urgency","")}
    closure code {row.get("Closure_Code","")}
    """

    text = normalize_text(text)

    documents.append(text.split())

    incident_ids.append(str(row.get("Incident_ID","")))


# ==============================
# BUILD BM25 INDEX
# ==============================

print("Building BM25 index...")

bm25 = BM25Okapi(documents)


# ==============================
# SAVE INDEX
# ==============================

data_to_save = {
    "bm25": bm25,
    "incident_ids": incident_ids
}

with open(INDEX_PATH, "wb") as f:
    pickle.dump(data_to_save, f)

print(f"BM25 index saved to {INDEX_PATH}")