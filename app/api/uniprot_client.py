import logging
from typing import Dict, List, Tuple, Any, Optional
from requests import get
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
    
    def get_sequence_data(self, identifier: str) -> str:
        """
        Получить последовательность белка из UniProt
        Возвращает: sequence
        """
        try:
            data = self._fetch_uniprot_seq(identifier)
            return self._process_sequence_data(data)
        except Exception as e:
            self.logger.error(f"Failed to get UniProt sequence for {identifier}: {e}")
            raise APIError(f"Failed to get UniProt sequence: {e}")
    
    def get_protein_domains(self, identifier: str) -> List[Tuple[int, int, str]]:
        """
        Получить данные о доменах белка
        Возвращает список кортежей: (start, end, description)
        """
        try:
            data = self._fetch_uniprot_dom(identifier)
            return self._process_domains_data(data)
        except Exception as e:
            self.logger.error(f"Failed to get UniProt domains for {identifier}: {e}")
            raise APIError(f"Failed to get UniProt domains: {e}")
    
    def get_protein_features(self, identifier: str) -> Dict[str, Any]:
        """
        Получить расширенную информацию о белке
        """
        try:
            data = self._fetch_uniprot_dom(identifier)
            return self._process_features_data(data)
        except Exception as e:
            self.logger.error(f"Failed to get UniProt features for {identifier}: {e}")
            raise APIError(f"Failed to get UniProt features: {e}")
    
    @retry_on_failure(max_retries=3, delay=1.0)
    def _fetch_uniprot_seq(self, identifier: str) -> Dict[str, Any]:
        """Получить данные из UniProt REST API"""
        url = config.UNIPROT_REST_URL + identifier
        
        response = get(url)
        if not response.ok:
            raise APIError(f"UniProt API error: {response.status_code}")
        
        return response.json()

    @retry_on_failure(max_retries=3, delay=1.0)
    def _fetch_uniprot_dom(self, identifier: str) -> Dict[str, Any]:
        """Получить данные из UniProt REST API"""
        url = config.UNIPROT_REST_URL + identifier + ".json" + "?fields=ft_domain%2Cft_compbias"
        
        response = get(url)
        if not response.ok:
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
    
    def _process_features_data(self, data: Dict) -> Dict[str, Any]:
        """Обработка расширенной информации о белке"""
        try:
            protein_info = {
                "accession": data.get("primaryAccession"),
                "name": data.get("proteinDescription", {}).get("recommendedName", {}).get("fullName", {}).get("value"),
                "gene_name": data.get("genes", [{}])[0].get("geneName", {}).get("value"),
                "organism": data.get("organism", {}).get("scientificName"),
                "sequence_length": data.get("sequence", {}).get("length"),
                "features": [],
                "comments": [],
                "keywords": []
            }
            
            # Обрабатываем features
            for feature in data.get("features", []):
                feature_info = {
                    "type": feature.get("type"),
                    "description": feature.get("description"),
                    "start": feature.get("location", {}).get("start", {}).get("value"),
                    "end": feature.get("location", {}).get("end", {}).get("value")
                }
                protein_info["features"].append(feature_info)
            
            # Обрабатываем comments
            for comment in data.get("comments", []):
                comment_info = {
                    "type": comment.get("commentType"),
                    "texts": []
                }
                
                if "texts" in comment:
                    for text in comment["texts"]:
                        comment_info["texts"].append(text.get("value"))
                
                protein_info["comments"].append(comment_info)
            
            # Обрабатываем keywords
            for keyword in data.get("keywords", []):
                protein_info["keywords"].append(keyword.get("name"))
            
            return protein_info
            
        except Exception as e:
            self.logger.error(f"Error processing UniProt features: {e}")
            raise APIError(f"Failed to process UniProt features: {e}")
    
    # Старые методы для обратной совместимости
    def get_sequence_legacy(self, identifier: str) -> str:
        """Старый метод для получения последовательности (совместимость)"""
        return self.get_sequence_data(identifier)
    
    def get_domains_legacy(self, identifier: str) -> List[Tuple[int, int, str]]:
        """Старый метод для получения доменов (совместимость)"""
        return self.get_protein_domains(identifier)