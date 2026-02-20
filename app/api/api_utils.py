import requests
import time
from functools import wraps

class APIError(Exception):
    """Кастомное исключение для ошибок API"""
    def __init__(self, message: str, status_code: int = None, url: str = None):
        self.message = message
        self.status_code = status_code
        self.url = url
        super().__init__(self.message)

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