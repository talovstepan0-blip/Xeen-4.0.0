# Файл: tests/test_config.py
"""
Тесты для модуля конфигурации
"""

import pytest
import os
import sys
from pathlib import Path

# Добавляем путь к проекту
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestConfig:
    """Тесты конфигурации"""
    
    def test_config_singleton(self):
        """Тест одиночного экземпляра конфигурации"""
        from core.config import Config, get_config
        
        config1 = Config()
        config2 = Config()
        
        assert config1 is config2
        assert get_config() is config1
    
    def test_config_default_values(self):
        """Тест значений по умолчанию"""
        from core.config import config
        
        assert config.debug in [True, False]
        assert config.log_level in ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        assert isinstance(config.orchestrator_port, int)
        assert config.orchestrator_port > 0
    
    def test_config_get_method(self):
        """Тест метода get()"""
        from core.config import config
        
        # Получение существующего значения
        value = config.get('app', 'name', default='Unknown')
        assert value == 'Сиен'
        
        # Получение несуществующего значения с default
        value = config.get('nonexistent', 'key', default='default_value')
        assert value == 'default_value'
        
        # Получение несуществующего значения без default
        value = config.get('nonexistent', 'key')
        assert value is None
    
    def test_agent_ports(self):
        """Тест портов агентов"""
        from core.config import config
        
        ports = config.agent_ports
        assert isinstance(ports, dict)
        assert 'wen' in ports or len(ports) > 0
        assert isinstance(ports.get('wen', 8008), int)


class TestSecurityManager:
    """Тесты менеджера безопасности"""
    
    def test_security_singleton(self):
        """Тест одиночного экземпляра"""
        from core.security import SecurityManager, get_security_manager
        
        security1 = SecurityManager()
        security2 = SecurityManager()
        
        assert security1 is security2
        assert get_security_manager() is security1
    
    def test_password_hashing(self):
        """Тест хеширования паролей"""
        from core.security import security_manager
        
        password = "test_password_123"
        hashed = security_manager.hash_password(password)
        
        # Проверка формата (salt$hash)
        assert '$' in hashed
        salt, pwd_hash = hashed.split('$')
        assert len(salt) == 32  # hex(16 bytes)
        assert len(pwd_hash) == 64  # SHA256 hex
        
        # Проверка верификации
        assert security_manager.verify_password(password, hashed) is True
        assert security_manager.verify_password("wrong_password", hashed) is False
    
    def test_jwt_token(self):
        """Тест JWT токенов"""
        from core.security import security_manager
        
        user_id = "test_user_123"
        username = "testuser"
        
        # Создание токена
        token = security_manager.create_token(user_id, username)
        assert isinstance(token, str)
        assert len(token) > 0
        
        # Декодирование токена
        payload = security_manager.decode_token(token)
        assert payload is not None
        assert payload['sub'] == user_id
        assert payload['username'] == username
        assert 'exp' in payload
        assert 'iat' in payload
    
    def test_expired_token(self):
        """Тест просроченного токена"""
        from core.security import SecurityManager
        from datetime import timedelta
        
        # Создаём менеджер с коротким временем жизни токена
        security = SecurityManager()
        security.token_expire_minutes = -1  # Токен истёк
        
        token = security.create_token("user", "test")
        payload = security.decode_token(token)
        
        # Токен должен быть недействителен
        assert payload is None
    
    def test_rate_limiting(self):
        """Тест rate limiting"""
        from core.security import security_manager
        
        client_id = "test_client"
        
        # Очищаем историю для чистоты теста
        security_manager.request_history[client_id] = []
        
        # Проверка прохождения запросов в пределах лимита
        for i in range(security_manager.rate_limit_requests):
            assert security_manager.check_rate_limit(client_id) is True
        
        # Следующий запрос должен быть отклонён
        assert security_manager.check_rate_limit(client_id) is False
        
        # Проверка информации о лимите
        info = security_manager.get_rate_limit_info(client_id)
        assert info['limit'] == security_manager.rate_limit_requests
        assert info['remaining'] == 0


