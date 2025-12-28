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

    def __post_init__(self):
        if self.length == 0:
            self.length = sum([exon.length for exon in self.exons])

        # Сортируем экзоны по номеру
        self.exons.sort(key=lambda x: x.number)

    @property
    def full_sequence(self) -> str:
        """Полная нуклеотидная последовательность"""
        return ''.join(exon.sequence for exon in self.exons)
    
    @property
    def coding_sequence(self) -> str:
        """Полная нуклеотидная последовательность"""
        return ''.join(exon.sequence for exon in self.exons)[self.utr3.length:self.utr5.length]
        
    def _translate_nucleotide_position(self, nucleotide_position: int) -> int:
        """"Пересчет позиции из-за смещения некодируемой области"""
        return nucleotide_position - 1 + self.utr5.length
    
    def find_exon_by_position(self, nucleotide_position: int) -> Optional[Exon]:
        """Найти экзон по позиции нуклеотида"""
        nucleotide_position_in_base_sequence = self._translate_nucleotide_position(nucleotide_position)
        for exon in self.exons:
            if exon.start_position <= nucleotide_position_in_base_sequence <= exon.end_position:
                return exon
        return None

    def substitution_nucleotide_in_exon(self, nucleotide_position: int, nucleotide: str) -> None:
        exon = self.find_exon_by_position(nucleotide_position)
        nucleotide_position_in_base_sequence = self._translate_nucleotide_position(nucleotide_position)
        sequence = list(exon.sequence)
        sequence[nucleotide_position_in_base_sequence - exon.start_position] = nucleotide
        exon.sequence = ''.join(sequence)

    def get_codon_by_nucleotide(self, nucleotide_position: int) -> str:
        """Получить кодон по номеру нуклеотида"""
        nucleotide_position_in_base_sequence = self._translate_nucleotide_position(nucleotide_position)
        index = (nucleotide_position_in_base_sequence // 3 ) * 3
        return self.full_sequence[index:index + 3]

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

    def get_amino_acid(self, amino_acid_position: int) -> str:
        return self.sequence[amino_acid_position]

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