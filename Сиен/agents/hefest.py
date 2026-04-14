# Файл: agents/hefest.py
"""
Агент Hefest - Генерация кода
Порт: 8018
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
import logging
from datetime import datetime
from typing import Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("hefest")

app = FastAPI(title="Hefest Agent", version="1.0.0")


class CodeRequest(BaseModel):
    prompt: str
    language: Optional[str] = "python"


class CodeResponse(BaseModel):
    code: str
    language: str
    explanation: str


@app.get("/health")
async def health_check():
    return {"status": "healthy", "agent": "hefest", "timestamp": datetime.now().isoformat()}


@app.get("/ping")
async def ping():
    return {"pong": True}


@app.post("/execute", response_model=CodeResponse)
async def execute(request: CodeRequest):
    """Сгенерировать код"""
    logger.info(f"Generating {request.language} code for: {request.prompt}")
    
    # Заглушка для генерации кода (в реальности нужен LLM API)
    code_templates = {
        "python": f"# Generated code for: {request.prompt}\n\ndef main():\n    print('Hello from generated code!')\n\nif __name__ == '__main__':\n    main()",
        "javascript": f"// Generated code for: {request.prompt}\n\nfunction main() {{\n    console.log('Hello from generated code!');\n}}\n\nmain();",
        "html": f"<!-- Generated code for: {request.prompt} -->\n\n<!DOCTYPE html>\n<html>\n<head><title>Generated Page</title></head>\n<body>\n    <h1>Hello from generated code!</h1>\n</body>\n</html>",
    }
    
    code = code_templates.get(request.language.lower(), f"# {request.language} code\nprint('Hello')")
    
    return CodeResponse(
        code=code,
        language=request.language,
        explanation=f"Generated {request.language} code based on prompt: {request.prompt}"
    )


def main():
    uvicorn.run(app, host="0.0.0.0", port=8018)


if __name__ == "__main__":
    main()
