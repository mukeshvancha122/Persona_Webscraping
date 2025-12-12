import json
import os
from typing import Optional
import httpx
from src.types.orchestrator_plan import OrchestratorPlan
from src.services.prompt import build_orchestrator_prompt


async def spin_up_orchestrator(query: str) -> OrchestratorPlan:
    """
    Use Google Gemini to break down the query into a structured plan
    
    Args:
        query: The user's query
        
    Returns:
        OrchestratorPlan with response and agents
    """
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY not set")
    
    try:
        # Using Google's generative AI REST API
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent",
                params={"key": api_key},
                json={
                    "contents": [
                        {
                            "role": "user",
                            "parts": [
                                {
                                    "text": f"""System: {build_orchestrator_prompt()}

User Query: {query}

Please respond with a JSON object containing:
- response: A brief description of your plan
- agents: An array of agent objects, each with "task" and "prompt" fields"""
                                }
                            ]
                        }
                    ],
                    "generationConfig": {
                        "temperature": 0.7,
                        "maxOutputTokens": 2000,
                    }
                },
                timeout=30.0,
            )
            response.raise_for_status()
            data = response.json()
            
        # Extract the text response
        if data.get("candidates"):
            content = data["candidates"][0]["content"]["parts"][0]["text"]
            
            # Parse JSON from response
            try:
                # Try to extract JSON if it's wrapped in markdown code blocks
                if "```json" in content:
                    json_str = content.split("```json")[1].split("```")[0].strip()
                elif "```" in content:
                    json_str = content.split("```")[1].split("```")[0].strip()
                else:
                    json_str = content
                
                plan_data = json.loads(json_str)
                return OrchestratorPlan(**plan_data)
            except json.JSONDecodeError as e:
                print(f"[orchestrator] Failed to parse response as JSON: {e}")
                print(f"Response was: {content}")
                # Return a default plan
                return OrchestratorPlan(
                    response="Unable to parse orchestrator response",
                    agents=[]
                )
        else:
            raise ValueError("No candidates in response")
            
    except Exception as e:
        print(f"[orchestrator] Request failed: {e}")
        raise


async def spin_up_orchestrator_anthropic(query: str) -> OrchestratorPlan:
    """
    Alternative: Use Anthropic Claude for orchestration
    
    Args:
        query: The user's query
        
    Returns:
        OrchestratorPlan with response and agents
    """
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY not set")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": "claude-3-opus-20240229",
                    "max_tokens": 2000,
                    "system": build_orchestrator_prompt(),
                    "messages": [
                        {
                            "role": "user",
                            "content": f"""{query}

Please respond with a JSON object containing:
- response: A brief description of your plan
- agents: An array of agent objects, each with "task" and "prompt" fields"""
                        }
                    ]
                },
                timeout=30.0,
            )
            response.raise_for_status()
            data = response.json()
            
        # Extract the text response
        if data.get("content"):
            content = data["content"][0]["text"]
            
            # Parse JSON from response
            try:
                if "```json" in content:
                    json_str = content.split("```json")[1].split("```")[0].strip()
                elif "```" in content:
                    json_str = content.split("```")[1].split("```")[0].strip()
                else:
                    json_str = content
                
                plan_data = json.loads(json_str)
                return OrchestratorPlan(**plan_data)
            except json.JSONDecodeError as e:
                print(f"[orchestrator] Failed to parse response as JSON: {e}")
                print(f"Response was: {content}")
                return OrchestratorPlan(
                    response="Unable to parse orchestrator response",
                    agents=[]
                )
        else:
            raise ValueError("No content in response")
            
    except Exception as e:
        print(f"[orchestrator] Anthropic request failed: {e}")
        raise
