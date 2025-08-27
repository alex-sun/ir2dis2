#!/usr/bin/env python3

"""
Structured logging configuration for the iRacing Discord Bot.
Provides JSON-formatted logging with configurable LOG_LEVEL support.
"""

import os
import logging
import json
from typing import Optional, Dict, Any
from datetime import datetime

class JSONFormatter(logging.Formatter):
    """Custom formatter that outputs logs in JSON format"""
    
    def __init__(self):
        super().__init__()
        self.log_levels = {
            logging.DEBUG: "DEBUG",
            logging.INFO: "INFO",
            logging.WARNING: "WARNING",
            logging.ERROR: "ERROR",
            logging.CRITICAL: "CRITICAL"
        }

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON"""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": self.log_levels.get(record.levelno, "INFO"),
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }

        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        # Add extra fields if they exist
        if hasattr(record, 'extra_fields') and record.extra_fields:
            log_entry.update(record.extra_fields)

        return json.dumps(log_entry)

    def formatException(self, exc_info: tuple) -> str:
        """Format exception information"""
        return logging.Formatter.formatException(self, exc_info).strip()

def setup_logging(log_level: Optional[str] = None) -> logging.Logger:
    """
    Set up structured logging with JSON format.
    
    Args:
        log_level: Optional log level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
                  If not provided, uses LOG_LEVEL environment variable or defaults to INFO.
    
    Returns:
        Configured logger instance
    """
    # Determine log level
    if not log_level:
        log_level = os.environ.get('LOG_LEVEL', 'INFO').upper()
    
    # Validate log level
    numeric_level = getattr(logging, log_level, None)
    if not isinstance(numeric_level, int):
        raise ValueError(f"Invalid LOG_LEVEL: {log_level}. Must be one of: DEBUG, INFO, WARNING, ERROR, CRITICAL")

    # Create logger
    logger = logging.getLogger()
    logger.setLevel(numeric_level)
    logger.propagate = False

    # Remove existing handlers to avoid duplication
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    # Create and add JSON handler
    json_handler = logging.StreamHandler()
    json_handler.setFormatter(JSONFormatter())
    logger.addHandler(json_handler)

    return logger

def get_logger(name: str) -> logging.Logger:
    """Get a configured logger instance"""
    return logging.getLogger(name)

# Helper function to add correlation IDs to log records
def add_correlation_id(logger: logging.Logger, correlation_id: str) -> None:
    """Add correlation ID to all future log records from this logger"""
    if not hasattr(logger, 'correlation_id'):
        logger.correlation_id = correlation_id
        # Monkey patch the makeRecord method to include correlation_id in extra_fields
        original_makeRecord = logger.makeRecord
        
        def makeRecord_with_correlation_id(*args, **kwargs):
            record = original_makeRecord(*args, **kwargs)
            if not hasattr(record, 'extra_fields'):
                record.extra_fields = {}
            record.extra_fields['correlation_id'] = correlation_id
            return record
        
        logger.makeRecord = makeRecord_with_correlation_id

def get_logger_with_correlation(name: str, correlation_id: str) -> logging.Logger:
    """Get a logger with a specific correlation ID"""
    logger = get_logger(name)
    add_correlation_id(logger, correlation_id)
    return logger

def generate_correlation_id() -> str:
    """Generate a unique correlation ID for tracking related events"""
    import uuid
    return str(uuid.uuid4())