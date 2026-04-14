# Файл: core/hide_console.py
"""
Функции для скрытия консольных окон при запуске процессов
"""

import sys
import subprocess


def get_startupinfo():
    """Получить информацию о запуске для скрытия окна (Windows)"""
    if sys.platform == "win32":
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = subprocess.SW_HIDE
        return startupinfo
    return None


def get_creationflags():
    """Получить флаги создания процесса для скрытия окна (Windows)"""
    if sys.platform == "win32":
        return subprocess.CREATE_NO_WINDOW
    return 0


def run_hidden(cmd: list, **kwargs) -> subprocess.Popen:
    """Запустить процесс без консольного окна"""
    startupinfo = get_startupinfo()
    creationflags = get_creationflags()
    
    return subprocess.Popen(
        cmd,
        startupinfo=startupinfo,
        creationflags=creationflags,
        **kwargs
    )
