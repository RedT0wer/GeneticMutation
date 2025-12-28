from dataclasses import dataclass, field
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
    translation: Dict = {'TTT': 'F', 'TTC': 'F', 'TTA': 'L', 'TTG': 'L', 'TCT': 'S', 'TCC': 'S', 'TCA': 'S', 'TCG': 'S', 'TAT': 'Y', 'TAC': 'Y', 'TAA': '*', 'TAG': '*', 'TGT': 'C', 'TGC': 'C', 'TGA': '*', 'TGG': 'W', 'CTT': 'L', 'CTC': 'L', 'CTA': 'L', 'CTG': 'L', 'CCT': 'P', 'CCC': 'P', 'CCA': 'P', 'CCG': 'P', 'CAT': 'H', 'CAC': 'H', 'CAA': 'Q', 'CAG': 'Q', 'CGT': 'R', 'CGC': 'R', 'CGA': 'R', 'CGG': 'R', 'ATT': 'I', 'ATC': 'I', 'ATA': 'I', 'ATG': 'M', 'ACT': 'T', 'ACC': 'T', 'ACA': 'T', 'ACG': 'T', 'AAT': 'N', 'AAC': 'N', 'AAA': 'K', 'AAG': 'K', 'AGT': 'S', 'AGC': 'S', 'AGA': 'R', 'AGG': 'R', 'GTT': 'V', 'GTC': 'V', 'GTA': 'V', 'GTG': 'V', 'GCT': 'A', 'GCC': 'A', 'GCA': 'A', 'GCG': 'A', 'GAT': 'D', 'GAC': 'D', 'GAA': 'E', 'GAG': 'E', 'GGT': 'G', 'GGC': 'G', 'GGA': 'G', 'GGG': 'G'}
       
    @classmethod
    def transaltion_sequense(self, sequense: str, start: int, end: int) -> Tuple[str, int]:
        stopCodon = -1
        seqAminoacid = ""
        for i in range(start, end + 1, 3):
            codon = sequense[i] + sequense[i + 1] + sequense[i + 2]
            aminoacid = self.get_aminoacid(codon)
            seqAminoacid += aminoacid
            if aminoacid == "*": 
                stopCodon = i
                break
        return (seqAminoacid, stopCodon)
    
    @classmethod
    def get_aminoacid(self, codon: str) -> str:
        return self.translation[codon]

    def to_dict(self) -> Dict:
        return {
            'protein': self.protein.to_dict(),
            'translated_protein': self.translated_protein.to_dict(),
            'base_sequence': self.base_sequence.to_dict(),
        }

    def _translate_nucleotide_position(self, nucleotide_position: int) -> int:
        """"Пересчет позиции из-за смещения некодируемой области"""
        return nucleotide_position - 1 - self.base_sequence.utr5.length
    
    def find_exon_by_position(self, nucleotide_position: int) -> Optional[Exon]:
        """Найти экзон по позиции нуклеотида"""
        nucleotide_position_in_base_sequence = self._translate_nucleotide_position(nucleotide_position)
        for exon in self.exons:
            if exon.start_position <= nucleotide_position_in_base_sequence <= exon.end_position:
                return exon
        return None
    
    def get_amino_acid_position(self, nucleotide_position: int) -> int:
        """Получить позицию аминокислоты по позиции нуклеотида"""
        return nucleotide_position // 3