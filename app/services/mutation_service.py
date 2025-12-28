from typing import Dict, Type
from dataclasses import dataclass

from ..models.gene_models import Gene
from ..models.mutation_models import *
from ..services.translation_service import TranslationService


class MutationStrategy:
    """Базовый класс стратегии мутации"""
    
    def execute(self, mutation: Mutation, gene: Gene) -> BaseMutationResult:
        raise NotImplementedError()


class SubstitutionStrategy(MutationStrategy):
    """Стратегия для замены нуклеотида"""
    
    def execute(self, mutation: SubstitutionMutation, gene: Gene) -> BaseMutationResult:        
        new_nucleotide = mutation.new_nucleotide
        position_nucleotide = mutation.position_nucleotide

        gene.base_sequence.substitution_nucleotide_in_exon(position_nucleotide, new_nucleotide)
        codon = gene.base_sequence.get_codon_by_nucleotide(position_nucleotide)

        translation_service = TranslationService()

        new_aminoacid = translation_service.get_aminoacid(codon)

        return SubstitutionResult(new_aminoacid=new_aminoacid)


class InsertionStrategy(MutationStrategy):
    """Стратегия для вставки нуклеотидов"""
    
    def execute(self, mutation: InsertionMutation, gene: Gene) -> BaseMutationResult:
        # Здесь должна быть логика вставки нуклеотидов
        return InsertionResult(
            new_domain=None,  # Здесь должен быть ProteinDomain
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