# Файл: agents/mnemon.py
"""
Агент Mnemon - Перевод текста
Порт: 8012
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mnemon")

app = FastAPI(title="Mnemon Agent", version="1.0.0")


class TranslateRequest(BaseModel):
    text: str
    target_lang: str = "en"
    source_lang: Optional[str] = None


class TranslateResponse(BaseModel):
    original_text: str
    translated_text: str
    source_lang: str
    target_lang: str


# Простой словарь для демонстрации (в реальности нужен API переводчика)
TRANSLATION_DICT = {
    "привет": {"en": "hello", "de": "hallo", "fr": "bonjour", "es": "hola"},
    "как дела": {"en": "how are you", "de": "wie geht es dir", "fr": "comment ça va", "es": "cómo estás"},
    "спасибо": {"en": "thank you", "de": "danke", "fr": "merci", "es": "gracias"},
    "до свидания": {"en": "goodbye", "de": "auf wiedersehen", "fr": "au revoir", "es": "adiós"},
}


@app.get("/health")
async def health_check():
    return {"status": "healthy", "agent": "mnemon", "timestamp": datetime.now().isoformat()}


@app.get("/ping")
async def ping():
    return {"pong": True}


@app.post("/execute", response_model=TranslateResponse)
async def execute(request: TranslateRequest):
    """Перевести текст"""
    logger.info(f"Translating to {request.target_lang}")
    
    text_lower = request.text.lower()
    translated = request.text  # По умолчанию возвращаем оригинал
    
    # Поиск в словаре
    for phrase, translations in TRANSLATION_DICT.items():
        if phrase in text_lower:
            if request.target_lang in translations:
                translated = text_lower.replace(phrase, translations[request.target_lang])
                break
    
    # Если не найдено в словаре - заглушка
    if translated == request.text:
        translated = f"[Translation to {request.target_lang}]: {request.text}"
    
    return TranslateResponse(
        original_text=request.text,
        translated_text=translated,
        source_lang=request.source_lang or "auto",
        target_lang=request.target_lang
    )


def main():
    uvicorn.run(app, host="0.0.0.0", port=8012)


if __name__ == "__main__":
    main()
