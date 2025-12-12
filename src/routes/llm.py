from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

from src.services.perplexity_sdk import PerplexitySDK
from src.services.persona_extractor import PersonaExtractor
from perplexity import Perplexity

router = APIRouter()


class GenerateRequest(BaseModel):
    prompt: str
    max_tokens: Optional[int] = 512

# class PersonaProfile(BaseModel):
#     name: str
#     current_job_title: Optional[str] = None
#     company: Optional[str] = None
#     location: Optional[str] = None
#     education: Optional[List[str]] = None
#     skills: Optional[List[str]] = None
#     professional_summary: Optional[str] = None
#     notable_achievements: Optional[List[str]] = None

class SearchRequest(BaseModel):
    queries: List[str]


class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str


class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    system_prompt: Optional[str] = None


@router.post("/generate")
async def generate(req: GenerateRequest):
    """Generate text from Perplexity."""
    try:
        sdk = PerplexitySDK()
        # Use the SDK search as a lightweight 'generate' — return first result
        resp = await sdk.search(req.prompt, max_results=1, max_tokens_per_page=req.max_tokens or 512)
        result = resp
        return {"ok": True, "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/search")
async def search(req: SearchRequest):
    """Run simple searches for each query and return results."""
    try:
        sdk = PerplexitySDK()
        out = []
        for q in req.queries:
            resp = await sdk.search(q)
            out.append({"query": q, "response": resp})
        results = out
        return {"ok": True, "results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/search_sdk")
async def search_sdk(queries: SearchRequest):
    """Use the official Perplexity SDK (via `perplexity` package) to run a single query per request.

    Request body: {"queries": ["q1", "q2"]}
    Returns an array of structured results for each query.
    """
    try:
        sdk = PerplexitySDK()
        out = []
        for q in queries.queries:
            resp = await sdk.search(q, max_results=5, max_tokens_per_page=1024)
            # SDK returns an object with `.results` (demo). Try to pull titles/urls.
            entries = []
            if hasattr(resp, "results") and resp.results:
                for r in resp.results:
                    entries.append(PerplexitySDK.extract_structured(r))
            elif isinstance(resp, dict) and resp.get("results"):
                for r in resp.get("results"):
                    entries.append(PerplexitySDK.extract_structured(r))
            else:
                entries.append({"raw": resp})

            out.append({"query": q, "results": entries})

        return {"ok": True, "results": out}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat")
async def chat(req: ChatRequest):
    """Chat endpoint using Perplexity OpenAI-compatible API.

    Request body:
    {
        "messages": [
            {"role": "user", "content": "Who is Elon Musk?"},
            {"role": "assistant", "content": "...previous response..."},
            {"role": "user", "content": "Tell me more about..."}
        ],
        "system_prompt": "Optional system message"
    }

    Returns: {"ok": true, "response": "..."}
    """
    try:
        client = Perplexity()
        messages = [{"role": m.role, "content": m.content} for m in req.messages]
        response = client.chat.completions.create(
        model="sonar-pro",
        messages=messages,
        # response_format={
        #     "type": "json_schema",
        #     "json_schema": {
        #         "schema": PersonaProfile.model_json_schema()
        #     }
        # },
        web_search_options={"search_context_size": "high"}
        )
        return {"ok": True, "response": response.choices[0].message.content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/extract_persona")
async def extract_persona(queries: SearchRequest):
    """Search for a person and extract structured persona from results.

    Request body: {"queries": ["Name or description"]}
    Returns structured personas: full_name, job_title, company, experience, email, social_media, bio, source_url.
    """
    try:
        sdk = PerplexitySDK()
        out = []

        for q in queries.queries:
            # Search for the person
            resp = await sdk.search(q, max_results=5, max_tokens_per_page=1024)

            # Extract results (SDK returns object with .results attribute or dict with 'results' key)
            search_results = []
            if hasattr(resp, "results") and resp.results:
                search_results = [
                    {"title": getattr(r, "title", ""), "url": getattr(r, "url", ""), "snippet": getattr(r, "snippet", "")}
                    for r in resp.results
                ]
            elif isinstance(resp, dict) and resp.get("results"):
                search_results = resp.get("results", [])

            # Extract personas from the first result (index 0 as per requirement)
            personas = []
            if search_results:
                # Use 0th index (first result) as primary
                primary_result = search_results[0]
                primary_persona = PersonaExtractor.extract_persona(primary_result)
                personas.append(primary_persona)

                # Optionally parse additional results
                if len(search_results) > 1:
                    additional_personas = PersonaExtractor.extract_personas_from_results(search_results[1:])
                    personas.extend(additional_personas)

            out.append({"query": q, "personas": personas})

        return {"ok": True, "results": out}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
