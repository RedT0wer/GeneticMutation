from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum

class Strand(Enum):
    FORWARD = "+"
    REVERSE = "-"

@dataclass
class Exon:
    """Модель экзона"""
    number: int
    sequence: str
    start_position: int
    end_position: int
    length: int
    is_modified: bool = False
    modifications: List[Dict] = field(default_factory=list)
    
    def __post_init__(self):
        if self.length == 0:
            self.length = len(self.sequence)
    
    def to_dict(self) -> Dict:
        return {
            'number': self.number,
            'sequence': self.sequence,
            'start_position': self.start_position,
            'end_position': self.end_position,
            'length': self.length,
            'is_modified': self.is_modified,
            'modifications': self.modifications
        }

@dataclass
class ProteinDomain:
    """Модель белкового домена"""
    name: str
    start: int
    end: int
    sequence: str
    type: str = "unknown"
    description: str = ""
    is_modified: bool = False
    changes: List[Dict] = field(default_factory=list)
    
    def __post_init__(self):
        if not self.sequence:
            self.sequence = ""
    
    @property
    def length(self) -> int:
        return self.end - self.start + 1
    
    def to_dict(self) -> Dict:
        return {
            'name': self.name,
            'start': self.start,
            'end': self.end,
            'sequence': self.sequence,
            'type': self.type,
            'description': self.description,
            'is_modified': self.is_modified,
            'changes': self.changes,
            'length': self.length
        }

@dataclass
class Protein:
    """Модель белка"""
    id: str
    name: str
    sequence: str
    length: int
    domains: List[ProteinDomain]
    molecular_weight: Optional[float] = None
    is_modified: bool = False
    
    def __post_init__(self):
        if self.length == 0:
            self.length = len(self.sequence)
    
    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'name': self.name,
            'sequence': self.sequence,
            'length': self.length,
            'domains': [domain.to_dict() for domain in self.domains],
            'molecular_weight': self.molecular_weight,
            'is_modified': self.is_modified
        }

@dataclass
class Gene:
    """Модель гена"""
    id: str
    name: str
    species: str
    chromosome: str
    strand: Strand
    protein: Protein
    exons: List[Exon]
    transcript_id: Optional[str] = None
    
    def __post_init__(self):
        # Сортируем экзоны по номеру
        self.exons.sort(key=lambda x: x.number)
    
    @property
    def full_sequence(self) -> str:
        """Полная нуклеотидная последовательность"""
        return ''.join(exon.sequence for exon in self.exons)
    
    @property
    def exons_count(self) -> int:
        return len(self.exons)
    
    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'name': self.name,
            'species': self.species,
            'chromosome': self.chromosome,
            'strand': self.strand.value,
            'protein': self.protein.to_dict(),
            'exons': [exon.to_dict() for exon in self.exons],
            'transcript_id': self.transcript_id,
            'exons_count': self.exons_count
        }
    
    def find_exon_by_position(self, nucleotide_position: int) -> Optional[Exon]:
        """Найти экзон по позиции нуклеотида"""
        current_pos = 0
        for exon in self.exons:
            exon_end = current_pos + exon.length
            if current_pos <= nucleotide_position < exon_end:
                return exon, current_pos
            current_pos = exon_end
        return None, -1
    
    def get_amino_acid_position(self, nucleotide_position: int) -> int:
        """Получить позицию аминокислоты по позиции нуклеотида"""
        return nucleotide_position // 3