class TestTaskQueue:
    """Тесты очереди задач"""
    
    @pytest.mark.asyncio
    async def test_task_creation(self):
        """Тест создания задачи"""
        from core.task_queue import EnhancedTaskQueue, Task, TaskPriority
        
        queue = EnhancedTaskQueue()
        
        task = Task(
            id="test-123",
            name="test_task",
            payload={"key": "value"},
            priority=TaskPriority.HIGH
        )
        
        assert task.id == "test-123"
        assert task.name == "test_task"
        assert task.priority == TaskPriority.HIGH
        assert task.payload == {"key": "value"}
    
    @pytest.mark.asyncio
    async def test_task_serialization(self):
        """Тест сериализации задачи"""
        from core.task_queue import Task, TaskPriority, TaskStatus
        from datetime import datetime
        
        task = Task(
            id="test-456",
            name="serialize_task",
            payload={"data": [1, 2, 3]},
            priority=TaskPriority.MEDIUM,
            status=TaskStatus.PENDING
        )
        
        # Сериализация
        task_dict = task.to_dict()
        assert isinstance(task_dict, dict)
        assert task_dict['id'] == "test-456"
        
        # Десериализация
        restored_task = Task.from_dict(task_dict)
        assert restored_task.id == task.id
        assert restored_task.name == task.name
        assert restored_task.payload == task.payload
    
    @pytest.mark.asyncio
    async def test_queue_operations(self):
        """Тест операций очереди"""
        from core.task_queue import EnhancedTaskQueue, Task, TaskPriority
        
        queue = EnhancedTaskQueue()
        
        # Создание и добавление задачи
        task = Task(
            id="queue-test-1",
            name="queue_task",
            payload={},
            priority=TaskPriority.HIGH
        )
        
        result = await queue.put(task)
        assert result is True
        
        # Получение задачи
        retrieved_task = await queue.get()
        assert retrieved_task is not None
        assert retrieved_task.id == "queue-test-1"
    
    @pytest.mark.asyncio
    async def test_queue_priority(self):
        """Тест приоритетов очереди"""
        from core.task_queue import EnhancedTaskQueue, Task, TaskPriority
        
        queue = EnhancedTaskQueue()
        
        # Добавляем задачи в разном порядке
        low_task = Task(id="low", name="t", payload={}, priority=TaskPriority.LOW)
        high_task = Task(id="high", name="t", payload={}, priority=TaskPriority.HIGH)
        critical_task = Task(id="critical", name="t", payload={}, priority=TaskPriority.CRITICAL)
        
        await queue.put(low_task)
        await queue.put(high_task)
        await queue.put(critical_task)
        
        # Задачи должны извлекаться по приоритету
        first = await queue.get()
        assert first.id == "critical"
        
        second = await queue.get()
        assert second.id == "high"
        
        third = await queue.get()
        assert third.id == "low"
    
    @pytest.mark.asyncio
    async def test_queue_stats(self):
        """Тест статистики очереди"""
        from core.task_queue import EnhancedTaskQueue
        
        queue = EnhancedTaskQueue()
        
        stats = queue.get_stats()
        assert 'pending' in stats
        assert 'active' in stats
        assert 'completed' in stats
        assert 'handlers' in stats


class TestLoggingConfig:
    """Тесты конфигурации логирования"""
    
    def test_logger_initialization(self):
        """Тест инициализации логгера"""
        from core.logging_config import SienLogger, setup_logging
        
        logger = SienLogger()
        assert logger is not None
        assert logger._initialized is True
    
    def test_get_logger(self):
        """Тест получения логгера"""
        from core.logging_config import get_logger
        import logging
        
        logger = get_logger("test_module")
        assert isinstance(logger, logging.Logger)
        assert logger.name == "test_module"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
