from typing import List, Tuple, Optional, Dict
import logging
from ..models.gene_models import Gene, Protein, BaseSequence, Exon, UTR, ProteinDomain
from ..api import EnsemblClient, UniProtClient, NCBIClient


logger = logging.getLogger(__name__)

class GeneService:
    """Сервис для загрузки и построения структуры гена с использованием новых клиентов""" 
    def __init__(self):
        # Инициализация клиентов API
        self.uniprot_client = UniProtClient()
        self.ncbi_client = NCBIClient()
        self.ensembl_client = EnsemblClient()
    
    def build_gene_from_ensembl(
        self, 
        gene_id: str, 
        protein_id: str
    ) -> Optional[Gene]:
        """
        Построить ген из данных Ensembl + UniProt
        
        Args:
            gene_id: ENSEMBL ID (например, ENSG00000139618)
            protein_id: UniProt ID (например, P04637)
        """
        try:
            logger.info(f"Building gene: Ensembl={gene_id}, UniProt={protein_id}")
            
            # 1. Получаем экзоны из Ensembl
            exons = self.ensembl_client.get_exons_data(gene_id)
            
            # 2. Получаем последовательность и UTR из Ensembl
            sequence, utr5_start, utr3_start = self.ensembl_client.get_sequence_data(gene_id)
            
            # 3. Создаём UTR объекты
            utr5, utr3 = self._create_utrs(sequence, utr5_start, utr3_start)
            
            # 4. Создаём базовую последовательность
            base_sequence = BaseSequence(
                identifier=gene_id,
                length=len(sequence),
                exons=exons,
                utr3=utr3,
                utr5=utr5
            )
            
            # 5. Получаем белок из UniProt
            protein = self._build_protein_from_uniprot(protein_id)
            
            # 6. Создаём ген
            gene = Gene(
                protein=protein,
                base_sequence=base_sequence
            )
            
            logger.info(f"Gene built: {len(exons)} exons, {len(protein.domains)} domains")
            return gene
            
        except Exception as e:
            logger.error(f"Error building gene from Ensembl: {e}", exc_info=True)
            return None
    
    def build_gene_from_ncbi(
        self,
        ncbi_id: str,
        protein_id: str
    ) -> Optional[Gene]:
        """
        Построить ген из данных NCBI + UniProt
        """
        try:
            logger.info(f"Building gene: NCBI={ncbi_id}, UniProt={protein_id}")
            
            # 1. Получаем экзоны из NCBI
            exons = self.ncbi_client.get_exons_data(ncbi_id)
            
            # 2. Получаем последовательность и UTR из NCBI
            sequence, utr5_start, utr3_start = self.ncbi_client.get_sequence_data(ncbi_id)
            
            # 3. Создаём UTR объекты
            utr5, utr3 = self._create_utrs(sequence, utr5_start, utr3_start)
            
            # 4. Создаём базовую последовательность
            base_sequence = BaseSequence(
                identifier=ncbi_id,
                length=len(sequence),
                exons=exons,
                utr3=utr3,
                utr5=utr5
            )
            
            # 5. Получаем белок из UniProt
            protein = self._build_protein_from_uniprot(protein_id)
            
            # 6. Создаём ген
            gene = Gene(
                protein=protein,
                base_sequence=base_sequence
            )
            
            logger.info(f"Gene built from NCBI: {len(exons)} exons")
            return gene
            
        except Exception as e:
            logger.error(f"Error building gene from NCBI: {e}", exc_info=True)
            return None
    
    def _create_utrs(
        self, 
        sequence: str, 
        utr5_start: int, 
        utr3_start: int
    ) -> Tuple[UTR, UTR]:
        """Создать UTR объекты из позиций"""
        
        # Если позиции неизвестны
        if utr5_start == -1 and utr3_start == -1:
            empty_utr = UTR(
                sequence="",
                start_position=-1,
                end_position=-1,
                length=0
            )
            return empty_utr, empty_utr
        
        # 5' UTR
        utr5_seq = sequence[:utr5_start] if utr5_start > 0 else ""
        utr5 = UTR(
            sequence=utr5_seq,
            start_position=0,
            end_position=len(utr5_seq) - 1 if utr5_seq else -1,
            length=len(utr5_seq)
        )
        
        # 3' UTR
        utr3_seq = sequence[utr3_start:] if utr3_start > 0 else ""
        utr3 = UTR(
            sequence=utr3_seq,
            start_position=utr3_start if utr3_start > 0 else -1,
            end_position=len(sequence) - 1,
            length=len(utr3_seq)
        )
        
        return utr5, utr3
    
    def _build_protein_from_uniprot(self, protein_id: str) -> Protein:
        """Построить объект Protein из данных UniProt"""
        try:
            # 1. Получаем последовательность белка
            protein_seq = self.uniprot_client.get_sequence_data(protein_id)
            
            # 2. Получаем домены белка (start, end, description)
            domains_data = self.uniprot_client.get_protein_domains(protein_id)
            
            # 3. Создаём объекты ProteinDomain
            domains = []
            for start, end, description in domains_data:
                # Вырезаем последовательность домена
                domain_seq = protein_seq[start:end + 1] if start < len(protein_seq) else ""
                
                domain = ProteinDomain(
                    name=description or f"Domain_{start}_{end}",
                    start=start,
                    end=end,
                    sequence=domain_seq,
                    type="domain",  # Можно уточнить из feature type
                )
                domains.append(domain)
            
            # 4. Создаём объект Protein
            protein = Protein(
                identifier=protein_id,
                sequence=protein_seq,
                length=len(protein_seq),
                domains=domains
            )
            
            return protein
            
        except Exception as e:
            logger.error(f"Error building protein {protein_id}: {e}")
            # Возвращаем минимальный белок в случае ошибки
            return Protein(
                identifier=protein_id,
                sequence="",
                length=0,
                domains=[]
            )
    
    def get_exon_by_position(
        self, 
        gene: Gene, 
        nucleotide_position: int
    ) -> Optional[Exon]:
        """Найти экзон по позиции нуклеотида в гене"""
        return gene.find_exon_by_position(nucleotide_position)
    
    def get_amino_acid_position(
        self, 
        gene: Gene, 
        nucleotide_position: int
    ) -> int:
        """Получить позицию аминокислоты по позиции нуклеотида"""
        return gene.get_amino_acid_position(nucleotide_position)
    
    def update_exon_phases(self, gene: Gene) -> Gene:
        """
        Обновить фазы экзонов (start_phase, end_phase)
        Вычисляется на основе рамки считывания
        """
        # TODO: Реализовать вычисление фаз
        # Для первого экзона start_phase = 0
        # Для следующих: start_phase = end_phase предыдущего экзона
        # end_phase = (start_phase + длина экзона) % 3
        
        current_phase = 0
        for exon in gene.base_sequence.exons:
            exon.start_phase = current_phase
            current_phase = (current_phase + exon.length) % 3
            exon.end_phase = current_phase
        
        return gene