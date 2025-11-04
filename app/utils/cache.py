import logging
import time
import pickle
from typing import Any, Optional, Dict
from functools import wraps

class Cache:
    """
    Простая in-memory система кэширования
    """
    
    def __init__(self, default_ttl: int = 3600, max_size: int = 1000):
        self._cache: Dict[str, Dict] = {}
        self.default_ttl = default_ttl
        self.max_size = max_size
        self.logger = logging.getLogger(__name__)
    
    def get(self, key: str) -> Optional[Any]:
        """
        Получить значение из кэша
        
        Args:
            key: Ключ кэша
            
        Returns:
            Значение или None если не найдено или просрочено
        """
        try:
            if key not in self._cache:
                return None
            
            cached_item = self._cache[key]
            
            # Проверяем TTL
            if time.time() > cached_item['expires']:
                del self._cache[key]
                return None
            
            return cached_item['value']
            
        except Exception as e:
            self.logger.error(f"Cache get error for key {key}: {e}")
            return None
    
    def set(self, key: str, value: Any, ttl: int = None) -> bool:
        """
        Установить значение в кэш
        
        Args:
            key: Ключ кэша
            value: Значение для кэширования
            ttl: Время жизни в секундах
            
        Returns:
            Успешность операции
        """
        try:
            # Очищаем место если нужно
            if len(self._cache) >= self.max_size:
                self._evict_oldest()
            
            ttl = ttl or self.default_ttl
            self._cache[key] = {
                'value': value,
                'expires': time.time() + ttl,
                'created': time.time()
            }
            return True
            
        except Exception as e:
            self.logger.error(f"Cache set error for key {key}: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """
        Удалить значение из кэша
        
        Args:
            key: Ключ кэша
            
        Returns:
            Успешность операции
        """
        try:
            if key in self._cache:
                del self._cache[key]
            return True
        except Exception as e:
            self.logger.error(f"Cache delete error for key {key}: {e}")
            return False
    
    def clear(self) -> bool:
        """Очистить весь кэш"""
        try:
            self._cache.clear()
            return True
        except Exception as e:
            self.logger.error(f"Cache clear error: {e}")
            return False
    
    def clear_pattern(self, pattern: str) -> int:
        """
        Очистить ключи по паттерну
        
        Args:
            pattern: Паттерн для поиска ключей
            
        Returns:
            Количество удаленных ключей
        """
        try:
            keys_to_delete = [key for key in self._cache.keys() if pattern in key]
            for key in keys_to_delete:
                del self._cache[key]
            return len(keys_to_delete)
        except Exception as e:
            self.logger.error(f"Cache clear pattern error: {e}")
            return 0
    
    def get_stats(self) -> Dict[str, Any]:
        """Получить статистику кэша"""
        current_time = time.time()
        expired_count = sum(1 for item in self._cache.values() 
                           if current_time > item['expires'])
        
        return {
            'total_items': len(self._cache),
            'expired_items': expired_count,
            'max_size': self.max_size,
            'default_ttl': self.default_ttl
        }
    
    def _evict_oldest(self) -> None:
        """Удалить самые старые записи"""
        try:
            if not self._cache:
                return
            
            # Находим 10% самых старых записей
            items_to_remove = max(1, len(self._cache) // 10)
            sorted_items = sorted(self._cache.items(), 
                                key=lambda x: x[1]['created'])
            
            for key, _ in sorted_items[:items_to_remove]:
                del self._cache[key]
                
        except Exception as e:
            self.logger.error(f"Cache eviction error: {e}")

# Глобальный экземпляр кэша
cache = Cache()

def cached(ttl: int = 3600, key_prefix: str = ""):
    """
    Декоратор для кэширования результатов функций
    
    Args:
        ttl: Время жизни кэша в секундах
        key_prefix: Префикс для ключа кэша
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Создаем ключ кэша на основе аргументов функции
            cache_key = f"{key_prefix}_{func.__name__}_{str(args)}_{str(kwargs)}"
            cached_result = cache.get(cache_key)
            
            if cached_result is not None:
                return cached_result
            
            # Выполняем функцию и кэшируем результат
            result = func(*args, **kwargs)
            cache.set(cache_key, result, ttl)
            
            return result
        return wrapper
    return decorator