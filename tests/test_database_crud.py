import os
from src.database import init_db, engine, SessionLocal
from src.database.crud import (
    get_guild_config, set_guild_config,
    get_tracked_member, add_tracked_member, remove_tracked_member,
    get_last_published, set_last_published
)

def test_guild_config_crud():
    """Test CRUD operations for guild_config table"""
    
    # Use a test database file
    test_db_file = "/app/test_guild_config.db"
    os.environ['SQLITE_DB_PATH'] = test_db_file
    
    try:
        # Initialize database
        init_db()
        print("✓ Guild config test: Database initialized")
        
        with SessionLocal() as db:
            # Test 1: Set guild config
            guild_id = 123456789
            channel_id = 987654321
            
            result = set_guild_config(db, guild_id, channel_id)
            assert result is not None, "set_guild_config should return a config object"
            assert result.guild_id == guild_id, "set_guild_config returned wrong guild_id"
            assert result.channel_id == channel_id, "set_guild_config returned wrong channel_id"
            print("✓ Guild config test: Set operation passed")
            
            # Test 2: Get guild config
            retrieved = get_guild_config(db, guild_id)
            assert retrieved is not None, "get_guild_config should return a config object"
            assert retrieved.channel_id == channel_id, "get_guild_config returned wrong channel_id"
            print("✓ Guild config test: Get operation passed")
            
            # Test 3: Update guild config
            new_channel_id = 112233445
            updated = set_guild_config(db, guild_id, new_channel_id)
            assert updated.channel_id == new_channel_id, "set_guild_config failed to update"
            print("✓ Guild config test: Update operation passed")
            
    finally:
        # Clean up
        if os.path.exists(test_db_file):
            os.remove(test_db_file)

def test_tracked_member_crud():
    """Test CRUD operations for tracked_member table"""
    
    # Use a test database file
    test_db_file = "/app/test_tracked_member.db"
    os.environ['SQLITE_DB_PATH'] = test_db_file
    
    try:
        # Initialize database
        init_db()
        print("✓ Tracked member test: Database initialized")
        
        with SessionLocal() as db:
            # Test 1: Add tracked member
            guild_id = 123456789
            customer_id = 555555
            
            result = add_tracked_member(db, guild_id, customer_id)
            assert result is True, "add_tracked_member should return True"
            print("✓ Tracked member test: Add operation passed")
            
            # Test 2: Check if member is tracked
            is_tracked = get_tracked_member(db, guild_id, customer_id)
            assert is_tracked is True, "get_tracked_member should return True for tracked member"
            print("✓ Tracked member test: Check operation passed")
            
            # Test 3: Try to add the same member again (should fail)
            result = add_tracked_member(db, guild_id, customer_id)
            assert result is False, "add_tracked_member should return False for duplicate"
            print("✓ Tracked member test: Duplicate add operation passed")
            
            # Test 4: Remove tracked member
            result = remove_tracked_member(db, guild_id, customer_id)
            assert result is True, "remove_tracked_member should return True"
            print("✓ Tracked member test: Remove operation passed")
            
            # Test 5: Check if member is no longer tracked
            is_tracked = get_tracked_member(db, guild_id, customer_id)
            assert is_tracked is False, "get_tracked_member should return False for removed member"
            print("✓ Tracked member test: Removed check operation passed")
            
    finally:
        # Clean up
        if os.path.exists(test_db_file):
            os.remove(test_db_file)

if __name__ == "__main__":
    test_guild_config_crud()
    print()
    test_tracked_member_crud()
    def test_last_published_crud():
        """Test CRUD operations for last_published table"""
        
        # Use a test database file
        test_db_file = "/app/test_last_published.db"
        os.environ['SQLITE_DB_PATH'] = test_db_file
        
        try:
            # Initialize database
            init_db()
            print("✓ Last published test: Database initialized")
            
            with SessionLocal() as db:
                # Test 1: Set last published subsession
                guild_id = 123456789
                customer_id = 555555
                subsession_id = "20250826_123456"
                
                result = set_last_published(db, guild_id, customer_id, subsession_id)
                assert result == subsession_id, "set_last_published should return the subsession_id"
                print("✓ Last published test: Set operation passed")
                
                # Test 2: Get last published subsession
                retrieved = get_last_published(db, guild_id, customer_id)
                assert retrieved == subsession_id, "get_last_published should return the correct subsession_id"
                print("✓ Last published test: Get operation passed")
                
                # Test 3: Update last published subsession
                new_subsession_id = "20250826_654321"
                updated = set_last_published(db, guild_id, customer_id, new_subsession_id)
                assert updated == new_subsession_id, "set_last_published failed to update"
                print("✓ Last published test: Update operation passed")
                
        finally:
            # Clean up
            if os.path.exists(test_db_file):
                os.remove(test_db_file)
    
    def test_all_crud_operations():
        """Test all CRUD operations together to ensure they work in harmony"""
        
        # Use a test database file
        test_db_file = "/app/test_all_crud.db"
        os.environ['SQLITE_DB_PATH'] = test_db_file
        
        try:
            # Initialize database
            init_db()
            print("✓ All CRUD test: Database initialized")
            
            with SessionLocal() as db:
                guild_id = 123456789
                customer_id = 555555
                channel_id = 987654321
                subsession_id = "20250826_123456"
                
                # Test all operations in sequence
                set_guild_config(db, guild_id, channel_id)
                add_tracked_member(db, guild_id, customer_id)
                set_last_published(db, guild_id, customer_id, subsession_id)
                
                # Verify all data is correct
                config = get_guild_config(db, guild_id)
                assert config.channel_id == channel_id, "Guild config mismatch"
                
                is_tracked = get_tracked_member(db, guild_id, customer_id)
                assert is_tracked is True, "Tracked member mismatch"
                
                last_published = get_last_published(db, guild_id, customer_id)
                assert last_published == subsession_id, "Last published mismatch"
                
                print("✓ All CRUD test: Sequential operations passed")
                
        finally:
            # Clean up
            if os.path.exists(test_db_file):
                os.remove(test_db_file)
    
    if __name__ == "__main__":
        test_guild_config_crud()
        print()
        test_tracked_member_crud()
        print()
        test_last_published_crud()
        print()
        test_all_crud_operations()
        print()
        print("🎉 All CRUD tests passed!")