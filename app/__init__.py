from flask import Flask
from flask_cors import CORS
from .routes import api_bp

def create_app():
    """Фабрика для создания приложения Flask"""
    app = Flask(__name__)
    
    # Базовая конфигурация
    app.config.from_object('config.Config')
    
    # Включаем CORS
    CORS(app)
    
    # Регистрируем blueprint
    app.register_blueprint(api_bp, url_prefix='/api')
    
    # Простой маршрут для проверки работы
    @app.route('/')
    def index():
        return {
            'message': 'Genetic Mutation Analyzer API',
            'version': '1.0.0',
            'status': 'running'
        }
    
    @app.route('/health')
    def health():
        return {'status': 'healthy'}
    
    return app

# Глобальный экземпляр приложения
app = create_app()