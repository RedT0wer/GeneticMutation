import logging
from typing import List, Dict, Optional, Tuple
from Bio.Seq import Seq
from Bio.Data import CodonTable
from Bio.SeqUtils import molecular_weight
from Bio.Align import PairwiseAligner

class BiopythonUtils:
    """
    Утилиты на основе Biopython для работы с биологическими последовательностями
    """
    
    def __init__(self):
        self.standard_table = CodonTable.standard_dna_table
        self.logger = logging.getLogger(__name__)
    
    def translate_sequence(self, nucleotide_sequence: str, to_stop: bool = True) -> str:
        """
        Трансляция нуклеотидной последовательности в аминокислотную
        
        Args:
            nucleotide_sequence: Нуклеотидная последовательность
            to_stop: Останавливаться на стоп-кодоне
            
        Returns:
            Аминокислотная последовательность
        """
        try:
            if not nucleotide_sequence:
                return ""
            
            seq = Seq(nucleotide_sequence.upper())
            protein_seq = seq.translate(to_stop=to_stop)
            return str(protein_seq)
            
        except Exception as e:
            self.logger.error(f"Translation error: {e}")
            return ""
    
    def find_stop_codons(self, nucleotide_sequence: str) -> List[int]:
        """
        Найти позиции стоп-кодонов в нуклеотидной последовательности
        
        Args:
            nucleotide_sequence: Нуклеотидная последовательность
            
        Returns:
            Список позиций (0-based) начала стоп-кодонов
        """
        stops = []
        try:
            if not nucleotide_sequence or len(nucleotide_sequence) < 3:
                return stops
            
            # Проверяем каждую рамку считывания
            for frame in [0, 1, 2]:
                for i in range(frame, len(nucleotide_sequence) - 2, 3):
                    codon = nucleotide_sequence[i:i+3].upper()
                    if len(codon) == 3 and self._is_stop_codon(codon):
                        stops.append(i)
            
            return sorted(stops)
            
        except Exception as e:
            self.logger.error(f"Stop codon search error: {e}")
            return []
    
    def calculate_molecular_weight(self, protein_sequence: str, monoisotopic: bool = False) -> float:
        """
        Расчет молекулярной массы белка
        
        Args:
            protein_sequence: Аминокислотная последовательность
            monoisotopic: Использовать моноизотопные массы
            
        Returns:
            Молекулярная масса в Да
        """
        try:
            if not protein_sequence:
                return 0.0
            
            # Добавляем воду (H2O) для полной молекулы
            weight = molecular_weight(protein_sequence, seq_type='protein', monoisotopic=monoisotopic)
            return round(weight, 2) if weight else 0.0
            
        except Exception as e:
            self.logger.error(f"Molecular weight calculation error: {e}")
            return 0.0
    
    def get_codon_info(self, nucleotide_triplet: str) -> Dict[str, str]:
        """
        Получить информацию о кодоне
        
        Args:
            nucleotide_triplet: Три нуклеотида
            
        Returns:
            Информация о кодоне и соответствующей аминокислоте
        """
        try:
            if len(nucleotide_triplet) != 3:
                return {}
            
            seq = Seq(nucleotide_triplet.upper())
            amino_acid = str(seq.translate())
            
            return {
                'codon': nucleotide_triplet.upper(),
                'amino_acid': amino_acid,
                'is_stop_codon': amino_acid == '*',
                'is_start_codon': nucleotide_triplet.upper() in ['ATG', 'CTG', 'TTG']
            }
            
        except Exception as e:
            self.logger.error(f"Codon info error: {e}")
            return {}
    
    def reverse_translate(self, amino_acid: str, codon_usage: Dict[str, List[str]] = None) -> List[str]:
        """
        Обратная транскрипция аминокислоты в возможные кодоны
        
        Args:
            amino_acid: Аминокислота (однобуквенный код)
            codon_usage: Предпочтения кодонов по видам
            
        Returns:
            Список возможных кодонов
        """
        try:
            if amino_acid == '*':
                return ['TAA', 'TAG', 'TGA']  # Стоп-кодоны
            
            # Базовая таблица кодонов
            codon_map = {
                'A': ['GCT', 'GCC', 'GCA', 'GCG'],
                'R': ['CGT', 'CGC', 'CGA', 'CGG', 'AGA', 'AGG'],
                'N': ['AAT', 'AAC'],
                'D': ['GAT', 'GAC'],
                'C': ['TGT', 'TGC'],
                'Q': ['CAA', 'CAG'],
                'E': ['GAA', 'GAG'],
                'G': ['GGT', 'GGC', 'GGA', 'GGG'],
                'H': ['CAT', 'CAC'],
                'I': ['ATT', 'ATC', 'ATA'],
                'L': ['TTA', 'TTG', 'CTT', 'CTC', 'CTA', 'CTG'],
                'K': ['AAA', 'AAG'],
                'M': ['ATG'],
                'F': ['TTT', 'TTC'],
                'P': ['CCT', 'CCC', 'CCA', 'CCG'],
                'S': ['TCT', 'TCC', 'TCA', 'TCG', 'AGT', 'AGC'],
                'T': ['ACT', 'ACC', 'ACA', 'ACG'],
                'W': ['TGG'],
                'Y': ['TAT', 'TAC'],
                'V': ['GTT', 'GTC', 'GTA', 'GTG']
            }
            
            return codon_map.get(amino_acid.upper(), [])
            
        except Exception as e:
            self.logger.error(f"Reverse translation error: {e}")
            return []
    
    def calculate_gc_content(self, sequence: str) -> float:
        """
        Расчет GC-состава последовательности
        
        Args:
            sequence: Нуклеотидная последовательность
            
        Returns:
            Процент GC-оснований
        """
        try:
            if not sequence:
                return 0.0
            
            sequence = sequence.upper()
            gc_count = sequence.count('G') + sequence.count('C')
            total_length = len(sequence)
            
            return round((gc_count / total_length) * 100, 2) if total_length > 0 else 0.0
            
        except Exception as e:
            self.logger.error(f"GC content calculation error: {e}")
            return 0.0
    
    def pairwise_alignment(self, seq1: str, seq2: str, mode: str = 'global') -> Dict[str, any]:
        """
        Попарное выравнивание двух последовательностей
        
        Args:
            seq1: Первая последовательность
            seq2: Вторая последовательность
            mode: Тип выравнивания ('global', 'local')
            
        Returns:
            Результаты выравнивания
        """
        try:
            if not seq1 or not seq2:
                return {}
            
            aligner = PairwiseAligner()
            aligner.mode = mode
            alignments = aligner.align(seq1, seq2)
            
            if not alignments:
                return {}
            
            best_alignment = alignments[0]
            
            return {
                'alignment': str(best_alignment),
                'score': best_alignment.score,
                'identity': self._calculate_identity(seq1, seq2),
                'length': len(seq1)
            }
            
        except Exception as e:
            self.logger.error(f"Pairwise alignment error: {e}")
            return {}
    
    def predict_secondary_structure(self, protein_sequence: str) -> Dict[str, float]:
        """
        Простое предсказание вторичной структуры на основе состава аминокислот
        
        Args:
            protein_sequence: Аминокислотная последовательность
            
        Returns:
            Вероятности различных структурных элементов
        """
        try:
            if not protein_sequence:
                return {}
            
            # Упрощенный алгоритм на основе предпочтений аминокислот
            alpha_helix_favoring = 'ALEKMQRFVIW'
            beta_sheet_favoring = 'VITYFWC'
            turn_favoring = 'PGNDS'
            
            alpha_count = sum(1 for aa in protein_sequence if aa in alpha_helix_favoring)
            beta_count = sum(1 for aa in protein_sequence if aa in beta_sheet_favoring)
            turn_count = sum(1 for aa in protein_sequence if aa in turn_favoring)
            
            total = len(protein_sequence)
            
            return {
                'alpha_helix': round(alpha_count / total * 100, 2),
                'beta_sheet': round(beta_count / total * 100, 2),
                'turns': round(turn_count / total * 100, 2),
                'random_coil': round((total - alpha_count - beta_count - turn_count) / total * 100, 2)
            }
            
        except Exception as e:
            self.logger.error(f"Secondary structure prediction error: {e}")
            return {}
    
    def validate_sequence(self, sequence: str, sequence_type: str = 'dna') -> Dict[str, any]:
        """
        Валидация биологической последовательности
        
        Args:
            sequence: Последовательность для валидации
            sequence_type: Тип последовательности ('dna', 'rna', 'protein')
            
        Returns:
            Результаты валидации
        """
        try:
            if not sequence:
                return {'valid': False, 'errors': ['Empty sequence']}
            
            sequence = sequence.upper()
            errors = []
            
            if sequence_type == 'dna':
                valid_chars = 'ACGTN'
                invalid_chars = set(sequence) - set(valid_chars)
                if invalid_chars:
                    errors.append(f"Invalid DNA characters: {''.join(invalid_chars)}")
            
            elif sequence_type == 'rna':
                valid_chars = 'ACGUN'
                invalid_chars = set(sequence) - set(valid_chars)
                if invalid_chars:
                    errors.append(f"Invalid RNA characters: {''.join(invalid_chars)}")
            
            elif sequence_type == 'protein':
                valid_chars = 'ACDEFGHIKLMNPQRSTVWY*'
                invalid_chars = set(sequence) - set(valid_chars)
                if invalid_chars:
                    errors.append(f"Invalid protein characters: {''.join(invalid_chars)}")
            
            return {
                'valid': len(errors) == 0,
                'errors': errors,
                'length': len(sequence),
                'gc_content': self.calculate_gc_content(sequence) if sequence_type in ['dna', 'rna'] else None
            }
            
        except Exception as e:
            self.logger.error(f"Sequence validation error: {e}")
            return {'valid': False, 'errors': [f'Validation error: {e}']}
    
    def _is_stop_codon(self, codon: str) -> bool:
        """Проверить, является ли кодон стоп-кодоном"""
        return codon in ['TAA', 'TAG', 'TGA', 'TAA', 'TAG', 'TGA']
    
    def _calculate_identity(self, seq1: str, seq2: str) -> float:
        """Рассчитать процент идентичности между последовательностями"""
        if len(seq1) != len(seq2):
            return 0.0
        
        matches = sum(1 for a, b in zip(seq1, seq2) if a == b)
        return round((matches / len(seq1)) * 100, 2) if seq1 else 0.0