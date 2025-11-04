import logging
import time
from typing import List, Dict, Any, Optional
from datetime import datetime
from ..models.gene_models import Gene
from ..models.mutation_models import Mutation, MutationResult
from ..models.analysis_models import AnalysisRequest, AnalysisResult, AnalysisStatus
from .gene_service import GeneService
from .mutation_service import MutationService
from .data_service import DataService

class AnalysisService:
    """
    Координирующий сервис для управления всем процессом анализа
    Объединяет работу GeneService, MutationService и DataService
    """
    
    def __init__(self):
        self.gene_service = GeneService()
        self.mutation_service = MutationService()
        self.data_service = DataService()
        self.logger = logging.getLogger(__name__)
    
    def perform_analysis(self, request: AnalysisRequest) -> AnalysisResult:
        """
        Выполнить полный анализ: загрузка гена + анализ мутаций + подготовка данных
        """
        start_time = time.time()
        
        try:
            self.logger.info(f"Starting analysis for gene {request.gene_id}")
            
            # 1. Загружаем данные гена
            gene = self.gene_service.get_gene_with_protein(request.gene_id, request.species)
            
            # 2. Анализируем мутации
            mutation_results = self.mutation_service.analyze_multiple_mutations(gene, request.mutations)
            
            # 3. Подготавливаем данные для фронтенда
            frontend_data = self._prepare_frontend_data(gene, mutation_results, request)
            
            execution_time = time.time() - start_time
            
            return AnalysisResult(
                request=request,
                results=mutation_results,
                status=AnalysisStatus.COMPLETED,
                execution_time=execution_time,
                timestamp=datetime.now().isoformat(),
                frontend_data=frontend_data
            )
            
        except Exception as e:
            self.logger.error(f"Analysis failed for gene {request.gene_id}: {e}")
            execution_time = time.time() - start_time
            
            return AnalysisResult(
                request=request,
                results=[],
                status=AnalysisStatus.ERROR,
                execution_time=execution_time,
                timestamp=datetime.now().isoformat(),
                error_message=str(e)
            )
    
    def _prepare_frontend_data(self, gene: Gene, mutation_results: List[MutationResult], request: AnalysisRequest) -> Dict[str, Any]:
        """Подготовить все данные для фронтенда"""
        return {
            'gene_data': self.data_service.prepare_gene_data_for_frontend(gene),
            'mutation_results': [
                self.data_service.prepare_mutation_result_for_frontend(result)
                for result in mutation_results
            ],
            'analysis_summary': {
                'gene_id': gene.id,
                'gene_name': gene.name,
                'mutations_count': len(mutation_results),
                'species': gene.species,
                'timestamp': datetime.now().isoformat()
            }
        }
    
    def validate_analysis_request(self, request_data: Dict) -> List[str]:
        """
        Валидация запроса на анализ
        Возвращает список ошибок или пустой список если все ок
        """
        errors = []
        
        # Проверяем обязательные поля
        if not request_data.get('gene_id'):
            errors.append("Gene ID is required")
        
        if not request_data.get('mutations'):
            errors.append("At least one mutation is required")
        
        # Проверяем валидность gene_id
        gene_id = request_data.get('gene_id')
        species = request_data.get('species', 'human')
        if gene_id and not self.gene_service.validate_gene_id(gene_id, species):
            errors.append(f"Invalid gene ID: {gene_id}")
        
        # Проверяем мутации
        mutations = request_data.get('mutations', [])
        for i, mutation_data in enumerate(mutations):
            mutation_errors = self._validate_mutation_data(mutation_data, i)
            errors.extend(mutation_errors)
        
        return errors
    
    def _validate_mutation_data(self, mutation_data: Dict, index: int) -> List[str]:
        """Валидация данных мутации"""
        errors = []
        
        if not mutation_data.get('type'):
            errors.append(f"Mutation {index}: type is required")
        
        if mutation_data.get('position') is None:
            errors.append(f"Mutation {index}: position is required")
        elif not isinstance(mutation_data['position'], int) or mutation_data['position'] < 0:
            errors.append(f"Mutation {index}: position must be a positive integer")
        
        mutation_type = mutation_data.get('type')
        if mutation_type in ['substitution', 'insertion'] and not mutation_data.get('new_sequence'):
            errors.append(f"Mutation {index}: new_sequence is required for {mutation_type}")
        
        return errors
    
    def get_available_species(self) -> List[str]:
        """Получить список доступных видов"""
        return self.gene_service.get_available_species()
    
    def search_genes(self, query: str, species: str = "human") -> List[Dict]:
        """Поиск генов"""
        return self.gene_service.search_genes(query, species)
    
    def clear_cache(self):
        """Очистить кэш всех сервисов"""
        try:
            self.gene_service.clear_gene_cache()
            self.logger.info("Cache cleared successfully")
        except Exception as e:
            self.logger.warning(f"Failed to clear cache: {e}")