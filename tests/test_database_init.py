import os
from sqlalchemy import inspect, text
from src.database import init_db, engine, SessionLocal
from src.database.models import GuildConfig, TrackedMember, LastPublished

def test_database_connection():
    """Test that database connection works and models are properly defined"""
    
    # Use the default database path
    default_db_path = "/app/data/iresults.db"
    os.makedirs(os.path.dirname(default_db_path), exist_ok=True)
    os.environ['SQLITE_DB_PATH'] = default_db_path
    
    try:
        # Initialize the database (creates tables)
        from src.database import init_db
        success = init_db()
        assert success, "Database initialization failed"
        print("✓ Database initialization test passed")
        
        # Test engine creation and connection
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            assert result.scalar() == 1, "Basic SQL query failed"
        print("✓ Database connection test passed")
        
        # Test that models are properly registered with Base.metadata
        from src.database import Base
        tables = Base.metadata.tables.keys()
        assert 'guild_config' in tables, "guild_config model not registered"
        assert 'tracked_member' in tables, "tracked_member model not registered"
        assert 'last_published' in tables, "last_published model not registered"
        print(f"✓ Registered models: {tables}")
        
        # Test session creation
        with SessionLocal() as db:
           # Test basic model operations
           # Check if record already exists to avoid UNIQUE constraint violation
           existing_config = db.query(GuildConfig).filter(GuildConfig.guild_id == 123456789).first()
           
           if existing_config:
               # Update existing record
               existing_config.channel_id = 987654321
               db.commit()
               print("✓ Updated existing guild config record")
           else:
               # Insert new record
               test_config = GuildConfig(guild_id=123456789, channel_id=987654321)
               db.add(test_config)
               db.commit()
               print("✓ Inserted new guild config record")
           
           # Verify the record
           retrieved = db.query(GuildConfig).filter(GuildConfig.guild_id == 123456789).first()
           assert retrieved is not None, "Could not retrieve test record"
           assert retrieved.channel_id == 987654321, "Retrieved record has wrong channel_id"
           
           print("✓ Session and basic CRUD test passed")
            
    except Exception as e:
        print(f"✗ Test failed: {e}")
        raise

if __name__ == "__main__":
    test_database_connection()