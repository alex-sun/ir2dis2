# Database module for iRacing Discord Bot
# Handles SQLite connection, schema initialization, and CRUD operations

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.exc import SQLAlchemyError
import os
import logging

# Set up logging
logger = logging.getLogger(__name__)

# Create base class for models
Base = declarative_base()

# Database configuration
DATABASE_URL = os.environ.get('SQLITE_DB_PATH', '/app/data/iresults.db')
logger.info(f"Using database URL: {DATABASE_URL}")

# Create base class for models
Base = declarative_base()

# Create engine with connection pooling
engine = create_engine(
    f"sqlite:///{DATABASE_URL}",
    echo=False,  # Set to True for debugging
    pool_size=5,
    max_overflow=10,
    pool_timeout=30,
    pool_recycle=1800
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    """Initialize database schema - creates tables if they don't exist"""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database initialized successfully - all tables created")
        return True
    except SQLAlchemyError as e:
        logger.error(f"Failed to initialize database: {e}")
        return False

def get_db():
    """Dependency to get a database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def test_connection():
    """Test database connection"""
    try:
        with SessionLocal() as db:
            result = db.execute(text("SELECT 1"))
            if result.scalar() == 1:
                logger.info("Database connection test passed")
                return True
            else:
                logger.error("Database connection test failed - unexpected result")
                return False
    except SQLAlchemyError as e:
        logger.error(f"Database connection test failed: {e}")
        return False