from typing import List, Dict
from litellm import completion, embedding
from langchain_core.embeddings import Embeddings
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_core.outputs import ChatResult, ChatGeneration, LLMResult
from langchain_core.callbacks import CallbackManagerForLLMRun
import streamlit as st
import os
import dotenv
from config.constant_config import Config

dotenv.load_dotenv()

class LiteLLMEmbeddings(Embeddings):
    """LangChain-compatible embeddings using LiteLM"""
    
    def __init__(self, model: str, azure_key: str, azure_api_base: str, api_version: str):
        self.model = f"azure/{model}"
        self.azure_key = azure_key
        self.azure_api_base = azure_api_base
        self.api_version = api_version
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed multiple documents"""
        try:
            response = embedding(
                model=self.model,
                input=texts,
                api_key=self.azure_key,
                api_base=self.azure_api_base,
                api_version=self.api_version

            )
            return [item['embedding'] for item in response.data]
        except Exception as e:
            print(f"Error in embed_documents: {str(e)}")
            raise
    
    def embed_query(self, text: str) -> List[float]:
        """Embed a single query"""
        try:
            response = embedding(
                model=self.model,
                input=[text],
                api_key=self.azure_key,
                api_base=self.azure_api_base,
                api_version=self.api_version
            )
            return response.data[0]['embedding']
        except Exception as e:
            print(f"Error in embed_query: {str(e)}")
            raise


class LiteLLMChat(BaseChatModel):
    """LangChain-compatible chat model using LiteLM"""
    
    model: str
    azure_key: str
    azure_api_base: str
    api_version: str
    temperature: float = 0.3
    max_tokens: int = 1000
    
    def __init__(self, model: str, azure_key: str, azure_api_base: str, 
                 api_version: str, temperature: float = 0.3, max_tokens: int = 1000):
        super().__init__(
            model=model,
            azure_key=azure_key,
            azure_api_base=azure_api_base,
            api_version=api_version,
            temperature=temperature,
            max_tokens=max_tokens
        )
    
    def _generate(
        self,
        messages: List[BaseMessage],
        stop: List[str] = None,
        run_manager: CallbackManagerForLLMRun = None,
        **kwargs
    ) -> ChatResult:
        """Generate response using LiteLM"""
        try:
            litellm_messages = []
            for msg in messages:
                if isinstance(msg, HumanMessage):
                    litellm_messages.append({"role": "user", "content": msg.content})
                elif isinstance(msg, AIMessage):
                    litellm_messages.append({"role": "assistant", "content": msg.content})
                elif isinstance(msg, SystemMessage):
                    litellm_messages.append({"role": "system", "content": msg.content})
                else:
                    litellm_messages.append({"role": "user", "content": str(msg.content)})
            
            response = completion(
                model=f"azure/{self.model}",
                messages=litellm_messages,
                api_key=self.azure_key,
                api_base=self.azure_api_base,
                api_version=self.api_version,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                **kwargs
            )
            
            content = response.choices[0].message.content
            
            usage = response.get('usage', {})
            token_usage = {
                'prompt_tokens': usage.get('prompt_tokens', 0),
                'completion_tokens': usage.get('completion_tokens', 0),
                'total_tokens': usage.get('total_tokens', 0)
            }
            
            generation = ChatGeneration(
                message=AIMessage(content=content),
                generation_info={"token_usage": token_usage}
            )
            
            return ChatResult(
                generations=[generation],
                llm_output={"token_usage": token_usage}
            )
        except Exception as e:
            print(f"Error in _generate: {str(e)}")
            raise
    
    def _stream(self, messages: List[BaseMessage], stop: List[str] = None, 
                run_manager: CallbackManagerForLLMRun = None, **kwargs):
        """Stream response using LiteLM"""
        try:
            litellm_messages = []
            for msg in messages:
                if isinstance(msg, HumanMessage):
                    litellm_messages.append({"role": "user", "content": msg.content})
                elif isinstance(msg, AIMessage):
                    litellm_messages.append({"role": "assistant", "content": msg.content})
                elif isinstance(msg, SystemMessage):
                    litellm_messages.append({"role": "system", "content": msg.content})
                else:
                    litellm_messages.append({"role": "user", "content": str(msg.content)})
            
            response = completion(
                model=f"azure/{self.model}",
                messages=litellm_messages,
                api_key=self.azure_key,
                api_base=self.azure_api_base,
                api_version=self.api_version,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                stream=True,
                **kwargs
            )
            
            for chunk in response:
                if chunk.choices[0].delta.content:
                    yield ChatGeneration(
                        message=AIMessage(content=chunk.choices[0].delta.content)
                    )
        except Exception as e:
            print(f"Error in _stream: {str(e)}")
            raise
    
    @property
    def _llm_type(self) -> str:
        return "litellm-azure-chat"


def setup_llm_clients():
    """Setup LiteLLM embeddings and LLM objects with LangChain compatibility."""
    try:
        embedding_function = LiteLLMEmbeddings(
            model=Config.AZURE_EMBEDDING_DEPLOYMENT,
            azure_key=Config.AZURE_API_KEY,
            azure_api_base=Config.AZURE_ENDPOINT,
            api_version=Config.AZURE_API_VERSION
        )
        
        llm = LiteLLMChat(
            model=Config.AZURE_DEPLOYMENT,
            azure_key=Config.AZURE_API_KEY,
            azure_api_base=Config.AZURE_ENDPOINT,
            api_version=Config.AZURE_API_VERSION,
            temperature=float(Config.LLM_TEMP) if float(Config.LLM_TEMP) else 0.3,
            max_tokens=int(Config.MAX_TOKENS) if int(Config.MAX_TOKENS) else 1000,

        )
        
        return embedding_function, llm
    except Exception as e:
        st.error(f"Error setting up LiteLLM clients: {str(e)}")
        return None, None


def get_llm_greeting_response(chat_history: List[Dict], query: str):
    """Generates a non-RAG response using LiteLLM for greetings or uninitialized state."""
    
    try:
        messages = [
            {"role": "system", "content": "You are a professional Facilities Management Assistant. Your knowledge base is currently UNINITIALIZED. You CANNOT answer any questions about specific policies, procedures, or building information until the knowledge base is loaded. Be polite and explain that you need the knowledge base to be initialized first."},
        ]
        
        for msg in chat_history[-4:]:
            messages.append({"role": msg['role'], "content": msg['content']})
            
        messages.append({"role": "user", "content": query})
        
        model_string = f"azure/{Config.AZURE_DEPLOYMENT}"
        
        response = completion(
            model=model_string,
            messages=messages,
            api_key=Config.AZURE_API_KEY,
            api_base=Config.AZURE_ENDPOINT,
            api_version=Config.AZURE_API_VERSION,
            temperature=float(Config.GREETING_LLM_TEMP) if float(Config.GREETING_LLM_TEMP) else 0.7
        )
        
        return response['choices'][0]['message']['content']
    
    except Exception as e:
        st.error(f"LiteLLM Fallback Error: {str(e)}")
        return "Hello! I am your Facilities Management Assistant. I can't access my full knowledge yet. Please click 'Initialize Knowledge Base' in the sidebar to begin."
    
