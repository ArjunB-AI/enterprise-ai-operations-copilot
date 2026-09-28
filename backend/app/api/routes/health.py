import logging

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.app.db.dependencies import get_db


logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/health")
def health_check(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))

    logger.info("Health check successful | database=connected")

    return {
        "status": "ok",
        "database": "connected",
    }