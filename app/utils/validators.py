import re
import logging
from typing import Dict, List, Optional, Union
from urllib.parse import urlparse

class Validators:
    """
    Валидаторы для различных типов данных
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Регулярные выражения для валидации
        self.patterns = {
            'gene_id': re.compile(r'^[A-Z0-9_.-]+$', re.IGNORECASE),
            'protein_id': re.compile(r'^[A-Z0-9_.-]+$', re.IGNORECASE),
            'species': re.compile(r'^[a-z]+$', re.IGNORECASE),
            'dna_sequence': re.compile(r'^[ACGTN]+$', re.IGNORECASE),
            'rna_sequence': re.compile(r'^[ACGUN]+$', re.IGNORECASE),
            'protein_sequence': re.compile(r'^[ACDEFGHIKLMNPQRSTVWY*]+$', re.IGNORECASE),
            'email': re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
        }
    
    def validate_gene_id(self, gene_id: str) -> Dict[str, Union[bool, List[str]]]:
        """
        Валидация ID гена
        
        Args:
            gene_id: ID гена для валидации
            
        Returns:
            Результат валидации
        """
        errors = []
        
        if not gene_id:
            errors.append("Gene ID cannot be empty")
            return {'valid': False, 'errors': errors}
        
        if len(gene_id) > 50:
            errors.append("Gene ID too long (max 50 characters)")
        
        if not self.patterns['gene_id'].match(gene_id):
            errors.append("Gene ID contains invalid characters")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors
        }
    
    def validate_protein_id(self, protein_id: str) -> Dict[str, Union[bool, List[str]]]:
        """
        Валидация ID белка
        
        Args:
            protein_id: ID белка для валидации
            
        Returns:
            Результат валидации
        """
        errors = []
        
        if not protein_id:
            errors.append("Protein ID cannot be empty")
            return {'valid': False, 'errors': errors}
        
        if len(protein_id) > 20:
            errors.append("Protein ID too long (max 20 characters)")
        
        if not self.patterns['protein_id'].match(protein_id):
            errors.append("Protein ID contains invalid characters")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors
        }
    
    def validate_sequence(self, sequence: str, sequence_type: str = 'dna') -> Dict[str, Union[bool, List[str]]]:
        """
        Валидация биологической последовательности
        
        Args:
            sequence: Последовательность для валидации
            sequence_type: Тип последовательности ('dna', 'rna', 'protein')
            
        Returns:
            Результат валидации
        """
        errors = []
        
        if not sequence:
            errors.append("Sequence cannot be empty")
            return {'valid': False, 'errors': errors}
        
        if len(sequence) < 3:
            errors.append("Sequence too short (min 3 characters)")
        
        if len(sequence) > 100000:
            errors.append("Sequence too long (max 100,000 characters)")
        
        # Проверка допустимых символов
        pattern_key = f"{sequence_type}_sequence"
        if pattern_key in self.patterns:
            if not self.patterns[pattern_key].match(sequence.upper()):
                errors.append(f"Sequence contains invalid {sequence_type.upper()} characters")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'length': len(sequence)
        }
    
    def validate_mutation_data(self, mutation_data: Dict) -> Dict[str, Union[bool, List[str]]]:
        """
        Валидация данных мутации
        
        Args:
            mutation_data: Данные мутации
            
        Returns:
            Результат валидации
        """
        errors = []
        
        required_fields = ['type', 'position']
        for field in required_fields:
            if field not in mutation_data:
                errors.append(f"Missing required field: {field}")
        
        if 'type' in mutation_data:
            valid_types = ['substitution', 'deletion', 'insertion', 'exon_deletion']
            if mutation_data['type'] not in valid_types:
                errors.append(f"Invalid mutation type: {mutation_data['type']}")
        
        if 'position' in mutation_data:
            position = mutation_data['position']
            if not isinstance(position, int) or position < 0:
                errors.append("Position must be a non-negative integer")
        
        if mutation_data.get('type') in ['substitution', 'insertion']:
            if 'new_sequence' not in mutation_data or not mutation_data['new_sequence']:
                errors.append("new_sequence is required for substitution and insertion mutations")
        
        if mutation_data.get('type') == 'deletion':
            if 'length' not in mutation_data or not isinstance(mutation_data['length'], int) or mutation_data['length'] <= 0:
                errors.append("length must be a positive integer for deletion mutations")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors
        }
    
    def validate_url(self, url: str) -> bool:
        """
        Валидация URL
        
        Args:
            url: URL для валидации
            
        Returns:
            Результат валидации
        """
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except Exception:
            return False
    
    def validate_email(self, email: str) -> bool:
        """
        Валидация email адреса
        
        Args:
            email: Email для валидации
            
        Returns:
            Результат валидации
        """
        return bool(self.patterns['email'].match(email)) if email else False
    
    def validate_number_range(self, value: Union[int, float], 
                            min_val: Optional[Union[int, float]] = None,
                            max_val: Optional[Union[int, float]] = None) -> bool:
        """
        Валидация числового диапазона
        
        Args:
            value: Значение для проверки
            min_val: Минимальное значение
            max_val: Максимальное значение
            
        Returns:
            Результат валидации
        """
        if not isinstance(value, (int, float)):
            return False
        
        if min_val is not None and value < min_val:
            return False
        
        if max_val is not None and value > max_val:
            return False
        
        return True
    
    def validate_list_length(self, items: List, min_length: int = 0, 
                           max_length: Optional[int] = None) -> bool:
        """
        Валидация длины списка
        
        Args:
            items: Список для проверки
            min_length: Минимальная длина
            max_length: Максимальная длина
            
        Returns:
            Результат валидации
        """
        if not isinstance(items, list):
            return False
        
        if len(items) < min_length:
            return False
        
        if max_length is not None and len(items) > max_length:
            return False
        
        return True
    
    def sanitize_input(self, input_string: str, max_length: int = 1000) -> str:
        """
        Санитизация пользовательского ввода
        
        Args:
            input_string: Входная строка
            max_length: Максимальная длина
            
        Returns:
            Санитизированная строка
        """
        if not input_string:
            return ""
        
        # Обрезаем до максимальной длины
        sanitized = input_string[:max_length]
        
        # Удаляем потенциально опасные символы
        sanitized = re.sub(r'[<>"\'&]', '', sanitized)
        
        # Убираем лишние пробелы
        sanitized = ' '.join(sanitized.split())
        
        return sanitized