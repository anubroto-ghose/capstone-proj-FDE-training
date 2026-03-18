import os
import pandas as pd
from tqdm import tqdm
from pymilvus import (
    connections,
    FieldSchema,
    CollectionSchema,
    DataType,
    Collection,
    utility
)
from openai import OpenAI
from dotenv import load_dotenv
from pathlib import Path


load_dotenv()

# ==============================
# SETTINGS
# ==============================

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent

CSV_PATH = PROJECT_ROOT / "data" / "ITSM_data.csv"
BACKUP_PATH = PROJECT_ROOT / "data" / "incident_embeddings_backup.parquet"

MILVUS_HOST = "localhost"
MILVUS_PORT = "19530"

COLLECTION_NAME = "incident_vectors"

EMBEDDING_MODEL = "text-embedding-3-small"

VECTOR_DIM = 1536

BATCH_SIZE = 100


# ==============================
# OPENAI CLIENT
# ==============================

client = OpenAI(api_key=OPENAI_API_KEY)


# ==============================
# CONNECT MILVUS
# ==============================

print("Connecting to Milvus...")

connections.connect(
    alias="default",
    host=MILVUS_HOST,
    port=MILVUS_PORT
)


# ==============================
# CREATE COLLECTION
# ==============================

if utility.has_collection(COLLECTION_NAME):
    print(f"Dropping existing collection {COLLECTION_NAME} for schema update...")
    utility.drop_collection(COLLECTION_NAME)

print("Creating Milvus collection...")

fields = [

    FieldSchema(
        name="id",
        dtype=DataType.INT64,
        is_primary=True,
        auto_id=True
    ),

    FieldSchema(
        name="incident_id",
        dtype=DataType.VARCHAR,
        max_length=50
    ),

    FieldSchema(
        name="priority",
        dtype=DataType.INT64
    ),

    FieldSchema(
        name="impact",
        dtype=DataType.INT64
    ),

    FieldSchema(
        name="category",
        dtype=DataType.VARCHAR,
        max_length=50
    ),

    FieldSchema(
        name="resolved",
        dtype=DataType.BOOL
    ),

    FieldSchema(
        name="incident_date",
        dtype=DataType.VARCHAR,
        max_length=50
    ),

    FieldSchema(
        name="embedding",
        dtype=DataType.FLOAT_VECTOR,
        dim=VECTOR_DIM
    )
]

schema = CollectionSchema(
    fields,
    description="IT incident embeddings with metadata"
)

collection = Collection(
    name=COLLECTION_NAME,
    schema=schema
)

index_params = {
    "metric_type": "COSINE",
    "index_type": "HNSW",
    "params": {
        "M": 8,
        "efConstruction": 64
    }
}

collection.create_index(
    field_name="embedding",
    index_params=index_params
)


# ==============================
# LOAD CSV
# ==============================

print("Loading dataset...")

df = pd.read_csv(CSV_PATH)

print(f"Loaded {len(df)} incidents")


# ==============================
# TEXT BUILDER
# ==============================

def build_text(row):

    text = f"""
    Incident in category {row.get("Category", "")}.
    Configuration item category {row.get("CI_Cat", "")}.
    Subcategory {row.get("CI_Subcat", "")}.
    Impact level {row.get("Impact", "")}.
    Urgency level {row.get("Urgency", "")}.
    Priority level {row.get("Priority", "")}.
    Closure code {row.get("Closure_Code", "")}.
    """

    return text.strip()


# ==============================
# EMBEDDING FUNCTION
# ==============================

def generate_embeddings(texts):

    response = client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=texts
    )

    return [e.embedding for e in response.data]


# ==============================
# INGESTION
# ==============================

backup_rows = []

print("Starting embedding + ingestion...")

progress_bar = tqdm(
    total=len(df),
    desc="Processing incidents",
    unit="incident"
)

for i in range(0, len(df), BATCH_SIZE):

    batch = df.iloc[i:i+BATCH_SIZE]

    texts = []
    incident_ids = []
    priorities = []
    impacts = []
    categories = []
    resolved_flags = []
    incident_dates = []

    for _, row in batch.iterrows():

        text = build_text(row)

        texts.append(text)

        incident_ids.append(str(row.get("Incident_ID", "")))

        try:
            priorities.append(int(row.get("Priority", 0)))
        except:
            priorities.append(0)

        try:
            impacts.append(int(row.get("Impact", 0)))
        except:
            impacts.append(0)

        categories.append(str(row.get("Category", "")))

        # Determine if resolved
        status = str(row.get("Status", "")).lower()
        is_resolved = status in ["closed", "resolved", "complete"]
        resolved_flags.append(is_resolved)

        # Better date extraction
        raw_date = row.get("Resolved_Time")
        if pd.isna(raw_date):
            raw_date = row.get("Open_Time")
        
        incident_dates.append(str(raw_date) if not pd.isna(raw_date) else "")

    embeddings = generate_embeddings(texts)

    collection.insert([
        incident_ids,
        priorities,
        impacts,
        categories,
        resolved_flags,
        incident_dates,
        embeddings
    ])

    for j in range(len(embeddings)):

        backup_rows.append({
            "incident_id": incident_ids[j],
            "priority": priorities[j],
            "impact": impacts[j],
            "category": categories[j],
            "resolved": resolved_flags[j],
            "incident_date": incident_dates[j],
            "embedding": embeddings[j]
        })

    progress_bar.update(len(batch))

progress_bar.close()

print("Milvus ingestion complete")


# ==============================
# SAVE BACKUP
# ==============================

backup_df = pd.DataFrame(backup_rows)

backup_df.to_parquet(BACKUP_PATH)

print(f"Embeddings backup saved to {BACKUP_PATH}")

print("Done.")