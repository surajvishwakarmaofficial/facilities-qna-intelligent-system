import os
from typing import TypedDict, List, Dict
from langgraph.graph import StateGraph, END
import dotenv
from datetime import datetime
import uuid
import logging
import re
import json
from litellm import completion, completion_cost
from src.agents.states import TicketAgentState

dotenv.load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TicketManagementAgent:
    """Agent for handling ticket-related queries and actions"""
    
    def __init__(self, db_session):
        """Initialize with database session"""
        self.db = db_session
        logger.info("TicketManagementAgent initialized")
        
        self.model = os.getenv("LLM_MODEL", "gemini/gemini-2.5-flash")
        self.api_key = os.getenv("GOOGLE_API_KEY")
        
        if self.api_key:
            os.environ["GEMINI_API_KEY"] = self.api_key
        
        logger.info(f"Using LiteLLM model: {self.model}")
        
        self.graph = self._build_graph()
    
    def call_llm(self, messages: List[Dict], temperature: float = 0.7, max_tokens: int = int(os.getenv("MAX_TOKENS", 300))) -> Dict:
        """Call LiteLLM and return response with token usage and cost"""
        try:
            response = completion(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            token_usage = {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,

            }
            
            try:
                cost = completion_cost(completion_response=response)
                cost_info = {
                    "total_cost": round(cost, 6),
                    "currency": "USD",
                    "model": self.model
                }
            except Exception as e:
                logger.warning(f"Could not calculate cost: {e}")
                cost_info = {
                    "total_cost": 0.0,
                    "currency": "USD",
                    "model": self.model,
                    "note": "Cost calculation not available"
                }
            
            logger.info(f"Token Usage - Prompt: {token_usage['prompt_tokens']}, "
                       f"Completion: {token_usage['completion_tokens']}, "
                       f"Total: {token_usage['total_tokens']}")
            logger.info(f"Cost: ${cost_info['total_cost']}")
            
            return {
                "content": response.choices[0].message.content,
                "token_usage": token_usage,
                "cost_info": cost_info
            }
            
        except Exception as e:
            logger.error(f"LLM call failed: {str(e)}", exc_info=True)
            return {
                "content": None,
                "token_usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
                "cost_info": {"total_cost": 0.0, "currency": "USD", "error": str(e)}
            }
    
    def create_ticket_tool(self, category: str, description: str, priority: str, user_id: str) -> Dict:
        """Create a new ticket"""
        try:
            logger.info(f"Creating ticket for user: {user_id}")
            from src.database.models import Ticket
            
            ticket_id = f"TKT-{str(uuid.uuid4())[:8].upper()}"
            
            new_ticket = Ticket(
                ticket_id=ticket_id,
                user_id=user_id,
                category=category,
                description=description,
                priority=priority,
                status="Open",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                last_action_at=datetime.utcnow(),
                escalated=False,
                escalation_level=0,
                assigned_to=None,
                resolved_at=None,
                resolution_notes=None

            )
            
            self.db.add(new_ticket)
            self.db.commit()
            self.db.refresh(new_ticket)
            
            logger.info(f"Ticket created successfully: {ticket_id}")
            
            return {
                "success": True,
                "ticket_id": new_ticket.ticket_id,
                "status": new_ticket.status,
                "priority": new_ticket.priority,
                "category": new_ticket.category,
                "description": new_ticket.description,
                "created_at": new_ticket.created_at.isoformat() if new_ticket.created_at else "",
                "message": f"Ticket {new_ticket.ticket_id} created successfully",

            }
            
        except Exception as e:
            logger.error(f"Error creating ticket: {str(e)}", exc_info=True)
            self.db.rollback()
            return {"success": False, "error": f"Database error: {str(e)}"}
    
    def get_my_tickets_tool(self, user_id: str, status: str = None) -> Dict:
        """Get user tickets"""
        try:
            logger.info(f"Getting tickets for user: {user_id}, status: {status}")
            from src.database.models import Ticket
            
            query = self.db.query(Ticket).filter(Ticket.user_id == user_id)
            
            if status:
                query = query.filter(Ticket.status == status)
            
            tickets = query.order_by(Ticket.created_at.desc()).all()
            logger.info(f"Found {len(tickets)} tickets for user {user_id}")
            
            ticket_list = [
                {
                    "ticket_id": t.ticket_id,
                    "status": t.status,
                    "priority": t.priority,
                    "description": t.description,
                    "category": t.category,
                    "created_at": t.created_at.isoformat() if t.created_at else "",
                    "updated_at": t.updated_at.isoformat() if t.updated_at else ""
                }
                for t in tickets
            ]
            
            return {
                "success": True,
                "total": len(ticket_list),
                "tickets": ticket_list,
                "summary": f"Found {len(ticket_list)} tickets"
            }
            
        except Exception as e:
            logger.error(f"Error getting user tickets: {str(e)}", exc_info=True)
            return {"success": False, "error": f"Database error: {str(e)}"}
    
    def get_all_tickets_tool(self, status: str = None, priority: str = None) -> Dict:
        """Get all tickets - NO RBAC CHECK"""
        try:
            logger.info(f"Getting all tickets - status: {status}, priority: {priority}")
            from src.database.models import Ticket
            
            query = self.db.query(Ticket)
            
            if status:
                query = query.filter(Ticket.status == status)
            if priority:
                query = query.filter(Ticket.priority == priority)
            
            tickets = query.order_by(Ticket.created_at.desc()).all()
            logger.info(f"Found {len(tickets)} total tickets in system")
            
            ticket_list = [
                {
                    "ticket_id": t.ticket_id,
                    "user_id": t.user_id,
                    "status": t.status,
                    "priority": t.priority,
                    "description": t.description,
                    "category": t.category,
                    "created_at": t.created_at.isoformat() if t.created_at else "",
                    "updated_at": t.updated_at.isoformat() if t.updated_at else "",

                }
                for t in tickets
            ]
            
            return {
                "success": True,
                "total": len(ticket_list),
                "tickets": ticket_list,
                "summary": f"Found {len(ticket_list)} tickets in system"
            }
            
        except Exception as e:
            logger.error(f"Error getting all tickets: {str(e)}", exc_info=True)
            return {"success": False, "error": f"Database error: {str(e)}"}
    
    def get_ticket_stats_tool(self) -> Dict:
        """Get ticket stats - NO RBAC CHECK"""
        try:
            logger.info("Getting ticket statistics")
            from src.database.models import Ticket
            from sqlalchemy import func
            
            total = self.db.query(func.count(Ticket.id)).scalar() or 0
            open_count = self.db.query(func.count(Ticket.id)).filter(Ticket.status == "Open").scalar() or 0
            in_progress = self.db.query(func.count(Ticket.id)).filter(Ticket.status == "In Progress").scalar() or 0
            escalated = self.db.query(func.count(Ticket.id)).filter(Ticket.status == "Escalated").scalar() or 0
            resolved = self.db.query(func.count(Ticket.id)).filter(Ticket.status == "Resolved").scalar() or 0
            
            resolution_rate = (resolved / total * 100) if total > 0 else 0
            
            stats = {
                "total_tickets": total,
                "open": open_count,
                "in_progress": in_progress,
                "escalated": escalated,
                "resolved": resolved,
                "resolution_rate": round(resolution_rate, 2)
            }
            
            logger.info(f"Stats: {stats}")
            
            return {
                "success": True,
                "stats": stats,
                "summary": f"Total: {total}, Open: {open_count}, Escalated: {escalated}"
            }
            
        except Exception as e:
            logger.error(f"Error getting stats: {str(e)}", exc_info=True)
            return {"success": False, "error": f"Database error: {str(e)}"}
    
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow"""
        workflow = StateGraph(TicketAgentState)
        
        workflow.add_node("understand_intent", self.understand_intent)
        workflow.add_node("execute_action", self.execute_action)
        workflow.add_node("format_response", self.format_response)
        
        workflow.set_entry_point("understand_intent")
        workflow.add_edge("understand_intent", "execute_action")
        workflow.add_edge("execute_action", "format_response")
        workflow.add_edge("format_response", END)
        
        return workflow.compile()
    
    def understand_intent(self, state: TicketAgentState) -> TicketAgentState:
        """Understand user's intent using LiteLLM - NO ROLE CHECKING"""
        last_message = state["messages"][-1]["content"]
        user_id = state.get("user_id", "")
        
        logger.info(f"Understanding intent for message: '{last_message[:50]}...'")
        
        system_prompt = """You are a ticket management assistant. Analyze the user's message and extract structured information.

        For CREATE TICKET requests:
        - Extract ONLY the core issue description, remove all metadata words like "create", "ticket", "high priority", "maintenance"
        - Example: "Create a high priority maintenance ticket cleaning the floor in Room 7483" → "Cleaning the floor in Room 7483"
        - Example: "Create ticket for broken AC" → "Broken AC"

        For OTHER requests (viewing tickets, stats):
        - Just identify the action

        RULES:
        1. Description should be concise and start with capital letter
        2. Remove command words and priority/category mentions from description
        3. Only include the actual problem/issue in description

        Respond ONLY in valid JSON (no markdown, no extra text):
        {
            "action": "create_ticket|get_my_tickets|get_all_tickets|get_ticket_stats",
            "parameters": {
                "category": "IT Support|Maintenance|Housekeeping|Security|General",
                "priority": "Low|Medium|High|Critical",
                "status": "Open|In Progress|Escalated|Resolved",
                "description": "clean extracted issue description"
            }
        }"""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Message: {last_message}"}
        ]
        
        llm_response = self.call_llm(messages, temperature=0.1, max_tokens=150)
        
        state["token_usage"] = llm_response["token_usage"]
        state["cost_info"] = llm_response["cost_info"]
        
        action = "get_my_tickets"
        parameters = {"user_id": user_id}
        
        try:
            content = llm_response["content"].strip()
            content = re.sub(r'^``````$', '', content, flags=re.MULTILINE)
            content = content.strip()
            
            logger.info(f"LLM Response Content: {content[:200]}")
            
            intent_data = json.loads(content)
            action = intent_data.get("action", "get_my_tickets")
            parameters = intent_data.get("parameters", {})
            
            if "description" in parameters and parameters["description"]:
                desc = parameters["description"].strip()
                if desc and desc[0].islower():
                    desc = desc[0].upper() + desc[1:]
                parameters["description"] = desc
            
            parameters["user_id"] = user_id
            
            logger.info(f"Parsed - Action: {action}, Params: {parameters}")
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error: {e}")
            logger.error(f"Raw content: {llm_response['content']}")
            if "create" in last_message.lower() and "ticket" in last_message.lower():
                action = "create_ticket"
                parameters = self._rule_based_extraction(last_message, user_id)
            else:
                action = "get_my_tickets"
                parameters = {"user_id": user_id}
                
        except Exception as e:
            logger.error(f"Error parsing LLM response: {e}", exc_info=True)

            if "create" in last_message.lower() and "ticket" in last_message.lower():
                action = "create_ticket"
                parameters = self._rule_based_extraction(last_message, user_id)
            else:
                action = "get_my_tickets"
                parameters = {"user_id": user_id}
        
        logger.info(f"Final - Action: {action}, Parameters: {parameters}")
        
        state["ticket_data"] = {
            "action": action,
            "parameters": parameters
        }
        
        return state
    
    def _rule_based_extraction(self, message: str, user_id: str) -> Dict:
        """Fallback rule-based extraction for ticket creation"""
        params = {"user_id": user_id}
        msg_lower = message.lower()
        
        if "critical" in msg_lower:
            params["priority"] = "Critical"
        elif "high" in msg_lower or "urgent" in msg_lower:
            params["priority"] = "High"
        elif "low" in msg_lower:
            params["priority"] = "Low"
        else:
            params["priority"] = "Medium"
        
        if "maintenance" in msg_lower or "repair" in msg_lower or "cleaning" in msg_lower:
            params["category"] = "Maintenance"
        elif "it" in msg_lower or "computer" in msg_lower or "laptop" in msg_lower:
            params["category"] = "IT Support"
        elif "housekeeping" in msg_lower:
            params["category"] = "Housekeeping"
        elif "security" in msg_lower:
            params["category"] = "Security"
        else:
            params["category"] = "General"
        
        desc = message
        patterns = [
            r"create\s+a?\s*(high|low|medium|critical)?\s*priority?\s*(maintenance|it|housekeeping|security)?\s*ticket\s+(for\s+)?",
            r"create\s+ticket\s+(for\s+)?",
        ]
        
        for pattern in patterns:
            desc = re.sub(pattern, "", desc, flags=re.IGNORECASE).strip()
        
        if desc and desc[0].islower():
            desc = desc[0].upper() + desc[1:]
        
        params["description"] = desc
        return params
    
    def execute_action(self, state: TicketAgentState) -> TicketAgentState:
        """Execute the determined action"""
        action = state["ticket_data"].get("action")
        params = state["ticket_data"].get("parameters", {})
        
        logger.info(f"Executing action: {action}")
        
        try:
            if action == "create_ticket":
                filtered_params = {
                    k: v for k, v in params.items() 
                    if k in ['category', 'description', 'priority', 'user_id']
                }
                result = self.create_ticket_tool(**filtered_params)
                
            elif action == "get_my_tickets":
                filtered_params = {
                    k: v for k, v in params.items() 
                    if k in ['user_id', 'status']
                }
                result = self.get_my_tickets_tool(**filtered_params)
                
            elif action == "get_all_tickets":
                filtered_params = {
                    k: v for k, v in params.items() 
                    if k in ['status', 'priority']
                }
                result = self.get_all_tickets_tool(**filtered_params)
                
            elif action == "get_ticket_stats":
                result = self.get_ticket_stats_tool()
            else:
                result = {"success": False, "error": "Unknown action"}
            
            state["ticket_data"]["result"] = result
            
        except Exception as e:
            logger.error(f"Error executing action: {str(e)}", exc_info=True)
            state["ticket_data"]["result"] = {"success": False, "error": str(e)}
        
        return state

    def format_response(self, state: TicketAgentState) -> TicketAgentState:
        """Format the response with clean markdown - NO ROLE-BASED FORMATTING"""
        result = state["ticket_data"].get("result", {})
        
        logger.info(f"Formatting response")
        
        try:
            if result.get("success"):
                if "tickets" in result:
                    tickets = result["tickets"]
                    total = result['total']
                    
                    response = "**Tickets**\n\n"
                    response += f"Found **{total}** ticket{'s' if total != 1 else ''}\n\n"
                    
                    if total == 0:
                        response += "No tickets found matching your criteria."
                    else:
                        response += "---\n\n"
                        
                        for idx, ticket in enumerate(tickets[:15], 1):
                            created = ticket.get('created_at', 'Unknown')
                            if created and created != 'Unknown':
                                try:
                                    dt = datetime.fromisoformat(created)
                                    created = dt.strftime("%b %d, %Y at %I:%M %p")
                                except:
                                    pass
                            
                            response += f"### {idx}. Ticket {ticket['ticket_id']}\n\n"
                            
                            if 'user_id' in ticket:
                                response += f"**User:** {ticket['user_id']}\n"
                            
                            response += f"**Status:** {ticket['status']}\n"
                            response += f"**Priority:** {ticket['priority']}\n"
                            response += f"**Category:** {ticket.get('category', 'N/A')}\n"
                            response += f"**Description:** {ticket['description']}\n"
                            response += f"**Created:** {created}\n"
                            response += "\n---\n\n"
                        
                        if total > 15:
                            response += f"\nShowing 15 of {total} tickets._"
                
                elif "ticket_id" in result:
                    response = "**Ticket Created Successfully!**\n\n"
                    response += f"### Ticket: {result['ticket_id']}\n\n"
                    response += f"**Status:** {result['status']}\n"
                    response += f"**Priority:** {result['priority']}\n"
                    response += f"**Category:** {result.get('category', 'N/A')}\n"
                    response += f"**Description:** {result.get('description', 'N/A')}\n"
                
                elif "stats" in result:
                    stats = result["stats"]
                    response = " **Ticket Statistics**\n\n"
                    response += f"**Total:** {stats['total_tickets']}\n"
                    response += f"**Open:** {stats['open']}\n"
                    response += f"**In Progress:** {stats['in_progress']}\n"
                    response += f"**Escalated:** {stats['escalated']}\n"
                    response += f"**Resolved:** {stats['resolved']}\n"
                    response += f"**Resolution Rate:** {stats['resolution_rate']}%\n"
                else:
                    response = result.get("summary", "Action completed")
            else:
                response = f"**Error:** {result.get('error', 'Unknown error')}"
            
            state["response"] = response
            
        except Exception as e:
            logger.error(f"Error formatting response: {str(e)}", exc_info=True)
            state["response"] = f"Error: {str(e)}"
        
        return state
    
    def process_message(self, message: str, user_id: str) -> Dict:
        """Process a user message and return response with token info - NO ROLE PARAMETER"""
        initial_state = {
            "messages": [{"role": "user", "content": message}],
            "user_id": user_id,
            "ticket_data": {},
            "response": "",
            "token_usage": {},
            "cost_info": {}
        }
        
        try:
            logger.info(f"Processing message for user {user_id}")
            final_state = self.graph.invoke(initial_state)
            
            return {
                "response": final_state["response"],
                "token_usage": final_state.get("token_usage", {}),
                "cost_info": final_state.get("cost_info", {})
            }
        except Exception as e:
            logger.error(f"Error in process_message: {str(e)}", exc_info=True)
            return {
                "response": f"Error: {str(e)}",
                "token_usage": {},
                "cost_info": {}
            }

