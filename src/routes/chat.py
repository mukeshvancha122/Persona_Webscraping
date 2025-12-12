import json
import os
import httpx
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from src.types.orchestrator_plan import ChatRequest
from src.services.orchestrator import spin_up_orchestrator
from src.services.search import SearchService
from src.services.prompt import build_sub_agent_prompt


router = APIRouter()


async def stream_generator(query: str):
    """Generator function that yields SSE formatted messages"""
    try:
        knowledge_entries = []
        
        # Generate the orchestrator plan
        plan = await spin_up_orchestrator(query)
        
        # Send initial plan
        yield f"data: {json.dumps({'type': 'plan', 'plan': plan.model_dump()})}\n\n"
        
        # Process each agent
        for agent_idx, agent in enumerate(plan.agents):
            # Notify agent start
            yield f"data: {json.dumps({'type': 'agentStart', 'agent': agent.task, 'task': agent.task, 'prompt': agent.prompt})}\n\n"
            
            # Build system prompt with knowledge base
            system_prompt = build_sub_agent_prompt()
            if knowledge_entries:
                system_prompt += "\n\nKnowledge Base:\n"
                system_prompt += "\n".join([f"- {k}" for k in knowledge_entries])
            
            # Call the AI model with streaming
            agent_response = await call_ai_agent(
                agent.prompt,
                system_prompt,
                knowledge_entries
            )
            
            # Stream the response
            async for chunk in agent_response:
                yield f"data: {json.dumps(chunk)}\n\n"
            
            # Notify agent completion
            yield f"data: {json.dumps({'type': 'agentEnd', 'agent': agent.task})}\n\n"
    
    except Exception as e:
        print(f"[chat] Stream error: {e}")
        yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"


async def call_ai_agent(prompt: str, system_prompt: str, knowledge_entries: list):
    """Call an AI agent with tools and stream results"""
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY not set")
    
    tools = [
        {
            "name": "search",
            "description": "Run a web search",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query"
                    }
                },
                "required": ["query"]
            }
        },
        {
            "name": "viewPage",
            "description": "View the contents of a webpage",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "The URL of the page to visit"
                    }
                },
                "required": ["url"]
            }
        },
        {
            "name": "addToKnowledge",
            "description": "Add details to a knowledge base",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "knowledge": {
                        "type": "string",
                        "description": "Information to persist"
                    }
                },
                "required": ["knowledge"]
            }
        }
    ]
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:streamGenerateContent",
                params={"key": api_key},
                json={
                    "contents": [
                        {
                            "role": "user",
                            "parts": [
                                {"text": f"System: {system_prompt}\n\nUser: {prompt}"}
                            ]
                        }
                    ],
                    "tools": [{"googleSearch": {}}],
                    "generationConfig": {
                        "temperature": 0.7,
                        "maxOutputTokens": 2000,
                    }
                },
                timeout=60.0,
            )
            response.raise_for_status()
            
            # Stream the response
            async for line in response.aiter_lines():
                if line.strip():
                    try:
                        data = json.loads(line)
                        yield {"type": "response", "data": data}
                    except json.JSONDecodeError:
                        pass
    
    except Exception as e:
        print(f"[agent] Call failed: {e}")
        yield {"type": "error", "error": str(e)}


@router.post("/")
async def chat(request_data: ChatRequest):
    """Chat endpoint that accepts a query and returns a streaming response"""
    query = request_data.query
    
    if not query:
        return {"error": "Query is required"}, 400
    
    return StreamingResponse(
        stream_generator(query),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": os.getenv("FRONTEND_URL", "http://localhost:3000"),
        }
    )
