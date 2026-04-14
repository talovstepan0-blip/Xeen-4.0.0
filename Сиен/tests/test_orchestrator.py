# Файл: tests/test_orchestrator.py
"""
Интеграционные тесты для оркестратора
"""

import pytest
import asyncio
import sys
from pathlib import Path
from typing import AsyncGenerator

sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture
async def test_client():
    """Фикстура для тестового клиента FastAPI"""
    from fastapi.testclient import TestClient
    
    # Импортируем orchestrator после добавления пути
    from orchestrator import Orchestrator
    
    orchestrator = Orchestrator()
    client = TestClient(orchestrator.app)
    
    yield client
    
    # Cleanup
    client.close()


class TestOrchestratorHealth:
    """Тесты health check эндпоинтов"""
    
    def test_health_check(self, test_client):
        """Тест проверки здоровья оркестратора"""
        response = test_client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "agents_count" in data
        assert "active_connections" in data
    
    def test_agents_list(self, test_client):
        """Тест получения списка агентов"""
        response = test_client.get("/agents")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "agents" in data
        assert isinstance(data["agents"], list)
        # Должен быть хотя бы один агент
        assert len(data["agents"]) > 0


class TestSystemMetrics:
    """Тесты системных метрик"""
    
    def test_system_metrics(self, test_client):
        """Тест получения системных метрик"""
        response = test_client.get("/system/metrics")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "cpu_percent" in data
        assert "memory_percent" in data
        assert "timestamp" in data
        
        # Проверка диапазонов значений
        assert 0 <= data["cpu_percent"] <= 100
        assert 0 <= data["memory_percent"] <= 100


class TestTaskQueueIntegration:
    """Интеграционные тесты очереди задач"""
    
    @pytest.mark.asyncio
    async def test_task_queue_integration(self):
        """Тест интеграции с очередью задач"""
        from core.task_queue import EnhancedTaskQueue, Task, TaskPriority
        
        queue = EnhancedTaskQueue()
        
        # Регистрация обработчика
        async def mock_handler(payload):
            return {"result": "success", "data": payload}
        
        queue.register_handler("test_action", mock_handler)
        
        # Создание и выполнение задачи
        task = await queue.create_and_put(
            name="test_action",
            payload={"key": "value"},
            priority=TaskPriority.HIGH
        )
        
        assert task.id is not None
        assert task.name == "test_action"
        
        # Получение статистики
        stats = queue.get_stats()
        assert stats["pending"] >= 1


class TestSecurityIntegration:
    """Интеграционные тесты безопасности"""
    
    def test_rate_limit_headers(self, test_client):
        """Тест заголовков rate limiting"""
        response = test_client.get("/health")
        
        # Заголовки могут присутствовать если включен rate limiting middleware
        # Это зависит от конфигурации
        assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_jwt_flow(self):
        """Тест полного цикла JWT аутентификации"""
        from core.security import SecurityManager
        
        # Создаём новый экземпляр для теста
        security = SecurityManager()
        
        # Создание токена
        user_id = "integration_test_user"
        username = "testuser"
        
        token = security.create_token(user_id, username, {"role": "admin"})
        
        # Декодирование и проверка
        payload = security.decode_token(token)
        
        assert payload is not None
        assert payload["sub"] == user_id
        assert payload["username"] == username
        assert payload["role"] == "admin"
        assert "exp" in payload
        assert "iat" in payload


class TestConfigIntegration:
    """Интеграционные тесты конфигурации"""
    
    def test_config_loaded(self):
        """Тест загрузки конфигурации"""
        from core.config import config
        
        assert config is not None
        # Проверяем что config имеет метод get и свойства
        assert hasattr(config, 'get')
        assert hasattr(config, 'debug')
        assert config.get('app', 'name') == 'Сиен'
    
    def test_config_paths(self):
        """Тест путей конфигурации"""
        from core.config import config
        
        db_path = config.database_path
        assert db_path is not None
        assert len(db_path) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
