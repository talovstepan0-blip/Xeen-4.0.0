# Файл: plugins/calendar.py
"""
Плагин календаря - события с датами (SQLite)
"""

import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "sien.db")


def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS calendar_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            description TEXT,
            event_date TEXT,
            event_time TEXT,
            created_at TEXT
        )
    """)
    conn.commit()
    conn.close()


def execute(params: dict) -> dict:
    """Управление событиями календаря"""
    action = params.get("action", "list")
    
    if action == "create":
        return create_event(params)
    elif action == "list":
        return list_events(params)
    elif action == "delete":
        return delete_event(params.get("id"))
    else:
        return {"status": "error", "message": "Unknown action"}


def create_event(params: dict) -> dict:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO calendar_events (title, description, event_date, event_time, created_at) VALUES (?, ?, ?, ?, ?)",
        (params.get("title", ""), params.get("description", ""),
         params.get("date", ""), params.get("time", ""), datetime.now().isoformat())
    )
    conn.commit()
    event_id = cursor.lastrowid
    conn.close()
    
    return {"status": "success", "id": event_id}


def list_events(params: dict) -> dict:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM calendar_events ORDER BY event_date, event_time")
    events = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return {"status": "success", "events": events}


def delete_event(event_id: int) -> dict:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM calendar_events WHERE id = ?", (event_id,))
    conn.commit()
    conn.close()
    
    return {"status": "success"}


init_db()
