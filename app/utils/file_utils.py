import os
import json
import csv
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path

class FileUtils:
    """
    Утилиты для работы с файлами
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def ensure_directory(self, directory_path: str) -> bool:
        """
        Создание директории если она не существует
        
        Args:
            directory_path: Путь к директории
            
        Returns:
            Успешность операции
        """
        try:
            Path(directory_path).mkdir(parents=True, exist_ok=True)
            return True
        except Exception as e:
            self.logger.error(f"Directory creation error: {e}")
            return False
    
    def read_json_file(self, file_path: str, default: Any = None) -> Any:
        """
        Чтение JSON файла
        
        Args:
            file_path: Путь к файлу
            default: Значение по умолчанию при ошибке
            
        Returns:
            Распарсенные данные или значение по умолчанию
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError, IOError) as e:
            self.logger.warning(f"JSON file read error: {e}")
            return default
    
    def write_json_file(self, file_path: str, data: Any, indent: int = 2) -> bool:
        """
        Запись данных в JSON файл
        
        Args:
            file_path: Путь к файлу
            data: Данные для записи
            indent: Отступ для форматирования
            
        Returns:
            Успешность операции
        """
        try:
            # Создаем директорию если нужно
            directory = os.path.dirname(file_path)
            if directory:
                self.ensure_directory(directory)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=indent, default=str)
            return True
        except Exception as e:
            self.logger.error(f"JSON file write error: {e}")
            return False
    
    def read_csv_file(self, file_path: str, delimiter: str = ',') -> List[Dict]:
        """
        Чтение CSV файла
        
        Args:
            file_path: Путь к файлу
            delimiter: Разделитель
            
        Returns:
            Список словарей с данными
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f, delimiter=delimiter)
                return list(reader)
        except Exception as e:
            self.logger.error(f"CSV file read error: {e}")
            return []
    
    def write_csv_file(self, file_path: str, data: List[Dict], 
                      fieldnames: Optional[List[str]] = None) -> bool:
        """
        Запись данных в CSV файл
        
        Args:
            file_path: Путь к файлу
            data: Данные для записи
            fieldnames: Заголовки столбцов
            
        Returns:
            Успешность операции
        """
        try:
            if not data:
                return False
            
            # Создаем директорию если нужно
            directory = os.path.dirname(file_path)
            if directory:
                self.ensure_directory(directory)
            
            if fieldnames is None:
                fieldnames = list(data[0].keys())
            
            with open(file_path, 'w', encoding='utf-8', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(data)
            
            return True
        except Exception as e:
            self.logger.error(f"CSV file write error: {e}")
            return False
    
    def read_text_file(self, file_path: str, default: str = "") -> str:
        """
        Чтение текстового файла
        
        Args:
            file_path: Путь к файлу
            default: Значение по умолчанию при ошибке
            
        Returns:
            Содержимое файла
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            self.logger.warning(f"Text file read error: {e}")
            return default
    
    def write_text_file(self, file_path: str, content: str) -> bool:
        """
        Запись текста в файл
        
        Args:
            file_path: Путь к файлу
            content: Текст для записи
            
        Returns:
            Успешность операции
        """
        try:
            # Создаем директорию если нужно
            directory = os.path.dirname(file_path)
            if directory:
                self.ensure_directory(directory)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        except Exception as e:
            self.logger.error(f"Text file write error: {e}")
            return False
    
    def get_file_info(self, file_path: str) -> Optional[Dict[str, Any]]:
        """
        Получение информации о файле
        
        Args:
            file_path: Путь к файлу
            
        Returns:
            Информация о файле или None
        """
        try:
            stat = os.stat(file_path)
            return {
                'path': file_path,
                'size': stat.st_size,
                'created': stat.st_ctime,
                'modified': stat.st_mtime,
                'is_file': os.path.isfile(file_path),
                'is_dir': os.path.isdir(file_path),
                'extension': os.path.splitext(file_path)[1]
            }
        except Exception as e:
            self.logger.error(f"File info error: {e}")
            return None
    
    def list_files(self, directory: str, pattern: str = "*", 
                  recursive: bool = False) -> List[str]:
        """
        Список файлов в директории
        
        Args:
            directory: Путь к директории
            pattern: Паттерн для поиска
            recursive: Рекурсивный поиск
            
        Returns:
            Список путей к файлам
        """
        try:
            path = Path(directory)
            if recursive:
                files = list(path.rglob(pattern))
            else:
                files = list(path.glob(pattern))
            
            return [str(f) for f in files if f.is_file()]
        except Exception as e:
            self.logger.error(f"File listing error: {e}")
            return []
    
    def safe_delete(self, file_path: str) -> bool:
        """
        Безопасное удаление файла
        
        Args:
            file_path: Путь к файлу
            
        Returns:
            Успешность операции
        """
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
            return True
        except Exception as e:
            self.logger.error(f"File deletion error: {e}")
            return False
    
    def get_file_size(self, file_path: str) -> int:
        """
        Получение размера файла в байтах
        
        Args:
            file_path: Путь к файлу
            
        Returns:
            Размер файла в байтах
        """
        try:
            return os.path.getsize(file_path)
        except Exception as e:
            self.logger.error(f"File size error: {e}")
            return 0
    
    def is_valid_path(self, path: str) -> bool:
        """
        Проверка валидности пути
        
        Args:
            path: Путь для проверки
            
        Returns:
            Результат проверки
        """
        try:
            Path(path)
            return True
        except Exception:
            return False