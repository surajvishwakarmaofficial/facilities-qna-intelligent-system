import os
from typing import List, Dict
import streamlit as st
from pymilvus import connections, utility
from langchain_community.vectorstores import Milvus
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_community.document_loaders import PyPDFLoader, CSVLoader, TextLoader
import pathlib
import pandas as pd

from src.llm.clients import setup_llm_clients
import dotenv
from config.constant_config import Config
from src.utils.prompts import (
    FacilitiesPrompt,

)


dotenv.load_dotenv()

PROJECT_ROOT = pathlib.Path(__file__).parent.parent.parent
candidate_path = PROJECT_ROOT / "generative_ai_projects" / "data" / "knowledge_base.pdf"

class FacilitiesRAGSystem:
    """RAG System for Facilities Management"""

    def __init__(self):
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


    def initialize_clients(self):
        """Initializes LLM/Embedding clients and Milvus connection."""
        self.embedding_function, self.llm = setup_llm_clients()
        if not self.embedding_function or not self.llm:
            st.error("❌ Failed to initialize LLM or embedding function.")
            return False

        try:
            connections.connect(alias="default", uri=Config.MILVUS_URI, token=Config.MILVUS_TOKEN)
            st.success("✅ Connected to Milvus")

            if utility.has_collection(self.collection_name):
                utility.drop_collection(self.collection_name)
                st.info(f"✅ Collection Activated")

            self.vectorstore = Milvus(
                embedding_function=self.embedding_function,
                collection_name=self.collection_name,
                connection_args={"uri": Config.MILVUS_URI, "token": Config.MILVUS_TOKEN}
            )

            return True
        except Exception as e:
            st.error(f"Error connecting to Milvus: {str(e)}")
            return False
    
    def _get_file_extension(self, filename: str) -> str:
        """Extract file extension from filename."""
        return filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
    
    def _process_pdf_file(self, temp_file_path: str, filename: str) -> List[Document]:
        """Process PDF file and return documents."""
        loader = PyPDFLoader(temp_file_path)
        documents = loader.load()
        
        processed_documents = []
        for doc in documents:
            new_metadata = {
                "title": filename,
                "source": f"{filename} (Page {doc.metadata.get('page', 'N/A')})",
                "file_type": "pdf"
            }
            processed_doc = Document(page_content=doc.page_content, metadata=new_metadata)
            processed_documents.append(processed_doc)
        
        return processed_documents

    def _process_csv_file(self, temp_file_path: str, filename: str) -> List[Document]:
        """Process CSV file and return documents."""
        try:
            # Read CSV file
            df = pd.read_csv(temp_file_path)
            
            processed_documents = []
            
            # Convert each row to a document
            for idx, row in df.iterrows():
                # Create readable content from row
                content_parts = []
                for col in df.columns:
                    value = row[col]
                    if pd.notna(value):  # Skip NaN values
                        content_parts.append(f"{col}: {value}")
                
                content = "\n".join(content_parts)
                
                new_metadata = {
                    "title": filename,
                    "source": f"{filename} (Row {idx + 1})",
                    "file_type": "csv",
                    "row_number": idx + 1
                }
                
                processed_doc = Document(page_content=content, metadata=new_metadata)
                processed_documents.append(processed_doc)
            
            return processed_documents
            
        except Exception as e:
            st.error(f"Error processing CSV: {str(e)}")
            return []
    
    def _process_excel_file(self, temp_file_path: str, filename: str) -> List[Document]:
        """Process Excel file and return documents."""
        try:
            # Read Excel file (all sheets)
            excel_file = pd.ExcelFile(temp_file_path)
            processed_documents = []
            
            for sheet_name in excel_file.sheet_names:
                df = pd.read_excel(temp_file_path, sheet_name=sheet_name)
                
                # Convert each row to a document
                for idx, row in df.iterrows():
                    # Create readable content from row
                    content_parts = [f"Sheet: {sheet_name}"]
                    for col in df.columns:
                        value = row[col]
                        if pd.notna(value):  # Skip NaN values
                            content_parts.append(f"{col}: {value}")
                    
                    content = "\n".join(content_parts)
                    
                    new_metadata = {
                        "title": filename,
                        "source": f"{filename} (Sheet: {sheet_name}, Row {idx + 1})",
                        "file_type": "excel",
                        "sheet_name": sheet_name,
                        "row_number": idx + 1
                    }
                    
                    processed_doc = Document(page_content=content, metadata=new_metadata)
                    processed_documents.append(processed_doc)
            
            return processed_documents
            
        except Exception as e:
            st.error(f"Error processing Excel: {str(e)}")
            return []
    
    def _process_text_file(self, temp_file_path: str, filename: str) -> List[Document]:
        """Process text file and return documents."""
        try:
            with open(temp_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        
            paragraphs = content.split('\n\n')
            
            processed_documents = []
            for idx, paragraph in enumerate(paragraphs):
                if paragraph.strip(): 
                    new_metadata = {
                        "title": filename,
                        "source": f"{filename} (Section {idx + 1})",
                        "file_type": "txt",
                        "section_number": idx + 1
                    }
                    
                    processed_doc = Document(page_content=paragraph.strip(), metadata=new_metadata)
                    processed_documents.append(processed_doc)
            
            return processed_documents
        
        except UnicodeDecodeError:
            try:
                with open(temp_file_path, 'r', encoding='latin-1') as f:
                    content = f.read()
                
                paragraphs = content.split('\n\n')
                processed_documents = []
                
                for idx, paragraph in enumerate(paragraphs):
                    if paragraph.strip():
                        new_metadata = {
                            "title": filename,
                            "source": f"{filename} (Section {idx + 1})",
                            "file_type": "txt",
                            "section_number": idx + 1
                        }
                        processed_doc = Document(page_content=paragraph.strip(), metadata=new_metadata)
                        processed_documents.append(processed_doc)
                
                return processed_documents
            except Exception as e:
                st.error(f"Error processing text file: {str(e)}")
                return []
            
    def process_file(self, uploaded_file):
        """
        Universal file processor that handles PDF, CSV, Excel, and TXT files.
        Maintains the same logic as process_pdf but supports multiple formats.
        """
        temp_file_path = os.path.join(".", uploaded_file.name)
        
        try:
            file_ext = self._get_file_extension(uploaded_file.name)
            
            if file_ext not in self.supported_formats:
                st.error(f"Unsupported file format: .{file_ext}")
                st.info(f"Supported formats: {', '.join([f'.{ext}' for ext in self.supported_formats.keys()])}")
                return False
            
            with open(temp_file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            st.info(f"📄 Processing {file_ext.upper()} file: {uploaded_file.name}")
            
            processor = self.supported_formats[file_ext]
            processed_documents = processor(temp_file_path, uploaded_file.name)
            
            if not processed_documents:
                st.error("❌ No content extracted from file")
                return False
            
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=500,
                chunk_overlap=50
            )
            splits = text_splitter.split_documents(processed_documents)
            
            if self.vectorstore:
                self.vectorstore.add_documents(splits)
                st.success(f"Successfully added {len(splits)} chunks from {uploaded_file.name} to the knowledge base.")
            else:
                st.error("Vector store not initialized. Please click 'Initialize Knowledge Base' first.")
                return False

            return True
            
        except Exception as e:
            st.error(f"Error processing file: {str(e)}")
            return False
            
        finally:
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
    
    def process_pdf(self, uploaded_file):
        """
        Legacy PDF processor - now redirects to universal process_file.
        Kept for backward compatibility.
        """
        return self.process_file(uploaded_file)

    def load_knowledge_base(self):
        """Load knowledge base from the specified PDF file into vector database."""
        try:
            
            if not candidate_path.exists():
                st.error(f"PDF not found at: {candidate_path}")
                st.info("Please ensure you have uploaded the file")
                return False
            
            PDF_PATH = str(candidate_path)
            st.info(f"✅ File is processing to upload")

            loader = PyPDFLoader(PDF_PATH)
            documents = loader.load()

            processed_documents = []
            for doc in documents:
                new_metadata = {
                    "title": os.path.basename(PDF_PATH),
                    "source": f"{os.path.basename(PDF_PATH)} (Page {doc.metadata.get('page', 'N/A')})"
                }
                processed_doc = Document(page_content=doc.page_content, metadata=new_metadata)
                processed_documents.append(processed_doc)

            text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
            splits = text_splitter.split_documents(processed_documents)

            self.vectorstore = Milvus.from_documents(
                documents=splits,
                embedding=self.embedding_function,
                collection_name=self.collection_name,
                connection_args={"uri": Config.MILVUS_URI, "token": Config.MILVUS_TOKEN},
                drop_old=True
            )

            st.success(f"✅ Loaded {len(splits)} chunks from into vector database")
            return True
        except Exception as e:
            st.error(f"Error loading knowledge base: {str(e)}")
            return False

    def retrieve_relevant_info(self, query: str, k: int = 3):
        """Retrieve relevant facilities information from vector database."""
        try:
            retriever = self.vectorstore.as_retriever(search_kwargs={"k": k})
            relevant_docs = retriever.invoke(query)
            return relevant_docs
        except Exception as e:
            st.error(f"Error retrieving documents: {str(e)}")
            return []

    def generate_response(self, query: str):
        """Generate response using PURE RAG approach with chat history."""
        try:
            relevant_docs = self.retrieve_relevant_info(query)

            if not relevant_docs:
                return {
                    "answer": "I couldn't find relevant information. Please try rephrasing your question.",
                    "sources": [],
                    "error": True
                }

            context = "\n\n".join([doc.page_content for doc in relevant_docs])

            history_context = ""
            if self.chat_history:
                history_context = "Previous conversation:\n"
                for msg in self.chat_history[-4:]:
                    history_context += f"{msg['role']}: {msg['content']}\n"

            prompt_text = FacilitiesPrompt.create_prompt(history_context, context, query)

            response = self.llm.invoke(prompt_text)
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
