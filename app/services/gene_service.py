from typing import List, Tuple, Optional, Dict
import logging
import asyncio
from ..services.translation_service import TranslationService
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
        self.translation_service = TranslationService()
    
    async def build_gene_from_ensembl(self, gene_id: str, protein_id: str) -> Optional[Gene]:
        """
        Построить ген из данных Ensembl + UniProt
        
        Args:
            gene_id: ENSEMBL ID (например, ENSG00000139618)
            protein_id: UniProt ID (например, P04637)
        """
        try:
            logger.info(f"Building gene: Ensembl={gene_id}, UniProt={protein_id}")
        
            # 1. Запускаем все три корутины одновременно
            exons_task = self.ensembl_client.get_exons_legacy(gene_id)
            sequence_task = self.ensembl_client.get_sequence_data(gene_id)
            protein_task = self._build_protein_from_uniprot(protein_id)
        
            # 2. Ожидаем завершения всех трех задач
            raw_exons, sequence_data, protein = await asyncio.gather(
                exons_task,
                sequence_task,
                protein_task,
                return_exceptions=True  # Обрабатываем исключения по отдельности
            )
        
            # 3. Проверяем результаты на исключения
            if isinstance(raw_exons, Exception):
                raise Exception(f"Failed to get exons: {raw_exons}")
            if isinstance(sequence_data, Exception):
                raise Exception(f"Failed to get sequence data: {sequence_data}")
            if isinstance(protein, Exception):
                raise Exception(f"Failed to get protein: {protein}")
        
            # Распаковываем данные последовательности
            sequence, utr5_start, utr3_start = sequence_data
        
            # 4. Создаём UTR объекты
            utr5, utr3 = self._build_utrs(sequence, utr5_start, utr3_start)

            # 5. Создание экзонов
            exons = self._build_exons(raw_exons, utr5, utr3)
        
            # 6. Создаём базовую последовательность
            base_sequence = BaseSequence(
                identifier=gene_id,
                length=len(sequence),
                exons=exons,
                utr3=utr3,
                utr5=utr5,
                full_sequence=sequence
            )
        
            # 7. Создание транслируемого белка
            translated_protein = self._translated_base_nucleotide(base_sequence, protein)
        
            # 8. Создаём ген
            gene = Gene(
                protein=translated_protein,
                base_sequence=base_sequence
            )
        
            logger.info(f"Gene built: {len(exons)} exons, {len(protein.domains)} domains")
            return gene
            
        except Exception as e:
            logger.error(f"Error building gene from Ensembl: {e}", exc_info=True)
            return None
    
    async def build_gene_from_ncbi(self, ncbi_id: str, protein_id: str) -> Optional[Gene]:
        """
        Построить ген из данных NCBI + UniProt
        """
        try:
            logger.info(f"Building gene: NCBI={ncbi_id}, UniProt={protein_id}")
            
            # 1. Запускаем все три корутины одновременно
            exons_task = self.ncbi_client.get_exons_legacy(ncbi_id)
            sequence_task = self.ncbi_client.get_sequence_data(ncbi_id)
            protein_task = self._build_protein_from_uniprot(protein_id)

            # 2. Ожидаем завершения всех трех задач
            raw_exons, sequence_data, protein = await asyncio.gather(
                exons_task,
                sequence_task,
                protein_task,
                return_exceptions=True  # Обрабатываем исключения по отдельности
            )

            # 3. Проверяем результаты на исключения
            if isinstance(raw_exons, Exception):
                raise Exception(f"Failed to get exons: {raw_exons}")
            if isinstance(sequence_data, Exception):
                raise Exception(f"Failed to get sequence data: {sequence_data}")
            if isinstance(protein, Exception):
                raise Exception(f"Failed to get protein: {protein}")

            # Распаковываем данные последовательности
            sequence, utr5_start, utr3_start = sequence_data
            
            # 4. Создаём UTR объекты
            utr5, utr3 = self._build_utrs(sequence, utr5_start, utr3_start)

            # 5. Создание экзонов
            exons = self._build_exons(raw_exons, utr5, utr3)
            
            # 6. Создаём базовую последовательность
            base_sequence = BaseSequence(
                identifier=ncbi_id,
                length=len(sequence),
                exons=exons,
                utr3=utr3,
                utr5=utr5,
                full_sequence=sequence
            )
            
            # 7. Создание транслируемого белка
            translated_protein = self._translated_base_nucleotide(base_sequence, protein)
            
            # 8. Создаём ген
            gene = Gene(
                protein=translated_protein,
                base_sequence=base_sequence
            )
            
            logger.info(f"Gene built from NCBI: {len(exons)} exons")
            return gene
            
        except Exception as e:
            logger.error(f"Error building gene from NCBI: {e}", exc_info=True)
            return None
    
    async def _build_protein_from_uniprot(self, protein_id: str) -> Protein:
        """
        Построить объект Protein из данных UniProt
        """
        try:
            # 1. Получаем последовательность белка
            protein_seq = await self.uniprot_client.get_sequence_data(protein_id)
            
            # 2. Получаем домены белка (start, end, description)
            domains_data = await self.uniprot_client.get_protein_domains(protein_id)
            
            # 3. Создаём объекты ProteinDomain
            domains = self._build_protein_domains(protein_seq, domains_data)
            
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
            return None
    
    def _build_exons(self, raw_exons: List[Tuple[int, int]], utr5: UTR, utr3: UTR) -> List[Exon]:
        """
        Создание экзонов
        """

        exons = []

        # Обрабатываем каждый экзон
        prev_end_phase = 0
        for i, exon_data in enumerate(raw_exons, 1):            
            # Вычисляем позиции в конкатенированной последовательности
            start_pos,end_pos = exon_data

            length = end_pos - start_pos + 1

            # Считаем начало кодирующей области
            end_exons = False
            if utr5.end_position > end_pos or end_exons:
                start_phase = -1
                end_phase = -1
            elif start_pos <= utr5.end_position <= end_pos:
                start_phase = utr5.length - start_pos
                end_phase = (length - start_phase) % 3
            elif start_pos <= utr3.start_position <= end_pos:
                start_phase = (3 - prev_end_phase) % 3
                end_phase = end_pos - utr3.start_position
                end_exons = True
            else:
                start_phase = (3 - prev_end_phase) % 3
                end_phase = (length - start_phase) % 3
            prev_end_phase = end_phase

            exon = Exon(
                number=i,
                start_position=start_pos,
                end_position=end_pos,
                start_phase=start_phase,
                end_phase=end_phase,
                length=length,
            )
            
            exons.append(exon)
        
        return exons

    def _build_utrs(self, sequence: str, utr5_start: int, utr3_start: int) -> Tuple[UTR, UTR]:
        """
        Создать UTR объекты из позиций
        """
        
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
        utr3_seq = sequence[-utr3_start:] if utr3_start > 0 else ""
        utr3 = UTR(
            sequence=utr3_seq,
            start_position=len(sequence) - utr3_start if utr3_start > 0 else -1,
            end_position=len(sequence) - 1,
            length=len(utr3_seq)
        )
        
        return utr5, utr3
    
    def _translated_base_nucleotide(self, base_sequence: BaseSequence, protein: Protein) -> Protein:
        """
        Построить объект Protein из BaseSequence
        """
        # 1. 
        nucleotide_sequence = base_sequence.full_sequence

        # 2. 
        protein_sequence = self.translation_service.translation_sequence(nucleotide_sequence, base_sequence.utr5.end_position + 1, base_sequence.utr3.start_position)

        # 3.
        domains: List[ProteinDomain] = []
        for domain in protein.domains:
            name, seq = domain.name, domain.sequence
            index = protein_sequence.find(seq)
            if index == -1:
                continue
            else:
                if domains == [] and index != 0:
                    connection = ProteinDomain(
                        name="Connection",
                        start=0,
                        end=index-1,
                        sequence=protein_sequence[:index],
                        type="unknown"
                    )
                    domains.append(connection)
                elif domains and domains[-1].start + 1 < index:
                    prev = domains[-1]
                    connection = ProteinDomain(
                        name=f"Connection",
                        start=prev.end + 1,
                        end=index - 1,
                        sequence=protein_sequence[prev.end + 1:index],
                        type="unknown"
                    )
                    if connection.end >= connection.start: domains.append(connection)

                dom = ProteinDomain(
                    name=name,
                    start=index,
                    end=index + len(seq) - 1,
                    sequence=seq,
                    type=domain.type
                )
                domains.append(dom)
        if domains and domains[-1].end != len(protein_sequence) - 1:
            connection = ProteinDomain(
                name="Connection",
                start=domains[-1].end + 1,
                end=len(protein_sequence) - 1,
                sequence=protein_sequence[domains[-1].end + 1:],
                type="unknown"
            )
            domains.append(connection)

        for i,domain in enumerate(domains):
            if domain.name == "Connection":
                arr = []
                prev = domains[i - 1].name if i > 1 else ""
                if prev: arr.append(prev)

                arr.append(domain.name)

                next = domains[i + 1].name if i < len(domains)-1 else ""
                if next: arr.append(next)
                domain.name = " -> ".join(arr)
            
        # 4. Создаём объект Protein
        protein = Protein(
            identifier=base_sequence.identifier,
            sequence=protein_sequence,
            length=len(protein_sequence),
            domains=domains,
        )
            
        return protein

    def _build_protein_domains(self, protein_seq: str, domains_data: List[Tuple[int, int, str]]) -> List[ProteinDomain]:
        """
        Создание доменов белка
        """
        domains = []
        for start, end, description in domains_data:
            # Вырезаем последовательность домена
            domain_seq = protein_seq[start:end + 1]
                
            domain = ProteinDomain(
                name=description,
                start=start,
                end=end,
                sequence=domain_seq,
                type="domain",
            )
            domains.append(domain)
        return domains