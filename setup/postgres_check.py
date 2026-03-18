import psycopg2
from dotenv import load_dotenv
import os

load_dotenv()

CONNECTION_STRING = os.getenv("DB_CONNECTION_STRING", "")
conn = psycopg2.connect(CONNECTION_STRING)
print("Connected to Postgres!")