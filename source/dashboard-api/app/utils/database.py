import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

load_dotenv()

def get_db_url():
    conn_str = os.getenv("DB_CONNECTION_STRING", "")
    if "host=" in conn_str:
        parts = dict(x.split('=') for x in conn_str.split())
        return f"postgresql://{parts['user']}:{parts.get('password', '')}@{parts['host']}:{parts.get('port', 5432)}/{parts['dbname']}"
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
