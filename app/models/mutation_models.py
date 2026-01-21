from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum
from ..models.gene_models import ProteinDomain

class MutationType(Enum):
    SUBSTITUTION = "substitution"
    INSERTION = "insertion"
    DELETION = "deletion"

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
    inserted_sequence: str
    start_position: int
    end_position: int

@dataclass
class DeletionMutation(Mutation):
    """Удаление нуклеотидов"""
    start_position: int
    end_position: int

@dataclass
class BaseMutationResult:
    """Базовый результат мутации"""
    pass

@dataclass
class SubstitutionResult(BaseMutationResult):
    """Результат замены нуклеотида"""
    new_aminoacid: str

    def to_dict(self):
        return {
            "new_aminoacid" : self.new_aminoacid,    
        }

@dataclass
class InsertionResult(BaseMutationResult):
    """Результат вставки нуклеотида"""
    new_domain: ProteinDomain
    different_position: int
    stop_codon_position: int

    def to_dict(self):
        return {
            "new_domain" : self.new_domain.to_dict(),
            "different_position" : self.different_position,
            "stop_codon_position" : self.stop_codon_position,
        }

@dataclass
class DeletionResult(BaseMutationResult):
    """Результат удаления нуклеотида"""
    new_domain: ProteinDomain
    different_position: int
    stop_codon_position: int

    def to_dict(self):
        return {
            "new_domain" : self.new_domain.to_dict(),
            "different_position" : self.different_position,
            "stop_codon_position" : self.stop_codon_position,
        }