"""
Facilities RAG System - Main Orchestrator
"""

import os
from typing import List
import streamlit as st
from pymilvus import connections, utility, Collection
from langchain_community.vectorstores import Milvus
from langchain_core.documents import Document
from langchain_community.document_loaders import PyPDFLoader
import pathlib
import pandas as pd
import time

from src.llm.clients import setup_llm_clients
from src.rag.chunker import DocumentChunker
from src.rag.embeddings import EmbeddingManager
from src.rag.vector_store import MilvusStore
from src.rag.retriever import KnowledgeRetriever
import dotenv
from config.constant_config import Config
from src.database.s3_config import S3Uploader

dotenv.load_dotenv()



class FacilitiesRAGSystem:
    """RAG System for Facilities Management"""

    def __init__(self, knowledge_base_dir: str):
        print("=== [RAG_CORE] Initializing FacilitiesRAGSystem ===")
        self.knowledge_base_dir = knowledge_base_dir
        self.collection_name = Config.MILVUS_COLLECTION_NAME
        self.embedding_function = None
        self.vectorstore = None
        self.llm = None
        self.chat_history = []
        
        self.chunker = DocumentChunker(chunk_size=500, chunk_overlap=50)
        self.embedding_manager = EmbeddingManager()
        self.vector_store = None
        self.retriever = None
        
        self.supported_formats = {
            'pdf': self._process_pdf_file,
            'csv': self._process_csv_file,
            'xlsx': self._process_excel_file,
            'xls': self._process_excel_file,
            'txt': self._process_text_file,
        }
        print(f"[RAG_CORE] Supported formats: {list(self.supported_formats.keys())}")

    def initialize_clients(self, silent=False):
        """Initializes LLM/Embedding clients and Milvus connection."""
        print("[RAG_CORE] initialize_clients() called")
        
        if self.llm and self.embedding_function:
            print("[RAG_CORE] Clients already initialized, checking collection...")
            if utility.has_collection(self.collection_name):
                connection_args = {
                    "host": Config.MILVUS_HOST,
                    "port": Config.MILVUS_PORT,
                }
                if Config.MILVUS_DATABASE:
                    connection_args["db_name"] = Config.MILVUS_DATABASE
                
                self.vectorstore = Milvus(
                    embedding_function=self.embedding_function,
                    collection_name=self.collection_name,
                    connection_args=connection_args,
                    auto_id=True
                )
                print("[RAG_CORE] Vectorstore connected to existing collection")
            return True

        print("[RAG_CORE] Initializing embedding function and LLM...")
        self.embedding_function, self.llm = self.embedding_manager.initialize()
        
        if not self.embedding_function or not self.llm:
            print("[ERROR] Failed to initialize LLM or embedding function")
            return False

        print("[RAG_CORE] Creating MilvusStore connection...")
        self.vector_store = MilvusStore(
            host=Config.MILVUS_HOST,
            port=Config.MILVUS_PORT,
            database=Config.MILVUS_DATABASE,
            collection_name=self.collection_name,
            embedding_function=self.embedding_function,

        )
        
        if not self.vector_store.connect(silent=silent):
            print("[ERROR] MilvusStore connection failed")
            return False
        
        if self.vector_store.load_collection(silent=silent):
            self.vectorstore = self.vector_store.get_vectorstore()
            self.retriever = KnowledgeRetriever(self.vector_store, k=3)
            print("[RAG_CORE] Collection loaded successfully, retriever initialized")
            return True
        else:
            self.vectorstore = None
            if not silent:
                print("[WARNING] No existing knowledge base found")
            return True

    def rebuild_knowledge_base_from_directory(self):
        """Admin function: Rebuild entire knowledge base from scratch"""
        print(f"=== [RAG_CORE] Starting knowledge base rebuild from directory: {self.knowledge_base_dir} ===")
        
        if not self.embedding_function or not self.llm:
            print("[RAG_CORE] Initializing LLM clients for rebuild...")
            self.embedding_function, self.llm = setup_llm_clients()
            if not self.embedding_function or not self.llm:
                print("[ERROR] Failed to initialize LLM or embedding function")
                return False
        
        try:
            print("[RAG_CORE] Connecting to Milvus...")
            connections.connect(
                alias="default",
                host=Config.MILVUS_HOST,
                port=Config.MILVUS_PORT,
            )
        except Exception as e:
            print(f"[ERROR] Error connecting to Milvus: {str(e)}")
            return False
        
        if utility.has_collection(self.collection_name):
            print(f"[RAG_CORE] Dropping existing collection '{self.collection_name}'...")
            utility.drop_collection(self.collection_name)
        
        all_documents = []
        if not os.path.isdir(self.knowledge_base_dir):
            print(f"[ERROR] Knowledge base directory not found at {self.knowledge_base_dir}")
            return False

        print(f"[RAG_CORE] Scanning directory for files...")
        for root, _, files in os.walk(self.knowledge_base_dir):
            for file_name in files:
                file_path = os.path.join(root, file_name)
                file_ext = self._get_file_extension(file_name)
                if file_ext in self.supported_formats:
                    print(f"[RAG_CORE] Processing file: {file_name}")
                    processor = self.supported_formats[file_ext]
                    processed_docs = processor(file_path, file_name)
                    if processed_docs:
                        all_documents.extend(processed_docs)
                        print(f"[RAG_CORE] Added {len(processed_docs)} documents from {file_name}")
        
        if not all_documents:
            print("[ERROR] No documents were processed from the directory")
            return {
                "success": False,
                "message": "No documents were processed from the directory.",
                "num_documents": 0,
                "s3_url": None,

            }

        print(f"[RAG_CORE] Total documents collected: {len(all_documents)}")
        print("[RAG_CORE] Chunking documents...")
        splits = self.chunker.chunk_documents(all_documents)
        print(f"[RAG_CORE] Generated {len(splits)} chunks")

        connection_args = {
            "host": Config.MILVUS_HOST,
            "port": Config.MILVUS_PORT,
        }
        if Config.MILVUS_DATABASE:
            connection_args["db_name"] = Config.MILVUS_DATABASE

        print("[RAG_CORE] Creating Milvus collection from documents...")
        self.vectorstore = Milvus.from_documents(
            documents=splits,
            embedding=self.embedding_function,
            collection_name=self.collection_name,
            connection_args=connection_args,
        )
        
        try:
            collection = Collection(self.collection_name)
            collection.load()
            num_entities = collection.num_entities
            print(f"=== [SUCCESS] Knowledge base rebuilt with {num_entities} chunks ===")
        except Exception as e:
            print(f"[WARNING] Collection created but verification failed: {str(e)}")
        
        return True

    def process_file(self, uploaded_file):
        """ADMIN ACTION: Add new document to existing knowledge base"""
        print(f"\n=== [PROCESS_FILE] Starting file processing: {uploaded_file.name} ===")
        temp_file_path = os.path.join(".", uploaded_file.name)
        s3_url = None 
        
        try:
            if not self.embedding_function or not self.llm:
                print("[ERROR] System not initialized")
                return {
                    "success": False,
                    "message": "System not initialized. Please initialize clients first.",
                    "s3_url": None,

                }
            
            if utility.has_collection(self.collection_name):
                print("[PROCESS_FILE] Connecting to existing collection...")
                connection_args = {
                    "host": Config.MILVUS_HOST,
                    "port": Config.MILVUS_PORT,
                }
                if Config.MILVUS_DATABASE:
                    connection_args["db_name"] = Config.MILVUS_DATABASE
                
                self.vectorstore = Milvus(
                    embedding_function=self.embedding_function,
                    collection_name=self.collection_name,
                    connection_args=connection_args,
                    auto_id=True
                )
            
            file_ext = self._get_file_extension(uploaded_file.name)
            if file_ext not in self.supported_formats:
                print(f"[ERROR] Unsupported file format: .{file_ext}")                 
                return {
                    "success": False,
                    "message": f"Unsupported file format: .{file_ext}. Supported formats: {list(self.supported_formats.keys())}",
                    "s3_url": None,

                }
            
            print("[PROCESS_FILE] Step 1: Saving file to disk...")
            with open(temp_file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
                f.flush()
                os.fsync(f.fileno())
            
            if not os.path.exists(temp_file_path):
                print("[ERROR] Temporary file was not created")
                return {
                    "success": False,
                    "message": "Temporary file was not created.",
                    "s3_url": None,

                }
            
            file_size = os.path.getsize(temp_file_path)
            if file_size == 0:
                print("[ERROR] Temporary file is empty (0 bytes)")
                return {
                    "success": False,
                    "message": "Temporary file is empty (0 bytes).",
                    "s3_url": None,

                }
                        
            s3_uploader = S3Uploader()
            import datetime
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            s3_object_name = f"uploads/{timestamp}_{uploaded_file.name}"
            
            s3_url = s3_uploader.upload_file_and_get_url(
                temp_file_path, 
                object_name=s3_object_name,
                expiration=86400,
            )
            
            if not s3_url:
                return {
                    "success": False,
                    "message": "S3 upload failed.",
                    "s3_url": None,

                }
            
            processor = self.supported_formats[file_ext]
            processed_documents = processor(temp_file_path, uploaded_file.name)

            if not processed_documents:
                print("[ERROR] No content extracted from file")
                return {
                    "success": False,
                    "message": "No content extracted from file.",
                    "s3_url": None,

                }
    
            for doc in processed_documents:
                doc.metadata["s3_url"] = s3_url
                doc.metadata["s3_object_key"] = s3_object_name
            
            splits = self.chunker.chunk_documents(processed_documents)
            
            if not splits:
                return False
                    
            for chunk in splits:
                chunk.metadata["s3_url"] = s3_url
                chunk.metadata["s3_object_key"] = s3_object_name
            
            if self.vectorstore is None:
                print("Creating new Milvus collection...")
                connection_args = {
                    "host": Config.MILVUS_HOST,
                    "port": Config.MILVUS_PORT,
                }
                if Config.MILVUS_DATABASE:
                    connection_args["db_name"] = Config.MILVUS_DATABASE
                
                self.vectorstore = Milvus.from_documents(
                    documents=splits,
                    embedding=self.embedding_function,
                    collection_name=self.collection_name,
                    connection_args=connection_args,
                )
                
                collection = Collection(self.collection_name)
                collection.load()
                num_entities = collection.num_entities
                
                print(f"=== [SUCCESS] New collection created with {num_entities} chunks ===")
                return {
                    "success": True,
                    "message": f"New collection created with {num_entities} chunks.",
                    "s3_url": s3_url,

                }
            
            collection = Collection(self.collection_name)
            collection.load()
            count_before = collection.num_entities
            
            added_ids = self.vectorstore.add_documents(documents=splits)
            
            if not added_ids:
                return {
                    "success": False,
                    "message": "Upload failed: No IDs returned.",
                    "s3_url": s3_url,
                    "num_documents": len(splits),

                }
                        
            try:
                collection.flush()
                print("Data persisted to database")
            except Exception as flush_error:
                print(f"Flush warning: {flush_error}")
            
            time.sleep(2)
            
            collection.load()
            count_after = collection.num_entities            
            actual_added = count_after - count_before
            
            if actual_added > 0:                
                test_query = splits[0].page_content[:50]
                retriever = self.vectorstore.as_retriever(search_kwargs={"k": 1})
                test_results = retriever.invoke(test_query)
                
                if test_results:
                    print("New documents are searchable")
                
                print("===== Document successfully processed and uploaded =====")
                print(f"s3_url: {s3_url}")
                return {
                    "success": True,
                    "message": f"Added {actual_added} new chunks (Total: {count_before} : {count_after})",
                    "s3_url": s3_url,
                    "num_documents": actual_added,

                }
            else:
                return {
                    "success": False,
                    "message": "Upload verification failed: Document count unchanged.",
                    "s3_url": s3_url,
                    "num_documents": 0,

                }
            
        except Exception as e:
            import traceback
            print(traceback.format_exc())
            return False
        finally:
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
    
    def retrieve_relevant_info(self, query: str, k: int = 3):
        """Retrieve relevant information from all documents"""
        if self.retriever:
            return self.retriever.retrieve(query, k=k)
        
        try:
            if self.vectorstore and utility.has_collection(self.collection_name):
                collection = Collection(self.collection_name)
                collection.load()
            
            retriever = self.vectorstore.as_retriever(search_kwargs={"k": k})
            relevant_docs = retriever.invoke(query)
            return relevant_docs
        except Exception as e:
            print(f"Error retrieving documents: {str(e)}")
            return []

    def generate_response_stream(self, query: str):
        """Generate a streaming response using RAG"""
        try:
            if not self.vectorstore or not utility.has_collection(self.collection_name):
                def error_stream():
                    yield "The knowledge base has not been initialized. Please contact an administrator."
                return {
                    "answer_stream": error_stream(),
                    "sources": [],
                    "error": True
                }

            relevant_docs = self.retrieve_relevant_info(query)

            if not relevant_docs:
                def no_info_stream():
                    yield "I could not find relevant information in the facilities knowledge base to answer your question."
                return {
                    "answer_stream": no_info_stream(),
                    "sources": [],
                    "error": True
                }
            
            context = "\n\n".join([doc.page_content for doc in relevant_docs])
            history_context = ""
            if self.chat_history:
                history_context = "Previous conversation:\n"
                for msg in self.chat_history[-4:]:
                    history_context += f"{msg['role']}: {msg['content']}\n"
            
            prompt = f"""You are a professional and specialized Facilities Management Assistant. Your ONLY function is to answer questions related to the building's facilities, amenities, policies, and procedures, based STRICTLY on the context provided.

            If the user's question is NOT related to facilities management, you MUST politely refuse to answer.

            {history_context}

            Context from facilities documents:
            {context}

            Current Question: {query}

            Based on these strict instructions, please provide your response."""
            
            def stream_generator():
                stream = self.llm.stream(prompt)
                for chunk in stream:
                    yield chunk.content
            
            return {
                "answer_stream": stream_generator(),
                "sources": relevant_docs,
                "error": False
            }

        except Exception as e:
            def exception_stream():
                yield f"Sorry, I encountered an error: {str(e)}"
            return {
                "answer_stream": exception_stream(),
                "sources": [],
                "error": True
            }

    def generate_response(self, query: str):
        """Generate response using RAG"""
        try:
            if not self.vectorstore or not utility.has_collection(self.collection_name):
                return {"answer": "The knowledge base has not been initialized. Please contact an administrator.", "sources": [], "error": True}

            relevant_docs = self.retrieve_relevant_info(query)

            if not relevant_docs:
                return {
                    "answer": "I could not find relevant information in the facilities knowledge base to answer your question.",
                    "sources": [],
                    "error": True
                }

            context = "\n\n".join([doc.page_content for doc in relevant_docs])

            history_context = ""
            if self.chat_history:
                history_context = "Previous conversation:\n"
                for msg in self.chat_history[-4:]:
                    history_context += f"{msg['role']}: {msg['content']}\n"

            prompt = f"""You are a professional and specialized Facilities Management Assistant. Your ONLY function is to answer questions related to the building's facilities, amenities, policies, and procedures, based STRICTLY on the context provided.

            If the user's question is NOT related to facilities management, you MUST politely refuse to answer.

            {history_context}

            Context from facilities documents:
            {context}

            Current Question: {query}

            Based on these strict instructions, please provide your response."""

            response = self.llm.invoke(prompt)
            answer = response.content

            token_usage = None
            if hasattr(response, 'response_metadata'):
                usage = response.response_metadata.get('token_usage', {})
                if usage:
                    token_usage = {
                        "prompt_tokens": usage.get('prompt_tokens', 0),
                        "completion_tokens": usage.get('completion_tokens', 0),
                        "total_tokens": usage.get('total_tokens', 0)
                    }

            self.chat_history.append({"role": "user", "content": query})
            self.chat_history.append({"role": "assistant", "content": answer})

            return {
                "answer": answer,
                "sources": relevant_docs,
                "token_usage": token_usage,
                "error": False,

            }
        except Exception as e:
            print(f"[ERROR] Error generating response: {str(e)}")
            return {
                "answer": f"Sorry, I encountered an error: {str(e)}",
                "sources": [],
                "token_usage": None,
                "error": True,
                
            }

    def _get_file_extension(self, filename: str) -> str:
        return filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
    
    def _process_pdf_file(self, temp_file_path: str, filename: str) -> List[Document]:
        """Process PDF with image detection"""
        try:
            print(f"[PDF_PROCESSOR] Loading PDF: {filename}")
            loader = PyPDFLoader(temp_file_path)
            documents = loader.load()
            
            if not documents:
                print(f"[ERROR] PDF contains no pages: {filename}")
                return []
            
            total_text_length = sum(len(doc.page_content.strip()) for doc in documents)
            avg_text_per_page = total_text_length / len(documents) if documents else 0
            
            print(f"[PDF_PROCESSOR] Pages: {len(documents)}, Avg text/page: {avg_text_per_page:.2f} chars")
            
            if avg_text_per_page < 50:
                print("[ERROR] Image-based PDF detected (avg < 50 chars/page)")
                print("[INFO] Solution: Convert to text-based PDF using OCR tools")
                return []
            
            processed_documents = []
            
            for idx, doc in enumerate(documents):
                content = doc.page_content.strip()
                
                if len(content) < 10:
                    continue
                
                new_metadata = {
                    "title": filename, 
                    "source": f"{filename} (Page {doc.metadata.get('page', idx) + 1})", 
                    "file_type": "pdf",
                    "row_number": 0,
                    "sheet_name": "",
                    "section_number": idx + 1,
                    "page_number": doc.metadata.get('page', idx) + 1
                }
                
                processed_doc = Document(page_content=content, metadata=new_metadata)
                processed_documents.append(processed_doc)
            
            if not processed_documents:
                print(f"[ERROR] No readable text found in {filename}")
                return []
            
            print(f"[PDF_PROCESSOR] Successfully processed {len(processed_documents)} pages")
            return processed_documents
            
        except Exception as e:
            print(f"[ERROR] Error processing PDF: {str(e)}")
            return []

    def _process_csv_file(self, temp_file_path: str, filename: str) -> List[Document]:
        try:
            print(f"[CSV_PROCESSOR] Loading CSV: {filename}")
            df = pd.read_csv(temp_file_path)
            processed_documents = []
            for idx, row in df.iterrows():
                content_parts = [f"{col}: {value}" for col, value in row.items() if pd.notna(value)]
                content = "\n".join(content_parts)
                new_metadata = {
                    "title": filename, 
                    "source": f"{filename} (Row {idx + 1})", 
                    "file_type": "csv", 
                    "row_number": idx + 1,
                    "sheet_name": "",
                    "section_number": 0
                }
                processed_doc = Document(page_content=content, metadata=new_metadata)
                processed_documents.append(processed_doc)
            print(f"[CSV_PROCESSOR] Successfully processed {len(processed_documents)} rows")
            return processed_documents
        except Exception as e:
            print(f"[ERROR] Error processing CSV: {str(e)}")
            return []
    
    def _process_excel_file(self, temp_file_path: str, filename: str) -> List[Document]:
        try:
            print(f"[EXCEL_PROCESSOR] Loading Excel: {filename}")
            excel_file = pd.ExcelFile(temp_file_path)
            processed_documents = []
            for sheet_name in excel_file.sheet_names:
                print(f"[EXCEL_PROCESSOR] Processing sheet: {sheet_name}")
                df = pd.read_excel(temp_file_path, sheet_name=sheet_name)
                for idx, row in df.iterrows():
                    content_parts = [f"Sheet: {sheet_name}"] + [f"{col}: {value}" for col, value in row.items() if pd.notna(value)]
                    content = "\n".join(content_parts)
                    
                    new_metadata = {
                        "title": filename, 
                        "source": f"{filename} (Sheet: {sheet_name}, Row {idx + 1})", 
                        "file_type": "excel", 
                        "sheet_name": sheet_name, 
                        "row_number": idx + 1,
                        "section_number": 0
                    }
                    processed_doc = Document(page_content=content, metadata=new_metadata)
                    processed_documents.append(processed_doc)
            print(f"[EXCEL_PROCESSOR] Successfully processed {len(processed_documents)} rows across {len(excel_file.sheet_names)} sheets")
            return processed_documents
        except Exception as e:
            print(f"[ERROR] Error processing Excel: {str(e)}")
            return []
    
    def _process_text_file(self, temp_file_path: str, filename: str) -> List[Document]:
        try:
            print(f"[TXT_PROCESSOR] Loading text file: {filename}")
            with open(temp_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            try:
                with open(temp_file_path, 'r', encoding='latin-1') as f:
                    content = f.read()
            except Exception as e:
                print(f"[ERROR] Error processing text file: {str(e)}")
                return []
        
        paragraphs = content.split('\n\n')
        processed_documents = []
        for idx, paragraph in enumerate(paragraphs):
            if paragraph.strip():
                new_metadata = {
                    "title": filename, 
                    "source": f"{filename} (Section {idx + 1})", 
                    "file_type": "txt", 
                    "section_number": idx + 1,
                    "row_number": 0,
                    "sheet_name": ""
                }
                processed_doc = Document(page_content=paragraph.strip(), metadata=new_metadata)
                processed_documents.append(processed_doc)
        print(f"[TXT_PROCESSOR] Successfully processed {len(processed_documents)} paragraphs")
        return processed_documents
    
