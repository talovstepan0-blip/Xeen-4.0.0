# Файл: core/config.py
"""
Модуль конфигурации проекта "Сиен"
Загрузка настроек из YAML и переменных окружения
"""

import os
import yaml
from typing import Any, Dict, Optional
from pathlib import Path
from dotenv import load_dotenv


class Config:
    """Класс конфигурации с поддержкой YAML и .env"""
    
    _instance: Optional['Config'] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        # Определение путей
        self.base_dir = Path(__file__).parent.parent
        self.config_dir = self.base_dir / "config"
        
        # Загрузка .env
        env_file = self.config_dir / ".env"
        if env_file.exists():
            load_dotenv(env_file)
        
        # Загрузка YAML конфигурации
        self.yaml_config = self._load_yaml_config()
        
        # Слияние с переменными окружения
        self.config = self._merge_configs()
        
        self._initialized = True
    
    def _load_yaml_config(self) -> Dict[str, Any]:
        """Загрузка конфигурации из YAML файла"""
        config_file = self.config_dir / "settings.yaml"
        
        if not config_file.exists():
            # Конфигурация по умолчанию
            return self._get_default_config()
        
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            print(f"Warning: Could not load config file: {e}")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Конфигурация по умолчанию"""
        return {
            'app': {
                'name': 'Сиен',
                'version': '1.0.0',
                'debug': False,
                'log_level': 'INFO'
            },
            'server': {
                'host': '0.0.0.0',
                'orchestrator_port': 8000,
                'dashboard_port': 8001
            },
            'agents': {
                'argus': 8003,
                'cronos': 8004,
                'ahill': 8005,
                'fenix': 8006,
                'logos': 8007,
                'wen': 8008,
                'hermes': 8009,
                'apollo': 8010,
                'dike': 8011,
                'mnemon': 8012,
                'kun': 8013,
                'master': 8014,
                'plutos': 8015,
                'musa': 8016,
                'kallio': 8017,
                'hefest': 8018,
                'auto': 8019,
                'huei': 8020,
                'meng': 8021,
                'echo': 8022,
                'irida': 8023
            },
            'database': {
                'path': 'data/sien.db',
                'backup_enabled': True,
                'backup_interval_hours': 24
            },
            'security': {
                'jwt_secret_key': 'CHANGE_THIS_SECRET_KEY_IN_PRODUCTION',
                'jwt_algorithm': 'HS256',
                'token_expire_minutes': 60,
                'rate_limit_requests': 100,
                'rate_limit_window_seconds': 60
            },
            'logging': {
                'level': 'INFO',
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                'file': 'logs/sien.log',
                'max_size_mb': 10,
                'backup_count': 5,
                'json_format': False
            },
            'task_queue': {
                'max_size': 1000,
                'retry_attempts': 3,
                'retry_delay_seconds': 5,
                'task_timeout_seconds': 300
            },
            'monitoring': {
                'enabled': True,
                'metrics_interval_seconds': 30,
                'health_check_interval_seconds': 10,
                'trace_requests': False
            }
        }
    
    def _merge_configs(self) -> Dict[str, Any]:
        """Слияние YAML конфига с переменными окружения"""
        config = self.yaml_config.copy()
        
        # Переопределение из переменных окружения
        if os.getenv('SIEN_DEBUG'):
            config['app']['debug'] = os.getenv('SIEN_DEBUG').lower() == 'true'
        
        if os.getenv('SIEN_LOG_LEVEL'):
            config['app']['log_level'] = os.getenv('SIEN_LOG_LEVEL')
        
        if os.getenv('SIEN_JWT_SECRET_KEY'):
            config['security']['jwt_secret_key'] = os.getenv('SIEN_JWT_SECRET_KEY')
        
        if os.getenv('SIEN_HOST'):
            config['server']['host'] = os.getenv('SIEN_HOST')
        
        if os.getenv('SIEN_ORCHESTRATOR_PORT'):
            config['server']['orchestrator_port'] = int(os.getenv('SIEN_ORCHESTRATOR_PORT'))
        
        if os.getenv('SIEN_RATE_LIMIT_REQUESTS'):
            config['security']['rate_limit_requests'] = int(os.getenv('SIEN_RATE_LIMIT_REQUESTS'))
        
        if os.getenv('SIEN_DATABASE_PATH'):
            config['database']['path'] = os.getenv('SIEN_DATABASE_PATH')
        
        return config
    
    def get(self, *keys: str, default: Any = None) -> Any:
        """Получение значения конфигурации по цепочке ключей"""
        value = self.config
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        return value
    
    @property
    def debug(self) -> bool:
        return self.get('app', 'debug', default=False)
    
    @property
    def log_level(self) -> str:
        return self.get('app', 'log_level', default='INFO')
    
    @property
    def jwt_secret_key(self) -> str:
        return self.get('security', 'jwt_secret_key', default='')
    
    @property
    def rate_limit_requests(self) -> int:
        return self.get('security', 'rate_limit_requests', default=100)
    
    @property
    def rate_limit_window_seconds(self) -> int:
        return self.get('security', 'rate_limit_window_seconds', default=60)
    
    @property
    def orchestrator_port(self) -> int:
        return self.get('server', 'orchestrator_port', default=8000)
    
    @property
    def agent_ports(self) -> Dict[str, int]:
        return self.get('agents', default={})
    
    @property
    def database_path(self) -> str:
        db_path = self.get('database', 'path', default='data/sien.db')
        # Преобразование в абсолютный путь
        if not os.path.isabs(db_path):
            return str(self.base_dir / db_path)
        return db_path


# Глобальный экземпляр конфигурации
config = Config()


def get_config() -> Config:
    """Получение экземпляра конфигурации"""
    return config
