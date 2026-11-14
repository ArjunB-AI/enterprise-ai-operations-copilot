
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.core.config import settings


vector_engine = create_engine(
    settings.vector_database_url,
)

VectorSessionLocal = sessionmaker(
    bind=vector_engine,
    autocommit=False,
    autoflush=False,
)
