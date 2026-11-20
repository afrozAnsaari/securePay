import json

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.config import settings
from src.databases.postgres.base import Base

DATABASE_URL = settings.DATABASE_URL

engine = create_engine(
    DATABASE_URL,
    json_serializer=lambda obj: json.dumps(obj, default=str),
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
