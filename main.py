from dotenv import load_dotenv
from fastapi import FastAPI
from src.routes import llm

# Load environment variables from .env
load_dotenv()

app = FastAPI(title="Perplexity Integration API", version="0.1")

# Register LLM router only
app.include_router(llm.router, prefix="/api/llm", tags=["llm"])


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/")
async def index():
    return {"message": "Perplexity integration is ready", "docs": "/docs"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
