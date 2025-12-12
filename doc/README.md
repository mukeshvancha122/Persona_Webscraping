# PeopleFinder Backend (FastAPI)

FastAPI backend for the PeopleFinder application.

## Setup

1. Create a Python virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Copy environment variables:
```bash
cp .env.example .env
```

4. Fill in your API keys in the `.env` file:
- `ZENSERP_API_KEY` - ZenSERP API key for web search
- `BRAVE_SEARCH_API_KEY` - Brave Search API key (alternative)
- `OPENROUTER_API_KEY` - OpenRouter API key for AI models
- `MOONSHOTAI_API_KEY` - Moonshot AI API key
- `GOOGLE_API_KEY` - Google Gemini API key
- `ANTHROPIC_API_KEY` - Anthropic Claude API key
- `OPENAI_API_KEY` - OpenAI API key

## Development

Start the development server:
```bash
python -m uvicorn src.main:app --reload --port 3001
```

The server will run on `http://localhost:3001` by default.

## Production

Build and start the production server:
```bash
python -m uvicorn src.main:app --host 0.0.0.0 --port 3001
```

## Project Structure

```
src/
├── main.py              # FastAPI app initialization
├── routes/
│   └── chat.py          # Chat/orchestration endpoint
├── services/
│   ├── orchestrator.py  # AI orchestrator service
│   ├── search.py        # Web search service
│   ├── prompt.py        # Prompt building utilities
│   ├── openrouter.py    # OpenRouter API client
│   └── providers/
│       └── moonshot.py  # Moonshot AI provider
└── types/
    └── orchestrator_plan.py  # Type definitions
```
