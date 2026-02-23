import os
import sys
import json
import asyncio
from functools import wraps
from inspect import signature

class CacheService:
    """Класс для кастомного кэширования"""
    
    def __init__(self):
        # base_dir = os.path.dirname(sys.executable)
        base_dir = os.getcwd()
        self.cache_path = os.path.join(base_dir, 'cache')
        self._create_dir()

    def _create_dir(self):
        if not os.path.exists(self.cache_path):
            os.makedirs(self.cache_path)

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

            path = os.path.join(self.cache_path, f"{identifier}_{task}.json")
            loop = asyncio.get_event_loop()
            
            if os.path.isfile(path):
                def read():
                    with open(path, "r", encoding="utf-8") as f:
                        return json.load(f)
                return await loop.run_in_executor(None, read)

            result = await func(*args, **kwargs)

            def write():
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(result, f, ensure_ascii=False)
            await loop.run_in_executor(None, write)

            return result
        return wrapper

cache = CacheService()