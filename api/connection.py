
import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import URL

load_dotenv()

database_url = URL.create(
    drivername="postgresql+psycopg",
    username=os.getenv("PGUSER"),
    password=os.getenv("PGPASSWORD"),
    host=os.getenv("PGHOST"),
    database=os.getenv("PGDATABASE"),
    query={
        "sslmode": os.getenv("PGSSLMODE", "require"),
        "channel_binding": os.getenv("PGCHANNELBINDING", "require"),
    },
)

engine = create_engine(
    database_url,
    pool_pre_ping=True,
)


def get_connection():
    return engine.connect()
