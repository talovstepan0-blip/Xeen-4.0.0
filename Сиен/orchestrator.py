# Файл: orchestrator.py
"""
Оркестратор проекта "Сиен"
Главный сервер на FastAPI + WebSocket для управления агентами и распределения задач.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional
from enum import IntEnum
import psutil
import aiohttp
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Request
from fastapi.responses import JSONResponse
from starlette.websockets import WebSocketState
import uvicorn

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("orchestrator")


class Priority(IntEnum):
    """Приоритеты задач"""
    HIGHEST = 0
    HIGH = 1
    MEDIUM = 2
    LOW = 3


class TaskQueue:
    """Очередь задач с приоритетами"""
    
    def __init__(self):
        self.queues: Dict[Priority, asyncio.Queue] = {
            Priority.HIGHEST: asyncio.Queue(),
            Priority.HIGH: asyncio.Queue(),
            Priority.MEDIUM: asyncio.Queue(),
            Priority.LOW: asyncio.Queue()
        }
    
    async def put(self, task: dict, priority: Priority = Priority.MEDIUM):
        """Добавить задачу в очередь"""
        await self.queues[priority].put(task)
        logger.info(f"Task added with priority {priority.name}: {task.get('id', 'unknown')}")
    
    async def get(self) -> Optional[dict]:
        """Получить задачу из очереди (сначала высший приоритет)"""
        for priority in [Priority.HIGHEST, Priority.HIGH, Priority.MEDIUM, Priority.LOW]:
            if not self.queues[priority].empty():
                return await self.queues[priority].get()
        return None
    
    def empty(self) -> bool:
        """Проверить, пуста ли очередь"""
        return all(q.empty() for q in self.queues.values())


class AgentRegistry:
    """Реестр активных агентов"""
    
    def __init__(self):
        self.agents: Dict[str, dict] = {}
    
    def register(self, name: str, port: int, description: str):
        """Зарегистрировать агент"""
        self.agents[name] = {
            "name": name,
            "port": port,
            "description": description,
            "status": "offline",
            "last_seen": None
        }
        logger.info(f"Agent registered: {name} on port {port}")
    
    def update_status(self, name: str, status: str):
        """Обновить статус агента"""
        if name in self.agents:
            self.agents[name]["status"] = status
            self.agents[name]["last_seen"] = datetime.now().isoformat()
    
    def get_all(self) -> List[dict]:
        """Получить всех агентов"""
        return list(self.agents.values())
    
    def get_by_name(self, name: str) -> Optional[dict]:
        """Получить агент по имени"""
        return self.agents.get(name)


class Orchestrator:
    """Основной класс оркестратора"""
    
    def __init__(self):
        self.app = FastAPI(title="Сиен Оркестратор", version="1.0.0")
        self.task_queue = TaskQueue()
        self.agent_registry = AgentRegistry()
        self.websocket_connections: List[WebSocket] = []
        self.session: Optional[aiohttp.ClientSession] = None
        self._setup_routes()
        self._register_agents()
    
    def _register_agents(self):
        """Регистрация всех 22 агентов"""
        agents_config = [
            ("argus", 8003, "Поиск в интернете"),
            ("cronos", 8004, "Хранилище секретов"),
            ("ahill", 8005, "Управление прокси/VPS"),
            ("fenix", 8006, "Распознавание намерений"),
            ("logos", 8007, "Форматирование ответов"),
            ("wen", 8008, "Задачи и напоминания"),
            ("hermes", 8009, "Партнёрский маркетинг"),
            ("apollo", 8010, "Генерация коротких видео"),
            ("dike", 8011, "Бухгалтерия"),
            ("mnemon", 8012, "Перевод текста"),
            ("kun", 8013, "RAG обучение"),
            ("master", 8014, "Здоровье и тренировки"),
            ("plutos", 8015, "Инвестиции"),
            ("musa", 8016, "Генерация контента"),
            ("kallio", 8017, "Рекомендации"),
            ("hefest", 8018, "Генерация кода"),
            ("auto", 8019, "Макросы"),
            ("huei", 8020, "Генерация фото"),
            ("meng", 8021, "Генерация длинного видео"),
            ("echo", 8022, "Озвучка текста"),
            ("irida", 8023, "Telegram-бот"),
        ]
        
        for name, port, desc in agents_config:
            self.agent_registry.register(name, port, desc)
    
    def _setup_routes(self):
        """Настройка маршрутов"""
        
        @self.app.on_event("startup")
        async def startup():
            self.session = aiohttp.ClientSession()
            logger.info("Orchestrator started")
        
        @self.app.on_event("shutdown")
        async def shutdown():
            if self.session:
                await self.session.close()
            logger.info("Orchestrator stopped")
        
        @self.app.get("/health")
        async def health_check():
            """Проверка статуса оркестратора"""
            return {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "agents_count": len(self.agent_registry.agents),
                "active_connections": len(self.websocket_connections)
            }
        
        @self.app.get("/agents")
        async def get_agents():
            """Получить список всех агентов"""
            # Проверка статусов агентов
            for agent in self.agent_registry.agents.values():
                try:
                    async with self.session.get(f"http://localhost:{agent['port']}/health", timeout=2) as resp:
                        if resp.status == 200:
                            self.agent_registry.update_status(agent["name"], "online")
                        else:
                            self.agent_registry.update_status(agent["name"], "offline")
                except Exception:
                    self.agent_registry.update_status(agent["name"], "offline")
            
            return {"agents": self.agent_registry.get_all()}
        
        @self.app.get("/system/metrics")
        async def get_system_metrics():
            """Получить метрики системы"""
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            
            metrics = {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "memory_used_gb": round(memory.used / (1024**3), 2),
                "memory_total_gb": round(memory.total / (1024**3), 2),
                "timestamp": datetime.now().isoformat()
            }
            
            # Попытка получить VRAM (если доступна)
            try:
                import pynvml
                pynvml.nvmlInit()
                handle = pynvml.nvmlDeviceGetHandleByIndex(0)
                info = pynvml.nvmlDeviceGetMemoryInfo(handle)
                metrics["vram_percent"] = round((info.used / info.total) * 100, 2)
                metrics["vram_used_gb"] = round(info.used / (1024**3), 2)
                metrics["vram_total_gb"] = round(info.total / (1024**3), 2)
            except Exception:
                metrics["vram_available"] = False
            
            return metrics
        
        @self.app.api_route("/tasks/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
        async def proxy_to_wen(request: Request, path: str):
            """Прокси на агент Wen для работы с задачами"""
            wen_agent = self.agent_registry.get_by_name("wen")
            if not wen_agent or wen_agent["status"] != "online":
                raise HTTPException(status_code=503, detail="Wen agent unavailable")
            
            url = f"http://localhost:{wen_agent['port']}/{path}"
            
            try:
                if request.method == "GET":
                    async with self.session.get(url) as resp:
                        data = await resp.json()
                        return JSONResponse(content=data, status_code=resp.status)
                elif request.method == "POST":
                    body = await request.json()
                    async with self.session.post(url, json=body) as resp:
                        data = await resp.json()
                        return JSONResponse(content=data, status_code=resp.status)
                elif request.method == "PUT":
                    body = await request.json()
                    async with self.session.put(url, json=body) as resp:
                        data = await resp.json()
                        return JSONResponse(content=data, status_code=resp.status)
                elif request.method == "DELETE":
                    async with self.session.delete(url) as resp:
                        data = await resp.json()
                        return JSONResponse(content=data, status_code=resp.status)
            except Exception as e:
                logger.error(f"Error proxying to Wen: {e}")
                raise HTTPException(status_code=502, detail="Failed to communicate with Wen agent")
        
        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            """WebSocket соединение для HUD"""
            await websocket.accept()
            self.websocket_connections.append(websocket)
            logger.info(f"WebSocket connected. Total connections: {len(self.websocket_connections)}")
            
            try:
                while True:
                    data = await websocket.receive_text()
                    message = json.loads(data)
                    
                    # Обработка команды
                    response = await self._process_command(message)
                    
                    # Отправка ответа
                    await websocket.send_json(response)
                    
                    #Broadcast всем подключенным клиентам
                    await self._broadcast({
                        "type": "command_executed",
                        "data": response
                    })
                    
            except WebSocketDisconnect:
                logger.info("WebSocket disconnected")
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
            finally:
                self.websocket_connections.remove(websocket)
    
    async def _process_command(self, message: dict) -> dict:
        """Обработка команды от клиента"""
        cmd_type = message.get("type", "unknown")
        payload = message.get("payload", {})
        
        logger.info(f"Processing command: {cmd_type}")
        
        if cmd_type == "chat":
            # Отправка в Fenix для распознавания намерений
            return await self._forward_to_agent("fenix", {"action": "analyze", "text": payload.get("text", "")})
        
        elif cmd_type == "task_create":
            # Создание задачи через Wen
            return await self._forward_to_agent("wen", {"action": "create", **payload})
        
        elif cmd_type == "task_list":
            # Получение списка задач
            return await self._forward_to_agent("wen", {"action": "list"})
        
        elif cmd_type == "search":
            # Поиск через Argus
            return await self._forward_to_agent("argus", {"query": payload.get("query", "")})
        
        elif cmd_type == "translate":
            # Перевод через Mnemon
            return await self._forward_to_agent("mnemon", {
                "text": payload.get("text", ""),
                "target_lang": payload.get("lang", "en")
            })
        
        elif cmd_type == "generate_code":
            # Генерация кода через Hefest
            return await self._forward_to_agent("hefest", {"prompt": payload.get("prompt", "")})
        
        elif cmd_type == "generate_image":
            # Генерация изображения через Huei
            return await self._forward_to_agent("huei", {"prompt": payload.get("prompt", "")})
        
        elif cmd_type == "system_info":
            # Системная информация
            return {
                "type": "system_info",
                "data": await self._get_system_metrics()
            }
        
        else:
            return {
                "type": "error",
                "message": f"Unknown command type: {cmd_type}"
            }
    
    async def _forward_to_agent(self, agent_name: str, payload: dict) -> dict:
        """Пересылка команды агенту"""
        agent = self.agent_registry.get_by_name(agent_name)
        if not agent:
            return {"type": "error", "message": f"Agent {agent_name} not found"}
        
        if agent["status"] != "online":
            # Попытка проверить статус
            try:
                async with self.session.get(f"http://localhost:{agent['port']}/health", timeout=2) as resp:
                    if resp.status == 200:
                        self.agent_registry.update_status(agent_name, "online")
                    else:
                        return {"type": "error", "message": f"Agent {agent_name} is offline"}
            except Exception:
                return {"type": "error", "message": f"Agent {agent_name} is offline"}
        
        try:
            url = f"http://localhost:{agent['port']}/execute"
            async with self.session.post(url, json=payload) as resp:
                result = await resp.json()
                return {
                    "type": "agent_response",
                    "agent": agent_name,
                    "data": result
                }
        except Exception as e:
            logger.error(f"Error forwarding to {agent_name}: {e}")
            return {"type": "error", "message": f"Failed to communicate with {agent_name}"}
    
    async def _broadcast(self, message: dict):
        """Отправка сообщения всем подключенным WebSocket клиентам"""
        if not self.websocket_connections:
            return
        
        disconnected = []
        for ws in self.websocket_connections:
            try:
                if ws.client_state == WebSocketState.CONNECTED:
                    await ws.send_json(message)
            except Exception:
                disconnected.append(ws)
        
        # Удаление отключенных клиентов
        for ws in disconnected:
            if ws in self.websocket_connections:
                self.websocket_connections.remove(ws)
    
    async def _get_system_metrics(self) -> dict:
        """Получение системных метрик"""
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        
        return {
            "cpu_percent": cpu_percent,
            "memory_percent": memory.percent,
            "timestamp": datetime.now().isoformat()
        }
    
    def run(self, host: str = "0.0.0.0", port: int = 8000):
        """Запуск сервера"""
        uvicorn.run(self.app, host=host, port=port, log_level="info")


def main():
    """Точка входа"""
    orchestrator = Orchestrator()
    orchestrator.run(host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
