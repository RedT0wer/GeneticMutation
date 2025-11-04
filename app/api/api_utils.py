import requests
import time
import logging
from functools import wraps
from typing import Dict, Any, Optional
from dataclasses import dataclass
from ..utils.cache import cache

@dataclass
class CacheConfig:
    """Конфигурация кэширования"""
    enabled: bool = True
    default_ttl: int = 3600  # 1 час
    max_size: int = 1000

class APIError(Exception):
    """Кастомное исключение для ошибок API"""
    def __init__(self, message: str, status_code: int = None, url: str = None):
        self.message = message
        self.status_code = status_code
        self.url = url
        super().__init__(self.message)

class APIUtils:
    """Утилиты для работы с API"""
    
    def __init__(self, base_url: str, cache_config: CacheConfig = None):
        self.base_url = base_url.rstrip('/')
        self.cache_config = cache_config or CacheConfig()
        self.logger = logging.getLogger(__name__)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'GeneticMutationAnalyzer/1.0',
            'Content-Type': 'application/json'
        })
    
    def _make_request(self, endpoint: str, method: str = 'GET', 
                     params: Dict = None, data: Dict = None, 
                     use_cache: bool = True) -> Dict[str, Any]:
        """
        Универсальный метод для выполнения HTTP запросов
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        # Проверяем кэш для GET запросов
        cache_key = None
        if method == 'GET' and use_cache and self.cache_config.enabled:
            cache_key = f"{url}:{hash(frozenset(params.items() if params else {}))}"
            cached_data = self._get_cached(cache_key)
            if cached_data:
                self.logger.debug(f"Cache hit for {url}")
                return cached_data
        
        try:
            response = self.session.request(
                method=method,
                url=url,
                params=params,
                json=data,
                timeout=30
            )
            
            if response.status_code == 404:
                raise APIError(f"Resource not found: {url}", 404, url)
            elif response.status_code == 429:
                raise APIError("Rate limit exceeded", 429, url)
            elif not response.ok:
                raise APIError(
                    f"API request failed: {response.status_code} - {response.text}",
                    response.status_code,
                    url
                )
            
            result = response.json()
            
            # Сохраняем в кэш
            if cache_key and self.cache_config.enabled:
                self._set_cached(cache_key, result)
            
            return result
            
        except requests.exceptions.Timeout:
            raise APIError(f"Request timeout for {url}")
        except requests.exceptions.ConnectionError:
            raise APIError(f"Connection error for {url}")
        except ValueError as e:
            raise APIError(f"Invalid JSON response from {url}: {e}")
    
    def _get_cached(self, key: str) -> Optional[Dict]:
        """Получить данные из кэша"""
        try:
            return cache.get(key)
        except Exception as e:
            self.logger.warning(f"Cache get error: {e}")
            return None
    
    def _set_cached(self, key: str, data: Dict, ttl: int = None):
        """Сохранить данные в кэш"""
        try:
            ttl = ttl or self.cache_config.default_ttl
            cache.set(key, data, ttl)
        except Exception as e:
            self.logger.warning(f"Cache set error: {e}")
    
    def clear_cache(self, pattern: str = None):
        """Очистить кэш"""
        try:
            if pattern:
                cache.clear_pattern(pattern)
            else:
                cache.clear()
        except Exception as e:
            self.logger.warning(f"Cache clear error: {e}")

def retry_on_failure(max_retries: int = 3, delay: float = 1.0):
    """Декоратор для повторения запросов при неудаче"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except (APIError, requests.exceptions.RequestException) as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        time.sleep(delay * (2 ** attempt))  # Exponential backoff
                        continue
            raise last_exception
        return wrapper
    return decorator