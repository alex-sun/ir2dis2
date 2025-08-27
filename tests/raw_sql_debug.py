import os
from src.database import init_db, SessionLocal
from sqlalchemy import text

def raw_sql_debug():
    """Debug using raw SQL to see what's in the database"""
    
    # Use a test database file
    test_db_file = "/app/raw_sql_debug.db"
    os.environ['SQLITE_DB_PATH'] = test_db_file
    
    try:
        # Initialize database
        init_db()
        print("✓ Database initialized")
        
        with SessionLocal() as db:
            guild_id = 123456789
            customer_id = 555555
            
            # Check what tables exist
            result = db.execute(text("SELECT name FROM sqlite_master WHERE type='table';"))
            tables = result.fetchall()
            print(f"Tables in database: {tables}")
            
            # Check if tracked_member table has any rows
            result = db.execute(text(f"SELECT * FROM tracked_member;"))
            rows = result.fetchall()
            print(f"Rows in tracked_member before add: {rows}")
            
            # Try to insert directly with raw SQL
            result = db.execute(text(f"""
                INSERT INTO tracked_member (guild_id, customer_id) 
                VALUES ({guild_id}, {customer_id})
            """))
            db.commit()
            
            # Check again
            result = db.execute(text(f"SELECT * FROM tracked_member;"))
            rows = result.fetchall()
            print(f"Rows in tracked_member after direct insert: {rows}")
            
    finally:
        # Clean up
        if os.path.exists(test_db_file):
            os.remove(test_db_file)

if __name__ == "__main__":
    raw_sql_debug()