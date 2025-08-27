from sqlalchemy import Column, Integer, String, PrimaryKeyConstraint
from . import Base  # This will now work since Base is defined in __init__.py first

class GuildConfig(Base):
    """Table to store per-guild results channel configuration"""
    __tablename__ = 'guild_config'
    
    guild_id = Column(Integer, primary_key=True, index=True)
    channel_id = Column(Integer, nullable=False)

class TrackedMember(Base):
    """Table to store per-server tracking lists (no duplicates)"""
    __tablename__ = 'tracked_member'
    
    guild_id = Column(Integer, index=True)
    customer_id = Column(Integer, index=True)
    
    __table_args__ = (
        PrimaryKeyConstraint('guild_id', 'customer_id'),
    )

class LastPublished(Base):
    """Table to store last published subsession ID for de-duplication"""
    __tablename__ = 'last_published'
    
    guild_id = Column(Integer, index=True)
    customer_id = Column(Integer, index=True)
    subsession_id = Column(String(50), nullable=False)
    
    __table_args__ = (
        PrimaryKeyConstraint('guild_id', 'customer_id'),
    )