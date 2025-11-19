import os
from typing import TypedDict, List, Dict
from langgraph.graph import StateGraph, END
import dotenv
from datetime import datetime
import uuid
import logging
import re

dotenv.load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class UserAgentState(TypedDict):
    """State for user registration agent"""
    messages: List[Dict]
    admin_id: str
    admin_role: str
    user_data: Dict
    response: str

class UserRegistrationAgent:
    """Agent for handling user registration (Admin only)"""
    
    def __init__(self, db_session):
        """Initialize with database session"""
        self.db = db_session
        logger.info("UserRegistrationAgent initialized")
        
        try:
            from langchain_openai import AzureChatOpenAI
            self.llm = AzureChatOpenAI(
                azure_deployment=os.getenv("AZURE_DEPLOYMENT"),
                api_version=os.getenv("AZURE_API_VERSION", "2024-02-15-preview"),
                temperature=0,
                azure_endpoint=os.getenv("AZURE_ENDPOINT"),
                api_key=os.getenv("AZURE_API_KEY")
            )
        except Exception as e:
            logger.warning(f"LLM initialization failed: {e}")
            self.llm = None
        
        self.graph = self._build_graph()
    
    def register_user_tool(self, username: str, email: str, full_name: str, password: str, role: str = "user") -> Dict:
        """Register a new user - DIRECT DB ACCESS"""
        try:
            logger.info(f"Registering user: {username}")
            from src.database.models import User
            import bcrypt
            
            password = password.strip()
            
            if len(password) < 8:
                return {
                    "success": False,
                    "error": "Password must be at least 8 characters long"
                }
            
            if len(password) > 72:
                return {
                    "success": False,
                    "error": "Password must be 72 characters or less"
                }
            
            password_bytes = password.encode('utf-8')
            if len(password_bytes) > 72:
                password = password_bytes[:72].decode('utf-8', errors='ignore')
            
            if not re.search(r'[A-Za-z]', password) or not re.search(r'[0-9]', password):
                return {
                    "success": False,
                    "error": "Password must contain both letters and numbers"
                }
            
            existing_user = self.db.query(User).filter(User.username == username).first()
            if existing_user:
                return {
                    "success": False,
                    "error": f"Username '{username}' already exists"
                }
            
            existing_email = self.db.query(User).filter(User.email == email).first()
            if existing_email:
                return {
                    "success": False,
                    "error": f"Email '{email}' already registered"
                }
            
            salt = bcrypt.gensalt(rounds=12)
            hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
            
            new_user = User(
                id=str(uuid.uuid4()),
                username=username,
                email=email,
                full_name=full_name,
                hashed_password=hashed_password,
                role=role,
                created_at=datetime.utcnow(),
                is_active=True
            )
            
            self.db.add(new_user)
            self.db.commit()
            self.db.refresh(new_user)
            
            logger.info(f"User created successfully: {username}")
            
            return {
                "success": True,
                "user_id": new_user.id,
                "username": new_user.username,
                "email": new_user.email,
                "full_name": new_user.full_name,
                "role": new_user.role,
                "message": f"User '{username}' registered successfully"
            }
            
        except Exception as e:
            logger.error(f"Error creating user: {str(e)}", exc_info=True)
            self.db.rollback()
            return {"success": False, "error": f"Database error: {str(e)}"}
    
    def list_users_tool(self, role_filter: str = None) -> Dict:
        """List all users - ADMIN ONLY"""
        try:
            logger.info(f"Listing users with role filter: {role_filter}")
            from src.database.models import User
            
            query = self.db.query(User)
            
            if role_filter:
                query = query.filter(User.role == role_filter)
            
            users = query.order_by(User.created_at.desc()).all()
            logger.info(f"Found {len(users)} users")
            
            user_list = [
                {
                    "user_id": u.id,
                    "username": u.username,
                    "email": u.email,
                    "full_name": u.full_name,
                    "role": u.role,
                    "is_active": u.is_active,
                    "created_at": u.created_at.isoformat() if u.created_at else ""
                }
                for u in users
            ]
            
            return {
                "success": True,
                "total": len(user_list),
                "users": user_list,
                "summary": f"Found {len(user_list)} users"
            }
            
        except Exception as e:
            logger.error(f"Error listing users: {str(e)}", exc_info=True)
            return {"success": False, "error": f"Database error: {str(e)}"}
    
    def get_user_stats_tool(self) -> Dict:
        """Get user statistics - ADMIN ONLY"""
        try:
            logger.info("Getting user statistics")
            from src.database.models import User
            from sqlalchemy import func
            
            total = self.db.query(func.count(User.id)).scalar() or 0
            active = self.db.query(func.count(User.id)).filter(User.is_active == True).scalar() or 0
            admins = self.db.query(func.count(User.id)).filter(User.role == "admin").scalar() or 0
            managers = self.db.query(func.count(User.id)).filter(User.role == "manager").scalar() or 0
            users = self.db.query(func.count(User.id)).filter(User.role == "user").scalar() or 0
            
            stats = {
                "total_users": total,
                "active_users": active,
                "admins": admins,
                "managers": managers,
                "regular_users": users
            }
            
            logger.info(f"Stats: {stats}")
            
            return {
                "success": True,
                "stats": stats,
                "summary": f"Total: {total}, Active: {active}, Admins: {admins}"
            }
            
        except Exception as e:
            logger.error(f"Error getting stats: {str(e)}", exc_info=True)
            return {"success": False, "error": f"Database error: {str(e)}"}
    
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow"""
        workflow = StateGraph(UserAgentState)
        
        workflow.add_node("check_admin", self.check_admin)
        workflow.add_node("understand_intent", self.understand_intent)
        workflow.add_node("execute_action", self.execute_action)
        workflow.add_node("format_response", self.format_response)
        
        workflow.set_entry_point("check_admin")
        workflow.add_edge("check_admin", "understand_intent")
        workflow.add_edge("understand_intent", "execute_action")
        workflow.add_edge("execute_action", "format_response")
        workflow.add_edge("format_response", END)
        
        return workflow.compile()
    
    def check_admin(self, state: UserAgentState) -> UserAgentState:
        """Verify admin privileges"""
        admin_role = state.get("admin_role", "user")
        
        if admin_role != "admin":
            state["user_data"] = {
                "action": "unauthorized",
                "result": {
                    "success": False,
                    "error": "Only administrators can manage users"
                }
            }
        
        return state
    
    def understand_intent(self, state: UserAgentState) -> UserAgentState:
        """Understand admin's intent with improved regex patterns"""
        # Skip if unauthorized
        if state.get("user_data", {}).get("action") == "unauthorized":
            return state
        
        last_message = state["messages"][-1]["content"]
        original_message = last_message
        last_message_lower = last_message.lower()
        
        logger.info(f"Understanding intent for message: '{last_message[:50]}...'")
        
        action = None
        parameters = {}
        
        if any(word in last_message_lower for word in ["register", "create user", "add user", "new user"]):
            action = "register_user"
            
            username_patterns = [
                r'username[:\s]+["\']?(\w+)["\']?',
                r'user[:\s]+["\']?(\w+)["\']?',
                r'name[:\s]+["\']?(\w+)["\']?(?=.*@)',
            ]
            for pattern in username_patterns:
                username_match = re.search(pattern, last_message, re.IGNORECASE)
                if username_match:
                    parameters["username"] = username_match.group(1)
                    break
            
            email_patterns = [
                r'email[:\s]+["\']?([^\s,]+@[^\s,]+\.[^\s,]+)["\']?',
                r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',
            ]
            for pattern in email_patterns:
                email_match = re.search(pattern, last_message, re.IGNORECASE)
                if email_match:
                    parameters["email"] = email_match.group(1).strip('"\'')
                    break
            
            name_patterns = [
                r'(?:full\s*name|name)[:\s]+["\']?([^,"\'\n]+?)["\']?(?=\s*(?:email|username|password|,|$))',
                r'(?:full\s*name|name)[:\s]+["\']?([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)["\']?',
            ]
            for pattern in name_patterns:
                name_match = re.search(pattern, original_message, re.IGNORECASE)
                if name_match:
                    full_name = name_match.group(1).strip()
                    full_name = re.sub(r'\s*(?:email|username|password).*$', '', full_name, flags=re.IGNORECASE)
                    parameters["full_name"] = full_name.strip()
                    break
            
            password_patterns = [
                r'password[:\s]+["\']?([^\s,"\'\n]{8,72})["\']?',  # 8-72 chars
                r'pass[:\s]+["\']?([^\s,"\'\n]{8,72})["\']?',
            ]
            for pattern in password_patterns:
                password_match = re.search(pattern, last_message, re.IGNORECASE)
                if password_match:
                    pwd = password_match.group(1).strip('"\'')
                    if len(pwd.encode('utf-8')) > 72:
                        pwd = pwd.encode('utf-8')[:72].decode('utf-8', errors='ignore')
                    parameters["password"] = pwd
                    break
            
            if "admin" in last_message_lower and "role" in last_message_lower:
                parameters["role"] = "admin"
            elif "manager" in last_message_lower and "role" in last_message_lower:
                parameters["role"] = "manager"
            else:
                parameters["role"] = "user"
            
            logger.info(f"Extracted parameters: {parameters}")
        
        elif "list users" in last_message_lower or "show users" in last_message_lower or "all users" in last_message_lower:
            action = "list_users"
            
            if "admin" in last_message_lower:
                parameters["role_filter"] = "admin"
            elif "manager" in last_message_lower:
                parameters["role_filter"] = "manager"
            elif "regular" in last_message_lower or "normal" in last_message_lower:
                parameters["role_filter"] = "user"
        
        # User statistics
        elif "user stats" in last_message_lower or "user statistics" in last_message_lower or "how many users" in last_message_lower:
            action = "get_user_stats"
        
        # Default
        else:
            action = "unknown"
        
        logger.info(f"Action: {action}, Parameters: {parameters}")
        
        state["user_data"] = {
            "action": action,
            "parameters": parameters
        }
        
        return state
    
    def execute_action(self, state: UserAgentState) -> UserAgentState:
        """Execute the determined action"""
        if state.get("user_data", {}).get("action") == "unauthorized":
            return state
        
        action = state["user_data"].get("action")
        params = state["user_data"].get("parameters", {})
        
        logger.info(f"Executing action: {action}")
        
        try:
            if action == "register_user":
                # Validate required fields
                required = ["username", "email", "full_name", "password"]
                missing = [f for f in required if f not in params or not params[f]]
                
                if missing:
                    result = {
                        "success": False,
                        "error": f"Missing required fields: {', '.join(missing)}. Please provide username, email, full name, and password."
                    }
                else:
                    result = self.register_user_tool(**params)
            
            elif action == "list_users":
                result = self.list_users_tool(**params)
            
            elif action == "get_user_stats":
                result = self.get_user_stats_tool()
            
            else:
                result = {
                    "success": False,
                    "error": "I didn't understand that command. Try: 'Register user with username: john, email: john@example.com, name: John Doe, password: secure123'"
                }
            
            state["user_data"]["result"] = result
            
        except Exception as e:
            logger.error(f"Error executing action: {str(e)}", exc_info=True)
            state["user_data"]["result"] = {"success": False, "error": str(e)}
        
        return state
    
    def format_response(self, state: UserAgentState) -> UserAgentState:
        """Format the response"""
        result = state["user_data"].get("result", {})
        
        logger.info("Formatting response")
        
        try:
            if result.get("success"):
                if "users" in result:
                    # List of users
                    users = result["users"]
                    total = result['total']
                    
                    response = "👥 **User Management - System Users**\n\n"
                    response += f"✅ Found **{total}** user{'s' if total != 1 else ''}\n\n"
                    
                    if total == 0:
                        response += "No users found matching your criteria."
                    else:
                        response += "---\n\n"
                        
                        for idx, user in enumerate(users[:20], 1):
                            created = user.get('created_at', 'Unknown')
                            if created and created != 'Unknown':
                                try:
                                    dt = datetime.fromisoformat(created)
                                    created = dt.strftime("%b %d, %Y at %I:%M %p")
                                except:
                                    pass
                            
                            status_emoji = "✅" if user.get('is_active') else "❌"
                            
                            response += f"### {idx}. {user['full_name']}\n\n"
                            response += f"- 👤 **Username:** {user['username']}\n"
                            response += f"- 📧 **Email:** {user['email']}\n"
                            response += f"- 🎭 **Role:** {user['role'].title()}\n"
                            response += f"- {status_emoji} **Status:** {'Active' if user.get('is_active') else 'Inactive'}\n"
                            response += f"- 📅 **Created:** {created}\n"
                            response += "\n---\n\n"
                        
                        if total > 20:
                            response += f"\n📄 _Showing 20 of {total} users. {total - 20} more not displayed._"
                
                elif "user_id" in result:
                    # Single user registered
                    response = "✅ **User Registered Successfully!**\n\n"
                    response += "---\n\n"
                    response += f"### 👤 User: {result['full_name']}\n\n"
                    response += f"- **Username:** {result['username']}\n"
                    response += f"- **Email:** {result['email']}\n"
                    response += f"- **Role:** {result['role'].title()}\n"
                    response += f"- **User ID:** {result['user_id']}\n"
                    response += "\n---\n\n"
                    response += "💡 _The user can now log in with their username and password._"
                
                elif "stats" in result:
                    # User statistics
                    stats = result["stats"]
                    response = "📊 **User Statistics Dashboard**\n\n"
                    response += "---\n\n"
                    response += "### 📈 Overall Metrics\n\n"
                    response += f"- **Total Users:** {stats['total_users']}\n"
                    response += f"- **Active Users:** {stats['active_users']}\n\n"
                    response += "### 👥 By Role\n\n"
                    response += f"- 🔑 **Admins:** {stats['admins']}\n"
                    response += f"- 👔 **Managers:** {stats['managers']}\n"
                    response += f"- 👤 **Regular Users:** {stats['regular_users']}\n"
                    response += "\n---"
                else:
                    response = result.get("summary", "✅ Action completed successfully")
            else:
                response = f"❌ **Error:** {result.get('error', 'Unknown error occurred')}"
            
            state["response"] = response
            
        except Exception as e:
            logger.error(f"Error formatting response: {str(e)}", exc_info=True)
            state["response"] = f"❌ Error formatting response: {str(e)}"
        
        return state
    
    def process_message(self, message: str, admin_id: str, admin_role: str) -> str:
        """Process an admin message"""
        initial_state = {
            "messages": [{"role": "admin", "content": message}],
            "admin_id": admin_id,
            "admin_role": admin_role,
            "user_data": {},
            "response": ""
        }
        
        try:
            logger.info(f"Processing message from admin {admin_id}")
            final_state = self.graph.invoke(initial_state)
            return final_state["response"]
        except Exception as e:
            logger.error(f"Error in process_message: {str(e)}", exc_info=True)
            return f"❌ Error processing request: {str(e)}"
        