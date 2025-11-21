from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config.constant_config import Config
import logging

logger = logging.getLogger(__name__)

engine = create_engine(
    Config.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    pool_recycle=3600,
    connect_args={
        "connect_timeout": 10,
        "options": "-c timezone=utc"
    },
    echo=False  
)


SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_db_manager():
    """Get database manager instance"""
    from .session import DatabaseManager
    return DatabaseManager(Config.DATABASE_URL)

class db_connection:
    """Database connection utilities"""
    
    @staticmethod
    def create_tables():
        """Create all tables in the database"""
        try:
            from .models import Base
            Base.metadata.create_all(bind=engine)
            logger.info("All database tables created successfully")
        except Exception as e:
            logger.error(f"Error creating tables: {e}")
            raise
    
    @staticmethod
    def drop_tables():
        """Drop all tables (use with caution!)"""
        try:
            from .models import Base
            Base.metadata.drop_all(bind=engine)
            logger.info("All database tables dropped")
        except Exception as e:
            logger.error(f"Error dropping tables: {e}")
            raise
    
    @staticmethod
    def test_connection():
        """Test database connection"""
        try:
            from sqlalchemy import text
            with engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                logger.info("Database connection successful")
                return True
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            return False
        



