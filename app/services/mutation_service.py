from typing import Dict, Type
from dataclasses import dataclass

from ..models.gene_models import *
from ..models.mutation_models import *
from ..services.translation_service import TranslationService


class MutationStrategy:
    """Базовый класс стратегии мутации"""
    translation_service = TranslationService()
    
    def execute(self, mutation: Mutation, gene: Gene) -> BaseMutationResult:
        raise NotImplementedError()

    def _translate_nucleotide_position(self, nucleotide_position: int, utr5: UTR) -> int:
        """"Пересчет позиции из-за смещения некодируемой области"""
        return nucleotide_position - 1 + utr5.length

    def _find_exon_by_position(self, nucleotide_position: int, gene: Gene) -> Optional[Exon]:
        """Найти экзон по позиции нуклеотида"""
        # Поиск экзона
        for exon in gene.base_sequence.exons:
            if exon.start_position <= nucleotide_position <= exon.end_position:
                return exon
        return None

    def _get_codon_by_nucleotide(self, sequence: str, nucleotide_position: int) -> str:
        """Получить кодон по номеру нуклеотида"""
        index = (nucleotide_position // 3 ) * 3
        return sequence[index:index + 3]
    

class SubstitutionStrategy(MutationStrategy):
    """Стратегия для замены нуклеотида"""
    
    def _translate_position_in_exon(self, exon: Exon, nucleotide_position: int) -> int:
        return nucleotide_position - exon.start_position

    def _substitute_nucleotide_in_exon(self, exon: Exon, position_in_exon: int, new_nucleotide: str):
        """Заменить нуклеотид в экзоне"""
        sequence = list(exon.sequence)
        sequence[position_in_exon] = new_nucleotide
        exon.sequence = ''.join(sequence)
    
    def execute(self, mutation: SubstitutionMutation, gene: Gene) -> BaseMutationResult:        
        new_nucleotide = mutation.new_nucleotide
        nucleotide_position = mutation.position_nucleotide

        global_position = self._translate_nucleotide_position(nucleotide_position, gene.base_sequence.utr5)
        exon = self._find_exon_by_position(global_position, gene)
        position_in_exon = self._translate_position_in_exon(exon, global_position)
        
        self._substitute_nucleotide_in_exon(exon, position_in_exon, new_nucleotide)
        codon = self._get_codon_by_nucleotide(gene.base_sequence.full_sequence, global_position)

        new_aminoacid = self.translation_service.get_aminoacid(codon)

        return SubstitutionResult(new_aminoacid=new_aminoacid)


class InsertionStrategy(MutationStrategy):
    """Стратегия для вставки нуклеотидов"""

    def _substitute_nucleotide_in_exon(self, sequence: str, global_position: int, inserted_sequence: str):
        """Заменить нуклеотид в экзоне"""
        sequence = list(sequence)
        sequence = sequence[:global_position + 1] + list(inserted_sequence) + sequence[global_position + 1:]
        return ''.join(sequence)
    
    def execute(self, mutation: InsertionMutation, gene: Gene) -> BaseMutationResult:
        inserted_sequence = mutation.inserted_sequence
        start_position = mutation.start_position
        end_position = mutation.end_position

        global_position = self._translate_nucleotide_position(start_position, gene.base_sequence.utr5)
        sequence = self._substitute_nucleotide_in_exon(gene.base_sequence.full_sequence, global_position, inserted_sequence)
        
        protein_sequence = self.translation_service.translation_sequence(sequence, global_position, len(sequence)-1)

        protein_domain = ProteinDomain("mutation", 0, 0, protein_sequence, "unknown")

        return InsertionResult(
            new_domain=protein_domain,
            different_position=0,
            stop_codon_position=0
        )


class DeletionStrategy(MutationStrategy):
    """Стратегия для удаления нуклеотидов"""
    
    def execute(self, mutation: DeletionMutation, gene: Gene) -> BaseMutationResult:        
        # Здесь должна быть логика удаления нуклеотидов
        return DeletionResult(
            new_domain=None,  # Здесь должен быть ProteinDomain
            different_position=0,
            stop_codon_position=0
        )


class ExonDeletionStrategy(MutationStrategy):
    """Стратегия для удаления экзона"""
    
    def execute(self, mutation: ExonDeletionMutation, gene: Gene) -> BaseMutationResult:
        # Здесь должна быть логика удаления экзона
        return ExonDeletionResult(
            new_domain=None,  # Здесь должен быть ProteinDomain
            different_position=0,
            stop_codon_position=0
        )


@dataclass
class MutationService:
    """Сервис для обработки мутаций с использованием паттерна Стратегия"""
    
    strategies: Dict[MutationType, MutationStrategy] = None
    
    def __post_init__(self):
        if self.strategies is None:
            self.strategies = {
                MutationType.SUBSTITUTION: SubstitutionStrategy(),
                MutationType.INSERTION: InsertionStrategy(),
                MutationType.DELETION : DeletionStrategy(),
                MutationType.EXON_DELETION : ExonDeletionStrategy()
            }
    
    def apply_mutation(self, mutation: Mutation, gene: Gene) -> BaseMutationResult:
        """Применить мутацию к гену"""
        strategy = self.strategies.get(mutation.mutation_type)
        
        if not strategy:
            raise ValueError(f"No strategy found for mutation type: {mutation.mutation_type}")
        
        return strategy.execute(mutation, gene)