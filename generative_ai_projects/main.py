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
from src.database.models import Ticket
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

# Models & Endpoints (same as before)
class QueryRequest(BaseModel): user_id: str; query: str; session_id: Optional[str] = None
class QueryResponse(BaseModel): response: str; session_id: str; timestamp: str
class TicketRequest(BaseModel): user_id: str; category: str; description: str; priority: str = "Medium"
class TicketResponse(BaseModel): ticket_id: str; status: str; message: str

@app.post("/api/query", response_model=QueryResponse)
async def handle_query(request: QueryRequest):
    if not rate_limiter.is_allowed(request.user_id):
        raise HTTPException(429, "Rate limit exceeded")
    session_id = request.session_id or str(uuid.uuid4())
    response = await agent.handle_query(request.user_id, request.query, session_id)
    result = {"response": response, "session_id": session_id, "timestamp": datetime.utcnow().isoformat()}
    return QueryResponse(**result)

@app.post("/api/tickets", response_model=TicketResponse)
async def create_ticket(request: TicketRequest):
    db = db_manager.get_session()
    ticket_id = f"YASH-{uuid.uuid4().hex[:6].upper()}"
    ticket = Ticket(ticket_id=ticket_id, user_id=request.user_id, category=request.category,
                    description=request.description, priority=request.priority, status="Open", escalated=False)
    db.add(ticket); db.commit()
    return TicketResponse(ticket_id=ticket_id, status="Open", message="Ticket created!")

@app.get("/api/tickets/{ticket_id}")
async def get_ticket(ticket_id: str):
    db = db_manager.get_session()
    t = db.query(Ticket).filter_by(ticket_id=ticket_id).first()
    if not t: raise HTTPException(404, "Not found")
    age = round((datetime.utcnow() - t.created_at).total_seconds() / 3600, 1)
    return {**t.__dict__, "age_hours": age, "escalated": t.escalated}

@app.get("/api/ticket/{ticket_id}")
async def get_single_ticket(ticket_id: str):
    db = db_manager.get_session()
    try:
        t = db.query(Ticket).filter(Ticket.ticket_id == ticket_id).first()
        if not t:
            raise HTTPException(404, "Not found")
        age = (datetime.utcnow() - t.created_at).total_seconds() / 3600
        hours_until_escalation = max(0, 24 - age)
        return {
            "ticket_id": t.ticket_id,
            "category": t.category,
            "priority": t.priority,
            "status": t.status,
            "escalated": t.escalated,
            "description": t.description,
            "age_hours": round(age, 1),
            "hours_until_escalation": round(hours_until_escalation, 1),
            "created_at": t.created_at.isoformat(),
            "updated_at": t.updated_at.isoformat() if t.updated_at else None
        }
    finally:
        db.close()

@app.patch("/api/tickets/{ticket_id}/status")
async def update_ticket_status(ticket_id: str, status: str, db: Session = Depends(get_db)):
    if status not in ["Open", "In Progress", "Escalated", "Resolved"]:
        raise HTTPException(400, "Invalid status")

    ticket = db.query(Ticket).filter(Ticket.ticket_id == ticket_id).first()
    if not ticket:
        raise HTTPException(404, "Ticket not found")

    ticket.status = status
    if status == "Escalated":
        ticket.escalated = True
    if status == "Resolved":
        ticket.escalated = False
    db.commit()
    return {"message": f"Ticket {ticket_id} → {status}"}

@app.get("/api/my-tickets/{user_id}")
async def get_my_tickets(user_id: str):
    db = db_manager.get_session()
    try:
        tickets = db.query(Ticket).filter(Ticket.user_id == user_id)\
                  .order_by(Ticket.created_at.desc()).all()
        
        result = []
        for t in tickets:
            age = (datetime.utcnow() - t.created_at).total_seconds() / 3600
            result.append({
                "ticket_id": t.ticket_id,
                "category": t.category,
                "priority": t.priority,
                "status": t.status,
                "escalated": t.escalated,
                "description": t.description,
                "age_hours": round(age, 1),
                "created_at": t.created_at.isoformat()
            })
        return {"tickets": result}
    except Exception as e:
        raise HTTPException(500, f"DB Error: {str(e)}")
    finally:
        db.close()

@app.get("/health")
async def health(): return {"status": "YASH Facilities AI READY", "auto_escalation": "ACTIVE"}
