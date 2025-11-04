from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum

class AnalysisStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    ERROR = "error"

@dataclass
class AnalysisRequest:
    """Запрос на анализ"""
    gene_id: str
    species: str
    mutations: List[Mutation]
    include_domains: bool = True
    include_visualization: bool = True
    cache_results: bool = True
    
    def to_dict(self) -> Dict:
        return {
            'gene_id': self.gene_id,
            'species': self.species,
            'mutations': [mutation.to_dict() for mutation in self.mutations],
            'include_domains': self.include_domains,
            'include_visualization': self.include_visualization,
            'cache_results': self.cache_results
        }

@dataclass
class AnalysisResult:
    """Результат анализа"""
    request: AnalysisRequest
    results: List[MutationResult]
    status: AnalysisStatus
    execution_time: float
    timestamp: str
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            'request': self.request.to_dict(),
            'results': [result.to_dict() for result in self.results],
            'status': self.status.value,
            'execution_time': self.execution_time,
            'timestamp': self.timestamp,
            'error_message': self.error_message
        }

@dataclass
class VisualizationConfig:
    """Конфигурация визуализации"""
    colors: Dict[str, str] = field(default_factory=lambda: {
        'highlight_red': '#ff4444',
        'highlight_pink': '#ff69b4',
        'highlight_blue': '#0000ff',
        'highlight_green': '#00ff00',
        'domain_original': '#e8f4fd',
        'domain_modified': '#fff0f0',
        'exon_normal': '#f9f9f9',
        'exon_modified': '#fff9c4',
        'mutation_effect_high': '#ff6b6b',
        'mutation_effect_medium': '#ffd93d',
        'mutation_effect_low': '#6bcf7f'
    })
    
    show_domains: bool = True
    show_exons: bool = True
    show_sequences: bool = True
    highlight_changes: bool = True
    max_display_length: int = 1000
    
    def to_dict(self) -> Dict:
        return {
            'colors': self.colors,
            'show_domains': self.show_domains,
            'show_exons': self.show_exons,
            'show_sequences': self.show_sequences,
            'highlight_changes': self.highlight_changes,
            'max_display_length': self.max_display_length
        }