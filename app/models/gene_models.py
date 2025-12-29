from dataclasses import dataclass
from typing import List, Optional, Dict, Any, Tuple

@dataclass
class Exon:
    """Модель экзона"""
    number: int
    sequence: str
    start_position: int
    end_position: int
    start_phase: int
    end_phase: int
    length: int
    
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
        }

@dataclass
class UTR:
    """Модель нетраснлируемой области"""
    sequence: str
    start_position: int
    end_position: int
    length: int

    def __post_init__(self):
        if self.length == 0:
            self.length = len(self.sequence)

    def to_dict(self) -> Dict:
        return {
            'sequence': self.sequence,
            'start_position': self.start_position,
            'end_position': self.end_position,
            'length': self.length,
        }

@dataclass
class BaseSequence:
    """Модель последовательности нуклеотидов"""
    identifier: str
    length: int
    exons: List[Exon]
    utr3: UTR
    utr5: UTR
    full_sequence: str = ""

    def __post_init__(self):
        if self.length == 0:
            self.length = sum([exon.length for exon in self.exons])

        # Сортируем экзоны по номеру
        self.exons.sort(key=lambda x: x.number)

        self.full_sequence = ''.join(exon.sequence for exon in self.exons)

    def to_dict(self) -> Dict:
        return {
            'identifier': self.identifier,
            'length': self.length,
            'exons': [exon.to_dict() for exon in self.exons],
            'utr3': self.utr3.to_dict(),
            'utr5': self.utr5.to_dict(),
        }

@dataclass
class ProteinDomain:
    """Модель белкового домена"""
    name: str
    start: int
    end: int
    sequence: str
    type: str = "unknown"
    
    def to_dict(self) -> Dict:
        return {
            'name': self.name,
            'start': self.start,
            'end': self.end,
            'sequence': self.sequence,
            'type': self.type,
        }

@dataclass
class Protein:
    """Модель белка"""
    identifier: str
    sequence: str
    length: int
    domains: List[ProteinDomain]
         
    def __post_init__(self):
        if self.length == 0:
            self.length = len(self.sequence)

    def to_dict(self) -> Dict:
        return {
            'identifier': self.identifier,
            'length': self.length,
            'sequence': self.sequence,
            'domains': [domain.to_dict() for domain in self.domains],
        }

@dataclass
class Gene:
    """Модель гена"""
    protein: Protein
    translated_protein: Protein
    base_sequence: BaseSequence

    def to_dict(self) -> Dict:
        return {
            'protein': self.protein.to_dict(),
            'translated_protein': self.translated_protein.to_dict(),
            'base_sequence': self.base_sequence.to_dict(),
        }