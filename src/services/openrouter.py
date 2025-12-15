import os
import json
import httpx
from typing import Optional


class OpenRouterClient:
    """Client for OpenRouter API - OpenAI-compatible interface"""
    
    BASE_URL = "https://openrouter.ai/api/v1"
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
    
    async def chat_completion(
        self,
        messages: list,
        model: str = "openai/gpt-4-turbo",
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ) -> dict:
        """
        Make a chat completion request to OpenRouter
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            model: Model identifier (e.g., 'openai/gpt-4', 'anthropic/claude-3-opus')
            temperature: Sampling temperature
            max_tokens: Maximum tokens in response
            
        Returns:
            Response dict with choices and usage
        """
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY not set")
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.BASE_URL}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                        "HTTP-Referer": os.getenv("FRONTEND_URL", "http://localhost:3000"),
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
            print(f"[openrouter] Request failed: {e}")
            raise
    
    async def chat_completion_stream(
        self,
        messages: list,
        model: str = "openai/gpt-4-turbo",
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ):
        """
        Make a streaming chat completion request to OpenRouter
        
        Yields:
            Streamed response chunks
        """
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY not set")
        
        try:
            async with httpx.AsyncClient() as client:
                async with client.stream(
                    "POST",
                    f"{self.BASE_URL}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                        "HTTP-Referer": os.getenv("FRONTEND_URL", "http://localhost:3000"),
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
            print(f"[openrouter] Stream failed: {e}")
            raise


# Singleton instance
openrouter_client = OpenRouterClient()
