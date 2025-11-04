import logging
from typing import List, Dict, Any, Optional, Tuple
from requests import get
from .api_utils import APIUtils, APIError, retry_on_failure
from ..models.gene_models import Exon, Strand

class EnsemblClient:
    """Клиент для работы с Ensembl REST API (обновленная версия)"""
    
    def __init__(self):
        self.api = APIUtils(
            base_url="https://rest.ensembl.org",
            #cache_config=CacheConfig(enabled=True, default_ttl=7200)
        )
        self.logger = logging.getLogger(__name__)
    
    def get_exons_data(self, gene_id: str) -> List[Exon]:
        """
        Получить данные об экзонах гена
        Возвращает список экзонов с правильными позициями
        """
        try:
            # Получаем расширенную информацию о гене
            gene_data = self._get_gene_with_exons(gene_id)
            # Получаем последовательности экзонов
            exon_sequences = self._get_exon_sequences(gene_id)
            
            return self._process_exons_data(gene_data, exon_sequences)
        except Exception as e:
            self.logger.error(f"Failed to get exons data for {gene_id}: {e}")
            raise APIError(f"Failed to get exons data: {e}")
    
    def get_sequence_data(self, transcript_id: str) -> Tuple[str, int, int]:
        """
        Получить последовательность транскрипта
        Возвращает: (sequence, utr5_start, utr3_start)
        """
        try:
            data = self._get_sequence(transcript_id)
            return self._process_sequence_data(data)
        except Exception as e:
            self.logger.error(f"Failed to get sequence for {transcript_id}: {e}")
            raise APIError(f"Failed to get sequence: {e}")
    
    @retry_on_failure(max_retries=3, delay=1.0)
    def _get_gene_with_exons(self, gene_id: str) -> Dict[str, Any]:
        """Получить расширенную информацию о гене с экзонами"""
        url = f"https://rest.ensembl.org/lookup/id/{gene_id}"
        params = {
            "expand": "1",
            "content-type": "application/json"
        }
        
        response = get(f"{url}?{'&'.join([f'{k}={v}' for k, v in params.items()])}")
        if not response.ok:
            raise APIError(f"Ensembl API error: {response.status_code}")
        
        return response.json()
    
    @retry_on_failure(max_retries=3, delay=1.0)
    def _get_exon_sequences(self, transcript_id: str) -> Dict[str, Any]:
        """Получить последовательности экзонов"""
        url = f"https://rest.ensembl.org/sequence/id/{transcript_id}"
        params = {
            "mask_feature": "1",
            "type": "cdna", 
            "content-type": "application/json",
            "multiple_sequences": "1"
        }
        
        response = get(f"{url}?{'&'.join([f'{k}={v}' for k, v in params.items()])}")
        if not response.ok:
            raise APIError(f"Ensembl sequence API error: {response.status_code}")
        
        return response.json()
    
    @retry_on_failure(max_retries=3, delay=1.0)
    def _get_sequence(self, identifier: str) -> Dict[str, Any]:
        """Получить последовательность (оригинальный метод)"""
        url = f"https://rest.ensembl.org/sequence/id/{identifier}"
        params = {
            "mask_feature": "1",
            "type": "cdna",
            "content-type": "application/json"
        }
        
        response = get(f"{url}?{'&'.join([f'{k}={v}' for k, v in params.items()])}")
        if not response.ok:
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
            # Получаем последовательность экзона
            exon_sequence = self._extract_exon_sequence(exon_data.get("id"), exon_sequences)
            
            # Вычисляем позиции в конкатенированной последовательности
            start_pos = current_position
            end_pos = current_position + len(exon_sequence) - 1
            
            exon = Exon(
                number=i,
                sequence=exon_sequence,
                start_position=start_pos,
                end_position=end_pos,
                length=len(exon_sequence),
                is_modified=False
            )
            
            exons.append(exon)
            current_position = end_pos + 1
        
        return exons
    
    def _extract_exon_sequence(self, exon_id: str, exon_sequences: Dict) -> str:
        """Извлечь последовательность конкретного экзона"""
        if isinstance(exon_sequences, list):
            for exon_seq in exon_sequences:
                if exon_seq.get("id") == exon_id:
                    return exon_seq.get("seq", "")
        elif isinstance(exon_sequences, dict) and exon_sequences.get("id") == exon_id:
            return exon_sequences.get("seq", "")
        
        self.logger.warning(f"Sequence not found for exon {exon_id}")
        return ""
    
    def _process_sequence_data(self, response: Dict) -> Tuple[str, int, int]:
        """Обработка данных последовательности"""
        sequence = response.get("seq", "")
        
        # Для Ensembl UTR позиции обычно не предоставляются в этом endpoint
        # Можно получить их из другого endpoint или оставить -1
        utr5_start = -1
        utr3_start = -1
        
        return sequence, utr5_start, utr3_start
    
    # Старые методы для обратной совместимости
    def get_exons_legacy(self, identifier: str) -> List[Tuple[int, int]]:
        """Старый метод для получения экзонов (совместимость)"""
        exons = self.get_exons_data(identifier)
        return [(exon.start_position, exon.end_position) for exon in exons]
    
    def get_sequence_legacy(self, identifier: str) -> Tuple[str, int, int]:
        """Старый метод для получения последовательности (совместимость)"""
        return self.get_sequence_data(identifier)