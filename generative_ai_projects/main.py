import os
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import redis
import uuid
from datetime import datetime, timedelta
from jose import jwt

from src.llm.litellm_client import LiteLLMClient
from src.rag.vector_store import MilvusStore
from src.rag.retriever import KnowledgeRetriever
from src.agents.facilities_agent import FacilitiesAgent
from src.database.session import DatabaseManager
from sqlalchemy.orm import Session
from src.database.models import Ticket, TicketHistory, ChatHistory
from src.utils.rate_limiter import RateLimiter
from src.utils.cache import ResponseCache
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

litellm.set_verbose = True

dotenv.load_dotenv()


app = FastAPI(title="YASH Facilities AI API")

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

security = HTTPBasic()

llm_client = LiteLLMClient()

vector_store = MilvusStore(
    uri=os.environ.get("MILVUS_URI"),
    token=os.environ.get("MILVUS_TOKEN")
)

retriever = KnowledgeRetriever(vector_store, llm_client)
agent = FacilitiesAgent(llm_client, retriever)
db_manager = DatabaseManager(Config.SQLITE_DB_URL)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# Create tables
Base.metadata.create_all(bind=db_manager.engine)

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

@app.post("/api/register")
async def register(request: RegisterRequest, db: Session = Depends(get_db)):
    password = request.password.strip()
    
    if len(password) < 8:
        raise HTTPException(
            status_code=400,
            detail="Password must be min 8 characters"
        )
    
    if db.query(User).filter(User.username == request.username).first():
        raise HTTPException(400, "Username already exists")
    if db.query(User).filter(User.email == request.email).first():
        raise HTTPException(400, "Email already registered")
    
    hashed = get_password_hash(password)
    new_user = User(
        username=request.username,
        email=request.email,
        full_name=request.full_name,
        hashed_password=hashed
    )
    db.add(new_user)
    db.commit()
    return {"message": "Account created! Login with your 8-char password."}


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


@app.post("/api/login", response_model=LoginResponse)
async def login(request: LoginRequest, db: Session = Depends(get_db)):
    user = authenticate_user(db, request.username, request.password)

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(
        data={"sub": user.username}
    )
    data = {
        "status": 200,
        "message": "Login successful",
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role,

        },
        "access_token": access_token,
        "token_type": "bearer",
    }

    return data

@app.on_event("startup")
async def startup_event():
    await create_default_users()

@app.get("/health")
async def health(): return {"status": "YASH Facilities AI READY", "auto_escalation": "ACTIVE"}


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



@app.post("/api/tickets/create", response_model=TicketResponse)
async def create_ticket(request: TicketCreateRequest, db: Session = Depends(get_db)):
    """Create a new ticket"""
    if request.priority not in TicketPriority.ALL_PRIORITIES:
        raise HTTPException(400, f"Invalid priority. Must be one of: {', '.join(TicketPriority.ALL_PRIORITIES)}")
    
    ticket_id = f"YASH-{uuid.uuid4().hex[:8].upper()}"
    
    ticket = Ticket(
        ticket_id=ticket_id,
        user_id=request.user_id,
        category=request.category,
        description=request.description,
        priority=request.priority,
        status=TicketStatus.OPEN,
        escalated=False,
        escalation_level=0,
        last_action_at=datetime.utcnow()
    )
    
    db.add(ticket)
    
    history = TicketHistory(
        ticket_id=ticket_id,
        changed_by=request.user_id,
        old_status=None,
        new_status=TicketStatus.OPEN,
        comment="Ticket created"
    )
    db.add(history)
    
    db.commit()
    db.refresh(ticket)
    
    return format_ticket_response(ticket)


@app.get("/api/tickets/{ticket_id}", response_model=TicketResponse)
async def get_ticket_by_id(ticket_id: str, db: Session = Depends(get_db)):
    """Get a single ticket by ID"""
    ticket = db.query(Ticket).filter(Ticket.ticket_id == ticket_id).first()
    
    if not ticket:
        raise HTTPException(404, f"Ticket {ticket_id} not found")
    
    return format_ticket_response(ticket)


