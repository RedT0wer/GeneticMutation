import logging
from typing import List, Dict, Any, Optional
from requests import get
from .api_utils import APIUtils, APIError, retry_on_failure
from ..models.gene_models import ProteinDomain

class UniProtClient:
    """Клиент для работы с UniProt REST API (обновленная версия)"""
    
    def __init__(self):
        self.api = APIUtils(
            base_url="https://rest.uniprot.org",
            cache_config=CacheConfig(enabled=True, default_ttl=86400)
        )
        self.logger = logging.getLogger(__name__)
        self._field_mapping = self._create_field_mapping()
    
    def get_protein_domains(self, protein_id: str) -> List[ProteinDomain]:
        """
        Получить домены белка
        """
        try:
            data = self._fetch_uniprot_data(protein_id)
            return self._process_domains_data(data, protein_id)
        except Exception as e:
            self.logger.error(f"Failed to get domains for {protein_id}: {e}")
            raise APIError(f"Failed to get protein domains: {e}")
    
    def get_protein_sequence(self, protein_id: str) -> str:
        """
        Получить аминокислотную последовательность белка
        """
        try:
            data = self._fetch_uniprot_json(protein_id)
            return self._process_sequence_data(data)
        except Exception as e:
            self.logger.error(f"Failed to get sequence for {protein_id}: {e}")
            raise APIError(f"Failed to get protein sequence: {e}")
    
    @retry_on_failure(max_retries=3, delay=1.0)
    def _fetch_uniprot_data(self, protein_id: str) -> Dict[str, Any]:
        """Получить данные из UniProt с доменами"""
        fields = self._get_fields_for_protein(protein_id)
        url = f"https://rest.uniprot.org/uniprotkb/{protein_id}.json"
        
        if fields:
            url += f"?fields={fields}"
        
        response = get(url)
        if not response.ok:
            raise APIError(f"UniProt API error: {response.status_code}")
        
        return response.json()
    
    @retry_on_failure(max_retries=3, delay=1.0)
    def _fetch_uniprot_json(self, protein_id: str) -> Dict[str, Any]:
        """Получить базовые данные из UniProt"""
        url = f"https://rest.uniprot.org/uniprotkb/{protein_id}.json"
        
        response = get(url)
        if not response.ok:
            raise APIError(f"UniProt API error: {response.status_code}")
        
        return response.json()
    
    def _get_fields_for_protein(self, protein_id: str) -> str:
        """Получить поля для запроса based на protein_id"""
        # Можно настроить маппинг для разных белков
        default_fields = "accession,id,protein_name,gene_names,sequence,features"
        
        # Специфичные поля для известных белков
        specific_fields = {
            "p53": "accession,id,protein_name,gene_names,sequence,features,cc_function",
            "brca1": "accession,id,protein_name,gene_names,sequence,features,cc_domain",
            # Добавь другие белки по необходимости
        }
        
        # Ищем по ключу или по подстроке в ID
        for key, fields in specific_fields.items():
            if key.lower() in protein_id.lower():
                return fields
        
        return default_fields
    
    def _create_field_mapping(self) -> Dict[str, str]:
        """Создать маппинг полей для разных белков"""
        return {
            "p53": "accession,id,protein_name,gene_names,sequence,features,cc_function",
            "brca1": "accession,id,protein_name,gene_names,sequence,features,cc_domain",
            "cf