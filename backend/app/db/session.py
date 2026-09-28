from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.core.config import settings


engine = create_engine(
    settings.database_url,
)

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
)


# from sqlalchemy import create_engine, text

# from backend.app.core.config import settings


# engine = create_engine(
#     settings.database_url,
# )


# with engine.connect() as connection:
#     result = connection.execute(text("SELECT 1"))
#     print("Database connection successful:", result.scalar())
