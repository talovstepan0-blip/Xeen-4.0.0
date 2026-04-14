# Файл: core/security.py
"""
Модуль безопасности проекта "Сиен"
JWT аутентификация, rate limiting, hashing
"""

import jwt
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from functools import wraps
from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from collections import defaultdict
import time

from core.config import config


class SecurityManager:
    """Менеджер безопасности"""
    
    _instance: Optional['SecurityManager'] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self.jwt_secret = config.jwt_secret_key
        self.jwt_algorithm = config.get('security', 'jwt_algorithm', default='HS256')
        self.token_expire_minutes = config.get('security', 'token_expire_minutes', default=60)
        
        # Rate limiting
        self.rate_limit_requests = config.rate_limit_requests
        self.rate_limit_window = config.rate_limit_window_seconds
        self.request_history: Dict[str, list] = defaultdict(list)
        
        # HTTP Bearer auth
        self.bearer_scheme = HTTPBearer(auto_error=False)
        
        self._initialized = True
    
    def hash_password(self, password: str) -> str:
        """Хеширование пароля"""
        salt = secrets.token_hex(16)
        pwd_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000).hex()
        return f"{salt}${pwd_hash}"
    
    def verify_password(self, password: str, stored_hash: str) -> bool:
        """Проверка пароля"""
        try:
            salt, pwd_hash = stored_hash.split('$')
            new_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000).hex()
            return new_hash == pwd_hash
        except Exception:
            return False
    
    def create_token(self, user_id: str, username: str, extra_data: Optional[Dict] = None) -> str:
        """Создание JWT токена"""
        expire = datetime.utcnow() + timedelta(minutes=self.token_expire_minutes)
        
        payload = {
            "sub": user_id,
            "username": username,
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "access"
        }
        
        if extra_data:
            payload.update(extra_data)
        
        token = jwt.encode(payload, self.jwt_secret, algorithm=self.jwt_algorithm)
        return token
    
    def decode_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Декодирование JWT токена"""
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=[self.jwt_algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
    
    async def get_current_user(self, request: Request) -> Optional[Dict[str, Any]]:
        """Получение текущего пользователя из токена"""
        credentials: HTTPAuthorizationCredentials = await self.bearer_scheme(request)
        
        if credentials is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        payload = self.decode_token(credentials.credentials)
        
        if payload is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return payload
    
    def check_rate_limit(self, client_id: str) -> bool:
        """Проверка rate limiting"""
        current_time = time.time()
        window_start = current_time - self.rate_limit_window
        
        # Очистка старых записей
        self.request_history[client_id] = [
            req_time for req_time in self.request_history[client_id]
            if req_time > window_start
        ]
        
        # Проверка лимита
        if len(self.request_history[client_id]) >= self.rate_limit_requests:
            return False
        
        # Добавление текущей записи
        self.request_history[client_id].append(current_time)
        return True
    
    def get_rate_limit_info(self, client_id: str) -> Dict[str, Any]:
        """Получение информации о rate limiting"""
        current_time = time.time()
        window_start = current_time - self.rate_limit_window
        
        # Очистка старых записей
        self.request_history[client_id] = [
            req_time for req_time in self.request_history[client_id]
            if req_time > window_start
        ]
        
        requests_made = len(self.request_history[client_id])
        requests_remaining = max(0, self.rate_limit_requests - requests_made)
        
        return {
            "limit": self.rate_limit_requests,
            "remaining": requests_remaining,
            "reset_at": datetime.fromtimestamp(current_time + self.rate_limit_window).isoformat()
        }


def require_auth(func):
    """Декоратор для требующих аутентификации эндпоинтов"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        from fastapi import Request
        
        # Получаем request из args или kwargs
        request = None
        for arg in args:
            if isinstance(arg, Request):
                request = arg
                break
        
        if request is None:
            request = kwargs.get('request')
        
        if request is None:
            raise HTTPException(status_code=500, detail="Request not found")
        
        security = SecurityManager()
        user = await security.get_current_user(request)
        
        # Добавляем пользователя в контекст
        request.state.user = user
        
        return await func(*args, **kwargs)
    
    return wrapper


def rate_limit(func):
    """Декоратор для rate limiting"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        from fastapi import Request
        
        # Получаем request из args или kwargs
        request = None
        for arg in args:
            if isinstance(arg, Request):
                request = arg
                break
        
        if request is None:
            request = kwargs.get('request')
        
        if request is None:
            raise HTTPException(status_code=500, detail="Request not found")
        
        # Получаем client_id (IP адрес или user_id)
        client_id = request.client.host if request.client else "unknown"
        
        # Проверяем наличие пользователя (если есть аутентификация)
        if hasattr(request.state, 'user') and request.state.user:
            client_id = request.state.user.get('sub', client_id)
        
        security = SecurityManager()
        
        if not security.check_rate_limit(client_id):
            info = security.get_rate_limit_info(client_id)
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded",
                headers={
                    "X-RateLimit-Limit": str(info["limit"]),
                    "X-RateLimit-Remaining": str(info["remaining"]),
                    "X-RateLimit-Reset": info["reset_at"]
                }
            )
        
        response = await func(*args, **kwargs)
        
        # Добавляем заголовки rate limiting в ответ
        if hasattr(response, 'headers'):
            info = security.get_rate_limit_info(client_id)
            response.headers["X-RateLimit-Limit"] = str(info["limit"])
            response.headers["X-RateLimit-Remaining"] = str(info["remaining"])
            response.headers["X-RateLimit-Reset"] = info["reset_at"]
        
        return response
    
    return wrapper


# Глобальный экземпляр
security_manager = SecurityManager()


def get_security_manager() -> SecurityManager:
    """Получение экземпляра менеджера безопасности"""
    return security_manager
