# Express.js ↔ FastAPI Equivalence Guide

## Overview
This document shows how Express.js patterns in the original backend map to FastAPI patterns in the new backend.

---

## 1. Application Setup

### Express.js (`backend/src/app.ts`)
```typescript
import express from 'express';
import cors from 'cors';
import chatRoute from './routes/chat';

export function createApp() {
  const app = express();
  
  app.use(cors({
    origin: process.env.FRONTEND_URL || 'http://localhost:3000',
    credentials: true,
  }));
  app.use(express.json());
  app.use('/api/chat', chatRoute);
  
  app.get('/health', (req, res) => {
    res.json({ status: 'OK', timestamp: new Date().toISOString() });
  });
  
  return app;
}
```

### FastAPI (`backend-fastapi/src/main.py`)
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router, prefix="/api/chat", tags=["chat"])

@app.get("/health")
async def health_check():
    return {
        "status": "OK",
        "timestamp": datetime.utcnow().isoformat()
    }
```

**Key Differences:**
- Express: Middleware applied with `app.use()`
- FastAPI: Middleware added with `add_middleware()`
- Express: Routes mounted with `app.use()`
- FastAPI: Routes included with `include_router()`

---

## 2. Request Handling & Streaming

### Express.js (`backend/src/routes/chat.ts`)
```typescript
router.post('/', async (req: Request, res: Response) => {
  const { query } = req.body;
  
  res.setHeader('Content-Type', 'text/event-stream');
  res.setHeader('Cache-Control', 'no-cache, no-transform');
  res.setHeader('Connection', 'keep-alive');
  
  res.write(`data: ${JSON.stringify({ type: 'plan' })}\n\n`);
});
```

### FastAPI (`backend-fastapi/src/routes/chat.py`)
```python
from fastapi.responses import StreamingResponse

@router.post("/")
async def chat(request_data: ChatRequest):
    return StreamingResponse(
        stream_generator(query),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "Connection": "keep-alive",
        }
    )

async def stream_generator(query: str):
    yield f"data: {json.dumps({'type': 'plan'})}\n\n"
```

**Key Differences:**
- Express: Manual header setting, direct response writing
- FastAPI: Use `StreamingResponse` with generator function
- Express: Request body from `req.body`
- FastAPI: Request validation with Pydantic models

---

## 3. Type Definitions

### Express.js (`backend/src/types/OrchestratorPlan.ts`)
```typescript
export interface OrchestratorPlan {
    response: string;
    agents: OrchestratorAgent[];
}

export interface OrchestratorAgent {
    task: string;
    prompt: string;
}
```

### FastAPI (`backend-fastapi/src/types/orchestrator_plan.py`)
```python
from pydantic import BaseModel
from typing import List

class OrchestratorAgent(BaseModel):
    task: str
    prompt: str

class OrchestratorPlan(BaseModel):
    response: str
    agents: List[OrchestratorAgent]
```

**Key Differences:**
- Express: TypeScript interfaces (compile-time only)
- FastAPI: Pydantic models (runtime validation + docs)

---

## 4. Services / Search

### Express.js (`backend/src/services/search.ts`)
```typescript
type SearchProvider = "serpapi" | "brave";

async function search(query: string, providerOverride?: SearchProvider) {
    const provider = providerOverride || DEFAULT_PROVIDER;
    switch (provider) {
        case "brave":
            return searchBrave(query);
        case "serpapi":
        default:
            return searchSerpApi(query);
    }
}

async function searchBrave(query: string): Promise<SearchResult[]> {
    const apiKey = process.env["BRAVE_SEARCH_API_KEY"];
    const response = await fetch("...", {
        headers: { "X-Subscription-Token": apiKey }
    });
    return response.json();
}
```

### FastAPI (`backend-fastapi/src/services/search.py`)
```python
class SearchService:
    @staticmethod
    async def search(query: str, provider_override: Optional[str] = None) -> List[SearchResult]:
        provider = provider_override or os.getenv("SEARCH_PROVIDER", "brave")
        
        if provider == "brave":
            return await SearchService.search_brave(query)
        elif provider == "serpapi":
            return await SearchService.search_serpapi(query)
        else:
            return []

    @staticmethod
    async def search_brave(query: str) -> List[SearchResult]:
        api_key = os.getenv("BRAVE_SEARCH_API_KEY")
        async with httpx.AsyncClient() as client:
            response = await client.get("...", headers={"X-Subscription-Token": api_key})
            data = response.json()
