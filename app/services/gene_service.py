import logging
from typing import Dict, List, Optional, Tuple
from ..api import ensembl_client, uniprot_client, ncbi_client
from ..models.gene_models import Gene, Protein, Exon, ProteinDomain, Strand
from ..core.biopython_utils import BiopythonUtils
from ..utils.cache import cache

class GeneService:
    """Сервис для работы с генами и белковыми данными"""
    
    def __init__(self):
        self.ensembl = ensembl_client
        self.uniprot = uniprot_client
        self.ncbi = ncbi_client
        self.bp_utils = BiopythonUtils()
        self.logger = logging.getLogger(__name__)
    
    #@cache(expire=3600)  # Кэшируем на 1 час
    def get_gene_with_protein(self, gene_id: str, species: str = "human") -> Gene:
        """
        Получить полные данные о гене с белковой информацией
        """
        try:
            self.logger.info(f"Loading gene data for {gene_id}")
            
            # Получаем геномные данные из Ensembl
            ensembl_data = self.ensembl.get_gene_info(gene_id, species)
            
            # Получаем экзоны
            exons = self._get_exons_data(gene_id, ensembl_data)
            
            # Получаем белковые данные
            protein = self._get_protein_data(ensembl_data.get('protein_id'))
            
            # Создаем объект гена
            gene = Gene(
                id=gene_id,
                name=ensembl_data.get('gene_name', gene_id),
                species=species,
                chromosome=ensembl_data.get('chromosome', 'unknown'),
                strand=Strand.FORWARD if ensembl_data.get('strand') == 1 else Strand.REVERSE,
                protein=protein,
                exons=exons,
                transcript_id=ensembl_data.get('transcript_id')
            )
            
            self.logger.info(f"Successfully loaded gene {gene_id} with {len(exons)} exons")
            return gene
            
        except Exception as e:
            self.logger.error(f"Failed to load gene {gene_id}: {e}")
            raise
    
    def _get_exons_data(self, gene_id: str, ensembl_data: Dict) -> List[Exon]:
        """Получить данные об экзонах"""
        try:
            # Пробуем получить из Ensembl
            exons = self.ensembl.get_exons_data(gene_id)
            if exons:
                return exons
        except Exception as e:
            self.logger.warning(f"Failed to get exons from Ensembl for {gene_id}: {e}")
        
        try:
            # Fallback на NCBI
            exons = self.ncbi.get_exons_data(gene_id)
            if exons:
                return exons
        except Exception as e:
            self.logger.warning(f"Failed to get exons from NCBI for {gene_id}: {e}")
        
        # Если оба источника не сработали, создаем mock данные из Ensembl
        return self._create_mock_exons(ensembl_data)
    
    def _get_protein_data(self, protein_id: str) -> Protein:
        """Получить данные о белке"""
        if not protein_id:
            raise ValueError("Protein ID is required")
        
        try:
            # Получаем последовательность и домены из UniProt
            sequence = self.uniprot.get_protein_sequence(protein_id)
            domains = self.uniprot.get_protein_domains(protein_id)
            
            # Рассчитываем молекулярную массу
            molecular_weight = self.bp_utils.calculate_molecular_weight(sequence)
            
            return Protein(
                id=protein_id,
                name=f"Protein {protein_id}",
                sequence=sequence,
                length=len(sequence),
                domains=domains,
                molecular_weight=molecular_weight
            )
            
        except Exception as e:
            self.logger.error(f"Failed to get protein data for {protein_id}: {e}")
            # Возвращаем белок с минимальными данными
            return Protein(
                id=protein_id,
                name=f"Protein {protein_id}",
                sequence="",
                length=0,
                domains=[]
            )
    
    def _create_mock_exons(self, ensembl_data: Dict) -> List[Exon]:
        """Создать mock экзоны если данные недоступны"""
        exons = []
        transcript = ensembl_data.get('transcript', {})
        exon_data = transcript.get('Exon', []) if transcript else []
        
        current_position = 0
        for i, exon_info in enumerate(exon_data, 1):
            exon_length = exon_info.get('end', 0) - exon_info.get('start', 0) + 1
            exon = Exon(
                number=i,
                sequence="N" * exon_length,  # Mock последовательность
                start_position=current_position,
                end_position=current_position + exon_length - 1,
                length=exon_length
            )
            exons.append(exon)
            current_position += exon_length
        
        return exons
    
    def search_genes(self, query: str, species: str = "human", limit: int = 10) -> List[Dict]:
        """Поиск генов по названию или символу"""
        try:
            # Пробуем поиск в Ensembl
            results = self.ensembl.search_genes(query, species, limit)
            if results:
                return results
            
            # Fallback на UniProt для поиска белков
            protein_results = self.uniprot.search_proteins(query, species, limit)
            return [
                {
                    'gene_id': protein.get('gene_names', ''),
                    'gene_name': protein.get('protein_name', ''),
                    'species': species,
                    'protein_id': protein.get('protein_id', '')
                }
                for protein in protein_results
            ]
            
        except Exception as e:
            self.logger.error(f"Gene search failed for {query}: {e}")
            return []
    
    def validate_gene_id(self, gene_id: str, species: str = "human") -> bool:
        """Проверить валидность ID гена"""
        try:
            data = self.ensembl.get_gene_info(gene_id, species)
            return bool(data and data.get('id'))
        except Exception:
            return False
    
    def get_available_species(self) -> List[str]:
        """Получить список доступных видов"""
        try:
            return self.ensembl.get_species_list()
        except Exception as e:
            self.logger.error(f"Failed to get species list: {e}")
            return ['human', 'mouse', 'rat']  # Fallback
    
    def clear_gene_cache(self, gene_id: str = None):
        """Очистить кэш генов"""
        try:
            if gene_id:
                # Очищаем кэш для конкретного гена
                cache.delete(f"gene_{gene_id}")
            else:
                # Очищаем весь кэш генов
                cache.clear_pattern("gene_")
        except Exception as e:
            self.logger.warning(f"Failed to clear gene cache: {e}")