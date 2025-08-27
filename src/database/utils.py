#!/usr/bin/env python3

"""
Database utility functions for the iRacing Discord Bot.
Provides helper functions for connection management and cleanup.
"""

from src.database import SessionLocal
from src.logging_config import get_logger

logger = get_logger(__name__)

def close_all_connections():
    """Close all active database connections gracefully"""
    logger.info("Closing all database connections...")
    
    # Close any remaining active sessions
    try:
        # In SQLAlchemy 1.4+, we can close all connections via the engine
        from src.database import engine
        engine.dispose()
        logger.info("All database connections closed successfully")
    except Exception as e:
        logger.error(f"Error closing database connections: {str(e)}")
        raise

def cleanup_resources():
    """Clean up all resources before shutdown"""
    logger.info("Starting resource cleanup...")
    
    try:
        close_all_connections()
        logger.info("Resource cleanup completed successfully")
    except Exception as e:
        logger.error(f"Error during resource cleanup: {str(e)}")
        raise