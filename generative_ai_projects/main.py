import asyncio
import os
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timedelta
from jose import jwt

from src.llm.litellm_client import LiteLLMClient
from src.database.session import DatabaseManager
from sqlalchemy.orm import Session
from src.database.models import Ticket, TicketHistory, ChatHistory
import dotenv
from passlib.context import CryptContext

from fastapi.security import HTTPBasic, HTTPBasicCredentials
from src.database.models import User, Ticket, Base
import bcrypt
import litellm
from config.constant_config import Config
from src.utils.constants import (
    PREDEFINED_USERS,
    
)
from typing import Optional, List
from fastapi.responses import JSONResponse

import json
from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
import asyncio
import logging
from pydantic import BaseModel
from src.agents.ticket_agent import TicketManagementAgent
import json
from typing import Optional, List
from pydantic import BaseModel
from fastapi import HTTPException, Depends
from sqlalchemy.orm import Session
from datetime import datetime


logger = logging.getLogger(__name__)


from src.database import (
    db_connection,
    get_db,
    User,
    Ticket,
    TicketHistory,
    ChatHistory,

)


litellm.set_verbose = True

dotenv.load_dotenv()


app = FastAPI(title="YASH Facilities AI API")

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

security = HTTPBasic()

llm_client = LiteLLMClient()


db_manager = DatabaseManager(Config.SQLITE_DB_URL)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


db_connection.create_tables()


# === AUTH DEPENDENCY ===
def get_db() -> Session:
    db = db_manager.get_session()
    try:
        yield db
    finally:
        db.close()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

def get_password_hash(password: str) -> str:
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def authenticate_user(db: Session, username: str, password: str):
    user = db.query(User).filter(User.username == username).first()
    if not user or not verify_password(password, user.hashed_password):
        return None
    return user

# === AUTH APIs ===
class RegisterRequest(BaseModel):
    username: str
    email: str
    full_name: str
    password: str


import re

class LoginRequest(BaseModel):
    username: str
    password: str


@app.on_event("startup")
async def create_default_users():
    db = db_manager.get_session()
    try:
        for user_data in PREDEFINED_USERS:
            existing_user = db.query(User).filter(
                (User.username == user_data["username"]) | 
                (User.email == user_data["email"])
            ).first()

            if existing_user:
                continue
            
            if len(user_data["password"]) < 8:
                print(f"✗ Password for '{user_data['username']}' too short (min 8 chars)")
                continue

            hashed = get_password_hash(user_data["password"])
            new_user = User(
                username=user_data["username"],
                email=user_data["email"],
                full_name=user_data["full_name"],
                hashed_password=hashed,
                role=user_data["role"],
                
            )
            db.add(new_user)
            db.commit()
            print(f"✓ Created user: '{user_data['username']}'")
            
    except Exception as e:
        print(f"✗ Failed to create users: {e}")
        db.rollback()
    finally:
        db.close()

from pydantic import BaseModel
from typing import Optional

class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    full_name: Optional[str] = None
    role: str

class LoginResponse(BaseModel):
    user: UserResponse
    access_token: str
    token_type: str = "bearer"

class LoginRequest(BaseModel):
    username: str
    password: str

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_

# Add these imports to your existing main.py
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

class TicketStatus:
    OPEN = "Open"
    ASSIGNED = "Assigned"
    IN_PROGRESS = "In Progress"
    ON_HOLD = "On Hold"
    ESCALATED = "Escalated"
    RESOLVED = "Resolved"
    CLOSED = "Closed"
    
    ALL_STATUSES = [OPEN, ASSIGNED, IN_PROGRESS, ON_HOLD, ESCALATED, RESOLVED, CLOSED]

class TicketPriority:
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"
    
    ALL_PRIORITIES = [LOW, MEDIUM, HIGH, CRITICAL]

# Escalation thresholds (in hours)
ESCALATION_THRESHOLDS = {
    "Low": 0.0333,      # 2 minutes (for testing)
    "Medium": 0.0333,   # 2 minutes (for testing)
    "High": 0.0333,     # 2 minutes (for testing)
    "Critical": 0.0333  # 2 minutes (for testing)
}


class TicketCreateRequest(BaseModel):
    user_id: str
    category: str
    description: str
    priority: str = "Medium"

class TicketUpdateRequest(BaseModel):
    status: Optional[str] = None
    priority: Optional[str] = None
    assigned_to: Optional[str] = None
    resolution_notes: Optional[str] = None

class TicketResponse(BaseModel):
    ticket_id: str
    user_id: str
    category: str
    description: str
    priority: str
    status: str
    escalated: bool
    escalation_level: int
    assigned_to: Optional[str] = None
    age_hours: float
    hours_until_escalation: float
    created_at: str
    updated_at: Optional[str] = None
    last_action_at: str
    resolved_at: Optional[str] = None
    
    class Config:
        from_attributes = True

class TicketListResponse(BaseModel):
    total: int
    tickets: List[TicketResponse]


