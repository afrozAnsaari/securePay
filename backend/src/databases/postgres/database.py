import json

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.config import settings
from src.databases.postgres.base import Base

DATABASE_URL = settings.DATABASE_URL

engine = create_engine(
    DATABASE_URL,
    json_serializer=lambda obj: json.dumps(obj, default=str),
    # Hosted Postgres (e.g. Neon) suspends when idle and drops connections.
    # pre_ping checks a pooled connection before use and replaces dead ones,
    # so the first request after a quiet period doesn't fail.
    pool_pre_ping=True,
    pool_recycle=300,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
