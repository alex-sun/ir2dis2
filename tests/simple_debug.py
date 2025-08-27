import os
from src.database import init_db, SessionLocal
from src.database.crud import get_tracked_member, add_tracked_member

def simple_debug():
    """Simple debug test"""
    
    # Use a test database file
    test_db_file = "/app/simple_debug.db"
    os.environ['SQLITE_DB_PATH'] = test_db_file
    
    try:
        # Initialize database
        init_db()
        print("✓ Database initialized")
        
        with SessionLocal() as db:
            # Test 1: Check if member is tracked (should be False)
            guild_id = 123456789
            customer_id = 555555
            
            is_tracked = get_tracked_member(db, guild_id, customer_id)
            print(f"Test 1 - Is member tracked before adding? {is_tracked} (expected: False)")
            
            # Test 2: Add tracked member
            result = add_tracked_member(db, guild_id, customer_id)
            print(f"Test 2 - Add result: {result} (expected: True)")
            
            # Test 3: Check if member is tracked (should be True)
            is_tracked = get_tracked_member(db, guild_id, customer_id)
            print(f"Test 3 - Is member tracked after adding? {is_tracked} (expected: True)")
            
    finally:
        # Clean up
        if os.path.exists(test_db_file):
            os.remove(test_db_file)

if __name__ == "__main__":
    simple_debug()