```

**Key Differences:**
- Express: Free functions
- FastAPI: Static class methods for organization
- Express: `fetch()` for HTTP
- FastAPI: `httpx.AsyncClient()` for async HTTP

---

## 5. Orchestrator Service

### Express.js (`backend/src/services/orchestrator.ts`)
```typescript
export default async function spinUpOrchestrator(query: string): Promise<OrchestratorPlan> {
    const { object } = await generateObject({
        model: google('gemini-2.5-flash'),
        schema: z.object({
            response: z.string(),
            agents: z.array(z.object({
                task: z.string(),
                prompt: z.string()
            }))
        }),
        system: buildOrchestratorPrompt(),
        prompt: query
    });

    return object as OrchestratorPlan;
}
```

### FastAPI (`backend-fastapi/src/services/orchestrator.py`)
```python
async def spin_up_orchestrator(query: str) -> OrchestratorPlan:
    api_key = os.getenv("GOOGLE_API_KEY")
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent",
            params={"key": api_key},
            json={
                "contents": [{
                    "role": "user",
                    "parts": [{"text": f"{buildOrchestratorPrompt()}\n\n{query}"}]
                }],
                "generationConfig": {"temperature": 0.7, "maxOutputTokens": 2000}
            }
        )
        data = response.json()
        
    # Parse response and return OrchestratorPlan
    json_str = extract_json_from_response(data["candidates"][0]["content"]["parts"][0]["text"])
    plan_data = json.loads(json_str)
    return OrchestratorPlan(**plan_data)
```

**Key Differences:**
- Express: Uses `ai` SDK with high-level API
- FastAPI: Direct REST API calls (more control, more code)
- Express: Schema validation via Zod
- FastAPI: Uses Pydantic models for validation

---

## 6. Provider Integration

### Express.js (`backend/src/services/providers/moonshot.ts`)
```typescript
import { createOpenAICompatible } from "@ai-sdk/openai-compatible"

export const openrouter = createOpenAICompatible({
    baseURL: "https://openrouter.ai/api/v1",
    apiKey: process.env["OPENROUTER_API_KEY"],
    name: ""
})
```

### FastAPI (`backend-fastapi/src/services/providers/moonshot.py`)
```python
class MoonshotAIProvider:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("MOONSHOTAI_API_KEY")
    
    async def chat_completion(self, messages: list, model: str = "moonshot-v1-8k"):
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.moonshot.cn/v1/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={"model": model, "messages": messages}
            )
        return response.json()

moonshot_provider = MoonshotAIProvider()
```

**Key Differences:**
- Express: Uses SDK abstractions
- FastAPI: Manual HTTP handling for more flexibility

---

## 7. Configuration Management

### Express.js
```typescript
import 'dotenv/config';  // Load .env automatically

// Use with optional defaults
const url = process.env.FRONTEND_URL || 'http://localhost:3000';
```

### FastAPI
```python
from dotenv import load_dotenv

load_dotenv()  # Load .env file

# Use with optional defaults
frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
```

**Key Differences:**
- Express: Automatic import-time loading
- FastAPI: Manual loading in main.py

---

## 8. Running the Servers

### Express.js
```bash
npm install
npm run dev  # Runs with tsx watch for hot reload
# Server runs on localhost:3001
```

### FastAPI
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python -m uvicorn src.main:app --reload --port 3001
# Server runs on localhost:3001
```

---

## 9. API Differences Summary

| Feature | Express.js | FastAPI |
|---------|-----------|---------|
| **Framework** | Express | FastAPI |
| **Request Body** | `req.body` | Pydantic models |
| **Response Streaming** | `res.write()` | `StreamingResponse` |
| **Type Checking** | TypeScript (compile-time) | Pydantic (runtime) |
| **HTTP Client** | `fetch()` / `axios` | `httpx` |
| **Middleware** | `app.use()` | `add_middleware()` |
| **Routes** | `router.method()` | `@router.method()` |
| **Documentation** | Manual/Swagger | Auto-generated |
| **Async/Await** | Native | Native (better integration) |
| **Validation** | Zod/Manual | Pydantic (automatic) |

---

## 10. Common Patterns

### Error Handling

**Express.js:**
```typescript
try {
    // ...
} catch (err) {
    console.error(err);
    res.status(500).json({ error: 'Server error' });
}
```

**FastAPI:**
```python
try:
    # ...
except Exception as e:
    print(f"Error: {e}")
    yield json.dumps({"type": "error", "error": str(e)})
```

### Environment Variables

**Express.js:**
```typescript
process.env["API_KEY"]  // string | undefined
```

**FastAPI:**
```python
os.getenv("API_KEY")  # str | None
os.getenv("API_KEY", "default")  # str with default
```

---

## Migration Checklist

- [x] Create FastAPI app with CORS middleware
- [x] Create Pydantic models for types
- [x] Create chat route with SSE streaming
- [x] Implement orchestrator service
- [x] Implement search service
- [x] Implement providers (Moonshot, OpenRouter)
- [x] Create prompt utilities
- [x] Add .env configuration
- [x] Add documentation
