from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum
from ..models.gene_models import ProteinDomain

class MutationType(Enum):
    SUBSTITUTION = "substitution"
    INSERTION = "insertion"
    DELETION = "deletion"
    EXON_DELETION = "exon_deletion"

@dataclass
class Mutation:
    """Базовая модель мутации"""
    mutation_type: MutationType

@dataclass
class SubstitutionMutation(Mutation):
    """Замена одного нуклеотида"""
    new_nucleotide: str
    position_nucleotide: int

@dataclass
class InsertionMutation(Mutation):
    """Вставка нуклеотидов"""
    inserted_sequence: str = ""
    start_position: int
    end_position: int

@dataclass
class DeletionMutation(Mutation):
    """Удаление нуклеотидов"""
    start_position: int
    end_position: int

@dataclass
class ExonDeletionMutation(Mutation):
    """Удаление экзона"""
    number_exon: int

@dataclass
class BaseMutationResult:
    """Базовый результат мутации"""
    pass

@dataclass
class SubstitutionResult(BaseMutationResult):
    """Результат замены нуклеотида"""
    new_aminoacid: str

@dataclass
class InsertionResult(BaseMutationResult):
    """Результат вставки нуклеотида"""
    new_domain: ProteinDomain
    different_position: int
    stop_codon_position: int

@dataclass
class DeletionResult(BaseMutationResult):
    """Результат удаления нуклеотида"""
    new_domain: ProteinDomain
    different_position: int
    stop_codon_position: int

@dataclass
class ExonDeletionResult(BaseMutationResult):
    """Результат удаления экзона"""
    new_domain: ProteinDomain
    different_position: int
    stop_codon_position: int