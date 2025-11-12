from typing import Dict, List
from ..llm.litellm_client import LiteLLMClient
from ..rag.retriever import KnowledgeRetriever
from ..utils.logger import setup_logger

logger = setup_logger(__name__)

class FacilitiesAgent:
    def __init__(self, llm_client: LiteLLMClient, retriever: KnowledgeRetriever):
        self.llm = llm_client
        self.retriever = retriever
        self.conversation_history: Dict[str, List[Dict]] = {}
    
    async def handle_query(self, user_id: str, query: str, session_id: str) -> str:
        logger.info(f"Processing query for user {user_id}: {query}")
        
        # Retrieve relevant context
        context = await self.retriever.retrieve(query)
        
        # Get conversation history
        history = self.conversation_history.get(session_id, [])
        
        # Build messages
        messages = [
            {"role": "system", "content": self._get_system_prompt()},
        ]
        
        # Add history
        messages.extend(history[-6:])  # Last 3 turns
        
        # Add context
        if context:
            context_msg = f"Relevant information:\n" + "\n".join(context)
            messages.append({"role": "system", "content": context_msg})
        
        # Add current query
        messages.append({"role": "user", "content": query})
        
        # Generate response
        response = await self.llm.generate(messages)
        
        # Update history
        history.append({"role": "user", "content": query})
        history.append({"role": "assistant", "content": response})
        self.conversation_history[session_id] = history
        
        return response
    
    def _get_system_prompt(self) -> str:
        return """You are YASH Facilities Management AI Assistant.

Your responsibilities:
- Answer employee queries about facilities, policies, and benefits
- Help create support tickets for actionable requests
- Provide troubleshooting guidance
- Maintain professional and helpful tone

Guidelines:
- Use provided context to answer accurately
- If unsure, say you don't have that information
- For ticket creation, extract: category, priority, description
- Cite policy sources when relevant"""

