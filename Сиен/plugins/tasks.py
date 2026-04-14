# Файл: plugins/tasks.py
"""
Плагин задач - дублирует функциональность Wen
"""

import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "sien.db")


def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS plugin_tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            description TEXT,
            completed BOOLEAN DEFAULT 0,
            created_at TEXT
        )
    """)
    conn.commit()
    conn.close()


def execute(params: dict) -> dict:
    """Управление задачами"""
    action = params.get("action", "list")
    
    if action == "create":
        return create_task(params.get("title"), params.get("description"))
    elif action == "list":
        return list_tasks()
    elif action == "complete":
        return complete_task(params.get("id"))
    elif action == "delete":
        return delete_task(params.get("id"))
    else:
        return {"status": "error", "message": "Unknown action"}


def create_task(title: str, description: str = "") -> dict:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO plugin_tasks (title, description, created_at) VALUES (?, ?, ?)",
        (title, description, datetime.now().isoformat())
    )
    conn.commit()
    task_id = cursor.lastrowid
    conn.close()
    return {"status": "success", "id": task_id}


def list_tasks() -> dict:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM plugin_tasks ORDER BY created_at DESC")
    tasks = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return {"status": "success", "tasks": tasks}


def complete_task(task_id: int) -> dict:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE plugin_tasks SET completed = 1 WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()
    return {"status": "success"}


def delete_task(task_id: int) -> dict:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM plugin_tasks WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()
    return {"status": "success"}


init_db()
