from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .models import Base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import logging

logger = logging.getLogger(__name__)

Base = declarative_base()

class DatabaseManager:
    """Database manager for handling connections and sessions"""
    
    def __init__(self, database_url: str):
        """
        Initialize database connection for PostgreSQL
        
        Args:
            database_url: PostgreSQL connection string
        """
        self.database_url = database_url
        
        # Create PostgreSQL engine
        self.engine = create_engine(
            database_url,
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
        
        # Create session factory
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )
        
        logger.info("DatabaseManager initialized with PostgreSQL")
    
    def get_session(self):
        """Get a new database session"""
        return self.SessionLocal()
    
    def create_all_tables(self):
        """Create all tables in the database"""
        try:
            Base.metadata.create_all(bind=self.engine)
            logger.info("All tables created successfully")
        except Exception as e:
            logger.error(f"Error creating tables: {e}")
            raise
    
    def drop_all_tables(self):
        """Drop all tables (use with caution!)"""
        try:
            Base.metadata.drop_all(bind=self.engine)
            logger.info("All tables dropped")
        except Exception as e:
            logger.error(f"Error dropping tables: {e}")
            raise
    
    def close(self):
        """Close all connections"""
        self.engine.dispose()
        logger.info("✓ Database connections closed")
