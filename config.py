import os

class Config:
    """Конфигурация приложения"""
    
    # Базовые настройки
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    MODE = os.environ.get('DEBUG', 'True').lower() == 'true'
    
    # Настройки API
    ENSEMBL_REST_URL = "https://rest.ensembl.org"
    ENSEMBL_REST_URL_LOOKUP = f"https://rest.ensembl.org/lookup/id/"
    ENSEMBL_REST_URL_SEQUENCE = f"https://rest.ensembl.org/sequence/id/"

    UNIPROT_REST_URL = "https://rest.uniprot.org/uniprotkb/"

    NCBI_EUTILS_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"

# Глобальный экземпляр конфигурации
config = Config()