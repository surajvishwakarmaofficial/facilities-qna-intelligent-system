import litellm
from typing import List, Dict
from .base import BaseLLM


class LiteLLMClient(BaseLLM):
    def __init__(self, model: str = "gpt-4o-mini", embedding_model: str = "text-embedding-3-small"):
        self.model = model
        self.embedding_model_name = embedding_model
    
    async def generate(self, messages: List[Dict], **kwargs) -> str:
        response = await litellm.acompletion(
            model=self.model,
            messages=messages,
            temperature=kwargs.get("temperature", 0.3),
            max_tokens=kwargs.get("max_tokens", 500)
        )
        return response.choices[0].message.content
    
    async def embed(self, text: str) -> List[float]:
        response = await litellm.aembedding(
            model=self.embedding_model_name,
            input=[text]
        )
        return response.data[0].embedding