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
    
#NOTE: this api for testing purpose only need login from ui (not needed for agent flow)
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
    

#=== FILE UPLOAD and QNA API ===
from fastapi import FastAPI, Request, HTTPException, Depends
from typing import Optional, List
import os
import traceback

from src.rag.rag_core import FacilitiesRAGSystem
from config.constant_config import Config
import dotenv

dotenv.load_dotenv()

rag_system = None

def get_rag_system() -> FacilitiesRAGSystem:
    """Get or initialize RAG system"""
    global rag_system
    if rag_system is None:
        print("[API] Initializing RAG system...")
        rag_system = FacilitiesRAGSystem(knowledge_base_dir=Config.KNOWLEDGE_BASE_DIR)
        success = rag_system.initialize_clients(silent=False)
        if not success:
            raise RuntimeError("Failed to initialize RAG system")
        print("[API] RAG system initialized successfully")

    return rag_system

class FileUploadResponse(BaseModel):
    """Response model for file upload"""
    success: bool
    message: str
    filename: str
    s3_url: Optional[str] = None
    s3_key: Optional[str] = None
    file_size_kb: Optional[float] = None
    chunks_added: Optional[int] = None
    total_chunks: Optional[int] = None
    timestamp: str

class ChatRequest(BaseModel):
    """Request model for chat Q&A"""
    message: str
class SourceInfo(BaseModel):
    """Source document information"""
    title: str
    source: str
    content: str
    file_type: str
    s3_url: Optional[str] = None


class TokenUsage(BaseModel):
    """Token usage information"""
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class ChatResponse(BaseModel):
    """Response model for chat Q&A"""
    success: bool
    message: str
    response: str
    sources: List[SourceInfo]
    token_usage: TokenUsage
    timestamp: str
    
# ==================== Helper Classes ====================

class FormFileWrapper:
    """Wrapper to make form file compatible with process_file"""
    def __init__(self, filename: str, content: bytes):
        self.name = filename
        self.filename = filename
        self._content = content
    
    def getbuffer(self):
        return self._content
    
    def seek(self, pos):
        pass


@app.post("/api/v1/upload_knowledgebase_file", response_model=FileUploadResponse, tags=["Documentsknowledgebase"])
async def upload_document(request: Request):
    """
    Upload and process document for knowledge base
    
    **Form-data required:**
    - file: The document file (PDF, CSV, Excel, TXT)
    
    **Returns:**
    - Success status
    - S3 presigned URL
    - Chunks added information
    """
    print("File upload request received")
    
    try:
        system = get_rag_system()
        
        form = await request.form()
        
        if "file" not in form:
            raise HTTPException(
                status_code=400,
                detail="No file provided. Please upload a file with key 'file' in form-data"
            )
        
        uploaded_file = form["file"]
        
        if not hasattr(uploaded_file, 'filename'):
            raise HTTPException(
                status_code=400,
                detail="Invalid file object in form-data"
            )
        
        filename = uploaded_file.filename
        print(f"[API_UPLOAD] Received file: {filename}")
        
        file_ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
        if file_ext not in system.supported_formats:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": f"Unsupported file format: .{file_ext}",
                    "supported_formats": list(system.supported_formats.keys())
                }
            )
        
        file_content = await uploaded_file.read()
        file_size_bytes = len(file_content)
        file_size_kb = file_size_bytes / 1024
        
        print(f"[API_UPLOAD] File size: {file_size_kb:.2f} KB")
        
        if file_size_bytes == 0:
            raise HTTPException(
                status_code=400,
                detail="Uploaded file is empty (0 bytes)"
            )
        
        wrapped_file = FormFileWrapper(filename, file_content)
        
        print(f"[API_UPLOAD] Processing file...")
        result = system.process_file(wrapped_file)
        
        if isinstance(result, dict):
            success = result.get("success", False)
            s3_url = result.get("s3_url")
            s3_key = result.get("s3_key")
            chunks_added = result.get("chunks_added", 0)
            total_chunks = result.get("total_chunks", 0)
            
            if not success:
                error_msg = result.get("error", "File processing failed")
                raise HTTPException(status_code=500, detail=error_msg)
        else:
            success = result
            if not success:
                raise HTTPException(
                    status_code=500,
                    detail="File processing failed. Check server logs."
                )
            
            stats_after = system.vector_store.get_collection_stats()
            chunks_added = 0
            total_chunks = stats_after.get("num_entities", 0) if stats_after else 0
            s3_url = None
            s3_key = None
        
        print(f"[API_UPLOAD] Upload successful!")
        print(f"[API_UPLOAD] S3 URL: {s3_url}")
        return FileUploadResponse(
            success=True,
            message="Document uploaded and processed successfully",
            filename=filename,
            s3_url=s3_url,
            s3_key=s3_key,
            file_size_kb=round(file_size_kb, 2),
            chunks_added=chunks_added,
            total_chunks=total_chunks,
            timestamp=datetime.utcnow().isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[API_UPLOAD] Error: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Internal server error during file upload",
                "message": str(e)
            }
        )

def count_tokens(text: str) -> int:
    """Estimate token count (rough approximation: 1 token ≈ 4 characters)"""
    return len(text) // 4

@app.post("/api/v1/facility_qna", response_model=ChatResponse, tags=["Chatqna"])
async def chat_query(request: ChatRequest):
    """
    Ask a question to the facilities management assistant
    
    **Request body:**
    - message: The question to ask
    
    **Returns:**
    - Answer to the query
    - Source documents used
    - Token usage information
    """
    print("\n" + "="*60)
    print(f"[API_CHAT] Query received: {request.message}")
    print("="*60)
    
    try:
        system = get_rag_system()
        
        if not request.message or len(request.message.strip()) == 0:
            raise HTTPException(
                status_code=400,
                detail="Message cannot be empty"
            )
        
        if not system.vectorstore:
            raise HTTPException(
                status_code=400,
                detail="Knowledge base not initialized. Please upload documents first."
            )
        
        print("Generating response")
        result = system.generate_response(request.message)
        
        if result.get("error"):
            raise HTTPException(
                status_code=500,
                detail=result.get("answer", "Failed to generate response")
            )
        
        answer = result.get("answer", "")
        source_docs = result.get("sources", [])

        sources = []
        for doc in source_docs:
            sources.append(SourceInfo(
                title=doc.metadata.get("title", "Unknown"),
                source=doc.metadata.get("source", "Unknown"),
                content=doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content,
                file_type=doc.metadata.get("file_type", "unknown"),
                s3_url=doc.metadata.get("s3_url")
            ))
        
        retrieved_docs = system.retrieve_relevant_info(request.message)
        context = "\n\n".join([doc.page_content for doc in retrieved_docs])
        
        prompt_text = f"{context}\n\nQuestion: {request.message}"
        prompt_tokens = count_tokens(prompt_text)
        completion_tokens = count_tokens(answer)
        total_tokens = prompt_tokens + completion_tokens
        
        token_usage = TokenUsage(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens
        )
        
        print(f"[API_CHAT] Response generated successfully")
        print(f"[API_CHAT] Token usage: {total_tokens} tokens")
        print(f"[API_CHAT] Sources: {len(sources)} documents")
        print("="*60 + "\n")
        
        return ChatResponse(
            success=True,
            message="Query processed successfully",
            response=answer,
            sources=sources,
            token_usage=token_usage,
            timestamp=datetime.utcnow().isoformat(),

        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[API_CHAT] Error: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Internal server error during query processing",
                "message": str(e)
            }
        )

