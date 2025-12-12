# FastAPI Backend - Quick Start Guide

## 1. Prerequisites

- Python 3.10 or higher
- pip or poetry
- API keys for:
  - Google Gemini (for orchestrator)
  - Brave Search or ZenSERP (for web search)
  - Optional: Moonshot AI, OpenRouter, Anthropic

## 2. Initial Setup (5 minutes)

### Clone/Navigate to backend
```bash
cd /Users/mukeshreddy/Developer/AIOWL/peoplefinder-ai/backend-fastapi
```

### Create Virtual Environment
```bash
# Create virtual environment
/Users/mukeshreddy/Developer/AIOWL/peoplefinder-ai/backend-fastapi

# Activate it
source venv/bin/activate

# On Windows:
# venv\Scripts\activate
```

### Install Dependencies
```bash
# Install from requirements.txt
pip install -r requirements.txt

# Or use pyproject.toml
pip install -e .
```

### Configure Environment
```bash
# Copy example environment file
cp .env.example .env

# Edit .env and add your API keys
# Required:
# - GOOGLE_API_KEY (for Gemini)
# - BRAVE_SEARCH_API_KEY or ZENSERP_API_KEY (for search)

# Open with your editor
nano .env  # or use VS Code
```

## 3. Run the Server

### Development Mode (with auto-reload)
```bash
python -m uvicorn src.main:app --reload --port 3001

# You should see:
# INFO:     Uvicorn running on http://127.0.0.1:3001
# INFO:     Application startup complete
```

### Production Mode
```bash
python -m uvicorn src.main:app --host 0.0.0.0 --port 3001
```

## 4. Test the API

### Health Check
```bash
curl http://localhost:3001/health
```

### Chat Endpoint (Streaming)
```bash
curl -N -X POST http://localhost:3001/api/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "Find information about Alan Turing"}'
```

### Using the Test Script
```bash
chmod +x test.sh
./test.sh
```

## 5. Interactive Documentation

Once the server is running, visit:
- **Swagger UI**: http://localhost:3001/docs
- **ReDoc**: http://localhost:3001/redoc
- **OpenAPI JSON**: http://localhost:3001/openapi.json

## 6. Project Structure

```
backend-fastapi/
├── src/
│   ├── main.py              # App initialization
│   ├── routes/
│   │   └── chat.py          # Chat endpoint
│   ├── services/
│   │   ├── orchestrator.py  # AI planning
│   │   ├── search.py        # Web search
│   │   ├── prompt.py        # Prompt templates
│   │   ├── openrouter.py    # OpenRouter client
│   │   └── providers/
│   │       └── moonshot.py  # Moonshot AI
│   └── types/
│       └── orchestrator_plan.py  # Data models
├── requirements.txt
├── .env.example
└── README.md
```

## 7. Environment Variables Explained

```bash
# Frontend URL (for CORS)
FRONTEND_URL=http://localhost:3000

# Search provider (brave or serpapi)
SEARCH_PROVIDER=brave

# Search API Keys
BRAVE_SEARCH_API_KEY=your_key_here
ZENSERP_API_KEY=your_key_here

# AI Model API Keys
GOOGLE_API_KEY=your_key_here
ANTHROPIC_API_KEY=your_key_here
OPENAI_API_KEY=your_key_here
OPENROUTER_API_KEY=your_key_here
MOONSHOTAI_API_KEY=your_key_here
```

## 8. Common Issues

### "ModuleNotFoundError: No module named 'fastapi'"
→ Make sure virtual environment is activated
```bash
source venv/bin/activate
pip install -r requirements.txt
```

### "API key not set" errors
→ Check that all required API keys are in `.env` file
```bash
cat .env | grep API_KEY
```

### Port 3001 already in use
→ Use a different port
```bash
python -m uvicorn src.main:app --port 3002
```

### Streaming not working in client
→ Make sure client supports Server-Sent Events
→ Check CORS settings in `src/main.py`

## 9. Development Tips

### Auto-reload with watch
```bash
# Already enabled with --reload flag
python -m uvicorn src.main:app --reload --port 3001
```

### Debug mode
```python
# Add to src/main.py
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Access logs
```bash
# Enable with --access-log flag
python -m uvicorn src.main:app --reload --access-log
```

### Hot reload specific modules
```bash
# The --reload flag watches all .py files
# To watch specific directories:
python -m uvicorn src.main:app --reload --reload-dir src
```

## 10. Frontend Integration

### Update frontend API endpoint
In your Next.js frontend (`src/app/chat.tsx`):
```typescript
const response = await fetch('http://localhost:3001/api/chat', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ query: userInput })
});
```

### Handle streaming response
```typescript
const reader = response.body.getReader();
const decoder = new TextDecoder();

while (true) {
  const { done, value } = await reader.read();
  if (done) break;
  
  const chunk = decoder.decode(value);
  // Parse SSE format: "data: {...}\n\n"
  const lines = chunk.split('\n');
  for (const line of lines) {
    if (line.startsWith('data: ')) {
      const data = JSON.parse(line.slice(6));
      // Handle data based on type
    }
  }
}
```

## 11. Next Steps

1. ✅ Server running on localhost:3001
2. ✅ API keys configured in .env
3. ✅ Tested endpoints work
4. ⬜ Connect frontend to API
5. ⬜ Deploy to production (AWS Lambda, Heroku, etc.)

## 12. Deployment

### Docker
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY src ./src
COPY .env .

CMD ["python", "-m", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "3001"]
```

### Heroku
```bash
git push heroku main
heroku config:set GOOGLE_API_KEY=your_key
```

### AWS Lambda
See AWS Lambda deployment guide in backend docs.

## 13. Support & Resources

- **FastAPI Docs**: https://fastapi.tiangolo.com/
- **Uvicorn Docs**: https://www.uvicorn.org/
- **Pydantic Docs**: https://docs.pydantic.dev/
- **Project README**: See ARCHITECTURE.md

## 14. Troubleshooting

### Check Python version
```bash
python3 --version  # Should be 3.10+
```

### Verify installation
```bash
python -c "import fastapi; print(fastapi.__version__)"
```

### View logs in detail
```bash
python -m uvicorn src.main:app --reload --log-level debug
```

### Test individual services
```bash
python -c "from src.services.search import SearchService; print('✓ Search imported')"
```

---

**You're all set!** The FastAPI backend is ready to go. 🚀
