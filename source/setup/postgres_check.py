import psycopg2
from dotenv import load_dotenv
import os

load_dotenv()

CONNECTION_STRING = os.getenv(
    "DB_CONNECTION_STRING",
    "host=localhost port=5432 dbname=IncidentResolutionDB user=postgres password=root connect_timeout=10 sslmode=prefer",
)
CONNECTION_STRING = CONNECTION_STRING.replace("dbname==", "dbname=")
conn = psycopg2.connect(CONNECTION_STRING)
print("Connected to Postgres!")
