import logging
import json
import time
import hashlib
from typing import Any, Dict, List, Optional, Union
from datetime import datetime, timedelta

class Helpers:
    """
    Вспомогательные функции общего назначения
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def generate_id(self, prefix: str = "id", length: int = 8) -> str:
        """
        Генерация уникального ID
        
        Args:
            prefix: Префикс ID
            length: Длина случайной части
            
        Returns:
            Уникальный ID
        """
        import random
        import string
        
        timestamp = int(time.time() * 1000)
        random_part = ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))
        return f"{prefix}_{timestamp}_{random_part}"
    
    def calculate_hash(self, data: Any, algorithm: str = 'md5') -> str:
        """
        Расчет хэша данных
        
        Args:
            data: Данные для хэширования
            algorithm: Алгоритм хэширования
            
        Returns:
            Хэш-строка
        """
        try:
            data_str = json.dumps(data, sort_keys=True) if not isinstance(data, str) else data
            data_bytes = data_str.encode('utf-8')
            
            if algorithm == 'md5':
                return hashlib.md5(data_bytes).hexdigest()
            elif algorithm == 'sha1':
                return hashlib.sha1(data_bytes).hexdigest()
            elif algorithm == 'sha256':
                return hashlib.sha256(data_bytes).hexdigest()
            else:
                raise ValueError(f"Unsupported algorithm: {algorithm}")
                
        except Exception as e:
            self.logger.error(f"Hash calculation error: {e}")
            return ""
    
    def format_file_size(self, size_bytes: int) -> str:
        """
        Форматирование размера файла в читаемом виде
        
        Args:
            size_bytes: Размер в байтах
            
        Returns:
            Отформатированная строка
        """
        if size_bytes == 0:
            return "0 B"
        
        size_names = ["B", "KB", "MB", "GB", "TB"]
        i = 0
        size = float(size_bytes)
        
        while size >= 1024 and i < len(size_names) - 1:
            size /= 1024
            i += 1
        
        return f"{size:.2f} {size_names[i]}"
    
    def format_duration(self, seconds: float) -> str:
        """
        Форматирование длительности в читаемом виде
        
        Args:
            seconds: Длительность в секундах
            
        Returns:
            Отформатированная строка
        """
        if seconds < 1:
            return f"{seconds * 1000:.0f} ms"
        
        if seconds < 60:
            return f"{seconds:.2f} s"
        
        minutes, seconds = divmod(seconds, 60)
        if minutes < 60:
            return f"{int(minutes)}m {int(seconds)}s"
        
        hours, minutes = divmod(minutes, 60)
        return f"{int(hours)}h {int(minutes)}m {int(seconds)}s"
    
    def safe_json_parse(self, json_string: str, default: Any = None) -> Any:
        """
        Безопасный парсинг JSON
        
        Args:
            json_string: JSON строка
            default: Значение по умолчанию при ошибке
            
        Returns:
            Распарсенный объект или значение по умолчанию
        """
        try:
            return json.loads(json_string)
        except (json.JSONDecodeError, TypeError):
            return default
    
    def safe_json_stringify(self, data: Any, default: str = "{}") -> str:
        """
        Безопасная сериализация в JSON
        
        Args:
            data: Данные для сериализации
            default: Значение по умолчанию при ошибке
            
        Returns:
            JSON строка или значение по умолчанию
        """
        try:
            return json.dumps(data, ensure_ascii=False, default=str)
        except (TypeError, ValueError):
            return default
    
    def deep_merge_dicts(self, dict1: Dict, dict2: Dict) -> Dict:
        """
        Глубокое слияние двух словарей
        
        Args:
            dict1: Первый словарь
            dict2: Второй словарь
            
        Returns:
            Объединенный словарь
        """
        result = dict1.copy()
        
        for key, value in dict2.items():
            if (key in result and isinstance(result[key], dict) 
                and isinstance(value, dict)):
                result[key] = self.deep_merge_dicts(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def filter_dict(self, data: Dict, keys: List[str]) -> Dict:
        """
        Фильтрация словаря по списку ключей
        
        Args:
            data: Исходный словарь
            keys: Список ключей для включения
            
        Returns:
            Отфильтрованный словарь
        """
        return {key: data[key] for key in keys if key in data}
    
    def chunk_list(self, items: List, chunk_size: int) -> List[List]:
        """
        Разбиение списка на чанки
        
        Args:
            items: Исходный список
            chunk_size: Размер чанка
            
        Returns:
            Список чанков
        """
        return [items[i:i + chunk_size] for i in range(0, len(items), chunk_size)]
    
    def flatten_list(self, nested_list: List) -> List:
        """
        Выравнивание вложенного списка
        
        Args:
            nested_list: Вложенный список
            
        Returns:
            Выровненный список
        """
        result = []
        for item in nested_list:
            if isinstance(item, list):
                result.extend(self.flatten_list(item))
            else:
                result.append(item)
        return result
    
    def get_nested_value(self, data: Dict, path: str, default: Any = None) -> Any:
        """
        Получение значения из вложенного словаря по пути
        
        Args:
            data: Словарь для поиска
            path: Путь к значению (например: "user.profile.name")
            default: Значение по умолчанию
            
        Returns:
            Найденное значение или значение по умолчанию
        """
        try:
            keys = path.split('.')
            current = data
            
            for key in keys:
                if isinstance(current, dict) and key in current:
                    current = current[key]
                else:
                    return default
            
            return current
        except (AttributeError, TypeError):
            return default
    
    def set_nested_value(self, data: Dict, path: str, value: Any) -> Dict:
        """
        Установка значения во вложенном словаре по пути
        
        Args:
            data: Словарь для изменения
            path: Путь к значению
            value: Новое значение
            
        Returns:
            Измененный словарь
        """
        keys = path.split('.')
        current = data
        
        for key in keys[:-1]:
            if key not in current or not isinstance(current[key], dict):
                current[key] = {}
            current = current[key]
        
        current[keys[-1]] = value
        return data
    
    def retry_operation(self, operation, max_attempts: int = 3, 
                       delay: float = 1.0, exceptions: tuple = (Exception,)):
        """
        Повторение операции при неудаче
        
        Args:
            operation: Функция для выполнения
            max_attempts: Максимальное количество попыток
            delay: Задержка между попытками
            exceptions: Исключения для перехвата
            
        Returns:
            Результат операции
        """
        import time
        
        last_exception = None
        for attempt in range(max_attempts):
            try:
                return operation()
            except exceptions as e:
                last_exception = e
                if attempt < max_attempts - 1:
                    time.sleep(delay * (2 ** attempt))  # Exponential backoff
                    continue
        
        raise last_exception