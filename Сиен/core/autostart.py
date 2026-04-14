# Файл: core/autostart.py
"""
Управление автозагрузкой через Task Scheduler (Windows)
"""

import os
import sys
import subprocess


def get_task_name() -> str:
    return "SienLauncher"


def get_launcher_path() -> str:
    """Получить путь к лаунчеру"""
    if getattr(sys, 'frozen', False):
        return sys.executable
    return os.path.abspath(__file__)


def is_autostart_enabled() -> bool:
    """Проверить, включена ли автозагрузка"""
    try:
        result = subprocess.run(
            ["schtasks", "/Query", "/TN", get_task_name()],
            capture_output=True,
            text=True
        )
        return result.returncode == 0
    except Exception:
        return False


def enable_autostart() -> bool:
    """Включить автозагрузку"""
    try:
        launcher_path = get_launcher_path()
        
        # Создание задачи в планировщике
        cmd = [
            "schtasks", "/Create", "/TN", get_task_name(),
            "/TR", f'"{launcher_path}"',
            "/SC", "ONLOGON",
            "/RL", "HIGHEST",
            "/F"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.returncode == 0
    except Exception as e:
        print(f"Error enabling autostart: {e}")
        return False


def disable_autostart() -> bool:
    """Отключить автозагрузку"""
    try:
        cmd = ["schtasks", "/Delete", "/TN", get_task_name(), "/F"]
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.returncode == 0
    except Exception as e:
        print(f"Error disabling autostart: {e}")
        return False
