import os
import json
import httpx
from typing import Optional


class MoonshotAIProvider:
    """Provider for Moonshot AI API"""
    
    BASE_URL = "https://api.moonshot.cn/v1"
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("MOONSHOTAI_API_KEY")
    
    async def chat_completion(
        self,
        messages: list,
        model: str = "moonshot-v1-8k",
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ) -> dict:
        """
        Make a chat completion request to Moonshot AI
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            model: Model identifier (moonshot-v1-8k, moonshot-v1-32k, moonshot-v1-128k)
            temperature: Sampling temperature
            max_tokens: Maximum tokens in response
            
        Returns:
            Response dict with choices and usage
        """
        if not self.api_key:
            raise ValueError("MOONSHOTAI_API_KEY not set")
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.BASE_URL}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": model,
                        "messages": messages,
                        "temperature": temperature,
                        "max_tokens": max_tokens,
                    },
                    timeout=30.0,
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            print(f"[moonshot] Request failed: {e}")
            raise
    
    async def chat_completion_stream(
        self,
        messages: list,
        model: str = "moonshot-v1-8k",
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ):
        """
        Make a streaming chat completion request to Moonshot AI
        
        Yields:
            Streamed response chunks
        """
        if not self.api_key:
            raise ValueError("MOONSHOTAI_API_KEY not set")
        
        try:
            async with httpx.AsyncClient() as client:
                async with client.stream(
                    "POST",
                    f"{self.BASE_URL}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": model,
                        "messages": messages,
                        "temperature": temperature,
                        "max_tokens": max_tokens,
                        "stream": True,
                    },
                    timeout=30.0,
                ) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if line.startswith("data: "):
                            data = line[6:]
                            if data != "[DONE]":
                                try:
                                    yield json.loads(data)
                                except json.JSONDecodeError:
                                    pass
        except Exception as e:
            print(f"[moonshot] Stream failed: {e}")
            raise


# Singleton instance
moonshot_provider = MoonshotAIProvider()
