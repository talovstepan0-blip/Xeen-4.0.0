# Файл: agents/logos.py
"""
Агент Logos - Форматирование ответов
Порт: 8007
"""

from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn
import logging
from datetime import datetime
from typing import Optional, Dict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("logos")

app = FastAPI(title="Logos Agent", version="1.0.0")


class FormatRequest(BaseModel):
    text: str
    style: Optional[str] = "plain"
    max_length: Optional[int] = None


class FormatResponse(BaseModel):
    formatted_text: str
    style: str
    original_length: int
    formatted_length: int


@app.get("/health")
async def health_check():
    return {"status": "healthy", "agent": "logos", "timestamp": datetime.now().isoformat()}


@app.get("/ping")
async def ping():
    return {"pong": True}


@app.post("/execute", response_model=FormatResponse)
async def execute(request: FormatRequest):
    """Форматировать текст"""
    logger.info(f"Formatting text with style: {request.style}")
    
    text = request.text
    original_length = len(text)
    
    # Ограничение длины
    if request.max_length and len(text) > request.max_length:
        text = text[:request.max_length - 3] + "..."
    
    # Применение стилей
    if request.style == "markdown":
        formatted = f"> {text.replace('\n', '\n> ')}"
    elif request.style == "code":
        formatted = f"```\n{text}\n```"
    elif request.style == "quote":
        formatted = f'"*{text}*"'
    elif request.style == "uppercase":
        formatted = text.upper()
    elif request.style == "lowercase":
        formatted = text.lower()
    elif request.style == "title":
        formatted = text.title()
    else:
        formatted = text
    
    return FormatResponse(
        formatted_text=formatted,
        style=request.style or "plain",
        original_length=original_length,
        formatted_length=len(formatted)
    )


def main():
    uvicorn.run(app, host="0.0.0.0", port=8007)


if __name__ == "__main__":
    main()
