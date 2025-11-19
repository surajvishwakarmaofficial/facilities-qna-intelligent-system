"""
Embedding Management Module
"""

from src.llm.clients import setup_llm_clients


class EmbeddingManager:
    """Manages embedding function"""
    
    def __init__(self):
        self.embedding_function = None
        self.llm = None
    
    def initialize(self):
        """Initialize embedding function and LLM"""
        self.embedding_function, self.llm = setup_llm_clients()
        return self.embedding_function, self.llm
    
    def get_embedding_function(self):
        """Get embedding function"""
        return self.embedding_function
    
    def get_llm(self):
        """Get LLM"""
        return self.llm

