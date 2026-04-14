# Файл: agents/huei.py
"""
Агент Huei - Генерация фото (Stable Diffusion заглушка)
Порт: 8020
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
import logging
from datetime import datetime
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("huei")

app = FastAPI(title="Huei Agent", version="1.0.0")

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "generated")


class ImageRequest(BaseModel):
    prompt: str
    width: int = 512
    height: int = 512
    steps: int = 20


class ImageResponse(BaseModel):
    status: str
    message: str
    prompt: str
    image_path: str


@app.get("/health")
async def health_check():
    return {"status": "healthy", "agent": "huei", "timestamp": datetime.now().isoformat()}


@app.get("/ping")
async def ping():
    return {"pong": True}


@app.post("/execute", response_model=ImageResponse)
async def execute(request: ImageRequest):
    """Сгенерировать изображение"""
    logger.info(f"Generating image: {request.prompt}")
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Заглушка (в реальности нужна интеграция со Stable Diffusion)
    filename = f"image_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    filepath = os.path.join(OUTPUT_DIR, filename)
    
    with open(filepath, "w") as f:
        f.write(f"Prompt: {request.prompt}\n")
        f.write(f"Size: {request.width}x{request.height}\n")
        f.write(f"Steps: {request.steps}\n")
        f.write("\n[This is a placeholder. Real implementation requires Stable Diffusion API]\n")
    
    return ImageResponse(
        status="success",
        message="Image generation placeholder created",
        prompt=request.prompt,
        image_path=filepath
    )


def main():
    uvicorn.run(app, host="0.0.0.0", port=8020)


if __name__ == "__main__":
    main()
