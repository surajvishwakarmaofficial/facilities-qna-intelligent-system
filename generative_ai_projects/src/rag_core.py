import os
from typing import List, Dict
import streamlit as st
from pymilvus import connections, utility, Collection
from langchain_community.vectorstores import Milvus
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_community.document_loaders import PyPDFLoader
import pathlib
import pandas as pd
import time

from src.llm.clients import setup_llm_clients
import dotenv
from config.constant_config import Config

dotenv.load_dotenv()

PROJECT_ROOT = pathlib.Path(__file__).parent.parent.parent
candidate_path = PROJECT_ROOT / "generative_ai_projects" / "data" / "knowledge_base.pdf"


class FacilitiesRAGSystem:
    """RAG System for Facilities Management"""

    def __init__(self, knowledge_base_dir: str):
        self.knowledge_base_dir = knowledge_base_dir
        self.collection_name = Config.COLLECTION_NAME
        self.embedding_function = None
        self.vectorstore = None
        self.llm = None
        self.chat_history = []
        self.supported_formats = {
            'pdf': self._process_pdf_file,
            'csv': self._process_csv_file,
            'xlsx': self._process_excel_file,
            'xls': self._process_excel_file,
            'txt': self._process_text_file,
        }

    def initialize_clients(self, silent=False):
        """Initializes LLM/Embedding clients and Milvus connection."""
        if self.llm and self.embedding_function:
            if utility.has_collection(self.collection_name):
                self.vectorstore = Milvus(
                    embedding_function=self.embedding_function,
                    collection_name=self.collection_name,
                    connection_args={"uri": Config.MILVUS_URI, "token": Config.MILVUS_TOKEN},
                    auto_id=True
                )
            return True

        self.embedding_function, self.llm = setup_llm_clients()
        if not self.embedding_function or not self.llm:
            if not silent:
                st.error("Failed to initialize LLM or embedding function.")
            return False

        try:
            connections.connect(alias="default", uri=Config.MILVUS_URI, token=Config.MILVUS_TOKEN)
            if not silent:
                st.success("Connected to Milvus")
            
            if utility.has_collection(self.collection_name):
                if not silent:
                    st.info(f"Loading existing collection: {self.collection_name}")
                
                self.vectorstore = Milvus(
                    embedding_function=self.embedding_function,
                    collection_name=self.collection_name,
                    connection_args={"uri": Config.MILVUS_URI, "token": Config.MILVUS_TOKEN},
                    auto_id=True
                )
                
                try:
                    collection = Collection(self.collection_name)
                    collection.load()
                    num_entities = collection.num_entities
                    
                    if not silent:
                        st.success(f"Loaded existing knowledge base with {num_entities} documents")
                    
                    return True
                except Exception as load_error:
                    if not silent:
                        st.warning(f"Collection exists but load had an issue: {load_error}")
                    return False
            else:
                self.vectorstore = None
                if not silent:
                    st.warning("No existing knowledge base found.")
                return True
            
        except Exception as e:
            if not silent:
                st.error(f"Error connecting to Milvus: {str(e)}")
            return False

    def rebuild_knowledge_base_from_directory(self):
        """Admin function: Rebuild entire knowledge base from scratch"""
        st.info(f"Starting knowledge base rebuild from directory: {self.knowledge_base_dir}")
        
        if not self.embedding_function or not self.llm:
            self.embedding_function, self.llm = setup_llm_clients()
            if not self.embedding_function or not self.llm:
                st.error("Failed to initialize LLM or embedding function.")
                return False
        
        try:
            connections.connect(alias="default", uri=Config.MILVUS_URI, token=Config.MILVUS_TOKEN)
        except Exception as e:
            st.error(f"Error connecting to Milvus: {str(e)}")
            return False
        
        if utility.has_collection(self.collection_name):
            utility.drop_collection(self.collection_name)
            st.info(f"Collection '{self.collection_name}' dropped for a fresh start.")
        
        all_documents = []
        if not os.path.isdir(self.knowledge_base_dir):
            st.error(f"Error: Knowledge base directory not found at {self.knowledge_base_dir}")
            return False

        for root, _, files in os.walk(self.knowledge_base_dir):
            for file_name in files:
                file_path = os.path.join(root, file_name)
                file_ext = self._get_file_extension(file_name)
                if file_ext in self.supported_formats:
                    processor = self.supported_formats[file_ext]
                    processed_docs = processor(file_path, file_name)
                    if processed_docs:
                        all_documents.extend(processed_docs)
        
        if not all_documents:
            st.error("No documents were processed from the directory.")
            return False

        text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
        splits = text_splitter.split_documents(all_documents)

        self.vectorstore = Milvus.from_documents(
            documents=splits,
            embedding=self.embedding_function,
            collection_name=self.collection_name,
            connection_args={"uri": Config.MILVUS_URI, "token": Config.MILVUS_TOKEN},
        )
        
        try:
            collection = Collection(self.collection_name)
            collection.load()
            num_entities = collection.num_entities
            st.success(f"Successfully rebuilt knowledge base with {num_entities} chunks from {len(splits)} processed chunks.")
        except Exception as e:
            st.warning(f"Collection created but verification failed: {str(e)}")
        
        return True
            
    def _get_file_extension(self, filename: str) -> str:
        return filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
    
    def _process_pdf_file(self, temp_file_path: str, filename: str) -> List[Document]:
        """Process PDF with image detection"""
        try:
            loader = PyPDFLoader(temp_file_path)
            documents = loader.load()
            
            if not documents:
                st.error(f"PDF contains no pages: {filename}")
                return []
            
            # Image detection
            total_text_length = sum(len(doc.page_content.strip()) for doc in documents)
            avg_text_per_page = total_text_length / len(documents) if documents else 0
            
            if avg_text_per_page < 50:
                st.error("Image-Based PDF Detected")
                st.markdown("""
                    <div style="background: #fff3cd; padding: 1rem; border-radius: 8px; border-left: 4px solid #ffc107;">
                        <h4 style="color: #856404; margin-top: 0;">This PDF contains images instead of text</h4>
                        <p style="color: #856404;"><strong>Solution:</strong> Convert to text-based PDF using OCR tools (Adobe Acrobat, Google Drive)</p>
                        <p style="color: #856404;"><strong>Test:</strong> Open PDF and try to select text with your cursor</p>
                        <p style="color: #856404;"><strong>Alternative:</strong> Upload as TXT, CSV, or Excel file</p>
                    </div>
                """, unsafe_allow_html=True)
                return []
            
            # Process text-based PDF
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
                st.error(f"No readable text found in {filename}")
                return []
            
            return processed_documents
            
        except Exception as e:
            st.error(f"Error processing PDF: {str(e)}")
            return []

    def _process_csv_file(self, temp_file_path: str, filename: str) -> List[Document]:
        try:
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
            return processed_documents
        except Exception as e:
            st.error(f"Error processing CSV: {str(e)}")
            return []
    
    def _process_excel_file(self, temp_file_path: str, filename: str) -> List[Document]:
        try:
            excel_file = pd.ExcelFile(temp_file_path)
            processed_documents = []
            for sheet_name in excel_file.sheet_names:
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
            return processed_documents
        except Exception as e:
            st.error(f"Error processing Excel: {str(e)}")
            return []
    
    def _process_text_file(self, temp_file_path: str, filename: str) -> List[Document]:
        try:
            with open(temp_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            try:
                with open(temp_file_path, 'r', encoding='latin-1') as f:
                    content = f.read()
            except Exception as e:
                st.error(f"Error processing text file: {str(e)}")
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
        return processed_documents
    
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
            st.error(f"Error generating streaming response: {str(e)}")
            def exception_stream():
                yield f"Sorry, I encountered an error: {str(e)}"
            return {
                "answer_stream": exception_stream(),
                "sources": [],
                "error": True
            }

    def process_file(self, uploaded_file):
        """ADMIN ACTION: Add new document to existing knowledge base"""
        temp_file_path = os.path.join(".", uploaded_file.name)
        
        try:
            if not self.embedding_function or not self.llm:
                st.error("System not initialized")
                return False
            
            if utility.has_collection(self.collection_name):
                st.info("Connecting to collection...")
                self.vectorstore = Milvus(
                    embedding_function=self.embedding_function,
                    collection_name=self.collection_name,
                    connection_args={"uri": Config.MILVUS_URI, "token": Config.MILVUS_TOKEN},
                    auto_id=True
                )
            
            file_ext = self._get_file_extension(uploaded_file.name)
            if file_ext not in self.supported_formats:
                st.error(f"Unsupported file format: .{file_ext}")
                st.info("Supported formats: PDF, CSV, Excel, TXT")
                return False

            with open(temp_file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            with st.spinner(f"Processing {uploaded_file.name}..."):
                processor = self.supported_formats[file_ext]
                processed_documents = processor(temp_file_path, uploaded_file.name)
            
            if not processed_documents:
                st.error("No content extracted from file")
                return False
            
            st.success(f"Extracted {len(processed_documents)} pages/sections")
            
            with st.spinner("Creating document chunks..."):
                text_splitter = RecursiveCharacterTextSplitter(
                    chunk_size=500, 
                    chunk_overlap=50,
                    length_function=len,
                    separators=["\n\n", "\n", " ", ""]
                )
                splits = text_splitter.split_documents(processed_documents)
            
            if not splits:
                st.error("Failed to create document chunks")
                return False
            
            st.info(f"Generated {len(splits)} chunks")
            
            if self.vectorstore is None:
                with st.spinner("Creating new collection..."):
                    self.vectorstore = Milvus.from_documents(
                        documents=splits,
                        embedding=self.embedding_function,
                        collection_name=self.collection_name,
                        connection_args={"uri": Config.MILVUS_URI, "token": Config.MILVUS_TOKEN},
                    )
                    
                    collection = Collection(self.collection_name)
                    collection.load()
                    num_entities = collection.num_entities
                
                st.success(f"Created collection with {num_entities} chunks")
                return True
            
            with st.spinner(f"Uploading {len(splits)} chunks to database..."):
                collection = Collection(self.collection_name)
                collection.load()
                count_before = collection.num_entities
                
                st.info(f"Current document count: {count_before}")
                
                added_ids = self.vectorstore.add_documents(documents=splits)
                
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
                    
                    test_query = splits[0].page_content[:50]
                    retriever = self.vectorstore.as_retriever(search_kwargs={"k": 1})
                    test_results = retriever.invoke(test_query)
                    
                    if test_results:
                        st.success("New documents are searchable")
                    
                    return True
                else:
                    st.error(f"Upload verification failed: Document count unchanged ({count_before})")
                    st.error(f"IDs returned: {len(added_ids)}, Expected: {len(splits)}, Actual: {actual_added}")
                    return False
            
        except Exception as e:
            st.error(f"Error: {str(e)}")
            import traceback
            with st.expander("Debug Information"):
                st.code(traceback.format_exc())
            return False
        finally:
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
    
    def retrieve_relevant_info(self, query: str, k: int = 3):
        """Retrieve relevant information from all documents"""
        try:
            if self.vectorstore and utility.has_collection(self.collection_name):
                collection = Collection(self.collection_name)
                collection.load()
            
            retriever = self.vectorstore.as_retriever(search_kwargs={"k": k})
            relevant_docs = retriever.invoke(query)
            return relevant_docs
        except Exception as e:
            st.error(f"Error retrieving documents: {str(e)}")
            return []

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

            self.chat_history.append({"role": "user", "content": query})
            self.chat_history.append({"role": "assistant", "content": answer})

            return {
                "answer": answer,
                "sources": relevant_docs,
                "error": False
            }
        except Exception as e:
            st.error(f"Error generating response: {str(e)}")
            return {
                "answer": f"Sorry, I encountered an error: {str(e)}",
                "sources": [],
                "error": True
            }
