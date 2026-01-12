import logging
from typing import Dict, List, Tuple, Any, Optional
import httpx
from .api_utils import APIUtils, APIError, retry_on_failure
from config import config

class UniProtClient:
    """Клиент для работы с UniProt REST API"""
    
    def __init__(self):
        self.api = APIUtils(
            base_url="https://rest.uniprot.org/uniprotkb",
            #cache_config=CacheConfig(enabled=True, default_ttl=86400)
        )
        self.logger = logging.getLogger(__name__)
    
    async def get_sequence_data(self, identifier: str) -> str:
        """
        Получить последовательность белка из UniProt
        Возвращает: sequence
        """
        try:
            data = await self._fetch_uniprot_seq(identifier)
            return self._process_sequence_data(data)
        except Exception as e:
            self.logger.error(f"Failed to get UniProt sequence for {identifier}: {e}")
            raise APIError(f"Failed to get UniProt sequence: {e}")
    
    async def get_protein_domains(self, identifier: str) -> List[Tuple[int, int, str]]:
        """
        Получить данные о доменах белка
        Возвращает список кортежей: (start, end, description)
        """
        try:
            data = await self._fetch_uniprot_dom(identifier)
            return self._process_domains_data(data)
        except Exception as e:
            self.logger.error(f"Failed to get UniProt domains for {identifier}: {e}")
            raise APIError(f"Failed to get UniProt domains: {e}")
    
    @retry_on_failure(max_retries=3, delay=1.0)
    async def _fetch_uniprot_seq(self, identifier: str) -> Dict[str, Any]:
        """Получить данные из UniProt REST API"""
        url = config.UNIPROT_REST_URL + identifier
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            if not response.is_success:
                raise APIError(f"UniProt API error: {response.status_code}")
            
            return response.json()

    @retry_on_failure(max_retries=3, delay=1.0)
    async def _fetch_uniprot_dom(self, identifier: str) -> Dict[str, Any]:
        """Получить данные из UniProt REST API"""
        url = config.UNIPROT_REST_URL + identifier + ".json" + "?fields=ft_domain%2Cft_region"
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            if not response.is_success:
                raise APIError(f"UniProt API error: {response.status_code}")
            
            return response.json()
    
    def _process_sequence_data(self, data: Dict) -> str:
        """Обработка данных последовательности белка"""
        try:
            sequence = data["sequence"]["value"]
            
            return sequence
            
        except KeyError as e:
            self.logger.error(f"Sequence data not found in UniProt response: {e}")
            raise APIError(f"Invalid UniProt response format: {e}")
        except Exception as e:
            self.logger.error(f"Error processing UniProt sequence: {e}")
            raise APIError(f"Failed to process UniProt sequence: {e}")
    
    def _process_domains_data(self, data: Dict) -> List[Tuple[int, int, str]]:
        """Обработка данных доменов белка"""
        domains = []
        
        try:
            features = data.get("features", [])
            
            for feature in features:
                #if feature.get("type") in ["DOMAIN", "REGION"]: #"REPEAT", "MOTIF", 
                location = feature.get("location", {})
                start = location.get("start", {}).get("value", 0)
                end = location.get("end", {}).get("value", 0)
                description = feature.get("description", "Unknown domain")
                    
                # Конвертируем в 0-based координаты если нужно
                if start > 0:
                    start -= 1
                if end > 0:
                    end -= 1
                    
                domains.append((start, end, description))
            
            return sorted(domains, key=lambda x: x[0])
            
        except Exception as e:
            self.logger.error(f"Error processing UniProt domains: {e}")
            raise APIError(f"Failed to process UniProt domains: {e}")
    
    # Старые методы для обратной совместимости
    async def get_sequence_legacy(self, identifier: str) -> str:
        """Старый метод для получения последовательности (совместимость)"""
        return await self.get_sequence_data(identifier)
    
    async def get_domains_legacy(self, identifier: str) -> List[Tuple[int, int, str]]:
        """Старый метод для получения доменов (совместимость)"""
        return await self.get_protein_domains(identifier)