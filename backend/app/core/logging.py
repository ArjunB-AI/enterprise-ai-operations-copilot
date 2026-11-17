
import logging
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path


LOG_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"

# Project root directory
BASE_DIR = Path(__file__).resolve().parents[3]

# Log directory
LOG_DIR = BASE_DIR / "logs"


def setup_logging(level: int = logging.INFO) -> None:
    # Create logs directory automatically if it does not exist.
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    # Console logging
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(LOG_FORMAT))

    # File logging with daily rotation
    file_handler = TimedRotatingFileHandler(
        filename=LOG_DIR / "app.log",
        when="midnight",
        interval=1,
        backupCount=14,
        encoding="utf-8",
    )
    file_handler.setFormatter(logging.Formatter(LOG_FORMAT))

    # Configure root logger
    logging.basicConfig(
        level=level,
        handlers=[console_handler, file_handler],
    )

    # Suppress noisy third-party library logs.
    noisy_loggers = [
        "groq",
        "httpx",
        "httpcore",
        "httpx2",
        "httpcore2",
        "sentence_transformers",
        "huggingface_hub",
        "transformers",
    ]

    for logger_name in noisy_loggers:
        logging.getLogger(logger_name).setLevel(logging.WARNING)
