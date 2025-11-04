from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum

class MutationType(Enum):
    SUBSTITUTION = "substitution"
    DELETION = "deletion"
    INSERTION = "insertion"
    EXON_DELETION = "exon_deletion"
    MULTIPLE = "multiple"

class ImpactSeverity(Enum):
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"

@dataclass
class AminoAcidChange:
    """Изменение аминокислоты"""
    position: int
    original: str
    new: str
    type: str  # 'substitution', 'deletion', 'insertion'
    codon_change: Optional[str] = None
    is_stop_codon: bool = False
    is_frameshift: bool = False
    
    def to_dict(self) -> Dict:
        return {
            'position': self.position,
            'original': self.original,
            'new': self.new,
            'type': self.type,
            'codon_change': self.codon_change,
            'is_stop_codon': self.is_stop_codon,
            'is_frameshift': self.is_frameshift
        }

@dataclass
class Mutation:
    """Модель мутации"""
    type: MutationType
    position: int
    length: int = 1
    original_sequence: str = ""
    new_sequence: str = ""
    exon_number: Optional[int] = None
    description: str = ""
    
    def to_dict(self) -> Dict:
        return {
            'type': self.type.value,
            'position': self.position,
            'length': self.length,
            'original_sequence': self.original_sequence,
            'new_sequence': self.new_sequence,
            'exon_number': self.exon_number,
            'description': self.description
        }

@dataclass
class MutationResult:
    """Результат анализа мутации"""
    mutation: Mutation
    original_gene: 'Gene'
    modified_gene: 'Gene'
    amino_acid_changes: List[AminoAcidChange]
    impact_severity: ImpactSeverity
    stop_codon_position: Optional[int] = None
    is_frameshift: bool = False
    domain_changes: List[Dict] = field(default_factory=list)
    visualization_data: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def has_structural_changes(self) -> bool:
        """Есть ли изменения в структуре белка"""
        return any(change.type != 'silent' for change in self.amino_acid_changes)
    
    @property
    def protein_length_change(self) -> int:
        """Изменение длины белка"""
        return len(self.modified_gene.protein.sequence) - len(self.original_gene.protein.sequence)
    
    def to_dict(self) -> Dict:
        return {
            'mutation': self.mutation.to_dict(),
            'original_gene': self.original_gene.to_dict(),
            'modified_gene': self.modified_gene.to_dict(),
            'amino_acid_changes': [change.to_dict() for change in self.amino_acid_changes],
            'impact_severity': self.impact_severity.value,
            'stop_codon_position': self.stop_codon_position,
            'is_frameshift': self.is_frameshift,
            'domain_changes': self.domain_changes,
            'visualization_data': self.visualization_data,
            'has_structural_changes': self.has_structural_changes,
            'protein_length_change': self.protein_length_change
        }