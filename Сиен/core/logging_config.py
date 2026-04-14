# Файл: core/logging_config.py
"""
Модуль настройки логирования проекта "Сиен"
Ротация логов, JSON форматирование, разные уровни
"""

import logging
import os
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from pathlib import Path
from typing import Optional
import json
from datetime import datetime

from core.config import config


class JSONFormatter(logging.Formatter):
    """JSON форматтер для логов"""
    
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # Добавляем exception если есть
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # Добавляем extra поля
        for key, value in record.__dict__.items():
            if key not in ['name', 'msg', 'args', 'created', 'filename', 'funcName', 
                          'levelname', 'levelno', 'lineno', 'module', 'msecs', 
                          'pathname', 'process', 'processName', 'relativeCreated',
                          'stack_info', 'exc_info', 'exc_text', 'thread', 'threadName']:
                log_data[key] = value
        
        return json.dumps(log_data, ensure_ascii=False)


class SienLogger:
    """Кастомный логгер проекта Сиен"""
    
    _instance: Optional['SienLogger'] = None
    _initialized: bool = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self.base_dir = Path(__file__).parent.parent
        self.log_dir = self.base_dir / "logs"
        self.log_dir.mkdir(exist_ok=True)
        
        # Конфигурация из settings
        self.log_level = getattr(logging, config.log_level.upper(), logging.INFO)
        self.log_file = self.log_dir / "sien.log"
        self.max_size_mb = config.get('logging', 'max_size_mb', default=10)
        self.backup_count = config.get('logging', 'backup_count', default=5)
        self.json_format = config.get('logging', 'json_format', default=False)
        
        self._setup_logging()
        self._initialized = True
    
    def _setup_logging(self):
        """Настройка логгеров"""
        
        # Выбор форматтера
        if self.json_format:
            formatter = JSONFormatter()
        else:
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
        
        # Root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(self.log_level)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(self.log_level)
        console_handler.setFormatter(formatter)
        
        # File handler с ротацией
        file_handler = RotatingFileHandler(
            self.log_file,
            maxBytes=self.max_size_mb * 1024 * 1024,
            backupCount=self.backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(self.log_level)
        file_handler.setFormatter(formatter)
        
        # Добавляем handlers только если их еще нет
        if not root_logger.handlers:
            root_logger.addHandler(console_handler)
            root_logger.addHandler(file_handler)
        
        # Специальный logger для оркестратора
        orchestrator_logger = logging.getLogger("orchestrator")
        orchestrator_logger.setLevel(self.log_level)
        
        # Logger для безопасности
        security_logger = logging.getLogger("security")
        security_logger.setLevel(logging.WARNING)
    
    def get_logger(self, name: str) -> logging.Logger:
        """Получение логгера по имени"""
        return logging.getLogger(name)
    
    def log_error(self, message: str, exc_info: Optional[Exception] = None, **extra):
        """Логирование ошибки с дополнительной информацией"""
        logger = logging.getLogger("sien")
        logger.error(message, exc_info=exc_info, extra=extra)
    
    def log_warning(self, message: str, **extra):
        """Логирование предупреждения"""
        logger = logging.getLogger("sien")
        logger.warning(message, extra=extra)
    
    def log_info(self, message: str, **extra):
        """Логирование информации"""
        logger = logging.getLogger("sien")
        logger.info(message, extra=extra)
    
    def log_debug(self, message: str, **extra):
        """Логирование отладочной информации"""
        logger = logging.getLogger("sien")
        logger.debug(message, extra=extra)


# Глобальный экземпляр
sien_logger = SienLogger()


def setup_logging():
    """Инициализация логирования (вызывать при старте приложения)"""
    return sien_logger


def get_logger(name: str) -> logging.Logger:
    """Получение логгера по имени"""
    return sien_logger.get_logger(name)


# Декоратор для логирования вызовов функций
def log_function_call(logger_name: str = "sien"):
    """Декоратор для логирования вызовов функций"""
    from functools import wraps
    
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            logger = logging.getLogger(logger_name)
            logger.debug(f"Calling {func.__name__} with args={args}, kwargs={kwargs}")
            
            try:
                result = await func(*args, **kwargs)
                logger.debug(f"{func.__name__} returned {result}")
                return result
            except Exception as e:
                logger.error(f"{func.__name__} raised exception: {e}", exc_info=True)
                raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            logger = logging.getLogger(logger_name)
            logger.debug(f"Calling {func.__name__} with args={args}, kwargs={kwargs}")
            
            try:
                result = func(*args, **kwargs)
                logger.debug(f"{func.__name__} returned {result}")
                return result
            except Exception as e:
                logger.error(f"{func.__name__} raised exception: {e}", exc_info=True)
                raise
        
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator
