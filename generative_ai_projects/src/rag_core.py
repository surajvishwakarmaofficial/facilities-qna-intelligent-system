import os
from typing import List, Dict
import streamlit as st
from pymilvus import connections, utility
from langchain_community.vectorstores import Milvus
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_community.document_loaders import PyPDFLoader
import pathlib

from src.llm.clients import setup_llm_clients
import dotenv

dotenv.load_dotenv()

COLLECTION_NAME = os.environ.get("COLLECTION_NAME")
MILVUS_URI = os.environ.get("MILVUS_URI")
MILVUS_TOKEN = os.environ.get("MILVUS_TOKEN")

PROJECT_ROOT = pathlib.Path(__file__).parent.parent.parent
candidate_path = PROJECT_ROOT / "generative_ai_projects" / "data" / "knowledge_base.pdf"

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
            st.error("❌ Failed to initialize LLM or embedding function.")
            return False

        try:
            connections.connect(alias="default", uri=MILVUS_URI, token=MILVUS_TOKEN)
            st.success("✅ Connected to Milvus")

            if utility.has_collection(self.collection_name):
                utility.drop_collection(self.collection_name)
                st.info(f"✅ Collection Activated")

            self.vectorstore = Milvus(
                embedding_function=self.embedding_function,
                collection_name=self.collection_name,
                connection_args={"uri": MILVUS_URI, "token": MILVUS_TOKEN}
            )

            return True
        except Exception as e:
            st.error(f"Error connecting to Milvus: {str(e)}")
            return False

    def load_knowledge_base(self):
        """Load knowledge base from the specified PDF file into vector database."""
        try:

            PROJECT_ROOT = pathlib.Path(__file__).parent.parent.parent
            candidate_path = PROJECT_ROOT / "generative_ai_projects" / "data" / "knowledge_base.pdf"
            
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
                connection_args={"uri": MILVUS_URI, "token": MILVUS_TOKEN},
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

            prompt = f"""You are a professional Facilities Management Assistant for an office building.
            Answer the question based ONLY on the context below. Be concise, helpful, and professional.

            {history_context}

            Context from facilities handbook:
            {context}

            Current Question: {query}

            Provide a clear, structured answer about facilities, amenities, policies, and procedures.
            Include relevant contact information (extensions) when applicable.
            If the context doesn't contain the answer, politely say so and suggest contacting the relevant department."""

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
