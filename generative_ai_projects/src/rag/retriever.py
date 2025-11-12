from typing import List, Dict
from .vector_store import MilvusStore
from ..llm.litellm_client import LiteLLMClient

class KnowledgeRetriever:
    def __init__(self, vector_store: MilvusStore, llm_client: LiteLLMClient):
        self.vector_store = vector_store
        self.llm_client = llm_client
    
    async def retrieve(self, query: str, top_k: int = 3) -> List[str]:
        # Generate query embedding
        query_embedding = await self.llm_client.embed(query)
        
        # Search vector store
        results = self.vector_store.search(query_embedding, top_k)
        
        # Extract texts
        contexts = [text for text, _ in results]
        return contexts
    
    async def retrieve_and_generate(self, query: str, context: List[str]) -> str:
        context_text = "\n\n".join(context)
        
        prompt = f"""Context from knowledge base:
{context_text}

Question: {query}

Answer based on the context provided. If the information is not in the context, say so clearly."""

        messages = [
            {"role": "system", "content": "You are a helpful facilities assistant."},
            {"role": "user", "content": prompt}
        ]
        
        response = await self.llm_client.generate(messages)
        return response

