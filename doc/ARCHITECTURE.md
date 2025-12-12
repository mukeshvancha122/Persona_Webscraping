# FastAPI Backend - Architecture Overview

This FastAPI backend replicates the functionality of the Express.js backend with the same multi-agent orchestration system.

## Project Structure

```
backend-fastapi/
├── src/
│   ├── main.py                      # FastAPI app initialization and middleware setup
│   ├── routes/
│   │   └── chat.py                  # Chat endpoint with SSE streaming
│   ├── services/
│   │   ├── orchestrator.py          # AI orchestrator using Google Gemini or Claude
│   │   ├── search.py                # Web search service (ZenSERP & Brave Search)
│   │   ├── prompt.py                # Prompt building utilities
│   │   ├── openrouter.py            # OpenRouter API client (OpenAI-compatible)
│   │   └── providers/
│   │       └── moonshot.py          # Moonshot AI provider
│   └── types/
│       └── orchestrator_plan.py     # Pydantic models for type safety
├── requirements.txt                 # Python dependencies
├── pyproject.toml                   # Project metadata
├── .env.example                     # Environment variables template
└── README.md                        # Setup and usage instructions
```

## Key Files

### `src/main.py`
- FastAPI application setup
- CORS middleware configuration
- Route registration
- Health check endpoint (`GET /health`)

### `src/routes/chat.py`
- `POST /api/chat` - Main chat endpoint
- Implements Server-Sent Events (SSE) streaming
- Processes orchestrator plan
- Manages agent execution and knowledge accumulation

### `src/services/orchestrator.py`
- `spin_up_orchestrator()` - Uses Google Gemini 2.5 Flash to break down queries
- `spin_up_orchestrator_anthropic()` - Alternative using Anthropic Claude
- Returns structured plan with multiple agent tasks

### `src/services/search.py`
- `SearchService.search()` - Multi-provider search (Brave, ZenSERP)
- `SearchService.search_brave()` - Brave Search integration
- `SearchService.search_serpapi()` - ZenSERP integration
- `SearchService.get_web_page()` - Web page fetching and parsing

### `src/services/openrouter.py`
- `OpenRouterClient` - OpenAI-compatible API client
- Supports chat completions and streaming
- Works with various models (GPT-4, Claude, etc.)

### `src/services/providers/moonshot.py`
- `MoonshotAIProvider` - Chinese AI provider support
- Similar interface to OpenRouter
- Supports multiple context window sizes

### `src/types/orchestrator_plan.py`
- `OrchestratorPlan` - Main orchestrator response model
- `OrchestratorAgent` - Individual agent task definition
- `ChatRequest` - Request body model
- `SearchResult` - Search result model
- Pydantic models for runtime validation

## API Endpoints

### `GET /health`
Health check endpoint
```bash
curl http://localhost:3001/health
```

### `POST /api/chat`
Chat endpoint with streaming response
```bash
curl -X POST http://localhost:3001/api/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "Find information about John Doe"}' \
  -N
```

## Streaming Response Format

The endpoint streams Server-Sent Events (SSE) with the following message types:

```json
// Plan message
{"type": "plan", "plan": {...}}

// Agent start
{"type": "agentStart", "agent": "...", "task": "...", "prompt": "..."}

// Response chunks
{"type": "response", "data": {...}}

// Agent end
{"type": "agentEnd", "agent": "..."}

// Errors
{"type": "error", "error": "error message"}
```

## Equivalence to Express Backend

| Express.js | FastAPI |
|-----------|---------|
| `app.ts` | `src/main.py` |
| `routes/chat.ts` | `src/routes/chat.py` |
| `services/orchestrator.ts` | `src/services/orchestrator.py` |
| `services/search.ts` | `src/services/search.py` |
| `services/prompt.ts` | `src/services/prompt.py` |
| `services/openrouter.ts` | `src/services/openrouter.py` |
| `services/providers/moonshot.ts` | `src/services/providers/moonshot.py` |
| `types/OrchestratorPlan.ts` | `src/types/orchestrator_plan.py` |

## Installation & Running

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy and configure environment
cp .env.example .env

# Run development server
python -m uvicorn src.main:app --reload --port 3001
```

## Dependencies

- **fastapi** - Web framework
- **uvicorn** - ASGI server
- **pydantic** - Data validation
- **httpx** - Async HTTP client
- **python-dotenv** - Environment variable loading
- **google-generativeai** - Google Gemini API (optional)
- **anthropic** - Anthropic Claude API (optional)
- **openai** - OpenAI API (optional)

## Features

✅ Multi-agent orchestration with AI planning
✅ Streaming responses with Server-Sent Events
✅ Multiple search provider support
✅ Web page fetching and parsing
✅ Knowledge base accumulation across agents
✅ Type-safe with Pydantic models
✅ Async/await throughout
✅ CORS-enabled for frontend integration
✅ Multiple AI provider support
✅ Environment-based configuration
