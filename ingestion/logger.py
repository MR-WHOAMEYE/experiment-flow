"""
Structured JSON logger shared across all EaaS pipeline stages.

Usage:
    from ingestion.logger import get_logger
    log = get_logger(__name__)
    log.info("stage started", extra={"rows": 100, "source": "myfile.csv"})
"""
import logging
import os
from pythonjsonlogger import jsonlogger


def get_logger(name: str) -> logging.Logger:
    """Return a JSON-formatted logger for the given module name."""
    logger = logging.getLogger(name)

    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = jsonlogger.JsonFormatter(
            fmt="%(asctime)s %(name)s %(levelname)s %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    level = os.getenv("LOG_LEVEL", "INFO").upper()
    logger.setLevel(getattr(logging, level, logging.INFO))
    return logger
