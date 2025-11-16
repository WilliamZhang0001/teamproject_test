from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from .config import settings

# Use SQLite for development
engine = create_engine(settings.sql_url, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

class Base(DeclarativeBase):
    pass

def create_tables():
    """Create database tables"""
    try:
        Base.metadata.create_all(bind=engine)
        print("Database tables created successfully")
        
        # Check and add missing columns if needed
        from sqlalchemy import inspect, text
        inspector = inspect(engine)
        
        # Check if extraction_records table exists and has literature_id column
        if 'extraction_records' in inspector.get_table_names():
            columns = [col['name'] for col in inspector.get_columns('extraction_records')]
            if 'literature_id' not in columns:
                print("Adding missing 'literature_id' column to extraction_records table...")
                with engine.connect() as conn:
                    # Add column
                    conn.execute(text("""
                        ALTER TABLE extraction_records 
                        ADD COLUMN literature_id INT
                    """))
                    # Add index
                    conn.execute(text("""
                        ALTER TABLE extraction_records 
                        ADD INDEX idx_literature_id (literature_id)
                    """))
                    # Add foreign key constraint
                    conn.execute(text("""
                        ALTER TABLE extraction_records 
                        ADD CONSTRAINT fk_extraction_literature FOREIGN KEY (literature_id)
                        REFERENCES literature(id) ON DELETE CASCADE
                    """))
                    conn.commit()
                print("Successfully added 'literature_id' column")
    except Exception as e:
        print(f"Error creating tables: {e}")

def init_db():
    """Initialize database - create tables if they don't exist"""
    try:
        create_tables()
        print("Database initialization completed")
    except Exception as e:
        print(f"Error initializing database: {e}")
        import traceback
        traceback.print_exc()
