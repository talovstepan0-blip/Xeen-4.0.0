# Файл: agents/wen.py
"""
Агент Wen - Задачи, напоминания, календарь, почта
Порт: 8008
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
import logging
from datetime import datetime
from typing import Optional, List, Dict
import aiosqlite
import os
import asyncio

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("wen")

app = FastAPI(title="Wen Agent", version="1.0.0")

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "sien.db")


class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = ""
    due_date: Optional[str] = None
    priority: int = 2  # 0-Highest, 1-High, 2-Medium, 3-Low
    reminder: Optional[bool] = False


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    due_date: Optional[str] = None
    priority: Optional[int] = None
    completed: Optional[bool] = None


class TaskResponse(BaseModel):
    id: int
    title: str
    description: str
    due_date: Optional[str]
    priority: int
    completed: bool
    created_at: str
    reminder: bool


async def init_db():
    """Инициализация базы данных"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT DEFAULT '',
                due_date TEXT,
                priority INTEGER DEFAULT 2,
                completed BOOLEAN DEFAULT 0,
                reminder BOOLEAN DEFAULT 0,
                created_at TEXT NOT NULL
            )
        """)
        await db.commit()


@app.on_event("startup")
async def startup():
    await init_db()
    logger.info("Wen agent started")


@app.get("/health")
async def health_check():
    return {"status": "healthy", "agent": "wen", "timestamp": datetime.now().isoformat()}


@app.get("/ping")
async def ping():
    return {"pong": True}


@app.post("/execute")
async def execute(request: dict):
    """Общий эндпоинт для выполнения действий"""
    action = request.get("action", "list")
    
    if action == "create":
        return await create_task(request)
    elif action == "list":
        return await list_tasks()
    elif action == "get":
        return await get_task(request.get("task_id"))
    elif action == "update":
        return await update_task(request.get("task_id"), request)
    elif action == "delete":
        return await delete_task(request.get("task_id"))
    elif action == "complete":
        return await complete_task(request.get("task_id"))
    else:
        raise HTTPException(status_code=400, detail=f"Unknown action: {action}")


async def create_task(data: dict) -> dict:
    """Создание задачи"""
    task = TaskCreate(**{k: v for k, v in data.items() if k != "action"})
    
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            """INSERT INTO tasks (title, description, due_date, priority, reminder, created_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (task.title, task.description, task.due_date, task.priority, 
             task.reminder, datetime.now().isoformat())
        )
        await db.commit()
        task_id = cursor.lastrowid
    
    logger.info(f"Task created: {task_id} - {task.title}")
    return {"status": "success", "task_id": task_id, "message": "Task created"}


async def list_tasks() -> dict:
    """Список всех задач"""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM tasks ORDER BY priority ASC, due_date ASC"
        )
        rows = await cursor.fetchall()
    
    tasks = [
        TaskResponse(
            id=row["id"],
            title=row["title"],
            description=row["description"],
            due_date=row["due_date"],
            priority=row["priority"],
            completed=bool(row["completed"]),
            created_at=row["created_at"],
            reminder=bool(row["reminder"])
        ).dict()
        for row in rows
    ]
    
    return {"tasks": tasks, "count": len(tasks)}


async def get_task(task_id: int) -> dict:
    """Получение задачи по ID"""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
        row = await cursor.fetchone()
    
    if not row:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task = TaskResponse(
        id=row["id"],
        title=row["title"],
        description=row["description"],
        due_date=row["due_date"],
        priority=row["priority"],
        completed=bool(row["completed"]),
        created_at=row["created_at"],
        reminder=bool(row["reminder"])
    )
    
    return {"task": task.dict()}


async def update_task(task_id: int, data: dict) -> dict:
    """Обновление задачи"""
    updates = []
    values = []
    
    if data.get("title"):
        updates.append("title = ?")
        values.append(data["title"])
    if data.get("description") is not None:
        updates.append("description = ?")
        values.append(data["description"])
    if data.get("due_date"):
        updates.append("due_date = ?")
        values.append(data["due_date"])
    if data.get("priority") is not None:
        updates.append("priority = ?")
        values.append(data["priority"])
    if data.get("completed") is not None:
        updates.append("completed = ?")
        values.append(1 if data["completed"] else 0)
    
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")
    
    values.append(task_id)
    
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            f"UPDATE tasks SET {', '.join(updates)} WHERE id = ?",
            values
        )
        await db.commit()
    
    logger.info(f"Task updated: {task_id}")
    return {"status": "success", "message": "Task updated"}


async def delete_task(task_id: int) -> dict:
    """Удаление задачи"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        await db.commit()
    
    logger.info(f"Task deleted: {task_id}")
    return {"status": "success", "message": "Task deleted"}


async def complete_task(task_id: int) -> dict:
    """Завершение задачи"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE tasks SET completed = 1 WHERE id = ?",
            (task_id,)
        )
        await db.commit()
    
    logger.info(f"Task completed: {task_id}")
    return {"status": "success", "message": "Task completed"}


def main():
    uvicorn.run(app, host="0.0.0.0", port=8008)


if __name__ == "__main__":
    main()
