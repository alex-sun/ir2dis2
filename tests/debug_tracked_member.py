import os
from src.database import init_db, SessionLocal
from src.database.crud import add_tracked_member

def debug_tracked_member():
    """Debug tracked member issue"""
    
    # Use a test database file
    test_db_file = "/app/debug_tracked_member.db"
    os.environ['SQLITE_DB_PATH'] = test_db_file
    
    try:
        # Initialize database
        init_db()
        print("✓ Database initialized")
        
        with SessionLocal() as db:
            # Test adding a tracked member
            guild_id = 123456789
            customer_id = 555555
            
            print(f"Calling add_tracked_member({guild_id}, {customer_id})")
            result = add_tracked_member(db, guild_id, customer_id)
            print(f"Result: {result}")
            
            # Let's also check what's in the database directly
            from sqlalchemy import text
            result = db.execute(text(f"""
                SELECT * FROM tracked_member 
                WHERE guild_id = {guild_id} AND customer_id = {customer_id}
            """))
            rows = result.fetchall()
            print(f"Rows in tracked_member table: {rows}")
            
    finally:
        # Clean up
        if os.path.exists(test_db_file):
            os.remove(test_db_file)

if __name__ == "__main__":
    debug_tracked_member()