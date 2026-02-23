import os
import sys
import json
import asyncio
from datetime import datetime, timedelta
from functools import wraps
from inspect import signature

class CacheService:
    """Класс для кастомного кэширования"""
    
    def __init__(self):
        # base_dir = os.path.dirname(sys.executable)
        base_dir = os.getcwd()
        self.cache_path = os.path.join(base_dir, 'cache')
        self.timestamp_file = os.path.join(self.cache_path, 'timestamp.json')
        self._create_dir()
        self._init_timestamp_file()

    def _create_dir(self):
        if not os.path.exists(self.cache_path):
            os.makedirs(self.cache_path)

    def _init_timestamp_file(self):
        if not os.path.exists(self.timestamp_file):
            with open(self.timestamp_file, 'w', encoding='utf-8') as f:
                json.dump({}, f, ensure_ascii=False)

    def _add_timestamp_if_not_exists(self, identifier):
        with open(self.timestamp_file, 'r', encoding='utf-8') as f:
            timestamps = json.load(f)

        if identifier not in timestamps:
            timestamps[identifier] = datetime.now().isoformat()
            
            with open(self.timestamp_file, 'w', encoding='utf-8') as f:
                json.dump(timestamps, f, ensure_ascii=False, indent=2)

    def _check_and_clean_cache(self, identifier):
        with open(self.timestamp_file, 'r', encoding='utf-8') as f:
            timestamps = json.load(f)

        if identifier in timestamps:
            cache_time = datetime.fromisoformat(timestamps[identifier])
            now = datetime.now()
            
            # Проверяем, что прошло не больше недели
            if now - cache_time > timedelta(weeks=1):
                # Удаляем все файлы кэша для этого identifier
                file_path = os.path.join(self.cache_path, identifier + ".json")
                os.remove(file_path)

                # Удаляем запись из timestamp.json
                del timestamps[identifier]
                with open(self.timestamp_file, 'w', encoding='utf-8') as f:
                    json.dump(timestamps, f, ensure_ascii=False, indent=2)

    def cached(self, func):
        sig = signature(func)
        params = list(sig.parameters.values())

        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Получаем identifier (второй аргумент по счету)
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()
        
            # Берем имя второго параметра из сигнатуры (как бы он ни назывался)
            id_param_name = params[1].name 
            identifier = bound_args.arguments.get(id_param_name)

            # Получаем task (он всегда называется "task" и имеет default)
            task = bound_args.arguments.get('task')

            # 1. Проверяем возраст кэша для данного identifier и удаляем если пора
            self._check_and_clean_cache(f"{identifier}_{task}")

            path = os.path.join(self.cache_path, f"{identifier}_{task}.json")
            loop = asyncio.get_event_loop()
            
            if os.path.isfile(path):
                def read():
                    with open(path, "r", encoding="utf-8") as f:
                        return json.load(f)
                return await loop.run_in_executor(None, read)

            result = await func(*args, **kwargs)
            print(path, type(result))
            def write():
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(result, f, ensure_ascii=False)
            await loop.run_in_executor(None, write)

            # 2. Добавляем timestamp только если identifier еще нет
            self._add_timestamp_if_not_exists(f"{identifier}_{task}")

            return result
        return wrapper

cache = CacheService()