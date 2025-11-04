import logging
import xmltodict
from typing import List, Dict, Any, Optional, Tuple
from requests import get
from .api_utils import APIUtils, APIError, retry_on_failure
from ..models.gene_models import Exon

class NCBIClient:
    """Клиент для работы с NCBI EUtils API"""
    
    def __init__(self):
        self.api = APIUtils(
            base_url="https://eutils.ncbi.nlm.nih.gov/entrez/eutils",
            cache_config=CacheConfig(enabled=True, default_ttl=86400)
        )
        self.logger = logging.getLogger(__name__)
    
    def get_exons_data(self, identifier: str) -> List[Exon]:
        """
        Получить данные об экзонах из NCBI
        """
        try:
            data = self._fetch_ncbi_data(identifier)
            return self._process_ncbi_exons(data)
        except Exception as e:
            self.logger.error(f"Failed to get NCBI exons for {identifier}: {e}")
            raise APIError(f"Failed to get NCBI exons: {e}")
    
    def get_sequence_data(self, identifier: str) -> Tuple[str, int, int]:
        """
        Получить последовательность из NCBI
        Возвращает: (sequence, utr5_start, utr3_start)
        """
        try:
            data = self._fetch_ncbi_data(identifier)
            return self._process_ncbi_sequence(data)
        except Exception as e:
            self.logger.error(f"Failed to get NCBI sequence for {identifier}: {e}")
            raise APIError(f"Failed to get NCBI sequence: {e}")
    
    @retry_on_failure(max_retries=3, delay=1.0)
    def _fetch_ncbi_data(self, identifier: str) -> Dict[str, Any]:
        """Получить данные из NCBI EUtils"""
        url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
        params = {
            "db": "nuccore",
            "retmode": "xml",
            "id": identifier
        }
        
        response = get(f"{url}?{'&'.join([f'{k}={v}' for k, v in params.items()])}")
        if not response.ok:
            raise APIError(f"NCBI API error: {response.status_code}")
        
        data = xmltodict.parse(response.text)
        return data
    
    def _process_ncbi_exons(self, data: Dict) -> List[Exon]:
        """Обработка данных экзонов из NCBI"""
        exons = []
        
        try:
            # Извлекаем features из XML
            features = data['GBSet']['GBSeq']['GBSeq_feature-table']['GBFeature']
            if not isinstance(features, list):
                features = [features]
            
            current_position = 0
            exon_number = 1
            
            for feature in features:
                if feature['GBFeature_key'] == 'exon':
                    # Парсим локацию экзона
                    location_str = feature['GBFeature_location']
                    start, end = self._parse_location(location_str)
                    
                    # Получаем последовательность экзона
                    exon_sequence = self._extract_exon_sequence(data, start, end)
                    
                    # Создаем объект экзона
                    exon = Exon(
                        number=exon_number,
                        sequence=exon_sequence,
                        start_position=current_position,
                        end_position=current_position + len(exon_sequence) - 1,
                        length=len(exon_sequence),
                        is_modified=False
                    )
                    
                    exons.append(exon)
                    current_position += len(exon_sequence)
                    exon_number += 1
            
            return exons
            
        except Exception as e:
            self.logger.error(f"Error processing NCBI exons: {e}")
            raise APIError(f"Failed to process NCBI exons data: {e}")
    
    def _process_ncbi_sequence(self, data: Dict) -> Tuple[str, int, int]:
        """Обработка последовательности из NCBI"""
        try:
            # Получаем полную последовательность
            sequence = data['GBSet']['GBSeq']['GBSeq_sequence'].upper()
            
            # Ищем CDS для определения UTR регионов
            features = data['GBSet']['GBSeq']['GBSeq_feature-table']['GBFeature']
            if not isinstance(features, list):
                features = [features]
            
            utr5_start = -1
            utr3_start = -1
            
            for feature in features:
                if feature['GBFeature_key'] == 'CDS':
                    location_str = feature['GBFeature_location']
                    cds_start, cds_end = self._parse_location(location_str)
                    
                    # Вычисляем UTR позиции
                    utr5_start = 0
                    utr3_start = cds_end + 1
                    
                    # Обрезаем последовательность до CDS если нужно
                    sequence = sequence[cds_start:cds_end + 1]
                    break
            
            return sequence, utr5_start, utr3_start
            
        except Exception as e:
            self.logger.error(f"Error processing NCBI sequence: {e}")
            raise APIError(f"Failed to process NCBI sequence: {e}")
    
    def _parse_location(self, location_str: str) -> Tuple[int, int]:
        """Парсинг строки локации NCBI"""
        try:
            if '..' in location_str:
                start, end = map(int, location_str.split('..'))
                return start - 1, end - 1  # Convert to 0-based
            else:
                # Если одна позиция
                pos = int(location_str) - 1
                return pos, pos
        except Exception as e:
            self.logger.error(f"Error parsing location {location_str}: {e}")
            return 0, 0
    
    def _extract_exon_sequence(self, data: Dict, start: int, end: int) -> str:
        """Извлечь последовательность экзона из полной последовательности"""
        try:
            full_sequence = data['GBSet']['GBSeq']['GBSeq_sequence'].upper()
            return full_sequence[start:end + 1]
        except Exception as e:
            self.logger.error(f"Error extracting exon sequence: {e}")
            return ""
    
    # Старые методы для обратной совместимости
    def get_exons_legacy(self, identifier: str) -> List[Tuple[int, int]]:
        """Старый метод для получения экзонов (совместимость)"""
        exons = self.get_exons_data(identifier)
        return [(exon.start_position, exon.end_position) for exon in exons]
    
    def get_sequence_legacy(self, identifier: str) -> Tuple[str, int, int]:
        """Старый метод для получения последовательности (совместимость)"""
        return self.get_sequence_data(identifier)