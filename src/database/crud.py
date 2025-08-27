from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
import logging
from .models import GuildConfig, TrackedMember, LastPublished

# Set up logging
logger = logging.getLogger(__name__)

# ------------------------------
# Guild Config CRUD Operations
# ------------------------------
def get_guild_config(db: Session, guild_id: int):
    """Get guild configuration for a specific guild"""
    try:
        return db.query(GuildConfig).filter(GuildConfig.guild_id == guild_id).first()
    except SQLAlchemyError as e:
        logger.error(f"Error getting guild config for guild {guild_id}: {e}")
        return None

def set_guild_config(db: Session, guild_id: int, channel_id: int):
    """Set or update guild configuration"""
    try:
        config = get_guild_config(db, guild_id)
        if config:
            config.channel_id = channel_id
            db.add(config)
        else:
            config = GuildConfig(guild_id=guild_id, channel_id=channel_id)
            db.add(config)
        db.commit()
        db.refresh(config)
        return config
    except SQLAlchemyError as e:
        logger.error(f"Error setting guild config for guild {guild_id}: {e}")
        db.rollback()
        return None

# ------------------------------
# Tracked Member CRUD Operations
# ------------------------------
def get_tracked_member(db: Session, guild_id: int, customer_id: int):
    """Check if a member is tracked in a specific guild"""
    try:
        return db.query(TrackedMember).filter(
            TrackedMember.guild_id == guild_id,
            TrackedMember.customer_id == customer_id
        ).first() is not None
    except SQLAlchemyError as e:
        logger.error(f"Error checking tracked member {customer_id} in guild {guild_id}: {e}")
        return False

def add_tracked_member(db: Session, guild_id: int, customer_id: int):
    """Add a member to the tracked list for a specific guild"""
    try:
        if get_tracked_member(db, guild_id, customer_id):
            return False  # Already tracked
        
        tracked_member = TrackedMember(guild_id=guild_id, customer_id=customer_id)
        db.add(tracked_member)
        db.commit()
        return True
    except SQLAlchemyError as e:
        logger.error(f"Error adding tracked member {customer_id} to guild {guild_id}: {e}")
        db.rollback()
        return False

def remove_tracked_member(db: Session, guild_id: int, customer_id: int):
    """Remove a member from the tracked list for a specific guild"""
    try:
        tracked_member = db.query(TrackedMember).filter(
            TrackedMember.guild_id == guild_id,
            TrackedMember.customer_id == customer_id
        ).first()
        
        if not tracked_member:
            return False  # Not tracked
        
        db.delete(tracked_member)
        db.commit()
        return True
    except SQLAlchemyError as e:
        logger.error(f"Error removing tracked member {customer_id} from guild {guild_id}: {e}")
        db.rollback()
        return False

# ------------------------------
# Last Published CRUD Operations
# ------------------------------
def get_last_published(db: Session, guild_id: int, customer_id: int):
    """Get the last published subsession ID for a specific guild and member"""
    try:
        record = db.query(LastPublished).filter(
            LastPublished.guild_id == guild_id,
            LastPublished.customer_id == customer_id
        ).first()
        
        return record.subsession_id if record else None
    except SQLAlchemyError as e:
        logger.error(f"Error getting last published for member {customer_id} in guild {guild_id}: {e}")
        return None

def set_last_published(db: Session, guild_id: int, customer_id: int, subsession_id: str):
    """Set the last published subsession ID for a specific guild and member"""
    try:
        record = db.query(LastPublished).filter(
            LastPublished.guild_id == guild_id,
            LastPublished.customer_id == customer_id
        ).first()
        
        if record:
            record.subsession_id = subsession_id
            db.add(record)
        else:
            record = LastPublished(
                guild_id=guild_id,
                customer_id=customer_id,
                subsession_id=subsession_id
            )
            db.add(record)
        
        db.commit()
        db.refresh(record)
        return record.subsession_id
    except SQLAlchemyError as e:
        logger.error(f"Error setting last published for member {customer_id} in guild {guild_id}: {e}")
        db.rollback()
        return None