from sqlalchemy import (
    Column, 
    Integer, 
    String, 
    DateTime, 
    Boolean, 
    Text,
    
)
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import uuid

Base = declarative_base()


class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True)
    role = Column(String, default="user")
    hashed_password = Column(String)
    full_name = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)

class Ticket(Base):
    __tablename__ = 'tickets'
    
    id = Column(Integer, primary_key=True)
    ticket_id = Column(String, unique=True, index=True)
    user_id = Column(String, index=True)
    category = Column(String)
    description = Column(Text)
    priority = Column(String)  # Low, Medium, High, Critical
    status = Column(String, default="Open")  # Open, Assigned, In Progress, On Hold, Escalated, Resolved, Closed
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
    escalated = Column(Boolean, default=False)
    escalation_level = Column(Integer, default=0)  # 0=None, 1=Supervisor, 2=Manager, 3=Director
    assigned_to = Column(String, nullable=True)  # User ID of assigned person
    resolved_at = Column(DateTime, nullable=True)
    resolution_notes = Column(Text, nullable=True)
    last_action_at = Column(DateTime, default=datetime.utcnow)  # Track last activity

class TicketHistory(Base):
    __tablename__ = 'ticket_history'
    
    id = Column(Integer, primary_key=True)
    ticket_id = Column(String, index=True)
    changed_by = Column(String)
    old_status = Column(String)
    new_status = Column(String)
    comment = Column(Text)
    changed_at = Column(DateTime, default=datetime.utcnow)


class Session(Base):
    __tablename__ = 'sessions'
    
    id = Column(Integer, primary_key=True)
    session_id = Column(String, unique=True, index=True)
    user_id = Column(String, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_activity = Column(DateTime, default=datetime.utcnow)
    context = Column(String)  # JSON string

class ChatHistory(Base):
    """
    Chat History Model - Stores conversation history for each user
    """
    __tablename__ = 'chat_history'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    conversation_id = Column(
        String(36), 
        unique=True, 
        index=True, 
        default=lambda: str(uuid.uuid4()),
        nullable=False
    )
    user_id = Column(String, index=True, nullable=False)
    title = Column(String(255), default="", nullable=False)
    messages = Column(Text, nullable=True)  # JSON string
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, 
        default=datetime.utcnow, 
        onupdate=datetime.utcnow, 
        nullable=False
    )
    is_archived = Column(Boolean, default=False, nullable=False)

