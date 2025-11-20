"""
Vector Store Module - Milvus Operations
"""

from typing import List
from langchain_core.documents import Document
from langchain_community.vectorstores import Milvus
from pymilvus import connections, utility, Collection, db


class MilvusStore:
    """Milvus vector store operations"""
    
    def __init__(self, host: str, port: str, database: str, collection_name: str, embedding_function):
        self.host = host
        self.port = port
        self.database = database
        self.collection_name = collection_name
        self.embedding_function = embedding_function
        self.vectorstore = None
        
        self.connection_args = {
            "host": host,
            "port": port,
        }
        
        if database:
            self.connection_args["db_name"] = database
        
        print(f"[MILVUS_STORE] Initialized with host={host}:{port}, db={database}, collection={collection_name}")
    
    def connect(self, silent=False):
        """Connect to Milvus with database selection"""
        try:
            connections.connect(
                alias="default",
                host=self.host,
                port=self.port
            )
            
            if not silent:
                print(f"[MILVUS_STORE] Connected to Milvus at {self.host}:{self.port}")
            
            if self.database:
                try:
                    database_list = db.list_database()
                    
                    if self.database not in database_list:
                        db.create_database(self.database)
                        if not silent:
                            print(f"[MILVUS_STORE] Created database: {self.database}")
                    
                    db.using_database(self.database)
                    if not silent:
                        print(f"[MILVUS_STORE] Using database: {self.database}")
                        
                except Exception as db_error:
                    if not silent:
                        print(f"[WARNING] Database operation warning: {db_error}")
                        print("[INFO] Continuing with default database")
            
            return True
            
        except Exception as e:
            if not silent:
                print(f"[ERROR] Error connecting to Milvus: {str(e)}")
            return False
    
    def has_collection(self) -> bool:
        """Check if collection exists in current database"""
        try:
            return utility.has_collection(self.collection_name)
        except Exception as e:
            return False
    
    def load_collection(self, silent=False):
        """Load existing collection"""
        try:
            if not self.has_collection():
                if not silent:
                    print(f"[MILVUS_STORE] No existing collection '{self.collection_name}' found")
                return False
            
            if not silent:
                print(f"[MILVUS_STORE] Loading existing collection: {self.collection_name}")
            
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
                print(f"[MILVUS_STORE] Loaded collection with {num_entities} documents")
            
            return True
            
        except Exception as e:
            if not silent:
                print(f"[WARNING] Collection exists but load had an issue: {e}")
            return False
    
    def create_collection(self, documents: List[Document]):
        """Create new collection from documents"""
        try:
            print(f"[MILVUS_STORE] Creating new collection '{self.collection_name}'...")
            
            self.vectorstore = Milvus.from_documents(
                documents=documents,
                embedding=self.embedding_function,
                collection_name=self.collection_name,
                connection_args=self.connection_args,
            )
            
            collection = Collection(self.collection_name)
            collection.load()
            num_entities = collection.num_entities
            
            print(f"[MILVUS_STORE] Collection created with {num_entities} entities")
            return num_entities
            
        except Exception as e:
            print(f"[ERROR] Error creating collection: {str(e)}")
            raise
    
    def drop_collection(self):
        """Drop collection"""
        try:
            if self.has_collection():
                utility.drop_collection(self.collection_name)
                print(f"[MILVUS_STORE] Collection '{self.collection_name}' dropped")
                return True
            return False
        except Exception as e:
            print(f"[ERROR] Error dropping collection: {str(e)}")
            return False
    
    def add_documents(self, documents: List[Document]):
        """Add documents to existing collection"""
        import time
        
        try:
            collection = Collection(self.collection_name)
            collection.load()
            count_before = collection.num_entities
            
            print(f"[MILVUS_STORE] Current document count: {count_before}")
            
            added_ids = self.vectorstore.add_documents(documents=documents)
            
            if not added_ids:
                print("[ERROR] Upload failed: No IDs returned")
                return False
            
            print(f"[MILVUS_STORE] Received {len(added_ids)} IDs from upload")
            
            try:
                collection.flush()
            except Exception as flush_error:
                print(f"[WARNING] Flush warning: {flush_error}")
            
            time.sleep(2)
            
            collection.load()
            count_after = collection.num_entities
            
            actual_added = count_after - count_before
            
            if actual_added > 0:
                print(f"[SUCCESS] Added {actual_added} new chunks (Total: {count_before} → {count_after})")
                return True
            else:
                print(f"[ERROR] Upload verification failed: Document count unchanged ({count_before})")
                print(f"[ERROR] IDs returned: {len(added_ids)}, Expected: {len(documents)}, Actual: {actual_added}")
                return False
                
        except Exception as e:
            print(f"[ERROR] Error adding documents: {str(e)}")
            return False
    
    def get_vectorstore(self):
        """Get vectorstore instance"""
        return self.vectorstore
    
    def get_collection_stats(self):
        """Get collection statistics"""
        try:
            if self.has_collection():
                collection = Collection(self.collection_name)
                collection.load()
                return {
                    "num_entities": collection.num_entities,
                    "collection_name": self.collection_name,
                    "database": self.database if self.database else "default"
                    
                }
            return None
        except Exception as e:
            print(f"[ERROR] Error getting collection stats: {str(e)}")
            return None
