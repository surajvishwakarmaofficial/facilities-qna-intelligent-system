"""
Vector Store Module - Milvus Operations
"""

from typing import List
from langchain_core.documents import Document
from langchain_community.vectorstores import Milvus
from pymilvus import connections, utility, Collection
import streamlit as st


class MilvusStore:
    """Milvus vector store operations"""
    
    def __init__(self, uri: str, token: str, collection_name: str, embedding_function):
        self.uri = uri
        self.token = token
        self.collection_name = collection_name
        self.embedding_function = embedding_function
        self.vectorstore = None
        self.connection_args = {"uri": uri, "token": token}
    
    def connect(self, silent=False):
        """Connect to Milvus"""
        try:
            connections.connect(alias="default", uri=self.uri, token=self.token)
            if not silent:
                st.success("Connected to Milvus")
            return True
        except Exception as e:
            if not silent:
                st.error(f"Error connecting to Milvus: {str(e)}")
            return False
    
    def has_collection(self) -> bool:
        """Check if collection exists"""
        return utility.has_collection(self.collection_name)
    
    def load_collection(self, silent=False):
        """Load existing collection"""
        try:
            if not self.has_collection():
                if not silent:
                    st.warning("No existing knowledge base found.")
                return False
            
            if not silent:
                st.info(f"Loading existing collection: {self.collection_name}")
            
            self.vectorstore = Milvus(
                embedding_function=self.embedding_function,
                collection_name=self.collection_name,
                connection_args=self.connection_args,
                auto_id=True
            )
            
            collection = Collection(self.collection_name)
            collection.load()
            num_entities = collection.num_entities
            
            if not silent:
                st.success(f"Loaded existing knowledge base with {num_entities} documents")
            
            return True
        except Exception as e:
            if not silent:
                st.warning(f"Collection exists but load had an issue: {e}")
            return False
    
    def create_collection(self, documents: List[Document]):
        """Create new collection from documents"""
        self.vectorstore = Milvus.from_documents(
            documents=documents,
            embedding=self.embedding_function,
            collection_name=self.collection_name,
            connection_args=self.connection_args,
        
        )
        
        collection = Collection(self.collection_name)
        collection.load()
        
        return collection.num_entities
    
    def drop_collection(self):
        """Drop collection"""
        if self.has_collection():
            utility.drop_collection(self.collection_name)
            st.info(f"Collection '{self.collection_name}' dropped for a fresh start.")
    
    def add_documents(self, documents: List[Document]):
        """Add documents to existing collection"""
        import time
        
        collection = Collection(self.collection_name)
        collection.load()
        count_before = collection.num_entities
        
        st.info(f"Current document count: {count_before}")
        
        added_ids = self.vectorstore.add_documents(documents=documents)
        
        if not added_ids:
            st.error("Upload failed: No IDs returned")
            return False
        
        st.info(f"Received {len(added_ids)} IDs from upload")
        
        try:
            collection.flush()
            st.info("Data persisted to database")
        except Exception as flush_error:
            st.warning(f"Flush warning: {flush_error}")
        
        time.sleep(2)
        
        collection.load()
        count_after = collection.num_entities
        
        st.info(f"Updated document count: {count_after}")
        
        actual_added = count_after - count_before
        
        if actual_added > 0:
            st.success(f"Successfully added {actual_added} new chunks")
            st.success(f"Total documents: {count_before} to {count_after}")
            return True
        else:
            st.error(f"Upload verification failed: Document count unchanged ({count_before})")
            st.error(f"IDs returned: {len(added_ids)}, Expected: {len(documents)}, Actual: {actual_added}")
            return False
    
    def get_vectorstore(self):
        """Get vectorstore instance"""
        return self.vectorstore

