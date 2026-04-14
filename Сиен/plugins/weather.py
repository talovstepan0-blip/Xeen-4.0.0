# Файл: plugins/weather.py
"""
Плагин погоды - OpenWeatherMap API с кэшированием 5 минут
"""

import time
from datetime import datetime

_cache = {}
CACHE_DURATION = 300  # 5 минут


def execute(params: dict) -> dict:
    """Получить погоду для города"""
    city = params.get("city", "Moscow")
    
    # Проверка кэша
    if city in _cache:
        cached_time, data = _cache[city]
        if time.time() - cached_time < CACHE_DURATION:
            return {"status": "success", "cached": True, **data}
    
    # Заглушка (в реальности нужен API запрос к OpenWeatherMap)
    data = {
        "city": city,
        "temperature": 20,
        "condition": "Sunny",
        "humidity": 65,
        "wind_speed": 5
    }
    
    _cache[city] = (time.time(), data)
    
    return {"status": "success", "cached": False, **data}