def check_and_escalate_tickets(db: Session):
    """
    Background job to check and auto-escalate tickets based on inactivity
    """
    try:
        # Get all non-closed, non-resolved tickets
        active_tickets = db.query(Ticket).filter(
            and_(
                Ticket.status.notin_([TicketStatus.RESOLVED, TicketStatus.CLOSED]),
                Ticket.escalated == False
            )
        ).all()
        
        escalated_count = 0
        now = datetime.utcnow()
        
        for ticket in active_tickets:
            # Calculate hours since last action
            time_since_action = now - ticket.last_action_at
            hours_inactive = time_since_action.total_seconds() / 3600
            
            # Get escalation threshold based on priority
            threshold = ESCALATION_THRESHOLDS.get(ticket.priority, 48)
            
            # Check if ticket should be escalated
            if hours_inactive >= threshold:
                ticket.status = TicketStatus.ESCALATED
                ticket.escalated = True
                ticket.escalation_level += 1
                ticket.updated_at = now
                
                # Add to history
                history = TicketHistory(
                    ticket_id=ticket.ticket_id,
                    changed_by="SYSTEM",
                    old_status=ticket.status,
                    new_status=TicketStatus.ESCALATED,
                    comment=f"Auto-escalated due to {hours_inactive:.1f} hours of inactivity (threshold: {threshold}h)"
                )
                db.add(history)
                escalated_count += 1
        
        if escalated_count > 0:
            db.commit()
            print(f"✓ Auto-escalated {escalated_count} tickets")
    
    except Exception as e:
        print(f"✗ Auto-escalation error: {e}")
        db.rollback()

scheduler = BackgroundScheduler()

@app.on_event("startup")
async def start_scheduler():
    """Start the background scheduler for auto-escalation"""
    if not scheduler.running:
        # Run escalation
        scheduler.add_job(
            func=lambda: check_and_escalate_tickets(db_manager.get_session()),
            trigger=IntervalTrigger(minutes=int(Config.AUTO_ESCALATION_SCHEDULAR)), #TODO: change 24 hours
            id='auto_escalate_tickets',
            name='Auto-escalate inactive tickets',
            replace_existing=True
        )
        scheduler.start()
        print("✓ Auto-escalation scheduler started (runs every 5 minutes)")

@app.on_event("shutdown")
async def shutdown_scheduler():
    """Shutdown the scheduler gracefully"""
    if scheduler.running:
        scheduler.shutdown()



def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=Config.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, Config.SECRET_KEY, algorithm=Config.ALGORITHM)
    return encoded_jwt


@app.on_event("startup")
async def startup_event():
    await create_default_users()


def format_ticket_response(ticket: Ticket) -> TicketResponse:
    """Format ticket for API response with calculated fields"""
    now = datetime.utcnow()
    age = (now - ticket.created_at).total_seconds() / 3600
    threshold = ESCALATION_THRESHOLDS.get(ticket.priority, 48)
    hours_until_escalation = max(0, threshold - age)
    
    return TicketResponse(
        ticket_id=ticket.ticket_id,
        user_id=ticket.user_id,
        category=ticket.category,
        description=ticket.description,
        priority=ticket.priority,
        status=ticket.status,
        escalated=ticket.escalated,
        escalation_level=ticket.escalation_level,
        assigned_to=ticket.assigned_to,
        age_hours=round(age, 2),
        hours_until_escalation=round(hours_until_escalation, 2),
        created_at=ticket.created_at.isoformat(),
        updated_at=ticket.updated_at.isoformat() if ticket.updated_at else None,
        last_action_at=ticket.last_action_at.isoformat(),
        resolved_at=ticket.resolved_at.isoformat() if ticket.resolved_at else None
    )

class SaveChatHistoryRequest(BaseModel):
    user_id: str
    conversation_id: Optional[str] = None
    title: Optional[str] = None
    messages: List[dict]

class UpdateTitleRequest(BaseModel):
    title: str


class ChatRequest(BaseModel):
    user_id: str
    message: str

class ChatResponse(BaseModel):
    success: bool
    response: str
    token_usage: dict
    cost_info: dict
    

@app.post("/api/v1/ticket_agent", response_model=ChatResponse)
async def chat_with_ticket_agent(
    request: ChatRequest,
    db: Session = Depends(get_db)
):
    """Chat with ticket management agent"""
    try:
        logger.info(f"Request from user: {request.user_id}")
        logger.info(f"Message: {request.message}")
        
        ticket_agent = TicketManagementAgent(db_session=db)
        
        loop = asyncio.get_event_loop()
        response = await asyncio.wait_for(
            loop.run_in_executor(
                None,
                ticket_agent.process_message,
                request.message,
                request.user_id
            ),
            timeout=90
        )
        
        return ChatResponse(
            success=True,
            response=response["response"],
            token_usage=response["token_usage"],
            cost_info=response["cost_info"]
        )
        
    except asyncio.TimeoutError:
        logger.error("Request timeout")
        return JSONResponse(
            content={
                "success": False,
                "response": "Request timeout",
                "token_usage": {},
                "cost_info": {},

            },
            status_code=504
        )
    except Exception as e:
        logger.error(f"Error: {str(e)}", exc_info=True)
        return JSONResponse(
            content={
                "success": False,
                "response": f"Error: {str(e)}",
                "token_usage": {},
                "cost_info": {},

            },
            status_code=500
        )
    