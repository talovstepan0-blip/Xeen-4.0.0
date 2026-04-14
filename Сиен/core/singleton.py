# Файл: core/singleton.py
"""
Проверка одиночного экземпляра через мьютекс (Windows)
"""

import sys

if sys.platform == "win32":
    import ctypes
    from ctypes import wintypes
    
    def check_singleton(app_name: str) -> bool:
        """Проверить, запущен ли уже экземпляр приложения"""
        mutex_name = f"Global\\{app_name}_Mutex"
        
        try:
            handle = ctypes.windll.kernel32.CreateMutexW(
                None,
                True,
                mutex_name
            )
            
            if handle == 0:
                return False
            
            error_code = ctypes.windll.kernel32.GetLastError()
            
            # ERROR_ALREADY_EXISTS = 183
            if error_code == 183:
                ctypes.windll.kernel32.CloseHandle(handle)
                return False
            
            return True
        except Exception as e:
            print(f"Singleton check error: {e}")
            return True
else:
    # Для Linux/Mac используем файл-лок
    import fcntl
    import os
    
    _lock_file = None
    
    def check_singleton(app_name: str) -> bool:
        global _lock_file
        
        lock_path = f"/tmp/{app_name}.lock"
        
        try:
            _lock_file = open(lock_path, 'w')
            fcntl.flock(_lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            return True
        except (IOError, OSError):
            if _lock_file:
                _lock_file.close()
            return False
