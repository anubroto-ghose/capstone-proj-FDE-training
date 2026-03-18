import os
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv
from urllib.parse import quote_plus

load_dotenv()

# Note: For asyncpg, the connection string needs to start with postgresql+asyncpg://
# The user provided: "host=localhost port=5432 dbname=capstoneDB user=postgres password=root connect_timeout=10 sslmode=prefer"
# We'll convert this format or use a standard URI if possible.

DB_CONN = os.getenv("DB_CONNECTION_STRING")

# Basic conversion if needed, but assuming a standard URI format will be easier for SQLAlchemy
# If it's the libpq format from the .env, we might need to parse it.
# Let's assume we can use a standard URI for SQLAlchemy.

# For this implementation, we'll use the async version for better performance with FastAPI
# DATABASE_URL = "postgresql+asyncpg://postgres:root@localhost/capstoneDB"
# However, let's stick to what's provided in .env and adapt if necessary.

# Assuming the user might provide a sync connection string for psycopg2 in .env
# We'll create a helper to get the SQLAlchemy URL
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

DATABASE_URL = get_db_url()

engine = create_async_engine(DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://"), echo=True)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
