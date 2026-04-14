# Файл: agents/argus.py
"""
Агент Argus - Поиск в интернете через DuckDuckGo
Порт: 8003
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
import logging
from datetime import datetime
from typing import List, Optional

try:
    from duckduckgo_search import DDGS
except ImportError:
    DDGS = None

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("argus")

app = FastAPI(title="Argus Agent", version="1.0.0")


class SearchRequest(BaseModel):
    query: str
    max_results: int = 10


class SearchResult(BaseModel):
    title: str
    link: str
    snippet: Optional[str] = None


class SearchResponse(BaseModel):
    query: str
    results: List[SearchResult]
    timestamp: str


@app.get("/health")
async def health_check():
    return {"status": "healthy", "agent": "argus", "timestamp": datetime.now().isoformat()}


@app.get("/ping")
async def ping():
    return {"pong": True}


@app.post("/execute", response_model=SearchResponse)
async def execute(request: SearchRequest):
    """Выполнить поиск в интернете"""
    logger.info(f"Search query: {request.query}")
    
    if DDGS is None:
        raise HTTPException(status_code=503, detail="DuckDuckGo library not available")
    
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(request.query, max_results=request.max_results))
        
        search_results = [
            SearchResult(
                title=r.get("title", "No title"),
                link=r.get("href", ""),
                snippet=r.get("body", "")
            )
            for r in results
        ]
        
        return SearchResponse(
            query=request.query,
            results=search_results,
            timestamp=datetime.now().isoformat()
        )
    except Exception as e:
        logger.error(f"Search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def main():
    uvicorn.run(app, host="0.0.0.0", port=8003)


if __name__ == "__main__":
    main()
