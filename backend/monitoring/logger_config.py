"""
Structured Logging Configuration
"""

import logging
import sys
from datetime import datetime
from typing import Any, Dict
import json


class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging"""
    
    def format(self, record: logging.LogRecord) -> str:
        log_data: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # Add custom fields
        if hasattr(record, "user_id"):
            log_data["user_id"] = record.user_id
        if hasattr(record, "project_id"):
            log_data["project_id"] = record.project_id
        if hasattr(record, "request_id"):
            log_data["request_id"] = record.request_id
        if hasattr(record, "duration"):
            log_data["duration_ms"] = record.duration
        
        return json.dumps(log_data)


def setup_logger(name: str, level: str = "INFO") -> logging.Logger:
    """
    Setup structured logger with JSON formatting
    
    Args:
        name: Logger name
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))
    
    # Console handler with JSON formatting
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(JSONFormatter())
    logger.addHandler(console_handler)
    
    # File handler for production
    file_handler = logging.FileHandler("app.log")
    file_handler.setFormatter(JSONFormatter())
    logger.addHandler(file_handler)
    
    return logger


def log_request(logger: logging.Logger, method: str, path: str, user_id: str = None, duration: float = None):
    """
    Log HTTP request with structured data
    
    Args:
        logger: Logger instance
        method: HTTP method
        path: Request path
        user_id: User ID (optional)
        duration: Request duration in ms (optional)
    """
    extra = {}
    if user_id:
        extra["user_id"] = user_id
    if duration:
        extra["duration"] = duration
    
    logger.info(f"{method} {path}", extra=extra)


def log_error(logger: logging.Logger, error: Exception, context: Dict[str, Any] = None):
    """
    Log error with context
    
    Args:
        logger: Logger instance
        error: Exception object
        context: Additional context (optional)
    """
    extra = context or {}
    logger.error(f"Error: {str(error)}", exc_info=True, extra=extra)


def log_metric(logger: logging.Logger, metric_name: str, value: float, tags: Dict[str, str] = None):
    """
    Log application metric
    
    Args:
        logger: Logger instance
        metric_name: Name of metric
        value: Metric value
        tags: Metric tags (optional)
    """
    extra = {"metric_name": metric_name, "metric_value": value}
    if tags:
        extra["tags"] = tags
    logger.info(f"Metric: {metric_name}={value}", extra=extra)


# Default application logger
app_logger = setup_logger("bugrisk", level="INFO")
