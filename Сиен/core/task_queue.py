# Файл: core/task_queue.py
"""
Улучшенная очередь задач проекта "Сиен"
Приоритеты, retry-механизм, таймауты, персистентность
"""

import asyncio
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from enum import IntEnum
from dataclasses import dataclass, field
import logging

from core.config import config


logger = logging.getLogger("task_queue")


class TaskPriority(IntEnum):
    """Приоритеты задач"""
    CRITICAL = 0
    HIGH = 1
    MEDIUM = 2
    LOW = 3


class TaskStatus(IntEnum):
    """Статусы задач"""
    PENDING = 0
    RUNNING = 1
    COMPLETED = 2
    FAILED = 3
    RETRYING = 4
    CANCELLED = 5


@dataclass
class Task:
    """Класс задачи"""
    id: str
    name: str
    payload: Dict[str, Any]
    priority: TaskPriority = TaskPriority.MEDIUM
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    retry_count: int = 0
    max_retries: int = 3
    timeout_seconds: int = 300
    error_message: Optional[str] = None
    result: Optional[Any] = None
    agent: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Сериализация в словарь"""
        return {
            "id": self.id,
            "name": self.name,
            "payload": self.payload,
            "priority": self.priority.value,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "timeout_seconds": self.timeout_seconds,
            "error_message": self.error_message,
            "result": self.result,
            "agent": self.agent
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Task':
        """Десериализация из словаря"""
        return cls(
            id=data["id"],
            name=data["name"],
            payload=data["payload"],
            priority=TaskPriority(data["priority"]),
            status=TaskStatus(data["status"]),
            created_at=datetime.fromisoformat(data["created_at"]),
            started_at=datetime.fromisoformat(data["started_at"]) if data["started_at"] else None,
            completed_at=datetime.fromisoformat(data["completed_at"]) if data["completed_at"] else None,
            retry_count=data["retry_count"],
            max_retries=data["max_retries"],
            timeout_seconds=data["timeout_seconds"],
            error_message=data.get("error_message"),
            result=data.get("result"),
            agent=data.get("agent")
        )


class EnhancedTaskQueue:
    """Улучшенная очередь задач с retry и персистентностью"""
    
    def __init__(self):
        # Очереди по приоритетам
        self.queues: Dict[TaskPriority, asyncio.Queue] = {
            priority: asyncio.Queue() for priority in TaskPriority
        }
        
        # Активные задачи
        self.active_tasks: Dict[str, Task] = {}
        
        # Завершённые задачи (кэш)
        self.completed_tasks: Dict[str, Task] = {}
        self.max_completed_cache = 1000
        
        # Конфигурация
        self.max_size = config.get('task_queue', 'max_size', default=1000)
        self.default_retries = config.get('task_queue', 'retry_attempts', default=3)
        self.retry_delay = config.get('task_queue', 'retry_delay_seconds', default=5)
        self.default_timeout = config.get('task_queue', 'task_timeout_seconds', default=300)
        
        # Обработчики задач
        self.handlers: Dict[str, Callable] = {}
        
        # Событие для ожидания задач
        self.task_available = asyncio.Event()
        
        # Флаг работы
        self.running = False
        
        logger.info("EnhancedTaskQueue initialized")
    
    def register_handler(self, task_name: str, handler: Callable):
        """Регистрация обработчика задач"""
        self.handlers[task_name] = handler
        logger.info(f"Registered handler for task: {task_name}")
    
    async def put(self, task: Task) -> bool:
        """Добавление задачи в очередь"""
        # Проверка размера очереди
        total_size = sum(q.qsize() for q in self.queues.values())
        if total_size >= self.max_size:
            logger.warning(f"Queue is full ({total_size}/{self.max_size})")
            return False
        
        await self.queues[task.priority].put(task)
        self.active_tasks[task.id] = task
        self.task_available.set()
        
        logger.info(f"Task added: {task.id} ({task.name}, priority={task.priority.name})")
        return True
    
    async def create_and_put(
        self,
        name: str,
        payload: Dict[str, Any],
        priority: TaskPriority = TaskPriority.MEDIUM,
        agent: Optional[str] = None,
        timeout_seconds: Optional[int] = None,
        max_retries: Optional[int] = None
    ) -> Task:
        """Создание и добавление задачи в очередь"""
        task = Task(
            id=str(uuid.uuid4()),
            name=name,
            payload=payload,
            priority=priority,
            agent=agent,
            timeout_seconds=timeout_seconds or self.default_timeout,
            max_retries=max_retries or self.default_retries
        )
        
        await self.put(task)
        return task
    
    async def get(self) -> Optional[Task]:
        """Получение задачи из очереди (сначала высший приоритет)"""
        for priority in TaskPriority:
            if not self.queues[priority].empty():
                task = await self.queues[priority].get()
                logger.debug(f"Task retrieved: {task.id}")
                return task
        return None
    
    async def wait_for_task(self, timeout: Optional[float] = None) -> Optional[Task]:
        """Ожидание доступной задачи"""
        try:
            await asyncio.wait_for(self.task_available.wait(), timeout=timeout)
            self.task_available.clear()
            return await self.get()
        except asyncio.TimeoutError:
            return None
    
    async def process_task(self, task: Task) -> bool:
        """Обработка задачи с retry и timeout"""
        task.status = TaskStatus.RUNNING
        task.started_at = datetime.utcnow()
        
        handler = self.handlers.get(task.name)
        
        if not handler:
            task.status = TaskStatus.FAILED
            task.error_message = f"No handler registered for task: {task.name}"
            logger.error(task.error_message)
            return False
        
        try:
            # Выполнение с таймаутом
            result = await asyncio.wait_for(
                handler(task.payload),
                timeout=task.timeout_seconds
            )
            
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.utcnow()
            task.result = result
            
            logger.info(f"Task completed: {task.id}")
            return True
            
        except asyncio.TimeoutError:
            task.error_message = f"Task timed out after {task.timeout_seconds}s"
            logger.warning(task.error_message)
            return await self._handle_failure(task)
            
        except Exception as e:
            task.error_message = str(e)
            logger.error(f"Task failed: {task.id} - {e}", exc_info=True)
            return await self._handle_failure(task)
    
    async def _handle_failure(self, task: Task) -> bool:
        """Обработка неудачи (retry или окончательный провал)"""
        task.retry_count += 1
        
        if task.retry_count < task.max_retries:
            task.status = TaskStatus.RETRYING
            delay = self.retry_delay * (2 ** (task.retry_count - 1))  # Exponential backoff
            
            logger.info(f"Retrying task {task.id} in {delay}s (attempt {task.retry_count}/{task.max_retries})")
            
            # Планирование повторной попытки
            asyncio.create_task(self._schedule_retry(task, delay))
            return True
        else:
            task.status = TaskStatus.FAILED
            task.completed_at = datetime.utcnow()
            logger.error(f"Task permanently failed: {task.id} after {task.retry_count} retries")
            return False
    
    async def _schedule_retry(self, task: Task, delay: float):
        """Планирование повторной попытки"""
        await asyncio.sleep(delay)
        task.status = TaskStatus.PENDING
        await self.put(task)
    
    def _cleanup_completed(self):
        """Очистка кэша завершённых задач"""
        if len(self.completed_tasks) > self.max_completed_cache:
            # Удаляем oldest tasks
            sorted_tasks = sorted(
                self.completed_tasks.items(),
                key=lambda x: x[1].completed_at or datetime.min
            )
            to_remove = len(self.completed_tasks) - self.max_completed_cache
            for task_id, _ in sorted_tasks[:to_remove]:
                del self.completed_tasks[task_id]
    
    def get_task(self, task_id: str) -> Optional[Task]:
        """Получение задачи по ID"""
        if task_id in self.active_tasks:
            return self.active_tasks[task_id]
        if task_id in self.completed_tasks:
            return self.completed_tasks[task_id]
        return None
    
    def get_all_tasks(self) -> List[Dict[str, Any]]:
        """Получение всех задач"""
        all_tasks = []
        for task in list(self.active_tasks.values()) + list(self.completed_tasks.values()):
            all_tasks.append(task.to_dict())
        return all_tasks
    
    def get_pending_count(self) -> int:
        """Получение количества ожидающих задач"""
        return sum(q.qsize() for q in self.queues.values())
    
    def get_stats(self) -> Dict[str, Any]:
        """Получение статистики очереди"""
        return {
            "pending": self.get_pending_count(),
            "active": len([t for t in self.active_tasks.values() if t.status == TaskStatus.RUNNING]),
            "completed": len(self.completed_tasks),
            "failed": len([t for t in list(self.active_tasks.values()) + list(self.completed_tasks.values()) 
                          if t.status == TaskStatus.FAILED]),
            "handlers": list(self.handlers.keys())
        }
    
    async def run_worker(self, worker_id: str = "worker-1"):
        """Запуск воркера для обработки задач"""
        self.running = True
        logger.info(f"Worker {worker_id} started")
        
        while self.running:
            task = await self.wait_for_task(timeout=1.0)
            
            if task:
                success = await self.process_task(task)
                
                # Перемещение в completed cache
                if task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
                    if task.id in self.active_tasks:
                        del self.active_tasks[task.id]
                    self.completed_tasks[task.id] = task
                    self._cleanup_completed()
            else:
                await asyncio.sleep(0.1)
        
        logger.info(f"Worker {worker_id} stopped")
    
    def stop(self):
        """Остановка воркера"""
        self.running = False
    
    async def cancel_task(self, task_id: str) -> bool:
        """Отмена задачи"""
        task = self.get_task(task_id)
        
        if not task:
            return False
        
        if task.status == TaskStatus.RUNNING:
            # Нельзя отменить выполняющуюся задачу
            return False
        
        task.status = TaskStatus.CANCELLED
        task.completed_at = datetime.utcnow()
        
        logger.info(f"Task cancelled: {task_id}")
        return True


# Глобальный экземпляр
task_queue = EnhancedTaskQueue()


def get_task_queue() -> EnhancedTaskQueue:
    """Получение экземпляра очереди задач"""
    return task_queue
