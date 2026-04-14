# Файл: sien_launcher.py
"""
Лаунчер проекта "Сиен"
Единая точка запуска - оркестратор и все агенты
Запуск скрытый (без консольных окон), с иконкой в трее
"""

import os
import sys
import time
import signal
import threading
import subprocess
from typing import List, Dict

# Добавляем путь к проекту
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

# Импорт модулей ядра
try:
    from core.singleton import check_singleton
    from core.hide_console import run_hidden, get_creationflags, get_startupinfo
except ImportError:
    # Заглушки для тестирования
    def check_singleton(name): return True
    def run_hidden(cmd, **kwargs): return subprocess.Popen(cmd, **kwargs)
    def get_creationflags(): return 0
    def get_startupinfo(): return None

import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("launcher")

# Конфигурация агентов
AGENTS_CONFIG = [
    ("orchestrator", "orchestrator.py", 8000),
    ("argus", "agents/argus.py", 8003),
    ("cronos", "agents/cronos.py", 8004),
    ("ahill", "agents/ahill.py", 8005),
    ("fenix", "agents/fenix.py", 8006),
    ("logos", "agents/logos.py", 8007),
    ("wen", "agents/wen.py", 8008),
    ("hermes", "agents/hermes.py", 8009),
    ("apollo", "agents/apollo.py", 8010),
    ("dike", "agents/dike.py", 8011),
    ("mnemon", "agents/mnemon.py", 8012),
    ("kun", "agents/kun.py", 8013),
    ("master", "agents/master.py", 8014),
    ("plutos", "agents/plutos.py", 8015),
    ("musa", "agents/musa.py", 8016),
    ("kallio", "agents/kallio.py", 8017),
    ("hefest", "agents/hefest.py", 8018),
    ("auto", "agents/auto.py", 8019),
    ("huei", "agents/huei.py", 8020),
    ("meng", "agents/meng.py", 8021),
    ("echo", "agents/echo.py", 8022),
    ("irida", "agents/irida.py", 8023),
]


class SienLauncher:
    """Лаунчер проекта Сиен"""
    
    def __init__(self):
        self.processes: Dict[str, subprocess.Popen] = {}
        self.running = False
        self.tray_icon = None
        
    def start_agent(self, name: str, script: str, port: int) -> bool:
        """Запустить агент"""
        try:
            script_path = os.path.join(BASE_DIR, script)
            
            if not os.path.exists(script_path):
                logger.warning(f"Script not found: {script_path}")
                return False
            
            cmd = [sys.executable, script_path]
            
            process = run_hidden(
                cmd,
                cwd=BASE_DIR,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            
            self.processes[name] = process
            logger.info(f"Started {name} on port {port} (PID: {process.pid})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start {name}: {e}")
            return False
    
    def start_all(self):
        """Запустить все компоненты"""
        logger.info("Starting Sien...")
        
        for name, script, port in AGENTS_CONFIG:
            self.start_agent(name, script, port)
            time.sleep(0.2)  # Небольшая задержка между запусками
        
        self.running = True
        logger.info("All components started")
    
    def stop_all(self):
        """Остановить все компоненты"""
        logger.info("Stopping Sien...")
        
        for name, process in self.processes.items():
            try:
                process.terminate()
                logger.info(f"Stopped {name}")
            except Exception as e:
                logger.error(f"Error stopping {name}: {e}")
        
        self.processes.clear()
        self.running = False
    
    def wait_for_exit(self):
        """Ждать завершения работы"""
        while self.running:
            time.sleep(1)
            
            # Проверка живых процессов
            for name, process in list(self.processes.items()):
                if process.poll() is not None:
                    logger.warning(f"{name} exited unexpectedly")
                    # Перезапуск критических компонентов
                    if name == "orchestrator":
                        for n, s, p in AGENTS_CONFIG:
                            if n == name:
                                self.start_agent(n, s, p)
                                break


def create_tray_icon(launcher: SienLauncher):
    """Создать иконку в системном трее"""
    try:
        import pystray
        from PIL import Image, ImageDraw
        
        # Создаем простую иконку программно
        image = Image.new('RGB', (64, 64), '#0a0a0f')
        draw = ImageDraw.Draw(image)
        draw.rectangle([10, 10, 54, 54], fill='#00ff88')
        draw.text((15, 20), "СИ", fill='#0a0a0f')
        
        def on_show_hud(icon, item):
            logger.info("Show HUD requested")
            # TODO: Открыть HUD
        
        def on_dashboard(icon, item):
            logger.info("Open dashboard requested")
            import webbrowser
            webbrowser.open("http://localhost:8000/dashboard")
        
        def on_exit(icon, item):
            icon.stop()
            launcher.stop_all()
        
        menu = pystray.Menu(
            pystray.MenuItem("Показать HUD", on_show_hud),
            pystray.MenuItem("Открыть дашборд", on_dashboard),
            pystray.MenuItem(None, None, enabled=False),  # Разделитель
            pystray.MenuItem("Выход", on_exit)
        )
        
        launcher.tray_icon = pystray.Icon("sien", image, "Сиен", menu)
        return True
        
    except ImportError:
        logger.warning("pystray or Pillow not available, running without tray icon")
        return False


def main():
    """Точка входа"""
    
    # Проверка одиночного экземпляра
    if not check_singleton("Sien"):
        print("Sien is already running!")
        sys.exit(1)
    
    # Инициализация БД
    try:
        from scripts.init_db import init_database
        init_database()
    except Exception as e:
        logger.error(f"Database initialization error: {e}")
    
    # Создание лаунчера
    launcher = SienLauncher()
    
    # Обработчики сигналов
    def signal_handler(sig, frame):
        logger.info("Received exit signal")
        launcher.stop_all()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Запуск всех компонентов
    launcher.start_all()
    
    # Попытка создать иконку в трее
    if create_tray_icon(launcher):
        # Запуск в режиме с треем
        launcher.tray_icon.run()
    else:
        # Запуск без трея (консольный режим)
        try:
            launcher.wait_for_exit()
        except KeyboardInterrupt:
            launcher.stop_all()


if __name__ == "__main__":
    main()
