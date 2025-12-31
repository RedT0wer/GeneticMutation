from flask import Blueprint, request, jsonify, render_template
from .services.gene_service import GeneService
from .services.mutation_service import MutationService
from .models.mutation_models import (
    Mutation, MutationType, 
    SubstitutionMutation, InsertionMutation, 
    DeletionMutation, ExonDeletionMutation
)
from .utils.validators import Validators

# Создаем blueprint для API
api_bp = Blueprint('api', __name__)
validators = Validators()
mutation_service = MutationService()
gene_service = GeneService()

# Маршруты для работы с генами
@api_bp.route('/gene/build', methods=['POST'])
def build_gene():
    """
    Построить структуру гена из данных внешних API
    """
    try:
        data = request.get_json()
        
        # Валидация входных данных
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        source = data.get('source')  # 'ensembl' или 'ncbi'
        gene_id = data.get('gene_id')
        protein_id = data.get('protein_id')
        
        if not source or not gene_id or not protein_id:
            return jsonify({
                'error': 'Missing required parameters: source, gene_id, protein_id'
            }), 400
        
        if source not in ['ensembl', 'ncbi']:
            return jsonify({
                'error': 'Invalid source. Must be "ensembl" or "ncbi"'
            }), 400
        
        # Построение гена
        gene = None
        if source == 'ensembl':
            gene = gene_service.build_gene_from_ensembl(gene_id, protein_id)
        elif source == 'ncbi':
            gene = gene_service.build_gene_from_ncbi(gene_id, protein_id)
        
        if not gene:
            return jsonify({'error': 'Failed to build gene structure'}), 500
        
        # Преобразование гена в словарь для JSON
        gene_dict = _gene_to_dict(gene)
        
        return jsonify({
            'success': True,
            'gene': gene_dict
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Error building gene: {str(e)}'}), 500

@api_bp.route('/gene/mutate', methods=['POST'])
def apply_mutation():
    """
    Применить мутацию к гену
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        # Получаем данные гена
        gene_data = data.get('gene')
        if not gene_data:
            return jsonify({'error': 'Gene data is required'}), 400
        
        # Строим объект Gene из данных
        gene = _dict_to_gene(gene_data)
        
        # Получаем данные мутации
        mutation_data = data.get('mutation')
        if not mutation_data:
            return jsonify({'error': 'Mutation data is required'}), 400
        
        # Создаем объект мутации
        mutation = _create_mutation_object(mutation_data)
        if not mutation:
            return jsonify({'error': 'Invalid mutation type or data'}), 400
        
        # Применяем мутацию
        result = mutation_service.apply_mutation(mutation, gene)
        
        # Преобразуем результат в словарь
        result_dict = _mutation_result_to_dict(result)
        
        return jsonify({
            'success': True,
            'mutation_result': result_dict,
            'mutation_type': mutation.mutation_type.value
        }), 200
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': f'Error applying mutation: {str(e)}'}), 500

@api_bp.route('/gene/mutate/batch', methods=['POST'])
def apply_batch_mutations():
    """
    Применить несколько мутаций к гену
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        gene_data = data.get('gene')
        if not gene_data:
            return jsonify({'error': 'Gene data is required'}), 400
        
        mutations_data = data.get('mutations', [])
        if not mutations_data:
            return jsonify({'error': 'Mutations data is required'}), 400
        
        # Строим объект Gene
        gene = _dict_to_gene(gene_data)
        
        results = []
        for mutation_data in mutations_data:
            try:
                mutation = _create_mutation_object(mutation_data)
                if mutation:
                    result = mutation_service.apply_mutation(mutation, gene)
                    result_dict = _mutation_result_to_dict(result)
                    results.append({
                        'mutation': mutation_data,
                        'result': result_dict,
                        'success': True
                    })
                else:
                    results.append({
                        'mutation': mutation_data,
                        'result': None,
                        'success': False,
                        'error': 'Invalid mutation data'
                    })
            except Exception as e:
                results.append({
                    'mutation': mutation_data,
                    'result': None,
                    'success': False,
                    'error': str(e)
                })
        
        return jsonify({
            'success': True,
            'results': results
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Error applying batch mutations: {str(e)}'}), 500

@api_bp.route('/mutation/types', methods=['GET'])
def get_mutation_types():
    """
    Получить список доступных типов мутаций
    """
    mutation_types = [
        {
            'type': mutation_type.value,
            'description': _get_mutation_description(mutation_type)
        }
        for mutation_type in MutationType
    ]
    
    return jsonify({
        'success': True,
        'mutation_types': mutation_types
    }), 200

# Вспомогательные функции
def _gene_to_dict(gene):
    """
    Преобразовать объект Gene в словарь для JSON
    """
    if not gene:
        return None
    
    return {
        'protein': {
            'identifier': gene.protein.identifier,
            'sequence': gene.protein.sequence,
            'length': gene.protein.length,
            'domains': [
                {
                    'name': domain.name,
                    'start': domain.start,
                    'end': domain.end,
                    'sequence': domain.sequence,
                    'type': domain.type
                }
                for domain in gene.protein.domains
            ]
        },
        'base_sequence': {
            'identifier': gene.base_sequence.identifier,
            'length': gene.base_sequence.length,
            'full_sequence': gene.base_sequence.full_sequence,
            'exons': [
                {
                    'number': exon.number,
                    'start_position': exon.start_position,
                    'end_position': exon.end_position,
                    'start_phase': exon.start_phase,
                    'end_phase': exon.end_phase,
                    'length': exon.length
                }
                for exon in gene.base_sequence.exons
            ],
            'utr5': {
                'sequence': gene.base_sequence.utr5.sequence,
                'start_position': gene.base_sequence.utr5.start_position,
                'end_position': gene.base_sequence.utr5.end_position,
                'length': gene.base_sequence.utr5.length
            },
            'utr3': {
                'sequence': gene.base_sequence.utr3.sequence,
                'start_position': gene.base_sequence.utr3.start_position,
                'end_position': gene.base_sequence.utr3.end_position,
                'length': gene.base_sequence.utr3.length
            }
        }
    }

def _dict_to_gene(gene_dict):
    """
    Преобразовать словарь обратно в объект Gene
    (упрощенная версия, в реальном проекте нужна полная реализация)
    """
    # Для простоты возвращаем исходный словарь
    # В реальном проекте здесь нужно создать объекты моделей
    return gene_dict

def _create_mutation_object(mutation_data):
    """
    Создать объект мутации из данных
    """
    mutation_type_str = mutation_data.get('mutation_type')
    
    try:
        mutation_type = MutationType(mutation_type_str)
    except ValueError:
        return None
    
    if mutation_type == MutationType.SUBSTITUTION:
        return SubstitutionMutation(
            mutation_type=mutation_type,
            new_nucleotide=mutation_data.get('new_nucleotide'),
            position_nucleotide=mutation_data.get('position_nucleotide')
        )
    elif mutation_type == MutationType.INSERTION:
        return InsertionMutation(
            mutation_type=mutation_type,
            inserted_sequence=mutation_data.get('inserted_sequence'),
            start_position=mutation_data.get('start_position'),
            end_position=mutation_data.get('end_position')
        )
    elif mutation_type == MutationType.DELETION:
        return DeletionMutation(
            mutation_type=mutation_type,
            start_position=mutation_data.get('start_position'),
            end_position=mutation_data.get('end_position')
        )
    elif mutation_type == MutationType.EXON_DELETION:
        return ExonDeletionMutation(
            mutation_type=mutation_type,
            nucleotide_position=mutation_data.get('nucleotide_position')
        )
    
    return None

def _mutation_result_to_dict(result):
    """
    Преобразовать результат мутации в словарь
    """
    if hasattr(result, 'new_aminoacid'):
        return {
            'type': 'substitution',
            'new_aminoacid': result.new_aminoacid
        }
    elif hasattr(result, 'new_domain'):
        return {
            'type': result.__class__.__name__.replace('Result', '').lower(),
            'new_domain': {
                'name': result.new_domain.name,
                'start': result.new_domain.start,
                'end': result.new_domain.end,
                'sequence': result.new_domain.sequence,
                'type': result.new_domain.type
            },
            'different_position': result.different_position,
            'stop_codon_position': result.stop_codon_position
        }
    return {}

def _get_mutation_description(mutation_type):
    """
    Получить описание типа мутации
    """
    descriptions = {
        MutationType.SUBSTITUTION: "Замена одного нуклеотида на другой",
        MutationType.INSERTION: "Вставка последовательности нуклеотидов",
        MutationType.DELETION: "Удаление последовательности нуклеотидов",
        MutationType.EXON_DELETION: "Удаление целого экзона"
    }
    return descriptions.get(mutation_type, "Неизвестный тип мутации")

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

# Дополнительные маршруты для отладки и тестирования
@api_bp.route('/health', methods=['GET'])
def health_check():
    """Проверка работоспособности API"""
    return jsonify({
        'status': 'healthy',
        'service': 'Gene Mutation API',
        'version': '1.0.0'
    }), 200