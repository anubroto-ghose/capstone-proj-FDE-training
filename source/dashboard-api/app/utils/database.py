import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv
from urllib.parse import quote_plus

load_dotenv()

def get_db_url():
    conn_str = os.getenv("DB_CONNECTION_STRING", "")
    if "host=" in conn_str:
        parts = {}
        for token in conn_str.split():
            if "=" not in token:
                continue
            key, value = token.split("=", 1)
            if key:
                parts[key.strip()] = value.strip()

        dbname = (parts.get("dbname", "")).lstrip("=")
        user = parts.get("user", "")
        password = quote_plus(parts.get("password", ""))
        host = parts.get("host", "localhost")
        port = parts.get("port", 5432)
        return f"postgresql://{user}:{password}@{host}:{port}/{dbname}"
    return conn_str

SQLALCHEMY_DATABASE_URL = get_db_url()

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
