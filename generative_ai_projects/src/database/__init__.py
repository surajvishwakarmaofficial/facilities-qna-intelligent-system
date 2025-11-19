"""
Database Module
"""

from .models import Base, User, Ticket, TicketHistory, ChatHistory
from .session import DatabaseManager
from .db_connection import db_connection, get_db, get_db_manager

__all__ = [
    "Base",
    "User",
    "Ticket",
    "TicketHistory",
    "ChatHistory",
    "DatabaseManager",
    "db_connection",
    "get_db",
    "get_db_manager",

]

