# src/llm/clients.py

from typing import List, Dict
from litellm import completion
from langchain_openai import AzureOpenAIEmbeddings, AzureChatOpenAI
import streamlit as st
import os
import dotenv

dotenv.load_dotenv()

AZURE_ENDPOINT = os.environ.get("AZURE_ENDPOINT")
AZURE_API_KEY = os.environ.get("AZURE_API_KEY")
AZURE_API_VERSION = os.environ.get("AZURE_API_VERSION")
AZURE_DEPLOYMENT = os.environ.get("AZURE_DEPLOYMENT") 
AZURE_EMBEDDING_DEPLOYMENT = os.environ.get("AZURE_EMBEDDING_DEPLOYMENT") 
GREETING_LLM_TEMP = os.environ.get("GREETING_LLM_TEMP")
MAX_TOKENS = os.environ.get("MAX_TOKENS")
LLM_TEMP = os.environ.get("LLM_TEMP")


def setup_llm_clients():
    """Setup Azure OpenAI embeddings and LLM objects."""
    try:
        # Setup embeddings
        embedding_function = AzureOpenAIEmbeddings(
            azure_endpoint=AZURE_ENDPOINT,
            azure_deployment=AZURE_EMBEDDING_DEPLOYMENT,
            api_key=AZURE_API_KEY,
            api_version=AZURE_API_VERSION
        )
        
        # Setup LLM
        llm = AzureChatOpenAI(
            azure_endpoint=AZURE_ENDPOINT,
            azure_deployment=AZURE_DEPLOYMENT,
            api_key=AZURE_API_KEY,
            api_version=AZURE_API_VERSION,
            temperature=0.3,
            max_tokens=1000
        )
        
        return embedding_function, llm
    except Exception as e:
        st.error(f"Error setting up Azure OpenAI clients: {str(e)}")
        return None, None

def get_llm_greeting_response(chat_history: List[Dict], query: str):
    """Generates a non-RAG response using LiteLLM for greetings or uninitialized state."""
    
    try:
        messages = [
            {"role": "system", "content": "You are a professional Facilities Management Assistant. Your knowledge base is currently UNINITIALIZED. You CANNOT answer any questions about specific policies... (rest of system prompt)"},
        ]
        
        for msg in chat_history[-4:]:
            messages.append({"role": msg['role'], "content": msg['content']})
            
        messages.append({"role": "user", "content": query})
        
        model_string = f"azure/{AZURE_DEPLOYMENT}"
        
        response = completion(
            model=model_string,
            messages=messages,
            azure_key=AZURE_API_KEY,
            azure_api_base=AZURE_ENDPOINT,
            api_version=AZURE_API_VERSION,
            temperature=GREETING_LLM_TEMP
        )
        
        return response['choices'][0]['message']['content']
    
    except Exception as e:
        st.error(f"LiteLLM Fallback Error: {str(e)}")
        return "Hello! I am your Facilities Management Assistant. I can't access my full knowledge yet. Please click 'Initialize Knowledge Base' in the sidebar to begin."
    
    