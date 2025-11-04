from flask import Blueprint, request, jsonify, render_template
from .services import analysis_service, gene_service
from .models.analysis_models import AnalysisRequest
from .models.mutation_models import Mutation, MutationType
from .utils.validators import Validators

# Создаем blueprint для API
api_bp = Blueprint('api', __name__)
validators = Validators()

@api_bp.route('/analyze', methods=['POST'])
def analyze_mutations():
    """
    Основной endpoint для анализа мутаций
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        # Валидация запроса
        validation_errors = analysis_service.validate_analysis_request(data)
        if validation_errors:
            return jsonify({'errors': validation_errors}), 400
        
        # Создаем объекты мутаций
        mutations = []
        for mutation_data in data.get('mutations', []):
            mutation = Mutation(
                type=MutationType(mutation_data['type']),
                position=mutation_data['position'],
                length=mutation_data.get('length', 1),
                new_sequence=mutation_data.get('new_sequence', ''),
                exon_number=mutation_data.get('exon_number'),
                description=mutation_data.get('description', '')
            )
            mutations.append(mutation)
        
        # Создаем запрос на анализ
        analysis_request = AnalysisRequest(
            gene_id=data['gene_id'],
            species=data.get('species', 'human'),
            mutations=mutations,
            include_domains=data.get('include_domains', True),
            include_visualization=data.get('include_visualization', True)
        )
        
        # Выполняем анализ
        result = analysis_service.perform_analysis(analysis_request)
        
        # Возвращаем результат
        if result.status.value == 'completed':
            return jsonify(result.frontend_data)
        else:
            return jsonify({
                'error': result.error_message,
                'status': result.status.value
            }), 500
            
    except Exception as e:
        return jsonify({'error': f'Analysis failed: {str(e)}'}), 500

@api_bp.route('/genes/search', methods=['GET'])
def search_genes():
    """
    Поиск генов по названию или символу
    """
    try:
        query = request.args.get('q', '')
        species = request.args.get('species', 'human')
        limit = int(request.args.get('limit', '10'))
        
        if not query:
            return jsonify({'error': 'Query parameter "q" is required'}), 400
        
        results = gene_service.search_genes(query, species, limit)
        return jsonify({'results': results})
        
    except Exception as e:
        return jsonify({'error': f'Search failed: {str(e)}'}), 500

@api_bp.route('/genes/<gene_id>', methods=['GET'])
def get_gene_info(gene_id: str):
    """
    Получение информации о гене
    """
    try:
        species = request.args.get('species', 'human')
        
        # Валидация gene_id
        validation = validators.validate_gene_id(gene_id)
        if not validation['valid']:
            return jsonify({'errors': validation['errors']}), 400
        
        gene_data = gene_service.get_gene_with_protein(gene_id, species)
        return jsonify(gene_data.to_dict())
        
    except Exception as e:
        return jsonify({'error': f'Failed to get gene info: {str(e)}'}), 500

@api_bp.route('/species', methods=['GET'])
def get_species():
    """
    Получение списка доступных видов
    """
    try:
        species_list = analysis_service.get_available_species()
        return jsonify({'species': species_list})
    except Exception as e:
        return jsonify({'error': f'Failed to get species list: {str(e)}'}), 500

@api_bp.route('/validate/gene', methods=['POST'])
def validate_gene():
    """
    Валидация ID гена
    """
    try:
        data = request.get_json()
        gene_id = data.get('gene_id')
        species = data.get('species', 'human')
        
        if not gene_id:
            return jsonify({'error': 'gene_id is required'}), 400
        
        is_valid = gene_service.validate_gene_id(gene_id, species)
        return jsonify({
            'gene_id': gene_id,
            'valid': is_valid,
            'species': species
        })
        
    except Exception as e:
        return jsonify({'error': f'Validation failed: {str(e)}'}), 500

@api_bp.route('/cache/clear', methods=['POST'])
def clear_cache():
    """
    Очистка кэша
    """
    try:
        analysis_service.clear_cache()
        return jsonify({'message': 'Cache cleared successfully'})
    except Exception as e:
        return jsonify({'error': f'Cache clear failed: {str(e)}'}), 500

# Обработчики ошибок
@api_bp.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@api_bp.errorhandler(405)
def method_not_allowed(error):
    return jsonify({'error': 'Method not allowed'}), 405

@api_bp.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500