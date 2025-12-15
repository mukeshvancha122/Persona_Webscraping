
import json
import os
import httpx
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
# Assuming these custom types/services are defined elsewhere
from src.types.orchestrator_plan import ChatRequest
# from src.services.orchestrator import spin_up_orchestrator
# from src.services.prompt import build_sub_agent_prompt

# --- PLACEHOLDER IMPORTS FOR SIMULATION ---
# You need to ensure these are correctly imported in your real project.

async def spin_up_orchestrator(query): # Placeholder
    class Agent(object):
        def __init__(self, task, prompt):
            self.task = task
            self.prompt = prompt
            
    class Plan(object):
        def __init__(self, agents):
            self.agents = [Agent(f"Task {i}", f"Prompt {i}") for i in range(2)]
        def model_dump(self):
            return {"agents": [a.__dict__ for a in self.agents]}
    return Plan(None)

def build_sub_agent_prompt(): # Placeholder
    return "You are a helpful assistant."

# --- END PLACEHOLDER IMPORTS ---


router = APIRouter()

# ... (stream_generator function remains the same, but the call to call_ai_agent needs the correct arguments)
# The full stream_generator logic is omitted for brevity but should be included here.

# --- Corrected call_ai_agent function ---

async def call_ai_agent(prompt: str, system_prompt: str, knowledge_entries: list):
    """Call an AI agent with the Google Search tool and stream results"""
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        # Check if the environment variable is GEMINI_API_KEY
        api_key = os.getenv("GEMINI_API_KEY") 
        if not api_key:
            raise ValueError("GEMINI_API_KEY or GOOGLE_API_KEY not set")
    
    # We remove the custom tools definition as it was unused and confusing the call.
    # The current call passes {"googleSearch": {}} which is the correct way for the official tool.
    
    # We must construct the contents list carefully to include the system prompt
    # and to stream the full response.
    
    contents = [
        {
            "role": "user",
            "parts": [
                {"text": f"System: {system_prompt}\n\nUser: {prompt}"}
            ]
        }
    ]
    
    try:
        async with httpx.AsyncClient() as client:
            # Note: The API call should ideally include the system prompt in its own block if possible,
            # but concatenating it to the user prompt is a common workaround for streaming.
            response = await client.post(
                "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:streamGenerateContent",
                params={"key": api_key},
                json={
                    "contents": contents,
                    "config": { # Use 'config' for tools in streaming
                        "tools": [{"googleSearch": {}}],
                    },
                    "generationConfig": {
                        "temperature": 0.7,
                        "maxOutputTokens": 2000,
                    }
                },
                timeout=60.0,
            )
            response.raise_for_status()
            
            # Stream the response
            # NOTE: We are now yielding the raw JSON line data directly. 
            async for line in response.aiter_lines():
                if line.strip():
                    # The Gemini API returns chunks that start with 'data: ' and are JSON objects.
                    # We only need to forward the data we receive.
                    yield line

    except Exception as e:
        print(f"[agent] Call failed: {e}")
        yield json.dumps({"type": "error", "error": str(e)}) # Yield JSON string for SSE


# --- Your stream_generator function (Re-included with corrected call) ---
async def stream_generator(query: str):
    """Generator function that yields SSE formatted messages"""
    try:
        knowledge_entries = []
        
        # Generate the orchestrator plan
        # NOTE: OrchestratorPlan is a placeholder, ensure it's imported
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
            # NOTE: The knowledge_entries is currently not used inside call_ai_agent, but passed for completeness
            agent_response_stream = call_ai_agent( 
                agent.prompt,
                system_prompt,
                knowledge_entries
            )
            
            # Stream the response
            async for line in agent_response_stream:
                # The line from call_ai_agent is either a raw JSON line from Gemini or an error JSON string.
                # We need to wrap it in the SSE format.
                if line.startswith("data: "):
                     yield f"{line}\n\n" # Already in SSE format
                else:
                    # This handles the error scenario where call_ai_agent yields a raw JSON string
                    yield f"data: {line}\n\n" 

            # Notify agent completion
            yield f"data: {json.dumps({'type': 'agentEnd', 'agent': agent.task})}\n\n"
    
    except Exception as e:
        print(f"[chat] Stream error: {e}")
        yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"


@router.post("/", response_model=None)
async def chat(request_data: ChatRequest):
    """Chat endpoint that accepts a query and returns a streaming response"""
    
    # We need to make sure ChatRequest is properly validated.
    # If the provided structure is not a Pydantic model, FastAPI will fail.
    # Assuming ChatRequest is a Pydantic model with a 'query' attribute.
    
    try:
        query = request_data.query
    except AttributeError:
        # Fallback if request_data is not a Pydantic model or is empty
        return {"error": "Invalid request body format."}, 400
    
    if not query:
        return {"error": "Query is required"}, 400
    
    return StreamingResponse(
        stream_generator(query),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "Connection": "keep-alive",
            # Ensure the CORS header is correctly set
            "Access-Control-Allow-Origin": os.getenv("FRONTEND_URL", "*"), 
        }
    )