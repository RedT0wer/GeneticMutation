import logging
import re
from typing import List, Dict, Tuple, Optional

class SequenceUtils:
    """
    Утилиты для работы с биологическими последовательностями
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def split_into_codons(self, sequence: str, frame: int = 0) -> List[str]:
        """
        Разбить последовательность на кодоны
        
        Args:
            sequence: Нуклеотидная последовательность
            frame: Рамка считывания (0, 1, 2)
            
        Returns:
            Список кодонов
        """
        try:
            if not sequence:
                return []
            
            sequence = sequence[frame:]
            codons = [sequence[i:i+3] for i in range(0, len(sequence) - 2, 3)]
            return [codon for codon in codons if len(codon) == 3]
            
        except Exception as e:
            self.logger.error(f"Split into codons error: {e}")
            return []
    
    def find_orf(self, sequence: str, min_length: int = 30) -> List[Dict]:
        """
        Найти открытые рамки считывания (ORF)
        
        Args:
            sequence: Нуклеотидная последовательность
            min_length: Минимальная длина ORF в нуклеотидах
            
        Returns:
            Список найденных ORF
        """
        orfs = []
        try:
            # Проверяем все 6 рамок (3 прямые, 3 обратные)
            for frame in range(3):
                orfs.extend(self._find_orf_in_frame(sequence, frame, min_length, True))
                orfs.extend(self._find_orf_in_frame(sequence, frame, min_length, False))
            
            # Сортируем по длине (по убыванию)
            orfs.sort(key=lambda x: x['length'], reverse=True)
            return orfs
            
        except Exception as e:
            self.logger.error(f"ORF finding error: {e}")
            return []
    
    def calculate_hydropathy(self, protein_sequence: str, window_size: int = 9) -> List[float]:
        """
        Расчет гидропатии по Kyte-Doolittle
        
        Args:
            protein_sequence: Аминокислотная последовательность
            window_size: Размер окна для скользящего среднего
            
        Returns:
            Список значений гидропатии
        """
        try:
            # Шкала гидропатии Kyte-Doolittle
            hydropathy_scale = {
                'A': 1.8, 'R': -4.5, 'N': -3.5, 'D': -3.5,
                'C': 2.5, 'Q': -3.5, 'E': -3.5, 'G': -0.4,
                'H': -3.2, 'I': 4.5, 'L': 3.8, 'K': -3.9,
                'M': 1.9, 'F': 2.8, 'P': -1.6, 'S': -0.8,
                'T': -0.7, 'W': -0.9, 'Y': -1.3, 'V': 4.2
            }
            
            hydropathy = []
            for i in range(len(protein_sequence)):
                aa = protein_sequence[i].upper()
                hydropathy.append(hydropathy_scale.get(aa, 0.0))
            
            # Применяем скользящее среднее
            if window_size > 1:
                smoothed = []
                for i in range(len(hydropathy)):
                    start = max(0, i - window_size // 2)
                    end = min(len(hydropathy), i + window_size // 2 + 1)
                    window_values = hydropathy[start:end]
                    smoothed.append(sum(window_values) / len(window_values))
                return smoothed
            
            return hydropathy
            
        except Exception as e:
            self.logger.error(f"Hydropathy calculation error: {e}")
            return []
    
    def find_motifs(self, sequence: str, motif: str, max_mismatches: int = 0) -> List[Dict]:
        """
        Поиск мотивов в последовательности
        
        Args:
            sequence: Последовательность для поиска
            motif: Искомый мотив (может содержать wildcards)
            max_mismatches: Максимальное количество несовпадений
            
        Returns:
            Список найденных мотивов с позициями
        """
        motifs = []
        try:
            if not sequence or not motif:
                return motifs
            
            # Простой поиск точного совпадения
            if max_mismatches == 0:
                start = 0
                while True:
                    pos = sequence.find(motif, start)
                    if pos == -1:
                        break
                    motifs.append({
                        'position': pos,
                        'sequence': motif,
                        'length': len(motif),
                        'mismatches': 0
                    })
                    start = pos + 1
            
            # Поиск с допущениями
            else:
                for i in range(len(sequence) - len(motif) + 1):
                    substring = sequence[i:i+len(motif)]
                    mismatches = self._count_mismatches(substring, motif)
                    if mismatches <= max_mismatches:
                        motifs.append({
                            'position': i,
                            'sequence': substring,
                            'length': len(motif),
                            'mismatches': mismatches
                        })
            
            return motifs
            
        except Exception as e:
            self.logger.error(f"Motif finding error: {e}")
            return []
    
    def calculate_sequence_complexity(self, sequence: str, window_size: int = 10) -> List[float]:
        """
        Расчет сложности последовательности
        
        Args:
            sequence: Последовательность для анализа
            window_size: Размер окна для расчета
            
        Returns:
            Список значений сложности
        """
        complexity = []
        try:
            for i in range(0, len(sequence) - window_size + 1):
                window = sequence[i:i+window_size]
                unique_chars = len(set(window))
                complexity.append(unique_chars / window_size)
            
            return complexity
            
        except Exception as e:
            self.logger.error(f"Sequence complexity calculation error: {e}")
            return []
    
    def reverse_complement(self, sequence: str) -> str:
        """
        Получить обратную комплементарную последовательность
        
        Args:
            sequence: Исходная последовательность
            
        Returns:
            Обратная комплементарная последовательность
        """
        try:
            complement = {'A': 'T', 'T': 'A', 'G': 'C', 'C': 'G', 'N': 'N'}
            return ''.join(complement.get(base, 'N') for base in sequence.upper()[::-1])
            
        except Exception as e:
            self.logger.error(f"Reverse complement error: {e}")
            return ""
    
    def format_sequence(self, sequence: str, line_length: int = 60) -> str:
        """
        Форматирование последовательности с переносами строк
        
        Args:
            sequence: Исходная последовательность
            line_length: Длина строки
            
        Returns:
            Отформатированная последовательность
        """
        try:
            lines = []
            for i in range(0, len(sequence), line_length):
                lines.append(sequence[i:i+line_length])
            return '\n'.join(lines)
            
        except Exception as e:
            self.logger.error(f"Sequence formatting error: {e}")
            return sequence
    
    def _find_orf_in_frame(self, sequence: str, frame: int, min_length: int, forward: bool) -> List[Dict]:
        """Найти ORF в конкретной рамке"""
        orfs = []
        try:
            if not forward:
                sequence = self.reverse_complement(sequence)
            
            codons = self.split_into_codons(sequence, frame)
            current_orf = []
            orf_start = -1
            
            for i, codon in enumerate(codons):
                if codon == 'ATG' and orf_start == -1:  # Start codon
                    orf_start = i * 3 + frame
                    current_orf = [codon]
                
                elif orf_start != -1:
                    current_orf.append(codon)
                    
                    if codon in ['TAA', 'TAG', 'TGA']:  # Stop codon
                        orf_length = len(''.join(current_orf))
                        if orf_length >= min_length:
                            orfs.append({
                                'start': orf_start,
                                'end': i * 3 + frame + 2,
                                'length': orf_length,
                                'frame': frame if forward else -frame,
                                'direction': 'forward' if forward else 'reverse',
                                'sequence': ''.join(current_orf)
                            })
                        current_orf = []
                        orf_start = -1
            
            # Обработка ORF без стоп-кодона
            if current_orf and orf_start != -1:
                orf_length = len(''.join(current_orf))
                if orf_length >= min_length:
                    orfs.append({
                        'start': orf_start,
                        'end': len(codons) * 3 + frame - 1,
                        'length': orf_length,
                        'frame': frame if forward else -frame,
                        'direction': 'forward' if forward else 'reverse',
                        'sequence': ''.join(current_orf),
                        'incomplete': True
                    })
            
            return orfs
            
        except Exception as e:
            self.logger.error(f"ORF in frame finding error: {e}")
            return []
    
    def _count_mismatches(self, seq1: str, seq2: str) -> int:
        """Подсчитать количество несовпадений между двумя последовательностями"""
        if len(seq1) != len(seq2):
            return max(len(seq1), len(seq2))
        
        mismatches = 0
        for a, b in zip(seq1, seq2):
            if a != b and b not in ['N', 'X']:  # Игнорируем wildcards
                mismatches += 1
        
        return mismatches