import logging
from typing import Dict, List, Any, Optional
from ..models.gene_models import Gene, Exon, ProteinDomain
from ..models.mutation_models import MutationResult
from ..models.analysis_models import VisualizationConfig

class DataService:
    """
    Сервис для подготовки и преобразования данных для фронтенда
    Не занимается визуализацией, только подготавливает данные в удобном формате
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.default_config = VisualizationConfig()
    
    def prepare_gene_data_for_frontend(self, gene: Gene) -> Dict[str, Any]:
        """
        Подготовить данные гена для отображения во фронтенде
        """
        return {
            'gene_info': {
                'id': gene.id,
                'name': gene.name,
                'species': gene.species,
                'chromosome': gene.chromosome,
                'strand': gene.strand.value,
                'transcript_id': gene.transcript_id
            },
            'protein_info': {
                'id': gene.protein.id,
                'name': gene.protein.name,
                'sequence': gene.protein.sequence,
                'length': gene.protein.length,
                'molecular_weight': gene.protein.molecular_weight
            },
            'exons': self._prepare_exons_data(gene.exons),
            'domains': self._prepare_domains_data(gene.protein.domains),
            'statistics': {
                'exons_count': len(gene.exons),
                'protein_length': gene.protein.length,
                'domains_count': len(gene.protein.domains),
                'total_sequence_length': len(gene.full_sequence)
            }
        }
    
    def prepare_mutation_result_for_frontend(self, result: MutationResult) -> Dict[str, Any]:
        """
        Подготовить результат анализа мутации для фронтенда
        """
        return {
            'mutation': result.mutation.to_dict(),
            'impact_assessment': {
                'severity': result.impact_severity.value,
                'is_frameshift': result.is_frameshift,
                'has_structural_changes': result.has_structural_changes,
                'protein_length_change': result.protein_length_change,
                'stop_codon_position': result.stop_codon_position
            },
            'sequence_changes': {
                'original_protein': result.original_gene.protein.sequence,
                'modified_protein': result.modified_gene.protein.sequence,
                'amino_acid_changes': [
                    self._prepare_amino_acid_change(change) 
                    for change in result.amino_acid_changes
                ]
            },
            'domain_changes': result.domain_changes,
            'visualization_data': {
                'exons_comparison': self._prepare_exons_comparison(
                    result.original_gene.exons, 
                    result.modified_gene.exons
                ),
                'domains_comparison': self._prepare_domains_comparison(
                    result.original_gene.protein.domains,
                    result.modified_gene.protein.domains
                ),
                'highlight_regions': self._prepare_highlight_regions(result)
            }
        }
    
    def _prepare_exons_data(self, exons: List[Exon]) -> List[Dict]:
        """Подготовить данные экзонов для фронтенда"""
        return [
            {
                'number': exon.number,
                'sequence': exon.sequence,
                'start_position': exon.start_position,
                'end_position': exon.end_position,
                'length': exon.length,
                'is_modified': exon.is_modified,
                'modifications': exon.modifications
            }
            for exon in exons
        ]
    
    def _prepare_domains_data(self, domains: List[ProteinDomain]) -> List[Dict]:
        """Подготовить данные доменов для фронтенда"""
        return [
            {
                'name': domain.name,
                'start': domain.start,
                'end': domain.end,
                'sequence': domain.sequence,
                'type': domain.type,
                'description': domain.description,
                'is_modified': domain.is_modified,
                'changes': domain.changes,
                'length': domain.length
            }
            for domain in domains
        ]
    
    def _prepare_amino_acid_change(self, change) -> Dict:
        """Подготовить данные об изменении аминокислоты"""
        return {
            'position': change.position,
            'original': change.original,
            'new': change.new,
            'type': change.type,
            'is_stop_codon': change.is_stop_codon,
            'is_frameshift': change.is_frameshift
        }
    
    def _prepare_exons_comparison(self, original_exons: List[Exon], modified_exons: List[Exon]) -> Dict:
        """Подготовить данные для сравнения экзонов"""
        return {
            'original': self._prepare_exons_data(original_exons),
            'modified': self._prepare_exons_data(modified_exons),
            'changes': self._find_exon_changes(original_exons, modified_exons)
        }
    
    def _prepare_domains_comparison(self, original_domains: List[ProteinDomain], modified_domains: List[ProteinDomain]) -> Dict:
        """Подготовить данные для сравнения доменов"""
        return {
            'original': self._prepare_domains_data(original_domains),
            'modified': self._prepare_domains_data(modified_domains),
            'changes': self._find_domain_changes(original_domains, modified_domains)
        }
    
    def _prepare_highlight_regions(self, result: MutationResult) -> Dict:
        """Подготовить регионы для подсветки во фронтенде"""
        highlights = {
            'nucleotide_level': [],
            'amino_acid_level': [],
            'domain_level': []
        }
        
        # Подсветка на нуклеотидном уровне
        mutation = result.mutation
        if mutation.type.value == 'substitution':
            highlights['nucleotide_level'].append({
                'type': 'substitution',
                'position': mutation.position,
                'length': 1,
                'color': 'red'
            })
        elif mutation.type.value == 'deletion':
            highlights['nucleotide_level'].append({
                'type': 'deletion',
                'position': mutation.position,
                'length': mutation.length,
                'color': 'red'
            })
        elif mutation.type.value == 'insertion':
            highlights['nucleotide_level'].append({
                'type': 'insertion',
                'position': mutation.position,
                'length': len(mutation.new_sequence),
                'color': 'blue'
            })
        
        # Подсветка на аминокислотном уровне
        for change in result.amino_acid_changes:
            highlights['amino_acid_level'].append({
                'position': change.position,
                'type': change.type,
                'color': 'red' if change.type in ['substitution', 'deletion'] else 'blue'
            })
        
        # Подсветка на доменном уровне
        for domain_change in result.domain_changes:
            highlights['domain_level'].append({
                'domain_name': domain_change['domain_name'],
                'changes_count': domain_change['changes_count'],
                'color': 'orange'
            })
        
        return highlights
    
    def _find_exon_changes(self, original: List[Exon], modified: List[Exon]) -> List[Dict]:
        """Найти изменения между экзонами"""
        changes = []
        
        # Проверяем изменения в количестве экзонов
        if len(original) != len(modified):
            changes.append({
                'type': 'exon_count_change',
                'original_count': len(original),
                'modified_count': len(modified)
            })
        
        # Проверяем изменения в последовательностях экзонов
        for orig_exon, mod_exon in zip(original, modified):
            if orig_exon.sequence != mod_exon.sequence:
                changes.append({
                    'type': 'sequence_change',
                    'exon_number': orig_exon.number,
                    'original_length': len(orig_exon.sequence),
                    'modified_length': len(mod_exon.sequence)
                })
        
        return changes
    
    def _find_domain_changes(self, original: List[ProteinDomain], modified: List[ProteinDomain]) -> List[Dict]:
        """Найти изменения между доменами"""
        changes = []
        
        # Упрощенная проверка - в реальности нужно более сложное сравнение
        if len(original) != len(modified):
            changes.append({
                'type': 'domain_count_change',
                'original_count': len(original),
                'modified_count': len(modified)
            })
        
        return changes
    
    def prepare_sequence_alignment_data(self, original_seq: str, modified_seq: str) -> Dict:
        """
        Подготовить данные для выравнивания последовательностей во фронтенде
        """
        # Находим различия между последовательностями
        differences = []
        min_len = min(len(original_seq), len(modified_seq))
        
        for i in range(min_len):
            if original_seq[i] != modified_seq[i]:
                differences.append({
                    'position': i,
                    'original': original_seq[i],
                    'modified': modified_seq[i]
                })
        
        # Обрабатываем разные длины
        length_diff = len(modified_seq) - len(original_seq)
        
        return {
            'original_sequence': original_seq,
            'modified_sequence': modified_seq,
            'differences': differences,
            'length_difference': length_diff,
            'identity_percentage': self._calculate_identity(original_seq, modified_seq)
        }
    
    def _calculate_identity(self, seq1: str, seq2: str) -> float:
        """Рассчитать процент идентичности между последовательностями"""
        if not seq1 or not seq2:
            return 0.0
        
        min_len = min(len(seq1), len(seq2))
        if min_len == 0:
            return 0.0
        
        matches = sum(1 for i in range(min_len) if seq1[i] == seq2[i])
        return (matches / min_len) * 100
    
    def prepare_export_data(self, gene: Gene, mutation_results: List[MutationResult]) -> Dict:
        """
        Подготовить данные для экспорта
        """
        return {
            'gene': self.prepare_gene_data_for_frontend(gene),
            'mutations': [
                self.prepare_mutation_result_for_frontend(result)
                for result in mutation_results
            ],
            'summary': {
                'total_mutations': len(mutation_results),
                'high_impact_count': sum(1 for r in mutation_results if r.impact_severity.value == 'high'),
                'moderate_impact_count': sum(1 for r in mutation_results if r.impact_severity.value == 'moderate'),
                'low_impact_count': sum(1 for r in mutation_results if r.impact_severity.value == 'low')
            }
        }