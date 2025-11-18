# Facilities Management AI Assistant

> AI-powered facilities management system with intelligent ticket handling, auto-escalation, and RAG-based knowledge retrieval.

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red.svg)](https://streamlit.io/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [API Documentation](#api-documentation)
- [Project Structure](#project-structure)
- [Contributing](#contributing)
- [License](#license)

## 🎯 Overview

The Facilities Management AI Assistant is an enterprise-grade solution that combines conversational AI with intelligent ticket management. It provides:

- **AI-Powered Chat Interface**: RAG-based question answering for facilities queries
- **Intelligent Ticket Management**: Create, track, and manage support tickets
- **Auto-Escalation System**: Automated ticket escalation based on priority and SLA
- **Multi-User Support**: Role-based access control (Admin, Manager, User)
- **Chat History**: Persistent conversation tracking and export

## ✨ Features

### 🤖 AI Assistant
- Context-aware responses using RAG (Retrieval-Augmented Generation)
- Document ingestion (PDF, CSV, Excel, TXT)
- Source citation for transparency
- Multi-turn conversation support
- Chat history with date-based organization

### 🎫 Ticket Management
- Create tickets with priority levels (Low, Medium, High, Critical)
- Real-time status tracking
- Auto-escalation based on configurable thresholds
- Ticket history and audit trail
- Dashboard with statistics

### 🔐 Security
- Bcrypt password hashing
- JWT-based authentication
- Role-based access control
- Secure session management

### 📊 Analytics
- Ticket statistics dashboard
- Resolution rate tracking
- Priority-based filtering
- User-specific ticket views

## 🏗️ Architecture

```
┌─────────────────┐
│  Streamlit UI   │ (Frontend)
└────────┬────────┘
         │
         │ HTTP/REST
         │
┌────────▼────────┐
│   FastAPI       │ (Backend)
│   - Auth        │
│   - Tickets     │
│   - Chat        │
└────────┬────────┘
         │
    ┌────┴────┬──────────┐
    │         │          │
┌───▼──┐  ┌──▼───┐    ┌──▼─────┐
│SQLite│  │Milvus│    │LiteLLM │
│(Data)│  │(RAG) │    │(LLM)   │
└──────┘  └──────┘    └────────┘
```

### Technology Stack

**Frontend:**
- Streamlit 1.28+
- Custom CSS for modern UI

**Backend:**
- FastAPI 0.100+
- SQLAlchemy (ORM)
- Pydantic (Validation)

**AI/ML:**
- LiteLLM (Multi-provider LLM interface)
- Milvus (Vector database)
- LangChain (RAG pipeline)

**Storage:**
- SQLite (Application data)
- Milvus (Vector embeddings)
- Redis (Caching & rate limiting)

**Scheduler:**
- APScheduler (Auto-escalation jobs)

## 📦 Prerequisites

- Python 3.8 or higher
- Docker (optional, for Milvus)
- Redis (optional, for caching)
- API keys for LLM provider (OpenAI, Anthropic, etc.)

## 🚀 Installation

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/facilities-ai-assistant.git
cd facilities-ai-assistant
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Set Up Environment Variables

Create a `.env` file in the root directory:

```env
# LLM Configuration
OPENAI_API_KEY=your_openai_api_key_here
# Or use other providers supported by LiteLLM

# Milvus Configuration
MILVUS_URI=http://localhost:19530
MILVUS_TOKEN=your_milvus_token

# Database
SQLITE_DB_URL=sqlite:///./facilities.db

# Security
SECRET_KEY=your-secret-key-min-32-chars
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# API Configuration
API_URL=http://localhost:8000

# Escalation
AUTO_ESCALATION_SCHEDULAR=5  # minutes
```

### 5. Start Milvus (Docker)

```bash
docker run -d --name milvus \
  -p 19530:19530 \
  -p 9091:9091 \
  milvusdb/milvus:latest
```

## ⚙️ Configuration

### Escalation Thresholds

Edit `main.py` to configure auto-escalation thresholds:

```python
ESCALATION_THRESHOLDS = {
    "Low": 48,      # 48 hours
    "Medium": 24,   # 24 hours
    "High": 12,     # 12 hours
    "Critical": 4   # 4 hours
}
```

### Predefined Users

Edit `src/utils/constants.py` to add default users:

```python
PREDEFINED_USERS = [
    {
        "username": "admin",
        "email": "admin@yash.com",
        "full_name": "System Admin",
        "password": "admin12345",
        "role": "admin"
    }
]
```

### Knowledge Base

Place your documents in:
```
data/knowledge_base_files/
├── policies.pdf
├── procedures.xlsx
└── faq.txt
```

## 🎮 Usage

### Start the Backend

```bash
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Backend will be available at: `http://localhost:8000`
API docs: `http://localhost:8000/docs`

### Start the Frontend

```bash
cd frontend
streamlit run ui.py
```

Frontend will be available at: `http://localhost:8501`

### Login

Use predefined credentials:
- **Username**: `admin`
- **Password**: `admin12345`

Or create a new account via the registration form.

## 📚 API Documentation

### Authentication Endpoints

#### POST `/api/register`
Register a new user.

**Request:**
```json
{
  "username": "john_doe",
  "email": "john@example.com",
  "full_name": "John Doe",
  "password": "securepass123"
}
```

#### POST `/api/login`
Authenticate user and receive JWT token.

**Request:**
```json
{
  "username": "john_doe",
  "password": "securepass123"
}
```

**Response:**
```json
{
  "user": {
    "id": "uuid",
    "username": "john_doe",
    "email": "john@example.com",
    "full_name": "John Doe",
    "role": "user"
  },
  "access_token": "eyJ0eXAi...",
  "token_type": "bearer"
}
```

### Ticket Endpoints

#### POST `/api/tickets/create`
Create a new support ticket.

**Request:**
```json
{
  "user_id": "user-uuid",
  "category": "IT Support",
  "description": "Laptop keyboard not working",
  "priority": "High"
}
```

#### GET `/api/tickets/user/{user_id}`
Get all tickets for a user.

**Query Parameters:**
- `status` (optional): Filter by status
- `priority` (optional): Filter by priority

#### PATCH `/api/tickets/{ticket_id}/status`
Update ticket status or properties.

**Request:**
```json
{
  "status": "In Progress",
  "priority": "Critical",
  "assigned_to": "admin-uuid",
  "resolution_notes": "Working on fix"
}
```

#### POST `/api/tickets/{ticket_id}/escalate`
Manually escalate a ticket.

#### GET `/api/tickets/{ticket_id}/history`
Get ticket audit trail.

### Chat History Endpoints

#### POST `/api/chat-history/save`
Save or update chat conversation.

#### GET `/api/chat-history/{user_id}`
Get all conversations for a user.

#### DELETE `/api/chat-history/{conversation_id}`
Archive a conversation.

## 📁 Project Structure

```
facilities-ai-assistant/
│
├── backend/
│   ├── main.py                      # FastAPI application
│   ├── src/
│   │   ├── agents/
│   │   │   └── facilities_agent.py  # AI agent logic
│   │   ├── database/
│   │   │   ├── models.py            # SQLAlchemy models
│   │   │   └── session.py           # DB session management
│   │   ├── llm/
│   │   │   ├── clients.py           # LLM client wrappers
│   │   │   └── litellm_client.py    # LiteLLM integration
│   │   ├── rag/
│   │   │   ├── vector_store.py      # Milvus integration
│   │   │   └── retriever.py         # RAG retriever
│   │   └── utils/
│   │       ├── cache.py             # Redis caching
│   │       ├── rate_limiter.py      # Rate limiting
│   │       └── constants.py         # Configuration
│   └── config/
│       └── constant_config.py       # App configuration
│
├── frontend/
│   ├── ui.py                        # Streamlit application
│   └── src/
│       ├── utils/
│       │   └── state_utils.py       # Session state management
│       └── rag_core.py              # RAG system integration
│
├── data/
│   └── knowledge_base_files/        # Document storage
│
├── requirements.txt                 # Python dependencies
├── .env                             # Environment variables
└── README.md                        # This file
```

## 🔄 Key Workflows

### 1. User Registration & Login
```
User → Register → Hash Password → Store in DB → Login → Generate JWT
```

### 2. Ticket Creation & Auto-Escalation
```
Create Ticket → Set Priority → Background Job Monitors
→ Check Inactivity → Auto-Escalate if Threshold Exceeded
```

### 3. RAG-Based Chat
```
User Query → Embed Query → Search Milvus → Retrieve Context
→ LLM Generation → Return Answer + Sources
```

### 4. Chat History Management
```
Message Exchange → Auto-Save → Store in DB
→ Group by Date → Display in Sidebar
```

## 🛠️ Development

### Running Tests

```bash
pytest tests/ -v
```

### Code Formatting

```bash
black .
isort .
flake8 .
```

### Database Migrations

```bash
alembic revision --autogenerate -m "description"
alembic upgrade head
```

## 🐛 Troubleshooting

### Milvus Connection Error
```
Error: Failed to connect to Milvus
Solution: Ensure Milvus is running on port 19530
```

### Backend Not Starting
```
Error: Port 8000 already in use
Solution: Kill existing process or use different port
uvicorn main:app --port 8001
```

### Knowledge Base Not Loading
```
Error: Failed to load documents
Solution: Check file formats (PDF, CSV, XLSX, TXT only)
Verify files exist in data/knowledge_base_files/
```

## 📈 Performance Optimization

- **Caching**: Redis caches frequently accessed data
- **Rate Limiting**: Prevents API abuse
- **Connection Pooling**: SQLAlchemy connection pool
- **Async Operations**: FastAPI async endpoints
- **Vector Search**: Milvus optimized for similarity search

## 🔒 Security Best Practices

1. Change default admin password immediately
2. Use strong SECRET_KEY (min 32 characters)
3. Enable HTTPS in production
4. Implement API rate limiting
5. Regular security audits
6. Keep dependencies updated

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open Pull Request

## 📄 License

This project is licensed under the MIT License - see [LICENSE](LICENSE) file for details.

## 👥 Authors

- **Your Name** - *Initial work* - [YourGitHub](https://github.com/yourusername)

## 🙏 Acknowledgments

- YASH Technologies for requirements and use case
- Milvus team for vector database
- LiteLLM for unified LLM interface
- Streamlit for rapid UI development

## 📞 Support

For support, email support@yash.com or open an issue on GitHub.

---

**Built with ❤️ for YASH Technologies Hackathon**