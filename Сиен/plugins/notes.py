# Файл: plugins/notes.py
"""
Плагин заметок с тегами (SQLite)
"""

import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "sien.db")


def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            content TEXT,
            tags TEXT,
            created_at TEXT
        )
    """)
    conn.commit()
    conn.close()


def execute(params: dict) -> dict:
    """Управление заметками"""
    action = params.get("action", "list")
    
    if action == "create":
        return create_note(params)
    elif action == "list":
        return list_notes(params)
    elif action == "delete":
        return delete_note(params.get("id"))
    else:
        return {"status": "error", "message": "Unknown action"}


def create_note(params: dict) -> dict:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO notes (title, content, tags, created_at) VALUES (?, ?, ?, ?)",
        (params.get("title", ""), params.get("content", ""), 
         params.get("tags", ""), datetime.now().isoformat())
    )
    conn.commit()
    note_id = cursor.lastrowid
    conn.close()
    
    return {"status": "success", "id": note_id}


def list_notes(params: dict) -> dict:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    tag_filter = params.get("tag")
    if tag_filter:
        cursor.execute("SELECT * FROM notes WHERE tags LIKE ?", (f"%{tag_filter}%",))
    else:
        cursor.execute("SELECT * FROM notes ORDER BY created_at DESC")
    
    notes = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return {"status": "success", "notes": notes}


def delete_note(note_id: int) -> dict:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM notes WHERE id = ?", (note_id,))
    conn.commit()
    conn.close()
    
    return {"status": "success"}


init_db()
