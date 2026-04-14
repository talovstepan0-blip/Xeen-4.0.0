# Файл: agents/fenix.py
"""
Агент Fenix - Распознавание намерений (NLU)
Порт: 8006
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
import logging
from datetime import datetime
from typing import Optional, Dict, List
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("fenix")

app = FastAPI(title="Fenix Agent", version="1.0.0")


class AnalyzeRequest(BaseModel):
    text: str


class IntentResult(BaseModel):
    intent: str
    confidence: float
    entities: Dict[str, str]
    action: Optional[str] = None


@app.get("/health")
async def health_check():
    return {"status": "healthy", "agent": "fenix", "timestamp": datetime.now().isoformat()}


@app.get("/ping")
async def ping():
    return {"pong": True}


@app.post("/execute", response_model=IntentResult)
async def execute(request: AnalyzeRequest):
    """Распознать намерение в тексте"""
    logger.info(f"Analyzing text: {request.text}")
    
    text = request.text.lower()
    entities = {}
    intent = "unknown"
    confidence = 0.5
    action = None
    
    # Паттерны для распознавания намерений
    patterns = {
        "search": {
            "keywords": ["найди", "поиск", "гугл", "google", "search", "find"],
            "action": "search"
        },
        "task_create": {
            "keywords": ["создай задачу", "напомни", "добавь задачу", "запланируй", "reminder", "task"],
            "action": "task_create"
        },
        "task_list": {
            "keywords": ["мои задачи", "список задач", "что нужно сделать", "tasks", "list"],
            "action": "task_list"
        },
        "translate": {
            "keywords": ["переведи", "translation", "translate", "на английский", "на русский"],
            "action": "translate"
        },
        "weather": {
            "keywords": ["погода", "weather", "температура", "дождь", "солнце"],
            "action": "weather"
        },
        "news": {
            "keywords": ["новости", "news", "что нового", "события"],
            "action": "news"
        },
        "code_generate": {
            "keywords": ["напиши код", "создай функцию", "generate code", "программа"],
            "action": "generate_code"
        },
        "image_generate": {
            "keywords": ["создай изображение", "нарисуй", "generate image", "картинка"],
            "action": "generate_image"
        },
        "greeting": {
            "keywords": ["привет", "здравствуй", "hello", "hi", "добрый день"],
            "action": "greet"
        },
        "help": {
            "keywords": ["помощь", "help", "что ты умеешь", "commands"],
            "action": "help"
        }
    }
    
    # Извлечение сущностей
    # Даты и время
    date_pattern = r'\b(\d{1,2}[./-]\d{1,2}[./-]\d{2,4})\b'
    date_match = re.search(date_pattern, text)
    if date_match:
        entities["date"] = date_match.group(1)
    
    time_pattern = r'\b(\d{1,2}:\d{2})\b'
    time_match = re.search(time_pattern, text)
    if time_match:
        entities["time"] = time_match.group(1)
    
    # Поиск упоминаний городов
    cities = ["москва", "спб", "петербург", "london", "new york", "paris"]
    for city in cities:
        if city in text:
            entities["location"] = city
            break
    
    # Определение намерения
    best_match = None
    best_score = 0
    
    for intent_name, config in patterns.items():
        score = sum(1 for kw in config["keywords"] if kw in text)
        if score > best_score:
            best_score = score
            best_match = (intent_name, config["action"])
    
    if best_match:
        intent = best_match[0]
        action = best_match[1]
        confidence = min(0.95, 0.5 + (best_score * 0.15))
    
    result = IntentResult(
        intent=intent,
        confidence=confidence,
        entities=entities,
        action=action
    )
    
    logger.info(f"Detected intent: {intent} (confidence: {confidence})")
    return result


def main():
    uvicorn.run(app, host="0.0.0.0", port=8006)


if __name__ == "__main__":
    main()
