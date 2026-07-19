"""
Centralized Structured Logging Configuration.
Configures Python logging with structured format for enterprise observability.
"""
import logging
import sys

def setup_logging():
    logger = logging.getLogger("fifa_ops")
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%SZ"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger

logger = setup_logging()
