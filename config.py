import os
from typing import Dict, Any

class Config:
    """Конфигурация приложения"""
    
    # Базовые настройки
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    DEBUG = os.environ.get('DEBUG', 'True').lower() == 'true'
    
    # Настройки API
    ENSEMBL_REST_URL = "https://rest.ensembl.org"
    ENSEMBL_REST_URL_LOOKUP = f"https://rest.ensembl.org/lookup/id/"
    ENSEMBL_REST_URL_SEQUENCE = f"https://rest.ensembl.org/sequence/id/"

    UNIPROT_REST_URL = "https://rest.uniprot.org"
    NCBI_EUTILS_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
    
    # Настройки кэша
    CACHE_ENABLED = True
    CACHE_DEFAULT_TTL = 3600  # 1 час
    
    # Настройки приложения
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    UPLOAD_FOLDER = 'uploads'
    ALLOWED_EXTENSIONS = {'json', 'csv', 'txt', 'fasta', 'fa'}
    
    # Цветовая схема для визуализации
    COLORS = {
        'highlight_red': '#ff4444',
        'highlight_pink': '#ff69b4', 
        'highlight_blue': '#4444ff',
        'highlight_green': '#44ff44',
        'domain_original': '#e8f4fd',
        'domain_modified': '#fff0f0',
        'exon_normal': '#f9f9f9',
        'exon_edited': '#fff9c4'
    }

# Глобальный экземпляр конфигурации
config = Config()