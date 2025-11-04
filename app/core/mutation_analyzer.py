import logging
from typing import List, Dict, Optional, Tuple
from ..models.gene_models import Gene, Exon
from ..models.mutation_models import Mutation, MutationType
from .biopython_utils import BiopythonUtils
from .sequence_utils import SequenceUtils

class MutationAnalyzer:
    """
    Анализатор генетических мутаций
    """
    
    def __init__(self):
        self.bp_utils = BiopythonUtils()
        self.seq_utils = SequenceUtils()
        self.logger = logging.getLogger(__name__)
    
    def analyze_mutation_impact(self, gene: Gene, mutation: Mutation) -> Dict[str, any]:
        """
        Анализ воздействия мутации на ген и белок
        
        Args:
            gene: Объект гена
            mutation: Объект мутации
            
        Returns:
            Результаты анализа воздействия
        """
        try:
            self.logger.info(f"Analyzing mutation impact: {mutation.type.value}")
            
            # Базовый анализ
            impact_analysis = {
                'mutation_type': mutation.type.value,
                'position': mutation.position,
                'nucleotide_changes': self._analyze_nucleotide_changes(gene, mutation),
                'amino_acid_changes': self._analyze_amino_acid_changes(gene, mutation),
                'structural_impact': self._analyze_structural_impact(gene, mutation),
                'functional_impact': self._analyze_functional_impact(gene, mutation)
            }
            
            # Оценка общего воздействия
            impact_analysis['overall_impact'] = self._assess_overall_impact(impact_analysis)
            
            return impact_analysis
            
        except Exception as e:
            self.logger.error(f"Mutation impact analysis error: {e}")
            return {}
    
    def predict_conservation(self, mutation: Mutation, homolog_sequences: List[str]) -> float:
        """
        Предсказание консервативности позиции мутации
        
        Args:
            mutation: Мутация для анализа
            homolog_sequences: Последовательности гомологов
            
        Returns:
            Оценка консервативности (0-1)
        """
        try:
            if not homolog_sequences:
                return 0.5  # Нейтральная оценка при отсутствии данных
            
            conservation_scores = []
            for seq in homolog_sequences:
                if len(seq) > mutation.position:
                    # Простая эвристика: насколько часто встречается аминокислота
                    aa_at_position = seq[mutation.position]
                    frequency = sum(1 for s in homolog_sequences 
                                  if len(s) > mutation.position and s[mutation.position] == aa_at_position)
                    conservation_scores.append(frequency / len(homolog_sequences))
            
            return sum(conservation_scores) / len(conservation_scores) if conservation_scores else 0.5
            
        except Exception as e:
            self.logger.error(f"Conservation prediction error: {e}")
            return 0.5
    
    def _analyze_nucleotide_changes(self, gene: Gene, mutation: Mutation) -> Dict[str, any]:
        """Анализ изменений на нуклеотидном уровне"""
        try:
            full_sequence = gene.full_sequence
            
            if mutation.position >= len(full_sequence):
                return {'error': 'Position out of sequence range'}
            
            original_base = full_sequence[mutation.position]
            
            changes = {
                'original_base': original_base,
                'position': mutation.position,
                'exon_number': self._find_exon_number(gene, mutation.position),
                'codon_position': self._get_codon_position(mutation.position)
            }
            
            if mutation.type == MutationType.SUBSTITUTION:
                changes.update({
                    'new_base': mutation.new_sequence,
                    'transition': self._is_transition(original_base, mutation.new_sequence),
                    'codon_change': self._analyze_codon_change(gene, mutation)
                })
            
            elif mutation.type == MutationType.DELETION:
                deleted_bases = full_sequence[mutation.position:mutation.position + mutation.length]
                changes.update({
                    'deleted_bases': deleted_bases,
                    'deletion_length': mutation.length,
                    'is_frameshift': mutation.length % 3 != 0
                })
            
            elif mutation.type == MutationType.INSERTION:
                changes.update({
                    'inserted_sequence': mutation.new_sequence,
                    'insertion_length': len(mutation.new_sequence),
                    'is_frameshift': len(mutation.new_sequence) % 3 != 0
                })
            
            return changes
            
        except Exception as e:
            self.logger.error(f"Nucleotide changes analysis error: {e}")
            return {'error': str(e)}
    
    def _analyze_amino_acid_changes(self, gene: Gene, mutation: Mutation) -> Dict[str, any]:
        """Анализ изменений на аминокислотном уровне"""
        try:
            original_protein = gene.protein.sequence
            modified_sequence = self._apply_mutation_to_sequence(gene.full_sequence, mutation)
            modified_protein = self.bp_utils.translate_sequence(modified_sequence)
            
            changes = {
                'original_protein_length': len(original_protein),
                'modified_protein_length': len(modified_protein),
                'length_change': len(modified_protein) - len(original_protein),
                'changes': []
            }
            
            # Находим конкретные изменения аминокислот
            min_len = min(len(original_protein), len(modified_protein))
            for i in range(min_len):
                if original_protein[i] != modified_protein[i]:
                    changes['changes'].append({
                        'position': i,
                        'original': original_protein[i],
                        'new': modified_protein[i],
                        'type': 'substitution'
                    })
            
            # Обработка изменений длины
            if len(original_protein) > len(modified_protein):
                for i in range(len(modified_protein), len(original_protein)):
                    changes['changes'].append({
                        'position': i,
                        'original': original_protein[i],
                        'new': '-',
                        'type': 'deletion'
                    })
            elif len(original_protein) < len(modified_protein):
                for i in range(len(original_protein), len(modified_protein)):
                    changes['changes'].append({
                        'position': i,
                        'original': '-',
                        'new': modified_protein[i],
                        'type': 'insertion'
                    })
            
            return changes
            
        except Exception as e:
            self.logger.error(f"Amino acid changes analysis error: {e}")
            return {'error': str(e)}
    
    def _analyze_structural_impact(self, gene: Gene, mutation: Mutation) -> Dict[str, any]:
        """Анализ структурного воздействия"""
        try:
            original_protein = gene.protein.sequence
            modified_sequence = self._apply_mutation_to_sequence(gene.full_sequence, mutation)
            modified_protein = self.bp_utils.translate_sequence(modified_sequence)
            
            # Анализ вторичной структуры
            original_ss = self.bp_utils.predict_secondary_structure(original_protein)
            modified_ss = self.bp_utils.predict_secondary_structure(modified_protein)
            
            # Анализ гидропатии
            original_hydropathy = self.seq_utils.calculate_hydropathy(original_protein)
            modified_hydropathy = self.seq_utils.calculate_hydropathy(modified_protein)
            
            return {
                'secondary_structure_changes': self._compare_secondary_structures(original_ss, modified_ss),
                'hydropathy_changes': self._compare_hydropathy(original_hydropathy, modified_hydropathy),
                'molecular_weight_change': self._calculate_mw_change(original_protein, modified_protein)
            }
            
        except Exception as e:
            self.logger.error(f"Structural impact analysis error: {e}")
            return {'error': str(e)}
    
    def _analyze_functional_impact(self, gene: Gene, mutation: Mutation) -> Dict[str, any]:
        """Анализ функционального воздействия"""
        try:
            impact = {
                'domain_impact': self._analyze_domain_impact(gene, mutation),
                'stop_codon_introduction': self._check_stop_codon_introduction(gene, mutation),
                'splice_site_impact': self._analyze_splice_site_impact(gene, mutation)
            }
            
            return impact
            
        except Exception as e:
            self.logger.error(f"Functional impact analysis error: {e}")
            return {'error': str(e)}
    
    def _apply_mutation_to_sequence(self, sequence: str, mutation: Mutation) -> str:
        """Применить мутацию к последовательности"""
        if mutation.type == MutationType.SUBSTITUTION:
            return (sequence[:mutation.position] + 
                   mutation.new_sequence + 
                   sequence[mutation.position + 1:])
        
        elif mutation.type == MutationType.DELETION:
            return (sequence[:mutation.position] + 
                   sequence[mutation.position + mutation.length:])
        
        elif mutation.type == MutationType.INSERTION:
            return (sequence[:mutation.position] + 
                   mutation.new_sequence + 
                   sequence[mutation.position:])
        
        return sequence
    
    def _find_exon_number(self, gene: Gene, position: int) -> Optional[int]:
        """Найти номер экзона по позиции"""
        for exon in gene.exons:
            if exon.start_position <= position <= exon.end_position:
                return exon.number
        return None
    
    def _get_codon_position(self, nucleotide_position: int) -> int:
        """Получить позицию в кодоне (0, 1, 2)"""
        return nucleotide_position % 3
    
    def _is_transition(self, base1: str, base2: str) -> bool:
        """Проверить, является ли замена транзицией"""
        transitions = [('A', 'G'), ('G', 'A'), ('C', 'T'), ('T', 'C')]
        return (base1, base2) in transitions
    
    def _analyze_codon_change(self, gene: Gene, mutation: Mutation) -> Dict[str, any]:
        """Анализ изменения кодона"""
        try:
            sequence = gene.full_sequence
            codon_start = (mutation.position // 3) * 3
            original_codon = sequence[codon_start:codon_start + 3]
            
            modified_sequence = self._apply_mutation_to_sequence(sequence, mutation)
            modified_codon = modified_sequence[codon_start:codon_start + 3]
            
            original_aa = self.bp_utils.translate_sequence(original_codon)
            modified_aa = self.bp_utils.translate_sequence(modified_codon)
            
            return {
                'original_codon': original_codon,
                'modified_codon': modified_codon,
                'original_aa': original_aa,
                'modified_aa': modified_aa,
                'is_silent': original_aa == modified_aa,
                'is_nonsense': modified_aa == '*',
                'is_missense': original_aa != modified_aa and modified_aa != '*'
            }
            
        except Exception as e:
            self.logger.error(f"Codon change analysis error: {e}")
            return {}
    
    # Дополнительные вспомогательные методы...
    def _compare_secondary_structures(self, ss1: Dict, ss2: Dict) -> Dict[str, float]:
        """Сравнить вторичные структуры"""
        changes = {}
        for key in ss1:
            if key in ss2:
                changes[key] = round(abs(ss1[key] - ss2[key]), 2)
        return changes
    
    def _compare_hydropathy(self, hp1: List[float], hp2: List[float]) -> Dict[str, float]:
        """Сравнить профили гидропатии"""
        if not hp1 or not hp2:
            return {}
        
        min_len = min(len(hp1), len(hp2))
        differences = [abs(hp1[i] - hp2[i]) for i in range(min_len)]
        
        return {
            'max_difference': max(differences) if differences else 0,
            'average_difference': sum(differences) / len(differences) if differences else 0
        }
    
    def _calculate_mw_change(self, seq1: str, seq2: str) -> float:
        """Рассчитать изменение молекулярной массы"""
        mw1 = self.bp_utils.calculate_molecular_weight(seq1)
        mw2 = self.bp_utils.calculate_molecular_weight(seq2)
        return mw2 - mw1
    
    def _analyze_domain_impact(self, gene: Gene, mutation: Mutation) -> List[Dict]:
        """Анализ воздействия на домены"""
        domain_impacts = []
        
        modified_sequence = self._apply_mutation_to_sequence(gene.full_sequence, mutation)
        modified_protein = self.bp_utils.translate_sequence(modified_sequence)
        
        for domain in gene.protein.domains:
            # Проверяем, попадает ли мутация в домен
            aa_position = mutation.position // 3
            if domain.start <= aa_position <= domain.end:
                domain_impacts.append({
                    'domain_name': domain.name,
                    'domain_type': domain.type,
                    'affected': True,
                    'change_position': aa_position - domain.start
                })
        
        return domain_impacts
    
    def _check_stop_codon_introduction(self, gene: Gene, mutation: Mutation) -> bool:
        """Проверить введение стоп-кодона"""
        modified_sequence = self._apply_mutation_to_sequence(gene.full_sequence, mutation)
        stops = self.bp_utils.find_stop_codons(modified_sequence)
        original_stops = self.bp_utils.find_stop_codons(gene.full_sequence)
        
        # Проверяем, появились ли новые стоп-кодоны
        return any(stop not in original_stops for stop in stops)
    
    def _analyze_splice_site_impact(self, gene: Gene, mutation: Mutation) -> Dict[str, any]:
        """Анализ воздействия на сайты сплайсинга"""
        # Упрощенный анализ - в реальности нужен более сложный алгоритм
        return {
            'potential_impact': 'low',  # low, medium, high
            'affected_sites': []
        }
    
    def _assess_overall_impact(self, impact_analysis: Dict) -> str:
        """Оценить общее воздействие мутации"""
        # Упрощенная эвристика
        if impact_analysis.get('amino_acid_changes', {}).get('length_change', 0) != 0:
            return 'high'
        
        if impact_analysis.get('functional_impact', {}).get('stop_codon_introduction'):
            return 'high'
        
        aa_changes = impact_analysis.get('amino_acid_changes', {}).get('changes', [])
        if any(change.get('type') != 'substitution' for change in aa_changes):
            return 'high'
        
        if len(aa_changes) > 0:
            return 'medium'
        
        return 'low'