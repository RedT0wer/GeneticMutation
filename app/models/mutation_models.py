from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum

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
    deleted_sequence: str = ""
    start_position: int
    end_position: int

@dataclass
class DeletionExonMutation(Mutation):
    """Удаление экзона"""
    number_exon: int

@dataclass 
class MutationResult:
    """Результат применения мутации"""
    mutation: Mutation
    context: MutationContext
    
    # Влияние на последовательности
    original_base_sequence: str
    mutated_base_sequence: str
    original_protein_sequence: Optional[str]
    mutated_protein_sequence: Optional[str]
    
    # Эффекты
    changes_amino_acid: bool
    creates_stop_codon: bool
    affects_domain: bool
    domains_changed: List[ProteinDomain]