import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from src.routes import chat, search

# Load environment variables
load_dotenv()

# Create FastAPI app
app = FastAPI(
    title="PeopleFinder Backend",
    description="AI-powered people finder backend with multi-agent orchestration",
    version="1.0.0"
)

# Setup CORS
frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[frontend_url, "http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(chat.router, prefix="/api/chat", tags=["chat"])
app.include_router(search.router, prefix="/api/search", tags=["search"])

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    from datetime import datetime
    return {
        "status": "OK",
        "timestamp": datetime.utcnow().isoformat()
    }

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "PeopleFinder Backend is running",
        "docs": "/docs",
        "openapi": "/openapi.json"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=3001,
        reload=True
    )
