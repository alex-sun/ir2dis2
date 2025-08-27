import os
from src.database import init_db, SessionLocal
from src.database.crud import (
    get_guild_config, set_guild_config,
    get_tracked_member, add_tracked_member, remove_tracked_member,
    get_last_published, set_last_published
)

def test_guild_config_unit():
    """Unit test for guild_config CRUD operations"""
    
    test_db = "/app/test_guild_config_unit.db"
    os.environ['SQLITE_DB_PATH'] = test_db
    
    try:
        init_db()
        
        with SessionLocal() as db:
            # Test set and get
            guild_id = 1
            channel_id = 100
            
            result = set_guild_config(db, guild_id, channel_id)
            assert result is not None
            assert result.guild_id == guild_id
            assert result.channel_id == channel_id
            
            retrieved = get_guild_config(db, guild_id)
            assert retrieved is not None
            assert retrieved.channel_id == channel_id
            
            # Test update
            new_channel_id = 200
            updated = set_guild_config(db, guild_id, new_channel_id)
            assert updated.channel_id == new_channel_id
            
            # Test non-existent
            non_existent = get_guild_config(db, 999)
            assert non_existent is None
            
        print("✓ Guild config unit tests passed")
        
    finally:
        if os.path.exists(test_db):
            os.remove(test_db)

def test_tracked_member_unit():
    """Unit test for tracked_member CRUD operations"""
    
    test_db = "/app/test_tracked_member_unit.db"
    os.environ['SQLITE_DB_PATH'] = test_db
    
    try:
        init_db()
        
        with SessionLocal() as db:
            # Test add
            guild_id = 2
            customer_id = 1001
            
            result = add_tracked_member(db, guild_id, customer_id)
            assert result is True
            
            # Test check
            is_tracked = get_tracked_member(db, guild_id, customer_id)
            assert is_tracked is True
            
            # Test duplicate add
            result = add_tracked_member(db, guild_id, customer_id)
            assert result is False
            
            # Test remove
            result = remove_tracked_member(db, guild_id, customer_id)
            assert result is True
            
            # Test check after remove
            is_tracked = get_tracked_member(db, guild_id, customer_id)
            assert is_tracked is False
            
            # Test remove non-existent
            result = remove_tracked_member(db, guild_id, 9999)
            assert result is False
            
        print("✓ Tracked member unit tests passed")
        
    finally:
        if os.path.exists(test_db):
            os.remove(test_db)

def test_last_published_unit():
    """Unit test for last_published CRUD operations"""
    
    test_db = "/app/test_last_published_unit.db"
    os.environ['SQLITE_DB_PATH'] = test_db
    
    try:
        init_db()
        
        with SessionLocal() as db:
            # Test set and get
            guild_id = 3
            customer_id = 2002
            subsession_id = "20250826_123456"
            
            result = set_last_published(db, guild_id, customer_id, subsession_id)
            assert result == subsession_id
            
            retrieved = get_last_published(db, guild_id, customer_id)
            assert retrieved == subsession_id
            
            # Test update
            new_subsession_id = "20250826_654321"
            updated = set_last_published(db, guild_id, customer_id, new_subsession_id)
            assert updated == new_subsession_id
            
            # Test non-existent
            non_existent = get_last_published(db, 999, 9999)
            assert non_existent is None
            
        print("✓ Last published unit tests passed")
        
    finally:
        if os.path.exists(test_db):
            os.remove(test_db)

def test_integration_unit():
    """Integration test for all operations together"""
    
    test_db = "/app/test_integration_unit.db"
    os.environ['SQLITE_DB_PATH'] = test_db
    
    try:
        init_db()
        
        with SessionLocal() as db:
            guild_id = 4
            customer_id = 3003
            channel_id = 300
            subsession_id = "20250826_Integration"
            
            # Test all operations in sequence
            set_guild_config(db, guild_id, channel_id)
            add_tracked_member(db, guild_id, customer_id)
            set_last_published(db, guild_id, customer_id, subsession_id)
            
            # Verify all data is correct
            config = get_guild_config(db, guild_id)
            assert config.channel_id == channel_id
            
            is_tracked = get_tracked_member(db, guild_id, customer_id)
            assert is_tracked is True
            
            last_published = get_last_published(db, guild_id, customer_id)
            assert last_published == subsession_id
            
        print("✓ Integration unit tests passed")
        
    finally:
        if os.path.exists(test_db):
            os.remove(test_db)

if __name__ == "__main__":
    test_guild_config_unit()
    test_tracked_member_unit()
    test_last_published_unit()
    test_integration_unit()
    print("🎉 All unit tests passed!")