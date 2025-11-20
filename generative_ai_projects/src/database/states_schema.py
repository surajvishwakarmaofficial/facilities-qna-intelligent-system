from pydantic import BaseModel
from typing import (
    Optional, 
    List,

)


class LoginRequest(BaseModel):
    username: str
    password: str

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


