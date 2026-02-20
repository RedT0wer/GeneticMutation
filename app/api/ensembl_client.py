import logging
from typing import List, Dict, Any, Optional, Tuple
import httpx
from .api_utils import APIError, retry_on_failure
from ..models.gene_models import Exon
from config import config

class EnsemblClient:
    """Клиент для работы с Ensembl REST API"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    async def get_exons_data(self, gene_id: str) -> List[Exon]:
        """
        Получить данные об экзонах гена
        Возвращает список экзонов с правильными позициями
        """
        try:
            # Получаем расширенную информацию о гене
            gene_data = await self._get_gene_with_exons(gene_id)
            # Получаем последовательности экзонов
            exon_sequences = await self._get_exon_sequences(gene_id)
            
            return self._process_exons_data(gene_data, exon_sequences)
        except Exception as e:
            self.logger.error(f"Failed to get exons data for {gene_id}: {e}")
            raise APIError(f"Failed to get exons data: {e}")
    
    async def get_sequence_data(self, transcript_id: str) -> Tuple[str, int, int]:
        """
        Получить последовательность транскрипта
        Возвращает: (sequence, utr5_start, utr3_start)
        """
        try:
            data = await self._get_sequence(transcript_id)
            return self._process_sequence_data(data)
        except Exception as e:
            self.logger.error(f"Failed to get sequence for {transcript_id}: {e}")
            raise APIError(f"Failed to get sequence: {e}")
    
    @retry_on_failure(max_retries=3, delay=1.0)
    async def _get_gene_with_exons(self, gene_id: str) -> Dict[str, Any]:
        """Получить расширенную информацию о гене с экзонами"""
        url = config.ENSEMBL_REST_URL_LOOKUP + gene_id
        params = {
            "expand": "1",
            "content-type": "application/json"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{url}?{'&'.join([f'{k}={v}' for k, v in params.items()])}")
            if not response.is_success:
                raise APIError(f"Ensembl API error: {response.status_code}")
            
            return response.json()
    
    @retry_on_failure(max_retries=3, delay=1.0)
    async def _get_exon_sequences(self, transcript_id: str) -> Dict[str, Any]:
        """Получить последовательности экзонов"""
        url = config.ENSEMBL_REST_URL_SEQUENCE + transcript_id
        params = {
            "mask_feature": "1",
            "type": "cdna", 
            "content-type": "application/json",
            "multiple_sequences": "1"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{url}?{'&'.join([f'{k}={v}' for k, v in params.items()])}")
            if not response.is_success:
                raise APIError(f"Ensembl sequence API error: {response.status_code}")
            
            return response.json()
    
    @retry_on_failure(max_retries=3, delay=1.0)
    async def _get_sequence(self, identifier: str) -> Dict[str, Any]:
        """Получить последовательность (оригинальный метод)"""
        url = config.ENSEMBL_REST_URL_SEQUENCE + identifier
        params = {
            "mask_feature": "1",
            "type": "cdna",
            "content-type": "application/json"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{url}?{'&'.join([f'{k}={v}' for k, v in params.items()])}")
            if not response.is_success:
                raise APIError(f"Ensembl sequence API error: {response.status_code}")
            
            return response.json()
    
    def _process_exons_data(self, gene_data: Dict, exon_sequences: Dict) -> List[Exon]:
        """Обработка данных экзонов (улучшенная версия)"""
        exons = []
        
        # Получаем экзоны из ответа
        raw_exons = gene_data.get("Exon", [])
        if not raw_exons:
            raise APIError("No exons found in response")
        
        # Обрабатываем каждый экзон
        current_position = 0
        for i, exon_data in enumerate(raw_exons, 1):            
            # Вычисляем позиции в конкатенированной последовательности
            start_pos = current_position
            end_pos = current_position + int(exon_data.get("end")) - int(exon_data.get("start"))
            
            exon = Exon(
                number=i,
                start_position=start_pos,
                end_position=end_pos,
                start_phase=0,
                end_phase=0,
                length=end_pos - start_pos + 1,
            )
            
            exons.append(exon)
            current_position = end_pos + 1
        
        return exons
    
    def _extract_exon_sequence(self, start_pos: int, end_pos: int, exon_sequences: Dict) -> str:
        """Извлечь последовательность конкретного экзона"""
        try:
            sequence = exon_sequences.get("seq")
            return sequence[start_pos:end_pos + 1]
        except:
            self.logger.warning(f"Sequence not found for exon {start_pos}:{end_pos}")
            return ""
    
    def _process_sequence_data(self, response: Dict) -> Tuple[str, int, int]:
        """Обработка данных последовательности"""
        sequence = response.get("seq", "")
        
        utr5_start = 0 if sequence[0].islower() else -1
        while utr5_start < len(sequence) and sequence[utr5_start].islower():
            utr5_start += 1

        utr3_start = 0 if sequence[-1].islower() else -1
        while utr3_start >= 0 and sequence[len(sequence) - 1 - utr3_start].islower():
            utr3_start += 1
        
        return sequence.upper(), utr5_start, utr3_start
    
    # Старые методы для обратной совместимости
    async def get_exons_legacy(self, identifier: str) -> List[Tuple[int, int]]:
        """Старый метод для получения экзонов (совместимость)"""
        exons = await self.get_exons_data(identifier)
        return [(exon.start_position, exon.end_position) for exon in exons]
    
    async def get_sequence_legacy(self, identifier: str) -> Tuple[str, int, int]:
        """Старый метод для получения последовательности (совместимость)"""
        return await self.get_sequence_data(identifier)