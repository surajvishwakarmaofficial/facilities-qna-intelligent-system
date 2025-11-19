"""
Retriever Module - Document Retrieval
"""

from typing import List
from langchain_core.documents import Document
import streamlit as st


class KnowledgeRetriever:
    """Handles document retrieval"""
    
    def __init__(self, vector_store, k: int = 3):
        self.vector_store = vector_store
        self.k = k
    
    def retrieve(self, query: str, k: int = None) -> List[Document]:
        """Retrieve relevant documents"""
        try:
            vectorstore = self.vector_store.get_vectorstore()
            
            if not vectorstore or not self.vector_store.has_collection():
                return []
            
            num_docs = k if k is not None else self.k
            
            retriever = vectorstore.as_retriever(search_kwargs={"k": num_docs})
            relevant_docs = retriever.invoke(query)
            
            return relevant_docs
        except Exception as e:
            st.error(f"Error retrieving documents: {str(e)}")
            return []
    
    def get_context_string(self, documents: List[Document]) -> str:
        """Convert documents to context string"""
        return "\n\n".join([doc.page_content for doc in documents])
