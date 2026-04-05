"""Structured logging configuration."""

import logging
import sys
from typing import Any

from app.core.config import settings


def setup_logging() -> None:
    """Configure structured logging for the application."""
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)


    formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)


    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)


    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)


    logging.getLogger("uvicorn").setLevel(log_level)
    logging.getLogger("fastapi").setLevel(log_level)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance for a module."""
    return logging.getLogger(name)


class AgentLogger:
    """Structured logger for agent operations."""

    def __init__(self, logger: logging.Logger):
        self.logger = logger

    def log_step(
        self,
        step_name: str,
        status: str,
        input_data: Any = None,
        output_data: Any = None,
        error: str = None,
    ) -> None:
        """Log an agent step with structured data."""
        log_data = {
            "step": step_name,
            "status": status,
        }
        if input_data is not None:
            log_data["input"] = str(input_data)[:500]  # Truncate long inputs
        if output_data is not None:
            log_data["output"] = str(output_data)[:500]
        if error is not None:
            log_data["error"] = error

        if error:
            self.logger.error(f"Agent step failed: {log_data}")
        else:
            self.logger.info(f"Agent step: {log_data}")
