# Файл: scripts/init_db.py
"""
Инициализация базы данных SQLite
Создание всех необходимых таблиц
"""

import sqlite3
import os
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
DB_PATH = os.path.join(DATA_DIR, "sien.db")


def init_database():
    """Создать все таблицы в базе данных"""
    
    # Создаем директорию data если не существует
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(os.path.join(DATA_DIR, "logs"), exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Таблица задач
    cursor.execute("""
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
    
    # Таблица профиля пользователя
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
    
    # Таблица заметок
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            content TEXT,
            tags TEXT,
            created_at TEXT
        )
    """)
    
    # Таблица событий календаря
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
    
    # Таблица настроек плагинов
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS plugins_settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            plugin_name TEXT UNIQUE,
            enabled BOOLEAN DEFAULT 1,
            settings TEXT,
            updated_at TEXT
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
    
    print(f"Database initialized at {DB_PATH}")
    print("Tables created:")
    print("  - tasks")
    print("  - user_profile")
    print("  - notes")
    print("  - calendar_events")
    print("  - plugins_settings")


if __name__ == "__main__":
    init_database()
