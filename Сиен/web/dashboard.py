# Файл: web/dashboard.py
"""
Веб-дашборд проекта "Сиен"
FastAPI + Jinja2 для веб-интерфейса
Порт: 8000
"""

from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn
import logging
from datetime import datetime
import os
import sys
import sqlite3
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("dashboard")

app = FastAPI(title="Сиен Дашборд", version="1.0.0")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")
DATA_DIR = os.path.join(os.path.dirname(BASE_DIR), "data")
DB_PATH = os.path.join(DATA_DIR, "sien.db")

templates = Jinja2Templates(directory=TEMPLATES_DIR)


def get_db():
    """Получить соединение с БД"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Инициализация БД профиля пользователя"""
    os.makedirs(DATA_DIR, exist_ok=True)
    
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_profile (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT DEFAULT 'User',
            email TEXT DEFAULT '',
            avatar TEXT DEFAULT '',
            timezone TEXT DEFAULT 'UTC',
            created_at TEXT NOT NULL
        )
    """)
    
    # Создаем профиль по умолчанию если нет
    cursor.execute("SELECT COUNT(*) FROM user_profile")
    if cursor.fetchone()[0] == 0:
        cursor.execute(
            "INSERT INTO user_profile (name, email, created_at) VALUES (?, ?, ?)",
            ("User", "", datetime.now().isoformat())
        )
    
    conn.commit()
    conn.close()


@app.on_event("startup")
async def startup():
    init_db()
    logger.info("Dashboard started")


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Перенаправление на дашборд"""
    from starlette.responses import RedirectResponse
    return RedirectResponse(url="/dashboard/profile")


@app.get("/dashboard/profile", response_class=HTMLResponse)
async def profile_page(request: Request):
    """Страница профиля"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM user_profile LIMIT 1")
    profile = cursor.fetchone()
    conn.close()
    
    return templates.TemplateResponse("profile.html", {
        "request": request,
        "profile": dict(profile) if profile else {}
    })


@app.post("/dashboard/profile/update")
async def update_profile(
    name: str = Form(...),
    email: str = Form(...),
    timezone: str = Form(...)
):
    """Обновление профиля"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        UPDATE user_profile SET name = ?, email = ?, timezone = ?
        WHERE id = (SELECT MIN(id) FROM user_profile)
    """, (name, email, timezone))
    
    conn.commit()
    conn.close()
    
    return {"status": "success", "message": "Profile updated"}


@app.get("/dashboard/agents", response_class=HTMLResponse)
async def agents_page(request: Request):
    """Страница агентов"""
    # Получаем статусы агентов от оркестратора
    agents = []
    try:
        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.get("http://localhost:8000/agents") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    agents = data.get("agents", [])
    except Exception as e:
        logger.error(f"Error fetching agents: {e}")
    
    return templates.TemplateResponse("agents.html", {
        "request": request,
        "agents": agents
    })


@app.get("/dashboard/autostart", response_class=HTMLResponse)
async def autostart_page(request: Request):
    """Страница автозагрузки"""
    enabled = False
    try:
        sys.path.insert(0, os.path.dirname(BASE_DIR))
        from core.autostart import is_autostart_enabled
        enabled = is_autostart_enabled()
    except Exception as e:
        logger.error(f"Error checking autostart: {e}")
    
    return templates.TemplateResponse("autostart.html", {
        "request": request,
        "enabled": enabled
    })


@app.post("/dashboard/autostart/toggle")
async def toggle_autostart(enable: bool = Form(...)):
    """Переключение автозагрузки"""
    try:
        sys.path.insert(0, os.path.dirname(BASE_DIR))
        from core.autostart import enable_autostart, disable_autostart
        
        if enable:
            success = enable_autostart()
        else:
            success = disable_autostart()
        
        return {"status": "success" if success else "error"}
    except Exception as e:
        logger.error(f"Error toggling autostart: {e}")
        return {"status": "error", "message": str(e)}


@app.get("/dashboard/system", response_class=HTMLResponse)
async def system_page(request: Request):
    """Страница системы"""
    return templates.TemplateResponse("system.html", {"request": request})


@app.get("/api/system/metrics")
async def get_system_metrics():
    """API для получения метрик системы"""
    import psutil
    
    cpu_percent = psutil.cpu_percent(interval=0.1)
    memory = psutil.virtual_memory()
    
    metrics = {
        "cpu_percent": cpu_percent,
        "memory_percent": memory.percent,
        "memory_used_gb": round(memory.used / (1024**3), 2),
        "memory_total_gb": round(memory.total / (1024**3), 2),
        "timestamp": datetime.now().isoformat()
    }
    
    return JSONResponse(content=metrics)


def main():
    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
