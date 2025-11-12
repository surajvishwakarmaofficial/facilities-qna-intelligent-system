from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import redis
import uuid
from datetime import datetime, timedelta
import asyncio
import uuid

from src.llm.litellm_client import LiteLLMClient
from src.rag.vector_store import MilvusStore
from src.rag.retriever import KnowledgeRetriever
from src.agents.facilities_agent import FacilitiesAgent
from src.database.session import DatabaseManager
from src.database.models import Ticket
from src.utils.rate_limiter import RateLimiter
from src.utils.cache import ResponseCache
import dotenv
import os
from passlib.context import CryptContext


from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel
from typing import Optional
import redis
import uuid
from datetime import datetime
import asyncio
import os
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from src.database.session import DatabaseManager
from src.database.models import User, Ticket, Base
import dotenv
import bcrypt


dotenv.load_dotenv()

app = FastAPI(title="YASH Facilities AI API")

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

security = HTTPBasic()

redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)
rate_limiter = RateLimiter(redis_client)
cache = ResponseCache(redis_client)
llm_client = LiteLLMClient()

vector_store = MilvusStore(
    uri=os.environ.get("MILVUS_URI"),
    token=os.environ.get("MILVUS_TOEKN")
)

retriever = KnowledgeRetriever(vector_store, llm_client)
agent = FacilitiesAgent(llm_client, retriever)
db_manager = DatabaseManager("sqlite:///./yash_tickets.db")

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
    
    if len(password) != 8:
        raise HTTPException(
            status_code=400,
            detail="Password must be exactly 8 characters. Example: yash2025"
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

@app.post("/api/login")
async def login(request: LoginRequest, db: Session = Depends(get_db)):
    user = authenticate_user(db, request.username, request.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    
    return {
        "message": "Login successful",
        "user": {
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name
        }
    }


# AUTO-ESCALATION ENGINE (GENAI + RULES)
async def auto_escalate_tickets():
    while True:
        await asyncio.sleep(60)
        db = db_manager.get_session()
        tickets = db.query(Ticket).filter(Ticket.status == "Open").all()
        
        for t in tickets:
            hours = (datetime.utcnow() - t.created_at).total_seconds() / 3600
            if hours > 24 and not t.escalated:
                prompt = f"Ticket {t.ticket_id}: {t.description}\nPending: {hours:.1f}h\nEscalate? Reply YES/NO + reason."
                decision = llm_client.generate(prompt)
                if "YES" in decision.upper():
                    t.escalated = True
                    t.priority = "Critical"
                    t.status = "Escalated"
                    db.commit()
                    print(f"AUTO-ESCALATED: {t.ticket_id} | {decision}")

app.add_event_handler("startup", lambda: asyncio.create_task(auto_escalate_tickets()))

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

@app.get("/health")
async def health(): return {"status": "YASH Facilities AI READY", "auto_escalation": "ACTIVE"}