@app.get("/api/tickets/user/{user_id}", response_model=TicketListResponse)
async def get_user_tickets(
    user_id: str,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Get all tickets for a specific user"""
    query = db.query(Ticket).filter(Ticket.user_id == user_id)
    
    if status:
        query = query.filter(Ticket.status == status)
    
    if priority:
        query = query.filter(Ticket.priority == priority)
    
    tickets = query.order_by(Ticket.created_at.desc()).limit(limit).all()
    
    return TicketListResponse(
        total=len(tickets),
        tickets=[format_ticket_response(t) for t in tickets]
    )



@app.get("/api/tickets/all", response_model=TicketListResponse)
async def get_all_tickets(
    status: Optional[str] = None,
    priority: Optional[str] = None,
    escalated: Optional[bool] = None,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    breakpoint()
    """Get all tickets with filters"""
    query = db.query(Ticket)
    
    if status:
        query = query.filter(Ticket.status == status)
    
    if priority:
        query = query.filter(Ticket.priority == priority)
    
    if escalated is not None:
        query = query.filter(Ticket.escalated == escalated)
    
    tickets = query.order_by(Ticket.created_at.desc()).limit(limit).all()
    
    return TicketListResponse(
        total=len(tickets),
        tickets=[format_ticket_response(t) for t in tickets]
    )


@app.patch("/api/tickets/{ticket_id}/status", response_model=TicketResponse)
async def update_ticket_status(
    ticket_id: str,
    request: TicketUpdateRequest,
    user_id: str,
    db: Session = Depends(get_db)
):
    """Update ticket status, priority, or assignment"""
    ticket = db.query(Ticket).filter(Ticket.ticket_id == ticket_id).first()
    
    if not ticket:
        raise HTTPException(404, f"Ticket {ticket_id} not found")
    
    old_status = ticket.status
    changes = []
    
    if request.status:
        if request.status not in TicketStatus.ALL_STATUSES:
            raise HTTPException(400, f"Invalid status")
        
        ticket.status = request.status
        ticket.last_action_at = datetime.utcnow()
        changes.append(f"Status: {old_status} → {request.status}")
        
        if request.status == TicketStatus.ESCALATED:
            ticket.escalated = True
            ticket.escalation_level += 1
        elif request.status in [TicketStatus.RESOLVED, TicketStatus.CLOSED]:
            ticket.resolved_at = datetime.utcnow()
            ticket.escalated = False
    
    if request.priority:
        if request.priority not in TicketPriority.ALL_PRIORITIES:
            raise HTTPException(400, f"Invalid priority")
        old_priority = ticket.priority
        ticket.priority = request.priority
        changes.append(f"Priority: {old_priority} → {request.priority}")
    
    if request.assigned_to:
        ticket.assigned_to = request.assigned_to
        ticket.last_action_at = datetime.utcnow()
        changes.append(f"Assigned to: {request.assigned_to}")
    
    if request.resolution_notes:
        ticket.resolution_notes = request.resolution_notes
    
    ticket.updated_at = datetime.utcnow()
    
    history = TicketHistory(
        ticket_id=ticket_id,
        changed_by=user_id,
        old_status=old_status,
        new_status=ticket.status,
        comment="; ".join(changes)
    )
    db.add(history)
    
    db.commit()
    db.refresh(ticket)
    
    return format_ticket_response(ticket)


@app.get("/api/tickets/{ticket_id}/history")
async def get_ticket_history(ticket_id: str, db: Session = Depends(get_db)):
    """Get ticket history"""
    ticket = db.query(Ticket).filter(Ticket.ticket_id == ticket_id).first()
    if not ticket:
        raise HTTPException(404, f"Ticket {ticket_id} not found")
    
    history = db.query(TicketHistory).filter(
        TicketHistory.ticket_id == ticket_id
    ).order_by(TicketHistory.changed_at.desc()).all()
    
    return {
        "ticket_id": ticket_id,
        "history": [
            {
                "changed_by": h.changed_by,
                "old_status": h.old_status,
                "new_status": h.new_status,
                "comment": h.comment,
                "changed_at": h.changed_at.isoformat()
            }
            for h in history
        ]
    }


@app.post("/api/tickets/{ticket_id}/escalate")
async def manual_escalate_ticket(
    ticket_id: str,
    user_id: str,
    reason: Optional[str] = "Manual escalation",
    db: Session = Depends(get_db)
):
    """Manually escalate a ticket"""
    ticket = db.query(Ticket).filter(Ticket.ticket_id == ticket_id).first()
    
    if not ticket:
        raise HTTPException(404, f"Ticket {ticket_id} not found")
    
    if ticket.status in [TicketStatus.RESOLVED, TicketStatus.CLOSED]:
        raise HTTPException(400, "Cannot escalate resolved or closed tickets")
    
    old_status = ticket.status
    ticket.status = TicketStatus.ESCALATED
    ticket.escalated = True
    ticket.escalation_level += 1
    ticket.updated_at = datetime.utcnow()
    ticket.last_action_at = datetime.utcnow()
    
    history = TicketHistory(
        ticket_id=ticket_id,
        changed_by=user_id,
        old_status=old_status,
        new_status=TicketStatus.ESCALATED,
        comment=f"Manual escalation: {reason}"
    )
    db.add(history)
    
    db.commit()
    
    return {
        "message": f"Ticket {ticket_id} escalated successfully",
        "escalation_level": ticket.escalation_level
    }



@app.get("/api/tickets/stats/dashboard")
async def get_ticket_stats(db: Session = Depends(get_db)):
    """Get ticket statistics"""
    total = db.query(Ticket).count()
    open_tickets = db.query(Ticket).filter(Ticket.status == TicketStatus.OPEN).count()
    in_progress = db.query(Ticket).filter(Ticket.status == TicketStatus.IN_PROGRESS).count()
    escalated = db.query(Ticket).filter(Ticket.escalated == True).count()
    resolved = db.query(Ticket).filter(Ticket.status == TicketStatus.RESOLVED).count()
    
    critical = db.query(Ticket).filter(
        and_(
            Ticket.priority == TicketPriority.CRITICAL,
            Ticket.status.notin_([TicketStatus.RESOLVED, TicketStatus.CLOSED])
        )
    ).count()
    
    high = db.query(Ticket).filter(
        and_(
            Ticket.priority == TicketPriority.HIGH,
            Ticket.status.notin_([TicketStatus.RESOLVED, TicketStatus.CLOSED])
        )
    ).count()
    
    return {
        "total_tickets": total,
        "open": open_tickets,
        "in_progress": in_progress,
        "escalated": escalated,
        "resolved": resolved,
        "active_critical": critical,
        "active_high": high,
        "resolution_rate": round((resolved / total * 100) if total > 0 else 0, 2)
    }

@app.post("/api/admin/run-escalation")
async def manual_run_escalation(db: Session = Depends(get_db)):
    """Manually trigger escalation check"""
    check_and_escalate_tickets(db)
    return {"message": "Escalation check completed"}


import json
from typing import Optional, List
from pydantic import BaseModel
from fastapi import HTTPException, Depends
from sqlalchemy.orm import Session
from datetime import datetime
import uuid

class SaveChatHistoryRequest(BaseModel):
    user_id: str
    conversation_id: Optional[str] = None
    title: Optional[str] = None
    messages: List[dict]

class UpdateTitleRequest(BaseModel):
    title: str

@app.post("/api/chat-history/save")
async def save_or_update_chat_history(request: SaveChatHistoryRequest, db: Session = Depends(get_db)):
    """
    Saves a new chat or updates an existing one with corrected title logic.
    """
    try:
        chat = None
        # Try to find an existing chat if an ID is provided
        if request.conversation_id:
            chat = db.query(ChatHistory).filter(
                ChatHistory.conversation_id == request.conversation_id,
                ChatHistory.user_id == request.user_id
            ).first()

        # If an existing chat is found, update it
        if chat:
            # Update title only if provided and not empty
            if request.title and request.title.strip():
                chat.title = request.title
            # If title is still "New Chat" and we have messages, update with first message
            elif chat.title == "New Chat" and request.messages:
                first_user_msg = next((msg for msg in request.messages if msg.get('role') == 'user'), None)
                if first_user_msg:
                    content = first_user_msg.get('content', '')
                    chat.title = content[:100] if len(content) > 100 else content
            
            chat.messages = json.dumps(request.messages)
            chat.updated_at = datetime.utcnow()
        
        # If no chat was found (it's a new conversation)
        else:
            new_conv_id = request.conversation_id or str(uuid.uuid4())
            
            # Determine title: use provided title, or first user message, or "New Chat"
            title = "New Chat"
            if request.title and request.title.strip():
                title = request.title
            elif request.messages:
                first_user_msg = next((msg for msg in request.messages if msg.get('role') == 'user'), None)
                if first_user_msg:
                    content = first_user_msg.get('content', '')
                    title = content[:100] if len(content) > 100 else content
            
            chat = ChatHistory(
                conversation_id=new_conv_id,
                user_id=request.user_id,
                title=title,
                messages=json.dumps(request.messages),
                is_archived=False  # Explicitly set to False
            )
            db.add(chat)
        
        db.commit()
        db.refresh(chat)
        return {
            "success": True, 
            "conversation_id": chat.conversation_id,
            "title": chat.title
        }
    except Exception as e:
        db.rollback()
        print(f"Error saving chat: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to save chat history: {str(e)}")

@app.get("/api/chat-history/{user_id}")
async def get_user_chat_histories(user_id: str, db: Session = Depends(get_db)):
    """Gets all non-archived chat histories for a user."""
    try:
        # First, let's check ALL records for this user (including archived)
        all_chats = db.query(ChatHistory).filter(
            ChatHistory.user_id == user_id
        ).all()
        
        print(f"\n=== DEBUG: Total chats for user {user_id}: {len(all_chats)} ===")
        for chat in all_chats:
            print(f"ID: {chat.conversation_id}, Title: {chat.title}, Archived: {chat.is_archived}, Updated: {chat.updated_at}")
        
        # Now get only non-archived
        histories = db.query(ChatHistory).filter(
            ChatHistory.user_id == user_id,
            ChatHistory.is_archived == False
        ).order_by(ChatHistory.updated_at.desc()).all()

        print(f"=== Non-archived chats: {len(histories)} ===\n")

        return {
            "success": True,
            "histories": [{
                "conversation_id": h.conversation_id,
                "title": h.title,
                "updated_at": h.updated_at.isoformat() + 'Z',
                "created_at": h.created_at.isoformat() + 'Z',
                "is_archived": h.is_archived
            } for h in histories]
        }
    except Exception as e:
        print(f"Error fetching histories: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch histories: {str(e)}")

@app.get("/api/chat-history/conversation/{conversation_id}")
async def get_conversation_details(conversation_id: str, db: Session = Depends(get_db)):
    """Gets the full message list for a specific conversation."""
    try:
        chat = db.query(ChatHistory).filter(ChatHistory.conversation_id == conversation_id).first()
        if not chat:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        return {
            "success": True,
            "messages": json.loads(chat.messages or '[]'),
            "title": chat.title
        }
    except Exception as e:
        print(f"Error fetching conversation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch conversation: {str(e)}")

@app.patch("/api/chat-history/{conversation_id}/title")
async def update_chat_title(conversation_id: str, request: UpdateTitleRequest, db: Session = Depends(get_db)):
    """Updates the title of a conversation."""
    try:
        chat = db.query(ChatHistory).filter(ChatHistory.conversation_id == conversation_id).first()
        if not chat:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        chat.title = request.title
        chat.updated_at = datetime.utcnow()
        db.commit()
        return {"success": True, "title": chat.title}
    except Exception as e:
        db.rollback()
        print(f"Error updating title: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update title: {str(e)}")

@app.delete("/api/chat-history/{conversation_id}")
async def delete_chat_history(conversation_id: str, db: Session = Depends(get_db)):
    """Deletes (archives) a conversation."""
    try:
        chat = db.query(ChatHistory).filter(ChatHistory.conversation_id == conversation_id).first()
        if not chat:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        chat.is_archived = True
        chat.updated_at = datetime.utcnow()
        db.commit()
        return {"success": True, "message": "Chat deleted"}
    except Exception as e:
        db.rollback()
        print(f"Error deleting chat: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete chat: {str(e)}")

@app.get("/api/chat-history/debug/{user_id}")
async def debug_chat_histories(user_id: str, db: Session = Depends(get_db)):
    """Debug endpoint to see all chats including archived ones"""
    try:
        all_chats = db.query(ChatHistory).filter(
            ChatHistory.user_id == user_id
        ).order_by(ChatHistory.updated_at.desc()).all()

        return {
            "success": True,
            "total_count": len(all_chats),
            "chats": [{
                "conversation_id": h.conversation_id,
                "title": h.title,
                "is_archived": h.is_archived,
                "updated_at": h.updated_at.isoformat() + 'Z',
                "created_at": h.created_at.isoformat() + 'Z',
                "message_count": len(json.loads(h.messages or '[]'))
            } for h in all_chats]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch debug info: {str(e)}")
    