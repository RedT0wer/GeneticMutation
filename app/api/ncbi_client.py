import logging
import xmltodict
from typing import List, Dict, Any, Optional, Tuple
import httpx
from .api_utils import APIError, retry_on_failure
from app.services.cache_service import cache
from ..models.gene_models import Exon
from config import config

class NCBIClient:
    """Клиент для работы с NCBI EUtils API"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    async def get_exons_data(self, identifier: str) -> List[Exon]:
        """
        Получить данные об экзонах из NCBI
        """
        try:
            data = await self._fetch_ncbi_data(identifier)
            return self._process_ncbi_exons(data)
        except Exception as e:
            self.logger.error(f"Failed to get NCBI exons for {identifier}: {e}")
            raise APIError(f"Failed to get NCBI exons: {e}")
    
    async def get_sequence_data(self, identifier: str) -> Tuple[str, int, int]:
        """
        Получить последовательность из NCBI
        Возвращает: (sequence, utr5_start, utr3_start)
        """
        try:
            data = await self._fetch_ncbi_data(identifier)
            return self._process_ncbi_sequence(data)
        except Exception as e:
            self.logger.error(f"Failed to get NCBI sequence for {identifier}: {e}")
            raise APIError(f"Failed to get NCBI sequence: {e}")
    
    @retry_on_failure(max_retries=3, delay=1.0)
    @cache.cached
    async def _fetch_ncbi_data(self, identifier: str, task: str = "seq_exons") -> Dict[str, Any]:
        """Получить данные из NCBI EUtils"""
        url = config.NCBI_EUTILS_URL
        params = {
            "db": "nuccore",
            "retmode": "xml",
            "id": identifier
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{url}?{'&'.join([f'{k}={v}' for k, v in params.items()])}")
            if not response.is_success:
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
                    length = end - start + 1
                    
                    # Создаем объект экзона
                    exon = Exon(
                        number=exon_number,
                        start_position=current_position,
                        end_position=current_position + length - 1,
                        start_phase=0,
                        end_phase=0,
                        length=length,
                    )
                    
                    exons.append(exon)
                    current_position += length
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
                    utr5_start = cds_start
                    utr3_start = cds_end
                    
                    break
            
            return sequence, utr5_start, len(sequence) - utr3_start - 1
            
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
    async def get_exons_legacy(self, identifier: str) -> List[Tuple[int, int]]:
        """Старый метод для получения экзонов (совместимость)"""
        exons = await self.get_exons_data(identifier)
        return [(exon.start_position, exon.end_position) for exon in exons]
    
    async def get_sequence_legacy(self, identifier: str) -> Tuple[str, int, int]:
        """Старый метод для получения последовательности (совместимость)"""
        return await self.get_sequence_data(identifier)