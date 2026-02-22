from datetime import datetime, date
from decimal import Decimal

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

from app.config import DATABASE_URL

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def serialize(obj):
    """Convert a SQLAlchemy model instance to a dict with JSON-safe values."""
    result = {}
    for col in obj.__table__.columns:
        val = getattr(obj, col.name)
        if isinstance(val, datetime):
            val = val.isoformat() if val else None
        elif isinstance(val, date):
            val = val.isoformat() if val else None
        elif isinstance(val, Decimal):
            val = float(val)
        result[col.name] = val
    return result
