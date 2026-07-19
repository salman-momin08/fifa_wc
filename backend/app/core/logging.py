"""
Centralized Structured Logging Configuration.

Configures Python logging with structured format for enterprise observability.
"""
import logging
import sys


def setup_logging() -> logging.Logger:
    """Configure and return the primary application logger instance.

    Returns:
        Configured Logger instance with standard stdout stream handler.
    """
    app_logger = logging.getLogger("fifa_ops")
    app_logger.setLevel(logging.INFO)

    if not app_logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%SZ",
        )
        handler.setFormatter(formatter)
        app_logger.addHandler(handler)

    return app_logger


logger = setup_logging()
