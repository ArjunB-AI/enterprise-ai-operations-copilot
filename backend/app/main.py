import logging

from fastapi import FastAPI

from backend.app.api.routes.health import router as health_router
from backend.app.api.routes.auth import router as auth_router
from backend.app.core.config import settings
from backend.app.core.logging import setup_logging


setup_logging()

logger = logging.getLogger(__name__)


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
)

app.include_router(health_router)
app.include_router(auth_router)

logger.info(
    "Application started | name=%s | version=%s | environment=%s",
    settings.app_name,
    settings.app_version,
    settings.environment,
)