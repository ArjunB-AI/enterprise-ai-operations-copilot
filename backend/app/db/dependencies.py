from collections.abc import Generator

from sqlalchemy.orm import Session

from backend.app.db.session import SessionLocal
from backend.app.db.vector_session import VectorSessionLocal


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


def get_vector_db() -> Generator[Session, None, None]:
    vector_db = VectorSessionLocal()

    try:
        yield vector_db
    finally:
        vector_db.close()