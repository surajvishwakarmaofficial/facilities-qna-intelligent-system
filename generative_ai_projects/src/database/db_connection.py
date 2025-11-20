"""
Database Connection Module
Centralized database session management
"""
from src.database.models import Base
from sqlalchemy.orm import Session
from src.database.session import DatabaseManager
from config.constant_config import Config


class DatabaseConnection:
    """Manages database connections and sessions"""
    
    _instance = None
    _db_manager = None
    
    def __new__(cls):
        """Singleton pattern to ensure single DB manager instance"""
        if cls._instance is None:
            cls._instance = super(DatabaseConnection, cls).__new__(cls)
            cls._db_manager = DatabaseManager(Config.SQLITE_DB_URL)

        return cls._instance
    
    @property
    def manager(self) -> DatabaseManager:
        """Get database manager instance"""
        return self._db_manager
    
    @property
    def engine(self):
        """Get SQLAlchemy engine"""
        return self._db_manager.engine
    
    def get_session(self) -> Session:
        """Get a new database session"""
        return self._db_manager.get_session()
    
    def create_tables(self):
        """Create all database tables"""
        Base.metadata.create_all(bind=self.engine)
        
        print("====== Database is activated and tables are created ======")


# Global database connection instance
db_connection = DatabaseConnection()


def get_db() -> Session:
    """
    FastAPI dependency for database sessions
    
    Usage:
        @app.get("/endpoint")
        async def endpoint(db: Session = Depends(get_db)):
            # use db here
    """
    db = db_connection.get_session()
    try:
        yield db
    finally:
        db.close()


def get_db_manager() -> DatabaseManager:
    """Get the database manager instance"""
    return db_connection.manager


