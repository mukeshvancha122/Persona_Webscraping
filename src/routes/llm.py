from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional

from src.services.perplexity_sdk import PerplexitySDK

router = APIRouter()


class GenerateRequest(BaseModel):
    prompt: str
    max_tokens: Optional[int] = 512


class SearchRequest(BaseModel):
    queries: List[str]


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
