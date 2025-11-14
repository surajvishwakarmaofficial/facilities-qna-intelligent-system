# src/rag_core.py

import os
from typing import List, Dict
import streamlit as st
from pymilvus import connections, utility
from langchain_community.vectorstores import Milvus
from langchain_text_splitters import RecursiveCharacterTextSplitter 
from langchain_core.documents import Document
from langchain_community.document_loaders import PyPDFLoader

from data.initial_data import SAMPLE_FACILITIES_DATA
from src.llm.clients import setup_llm_clients # To get the LLM and Embeddings objects
import os

import dotenv

dotenv.load_dotenv()

COLLECTION_NAME = os.environ.get("COLLECTION_NAME")
MILVUS_URI = os.environ.get("MILVUS_URI")
MILVUS_TOKEN = os.environ.get("MILVUS_TOKEN")


class FacilitiesRAGSystem:
    """RAG System for Facilities Management"""
    
    def __init__(self):
        self.collection_name = COLLECTION_NAME
        self.embedding_function = None
        self.vectorstore = None
        self.llm = None
        self.chat_history = []
        
    def initialize_clients(self):
        """Initializes LLM/Embedding clients and Milvus connection."""
        self.embedding_function, self.llm = setup_llm_clients()
        if not self.embedding_function or not self.llm:
            return False

        try:
            connections.connect(
                alias="default",
                uri=MILVUS_URI,
                token=MILVUS_TOKEN

            )
            st.success("✅ Connected to Milvus")
            
            # Clean existing collection if needed
            if utility.has_collection(self.collection_name):
                utility.drop_collection(self.collection_name)
                st.info(f"Cleaned existing collection: {self.collection_name}")
            
            # Initialize a placeholder vectorstore object
            self.vectorstore = Milvus(
                embedding_function=self.embedding_function,
                collection_name=self.collection_name,
                connection_args={"uri": MILVUS_URI, "token": MILVUS_TOKEN}
            )
            
            return True
        except Exception as e:
            st.error(f"Error connecting to Milvus: {str(e)}")
            return False
    
    def load_knowledge_base(self, initial_load=True):
        """Load initial facilities documents into vector database"""
        try:
            if not initial_load:
                return True
                
            documents = []
            for item in SAMPLE_FACILITIES_DATA:
                doc = Document(
                    page_content=item["content"],
                    metadata={"title": item["title"], "source": "facilities_handbook"}
                )
                documents.append(doc)
            
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=500,
                chunk_overlap=50
            )
            splits = text_splitter.split_documents(documents)
            
            # Create or update vectorstore using from_documents
            self.vectorstore = Milvus.from_documents(
                documents=splits,
                embedding=self.embedding_function,
                collection_name=self.collection_name,
                connection_args={"uri": MILVUS_URI, "token": MILVUS_TOKEN},
                drop_old=True
            )
            
            st.success(f"✅ Loaded {len(documents)} policy documents into vector database")
            return True
        except Exception as e:
            st.error(f"Error loading knowledge base: {str(e)}")
            return False

    def process_pdf(self, uploaded_file):
        """Process an uploaded PDF file and add its content to the vector store."""
        temp_file_path = os.path.join(".", uploaded_file.name)
        try:
            # Save the uploaded file temporarily
            with open(temp_file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            # Load documents from the PDF
            loader = PyPDFLoader(temp_file_path)
            documents = loader.load()
            
            # --- FIX: Unify the metadata to match the initial schema ('title', 'source') ---
            processed_documents = []
            for doc in documents:
                new_metadata = {
                    "title": uploaded_file.name, 
                    "source": f"{uploaded_file.name} (Page {doc.metadata.get('page', 'N/A')})"
                }
                processed_doc = Document(page_content=doc.page_content, metadata=new_metadata)
                processed_documents.append(processed_doc)
            # --------------------------------------------------------------------------------

            # Split the processed documents
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=500,
                chunk_overlap=50
            )
            splits = text_splitter.split_documents(processed_documents)
            
            # Add to the existing vectorstore
            if self.vectorstore:
                self.vectorstore.add_documents(splits)
                st.success(f"✅ Successfully added {len(splits)} chunks from {uploaded_file.name} to the knowledge base.")
            else:
                st.error("Vector store not initialized. Please click 'Initialize Knowledge Base' first.")
                return False

            return True
        except Exception as e:
            st.error(f"Error processing PDF: {str(e)}")
            return False
        finally:
             # Clean up the temporary file
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)


    def retrieve_relevant_info(self, query: str, k: int = 3):
        """Retrieve relevant facilities information from vector database"""
        try:
            retriever = self.vectorstore.as_retriever(search_kwargs={"k": k})
            relevant_docs = retriever.invoke(query)
            return relevant_docs
        except Exception as e:
            st.error(f"Error retrieving documents: {str(e)}")
            return []

    def generate_response(self, query: str):
        """Generate response using PURE RAG approach with chat history"""
        try:
            # Retrieve relevant documents
            relevant_docs = self.retrieve_relevant_info(query)
            
            if not relevant_docs:
                return {
                    "answer": "I couldn't find relevant information. Please try rephrasing your question.",
                    "sources": [],
                    "error": True
                }
            
            context = "\n\n".join([doc.page_content for doc in relevant_docs])
            
            # Create chat history context
            history_context = ""
            if self.chat_history:
                history_context = "Previous conversation:\n"
                for msg in self.chat_history[-4:]:  # Last 4 messages
                    history_context += f"{msg['role']}: {msg['content']}\n"
            
            # Create enhanced prompt
            prompt = f"""You are a professional Facilities Management Assistant for an office building.
                    Answer the question based ONLY on the context below. Be concise, helpful, and professional.

                    {history_context}

                    Context from facilities handbook:
                    {context}

                    Current Question: {query}

                    Provide a clear, structured answer about facilities, amenities, policies, and procedures.
                    Include relevant contact information (extensions) when applicable.
                    If the context doesn't contain the answer, politely say so and suggest contacting the relevant department."""

            # Generate response using LLM
            response = self.llm.invoke(prompt)
            answer = response.content
            
            # Update chat history
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


        
        