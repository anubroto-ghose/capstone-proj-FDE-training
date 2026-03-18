import psycopg2
import pandas as pd
from pathlib import Path
from uuid import uuid4
import os
from dotenv import load_dotenv
import re
from tqdm import tqdm
load_dotenv()

# ==============================
# DATABASE CONNECTION
# ==============================

DB_CONNECTION = os.getenv("DB_CONNECTION_STRING", "DB_CONNECTION_STRING")

# ==============================
# PATHS
# ==============================

BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent
CSV_PATH = PROJECT_ROOT / "data" / "ITSM_data.csv"


# ==============================
# CONNECT DATABASE
# ==============================

conn = psycopg2.connect(DB_CONNECTION)
conn.autocommit = True
cursor = conn.cursor()

print("Connected to PostgreSQL")


# ==============================
# USERS TABLE (AUTH)
# ==============================

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT DEFAULT 'user',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
""")

print("Users table ready")


# ==============================
# AGENT SESSION TABLE
# ==============================

cursor.execute("""
CREATE TABLE IF NOT EXISTS agent_sessions (
    session_id TEXT PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    session_name TEXT,
    current_agent VARCHAR DEFAULT 'L1 Support Specialist',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
""")

print("Agent sessions table ready")

# Ensure compatibility for older DBs created before current_agent existed.
cursor.execute("""
ALTER TABLE agent_sessions
ADD COLUMN IF NOT EXISTS current_agent VARCHAR DEFAULT 'L1 Support Specialist';
""")
print("Agent sessions 'current_agent' migration check complete")

cursor.execute("""
ALTER TABLE agent_sessions
ADD COLUMN IF NOT EXISTS session_name TEXT;
""")
print("Agent sessions 'session_name' migration check complete")


# ==============================
# AGENT MESSAGES TABLE
# ==============================

cursor.execute("""
CREATE TABLE IF NOT EXISTS agent_messages (
    id SERIAL PRIMARY KEY,
    session_id TEXT NOT NULL,
    role TEXT NOT NULL,
    content TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id)
        REFERENCES agent_sessions(session_id)
        ON DELETE CASCADE
);
""")

print("Agent messages table ready")


# ==============================
# MESSAGE STRUCTURE TABLE
# ==============================

cursor.execute("""
CREATE TABLE IF NOT EXISTS message_structure (
    id SERIAL PRIMARY KEY,
    session_id TEXT NOT NULL,
    message_id INTEGER NOT NULL,
    branch_id TEXT DEFAULT 'main',
    message_type TEXT NOT NULL,
    sequence_number INTEGER NOT NULL,
    user_turn_number INTEGER,
    branch_turn_number INTEGER,
    tool_name TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id)
        REFERENCES agent_sessions(session_id)
        ON DELETE CASCADE,
    FOREIGN KEY (message_id)
        REFERENCES agent_messages(id)
        ON DELETE CASCADE
);
""")

print("Message structure table ready")


# ==============================
# TOKEN USAGE TABLE
# ==============================

cursor.execute("""
CREATE TABLE IF NOT EXISTS turn_usage (
    id SERIAL PRIMARY KEY,
    session_id TEXT NOT NULL,
    branch_id TEXT DEFAULT 'main',
    user_turn_number INTEGER NOT NULL,
    requests INTEGER DEFAULT 0,
    input_tokens INTEGER DEFAULT 0,
    output_tokens INTEGER DEFAULT 0,
    total_tokens INTEGER DEFAULT 0,
    input_tokens_details JSONB,
    output_tokens_details JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(session_id, branch_id, user_turn_number),
    FOREIGN KEY (session_id)
        REFERENCES agent_sessions(session_id)
        ON DELETE CASCADE
);
""")

print("Token usage table ready")


# ==============================
# INCIDENT FEEDBACK TABLE (for continuous improvement feedback loop)
# ==============================

cursor.execute("""
CREATE TABLE IF NOT EXISTS incident_feedback (
    id SERIAL PRIMARY KEY,
    session_id TEXT NOT NULL,
    message_id INTEGER,
    helpful BOOLEAN NOT NULL,
    comment TEXT,
    agent_tier TEXT,
    incident_category TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
""")

print("Incident feedback table ready")

# ==============================
# A2A CONTEXT TABLE (durable agent-to-agent handoff context)
# ==============================

cursor.execute("""
CREATE TABLE IF NOT EXISTS a2a_context (
    id SERIAL PRIMARY KEY,
    session_id TEXT NOT NULL REFERENCES agent_sessions(session_id) ON DELETE CASCADE,
    from_agent TEXT NOT NULL,
    to_agent TEXT NOT NULL,
    context_type TEXT NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
""")

print("A2A context table ready")

conn.commit()


# ==============================
# INCIDENT DATA TABLE
# ==============================

cursor.execute("""
CREATE TABLE IF NOT EXISTS incidents (
    CI_Name TEXT,
    CI_Cat TEXT,
    CI_Subcat TEXT,
    WBS TEXT,
    Incident_ID TEXT PRIMARY KEY,
    Status TEXT,
    Impact TEXT,
    Urgency TEXT,
    Priority TEXT,
    number_cnt FLOAT,
    Category TEXT,
    KB_number TEXT,
    Alert_Status TEXT,
    No_of_Reassignments INTEGER,
    Open_Time TEXT,
    Reopen_Time TEXT,
    Resolved_Time TEXT,
    Close_Time TEXT,
    Handle_Time_hrs TEXT,
    Closure_Code TEXT,
    No_of_Related_Interactions INTEGER,
    Related_Interaction TEXT,
    No_of_Related_Incidents INTEGER,
    No_of_Related_Changes INTEGER,
    Related_Change TEXT
);
""")

print("Incidents table ready")



# ==============================
# HELPER FUNCTIONS
# ==============================

def clean_integer(value):
    """
    Convert messy numeric values into integer.
    Handles:
    - commas
    - floats
    - NA / NS
    """

    if pd.isna(value):
        return None

    value = str(value)

    # remove commas
    value = value.replace(",", "")

    # remove non numeric characters
    value = re.sub(r"[^\d\-]", "", value)

    if value == "":
        return None

    try:
        return int(value)
    except:
        return None


def clean_float(value):

    if pd.isna(value):
        return None

    try:
        return float(value)
    except:
        return None


def clean_text(value):

    if pd.isna(value):
        return None

    return str(value)


# ==============================
# LOAD DATASET
# ==============================

print("Loading CSV dataset...")

df = pd.read_csv(CSV_PATH, low_memory=False)

print(f"Loaded {len(df)} rows")


# ==============================
# INSERT INCIDENT DATA
# ==============================

insert_query = """
INSERT INTO incidents VALUES (
%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,
%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,
%s,%s,%s,%s,%s
)
ON CONFLICT (Incident_ID) DO NOTHING
"""

print("Inserting incidents into PostgreSQL...")

for _, row in tqdm(df.iterrows(), total=len(df)):

    data = (
        clean_text(row["CI_Name"]),
        clean_text(row["CI_Cat"]),
        clean_text(row["CI_Subcat"]),
        clean_text(row["WBS"]),
        clean_text(row["Incident_ID"]),
        clean_text(row["Status"]),
        clean_integer(row["Impact"]),
        clean_integer(row["Urgency"]),
        clean_integer(row["Priority"]),
        clean_float(row["number_cnt"]),
        clean_text(row["Category"]),
        clean_text(row["KB_number"]),
        clean_text(row["Alert_Status"]),
        clean_integer(row["No_of_Reassignments"]),
        clean_text(row["Open_Time"]),
        clean_text(row["Reopen_Time"]),
        clean_text(row["Resolved_Time"]),
        clean_text(row["Close_Time"]),
        clean_text(row["Handle_Time_hrs"]),
        clean_text(row["Closure_Code"]),
        clean_integer(row["No_of_Related_Interactions"]),
        clean_text(row["Related_Interaction"]),
        clean_integer(row["No_of_Related_Incidents"]),
        clean_integer(row["No_of_Related_Changes"]),
        clean_text(row["Related_Change"]),
    )

    cursor.execute(insert_query, data)


conn.commit()

cursor.close()
conn.close()

print("Incident data inserted successfully.")
