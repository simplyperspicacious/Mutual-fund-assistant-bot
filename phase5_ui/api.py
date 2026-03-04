import os
import sys
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# Add Phase 4 to path so we can import the engine
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

try:
    from phase4_rag.rag_engine import RAGEngine
except ImportError as e:
    print(f"Error loading RAG Engine. Did you set up Phase 4? {e}")
    sys.exit(1)


app = FastAPI(title="Mutual Fund RAG Assistant")

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize RAG Engine globally so it only loads into memory once
print("Initializing RAG Engine on server start...")
try:
    rag = RAGEngine()
    print("RAG Engine successfully initialized.")
except Exception as e:
    print(f"CRITICAL: Failed to initialize RAG Engine: {e}")
    import traceback
    traceback.print_exc()
    rag = None

class ChatRequest(BaseModel):
    query: str

class ChatResponse(BaseModel):
    answer: str
    sources: list[str]
    last_updated: str | None = None

@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(req: ChatRequest):
    if not rag:
        raise HTTPException(status_code=500, detail="RAG Engine failed to initialize. Check API keys and FAISS index.")
    
    if not req.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty.")
    
    try:
        # Run the full e2e Phase 4 pipeline
        result = rag.generate_answer(req.query)
        return ChatResponse(
            answer=result["answer"],
            sources=result["sources"],
            last_updated=result.get("last_updated")
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Generation Error: {str(e)}")

# Mount static frontend files at the root '/'
static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
if not os.path.exists(static_dir):
    os.makedirs(static_dir)

app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    # Get port from environment variable for deployment (Render/Heroku)
    port = int(os.environ.get("PORT", 8000))
    # In production, bind to 0.0.0.0
    print(f"Starting server on port {port}. To view frontend, visit: http://0.0.0.0:{port}")
    uvicorn.run("api:app", host="0.0.0.0", port=port, reload=False)
