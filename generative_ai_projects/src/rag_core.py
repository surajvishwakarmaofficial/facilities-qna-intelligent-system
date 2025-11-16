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



dotenv.load_dotenv()

PROJECT_ROOT = pathlib.Path(__file__).parent.parent.parent
candidate_path = PROJECT_ROOT / "generative_ai_projects" / "data" / "knowledge_base.pdf"

dotenv.load_dotenv()

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

    def initialize_clients(self):
        """Initializes LLM/Embedding clients and Milvus connection."""
        if self.llm and self.embedding_function and self.vectorstore:
            return True

        self.embedding_function, self.llm = setup_llm_clients()
        if not self.embedding_function or not self.llm:
            st.error("❌ Failed to initialize LLM or embedding function.")
            return False

        try:
            connections.connect(alias="default", uri=Config.MILVUS_URI, token=Config.MILVUS_TOKEN)
            st.success("✅ Connected to Milvus")
            self.vectorstore = Milvus(
                embedding_function=self.embedding_function,
                collection_name=self.collection_name,
                connection_args={"uri": Config.MILVUS_URI, "token": Config.MILVUS_TOKEN},
                auto_id=True
            )
            return True
        except Exception as e:
            st.error(f"Error connecting to Milvus: {str(e)}")
            return False

    def rebuild_knowledge_base_from_directory(self):
        st.info(f"📁 Starting knowledge base rebuild from directory: {self.knowledge_base_dir}")
        if not self.initialize_clients(): return False
        
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
            st.error("❌ No documents were processed from the directory.")
            return False

        text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
        splits = text_splitter.split_documents(all_documents)

        self.vectorstore = Milvus.from_documents(
            documents=splits,
            embedding=self.embedding_function,
            collection_name=self.collection_name,
            connection_args={"uri": Config.MILVUS_URI, "token": Config.MILVUS_TOKEN},
        )
        st.success(f"✅ Successfully rebuilt knowledge base with {len(splits)} chunks.")
        return True
            
    def _get_file_extension(self, filename: str) -> str:
        return filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
    
    def _process_pdf_file(self, temp_file_path: str, filename: str) -> List[Document]:
        loader = PyPDFLoader(temp_file_path)
        documents = loader.load()
        processed_documents = []
        for doc in documents:
            new_metadata = {"title": filename, "source": f"{filename} (Page {doc.metadata.get('page', 'N/A')})", "file_type": "pdf"}
            processed_doc = Document(page_content=doc.page_content, metadata=new_metadata)
            processed_documents.append(processed_doc)
        return processed_documents

    def _process_csv_file(self, temp_file_path: str, filename: str) -> List[Document]:
        try:
            df = pd.read_csv(temp_file_path)
            processed_documents = []
            for idx, row in df.iterrows():
                content_parts = [f"{col}: {value}" for col, value in row.items() if pd.notna(value)]
                content = "\n".join(content_parts)
                new_metadata = {"title": filename, "source": f"{filename} (Row {idx + 1})", "file_type": "csv", "row_number": idx + 1}
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
                    new_metadata = {"title": filename, "source": f"{filename} (Sheet: {sheet_name}, Row {idx + 1})", "file_type": "excel", "sheet_name": sheet_name, "row_number": idx + 1}
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
            encoding_to_use = 'utf-8'
        except UnicodeDecodeError:
            try:
                with open(temp_file_path, 'r', encoding='latin-1') as f:
                    content = f.read()
                encoding_to_use = 'latin-1'
            except Exception as e:
                st.error(f"Error processing text file: {str(e)}")
                return []
        
        paragraphs = content.split('\n\n')
        processed_documents = []
        for idx, paragraph in enumerate(paragraphs):
            if paragraph.strip():
                new_metadata = {"title": filename, "source": f"{filename} (Section {idx + 1})", "file_type": "txt", "section_number": idx + 1}
                processed_doc = Document(page_content=paragraph.strip(), metadata=new_metadata)
                processed_documents.append(processed_doc)
        return processed_documents
    
    def generate_response_stream(self, query: str):
        """
        Generate a streaming response using RAG, yielding tokens as they arrive.
        Also returns the source documents used for the response.
        """
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
            
            prompt = f"""You are a professional and specialized Facilities Management Assistant... (your full prompt here)"""
            
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
        """
        USER ACTION: Processes a single uploaded file and ADDS it to the existing collection.
        """
        temp_file_path = os.path.join(".", uploaded_file.name)
        try:
            if not self.vectorstore:
                st.error("Knowledge base is not initialized. Please ask an admin to initialize it first.")
                return False
            
            file_ext = self._get_file_extension(uploaded_file.name)
            if file_ext not in self.supported_formats:
                st.error(f"Unsupported file format: .{file_ext}")
                return False

            with open(temp_file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            st.info(f"📄 Processing {file_ext.upper()} file: {uploaded_file.name}")
            processor = self.supported_formats[file_ext]
            processed_documents = processor(temp_file_path, uploaded_file.name)
            
            if not processed_documents:
                st.error("❌ No content extracted from file")
                return False
            
            text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
            splits = text_splitter.split_documents(processed_documents)
            
            self.vectorstore.add_documents(splits)
            st.success(f"Successfully added {len(splits)} chunks from {uploaded_file.name} to the knowledge base.")
            return True
            
        except Exception as e:
            st.error(f"Error processing file: {str(e)}")
            return False
        finally:
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
    
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
            if not self.vectorstore or not utility.has_collection(self.collection_name):
                return {"answer": "The knowledge base has not been initialized. Please contact an administrator.", "sources": [], "error": True}

            relevant_docs = self.retrieve_relevant_info(query)

            if not relevant_docs:
                return {
                    "answer": "I could not find relevant information in the facilities knowledge base to answer your question. Please try rephrasing or ask a different facilities-related question.",
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

            If the user's question is NOT related to facilities management, you MUST politely refuse to answer. State that you can only assist with facilities-related inquiries. Do NOT answer the question, even if you know the answer from your general knowledge.

            {history_context}

            Context from facilities documents:
            {context}

            Current Question: {query}

            Based on these strict instructions, please provide your response. If the context does not contain the answer, but the question is about facilities, state that you do not have that specific information and can escalate the query to the facilities department."""

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
        