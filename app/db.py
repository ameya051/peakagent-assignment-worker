import os
import re
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv


# Load environment variables from .env (if present)
load_dotenv()

# Accept plain postgres/postgresql URLs and rewrite to psycopg v3 driver.
# Provide a safe local default if DATABASE_URL is not set.
raw_url = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://postgres:postgres@localhost:5432/peakagent",
)

# If the URL uses the generic scheme (postgres:// or postgresql://), rewrite to psycopg driver
DATABASE_URL = re.sub(r"^postgres(ql)?://", "postgresql+psycopg://", raw_url)

engine = create_engine(DATABASE_URL, pool_pre_ping=True, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
