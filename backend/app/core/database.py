"""Database engine and tenant-schema helpers (base product)."""

from collections.abc import Generator
from contextlib import contextmanager

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings

engine = create_engine(
    get_settings().database_url,
    pool_pre_ping=True,
    pool_recycle=3600,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# customer_id → MySQL schema name
CUSTOMER_SCHEMAS = {
    "customer-1": "schema_customer_1",
    "customer-2": "schema_customer_2",
    "customer-3": "schema_customer_3",
}


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def tenant_session(customer_id: str) -> Generator[Session, None, None]:
    """Open a session scoped to the customer's MySQL schema."""
    schema = CUSTOMER_SCHEMAS.get(customer_id)
    if not schema:
        raise ValueError(f"Unknown customer_id: {customer_id}")

    db = SessionLocal()
    try:
        db.execute(text(f"USE `{schema}`"))
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
