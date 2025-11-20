"""
Agent State Definitions
All TypedDict state classes for LangGraph agents
"""
from typing import TypedDict, List, Dict, Optional



class TicketAgentState(TypedDict):
    """State for ticket management agent"""
    messages: List[Dict]
    user_id: str
    ticket_data: Dict
    response: str
    token_usage: Dict
    cost_info: Dict

class UserAgentState(TypedDict):
    """State for user registration agent"""
    messages: List[Dict]
    admin_id: str
    admin_role: str
    user_data: Dict
    response: str
    

class QueryAgentState(TypedDict):
    """State for general query agent"""
    messages: List[Dict]
    user_id: str
    user_role: str
    query_context: Dict
    response: str
    token_usage: Dict
    cost_info: Dict


class EscalationAgentState(TypedDict):
    """State for escalation management agent"""
    messages: List[Dict]
    user_id: str
    user_role: str
    ticket_id: str
    escalation_data: Dict
    response: str
    token_usage: Dict
    cost_info: Dict
    

