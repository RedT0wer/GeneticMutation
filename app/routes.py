from flask import Blueprint, request, jsonify, render_template
from .services.gene_service import GeneService
from .services.mutation_service import MutationService
from .models.mutation_models import (
    Mutation, MutationType, 
    SubstitutionMutation, InsertionMutation, 
    DeletionMutation
)
from .models.gene_models import (
    Exon, ProteinDomain, UTR,
    BaseSequence, Protein,
    Gene
)

# Создаем blueprint для API
api_bp = Blueprint('api', __name__)
mutation_service = MutationService()
gene_service = GeneService()

# Маршруты для работы с генами
@api_bp.route('/gene/build', methods=['POST'])
async def build_gene():
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
            gene = await gene_service.build_gene_from_ensembl(gene_id, protein_id)
        elif source == 'ncbi':
            gene = await gene_service.build_gene_from_ncbi(gene_id, protein_id)
        
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

        return jsonify({
            'success': True,
            'data': result.to_dict(),
            'type': mutation.mutation_type.value,
        }), 200
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': f'Error applying mutation: {str(e)}'}), 500

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
    Преобразовать словарь обратно в объект Gene.
    """
    if not gene_dict:
        return None

    # Создаем объекты для доменов
    domains = [
        ProteinDomain(
            name=domain['name'],
            start=domain['start'],
            end=domain['end'],
            sequence=domain['sequence'],
            type=domain['type']
        ) for domain in gene_dict['protein']['domains']
    ]
    
    # Создаем объект Protein
    protein = Protein(
        identifier=gene_dict['protein']['identifier'],
        sequence=gene_dict['protein']['sequence'],
        length=gene_dict['protein']['length'],
        domains=domains
    )
    
    # Создаем объекты для экзонов
    exons = [
        Exon(
            number=exon['number'],
            start_position=exon['start_position'],
            end_position=exon['end_position'],
            start_phase=exon['start_phase'],
            end_phase=exon['end_phase'],
            length=exon['length']
        ) for exon in gene_dict['base_sequence']['exons']
    ]

    # Создаем объект UTR
    utr5 = UTR(
        sequence=gene_dict['base_sequence']['utr5']['sequence'],
        start_position=gene_dict['base_sequence']['utr5']['start_position'],
        end_position=gene_dict['base_sequence']['utr5']['end_position'],
        length=gene_dict['base_sequence']['utr5']['length']
    )

    utr3 = UTR(
        sequence=gene_dict['base_sequence']['utr3']['sequence'],
        start_position=gene_dict['base_sequence']['utr3']['start_position'],
        end_position=gene_dict['base_sequence']['utr3']['end_position'],
        length=gene_dict['base_sequence']['utr3']['length']
    )

    # Создаем объект BaseSequence
    base_sequence = BaseSequence(
        identifier=gene_dict['base_sequence']['identifier'],
        length=gene_dict['base_sequence']['length'],
        full_sequence=gene_dict['base_sequence']['full_sequence'],
        exons=exons,
        utr5=utr5,
        utr3=utr3
    )

    # Создаем и возвращаем объект Gene
    return Gene(
        protein=protein,
        base_sequence=base_sequence
    )

def _create_mutation_object(mutation_data):
    """
    Создать объект мутации из данных
    """
    mutation_type = mutation_data.get('mutation_type')
    
    if mutation_type == MutationType.SUBSTITUTION.name:
        return SubstitutionMutation(
            mutation_type=MutationType.SUBSTITUTION,
            new_nucleotide=mutation_data.get('new_nucleotide'),
            position_nucleotide=mutation_data.get('position_nucleotide')
        )
    elif mutation_type == MutationType.INSERTION.name:
        return InsertionMutation(
            mutation_type=MutationType.INSERTION,
            inserted_sequence=mutation_data.get('inserted_sequence'),
            start_position=mutation_data.get('start_position'),
            end_position=mutation_data.get('end_position')
        )
    elif mutation_type == MutationType.DELETION.name:
        return DeletionMutation(
            mutation_type=MutationType.DELETION,
            start_position=mutation_data.get('start_position'),
            end_position=mutation_data.get('end_position')
        )
    
    return None

def _get_mutation_description(mutation_type):
    """
    Получить описание типа мутации
    """
    descriptions = {
        MutationType.SUBSTITUTION: "Замена одного нуклеотида на другой",
        MutationType.INSERTION: "Вставка последовательности нуклеотидов",
        MutationType.DELETION: "Удаление последовательности нуклеотидов",
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