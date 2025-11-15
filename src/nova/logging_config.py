"""
JSON logging configuration for structured logging in production.
"""
import json
import logging
import time
from typing import Any, Dict


class JSONFormatter(logging.Formatter):
    """Log formatter that outputs JSON strings for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        log_data: Dict[str, Any] = {
            "timestamp": time.time(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add extra fields if present
        if hasattr(record, "extra"):
            log_data.update(record.extra)

        # Add trace_id, slot, and status if available in the message
        if hasattr(record, "trace_id"):
            log_data["trace_id"] = record.trace_id
        if hasattr(record, "slot"):
            log_data["slot"] = record.slot
        if hasattr(record, "status"):
            log_data["status"] = record.status

        return json.dumps(log_data)


def configure_logging(level: str = "INFO", json_format: bool = True) -> None:
    """Configure logging with optional JSON formatting."""
    level_num = getattr(logging, level.upper(), logging.INFO)

    # Clear existing handlers
    logging.getLogger().handlers.clear()

    # Create handler
    handler = logging.StreamHandler()
    handler.setLevel(level_num)

    # Set formatter
    if json_format:
        formatter = JSONFormatter()
    else:
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

    handler.setFormatter(formatter)

    # Configure root logger
    logging.getLogger().setLevel(level_num)
    logging.getLogger().addHandler(handler)

    # Set specific log levels for noisy modules
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)
