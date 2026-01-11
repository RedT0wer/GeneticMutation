from typing import Dict, Type, List, Tuple, Optional
from dataclasses import dataclass
from ..models.gene_models import *
from ..models.mutation_models import *
from ..services.translation_service import TranslationService


class MutationStrategy:
    """Базовый класс стратегии мутации"""
    translation_service = TranslationService()
    
    def execute(self, mutation: Mutation, gene: Gene) -> BaseMutationResult:
        raise NotImplementedError()

    def _translate_nucleotide_position(self, nucleotide_position: int, utr5: UTR) -> int:
        """Пересчет позиции из-за смещения некодируемой области"""
        return nucleotide_position - 1 + utr5.length

    def _find_exon_by_position(self, nucleotide_position: int, gene: Gene) -> Exon:
        """Найти экзон по позиции нуклеотида"""
        for exon in gene.base_sequence.exons:
            if exon.start_position <= nucleotide_position <= exon.end_position:
                return exon

    def _get_codon_by_nucleotide(self, sequence: str, nucleotide_position: int) -> str:
        """Получить кодон по номеру нуклеотида"""
        index = (nucleotide_position // 3) * 3
        return sequence[index:index + 3]
    
    def _get_protein_domain_at_position(self, gene: Gene, nucleotide_position: int) -> ProteinDomain:
        """Получить белковые домены по позиции нуклеотида"""
        aminoacid_position = nucleotide_position // 3
        for domain in gene.protein.domains:
            if domain.start <= aminoacid_position <= domain.end:
                return domain


class SequenceMutationStrategy(MutationStrategy):
    """Базовый класс для стратегий, работающих с последовательностями"""
    
    def _calculate_protein_result(self, mutated_sequence: str,
                                mutation_position: int, protein_domain: ProteinDomain, 
                                utr5: UTR, gene: Gene) -> Tuple[ProteinDomain, int, int]:
        """Рассчитать результат мутации для домена белка"""
        
        # 1. Определяем стартовую позицию для трансляции:
        # Максимум из начала домена и начала экзона, содержащего мутацию
        domain_start_nucleotide = utr5.length + protein_domain.start * 3
        
        # Находим экзон, содержащий мутацию
        mutation_global_pos = self._translate_nucleotide_position(mutation_position, utr5)
        exon_with_mutation = self._find_exon_by_position(mutation_global_pos, gene)
        
        # Стартовая позиция трансляции - либо начало домена, либо начало экзона (что раньше)
        translation_start = max(domain_start_nucleotide, exon_with_mutation.start_position + exon_with_mutation.start_phase)

        # Транслируем до стоп-кодона или конца
        translated_result = self.translation_service.translation_sequence(
            mutated_sequence, 
            translation_start, 
            (len(mutated_sequence) - translation_start) // 3 * 3 - 1
        )
        
        # Находим стоп-кодон в транслированной последовательности
        if translation_start + len(translated_result) * 3 >= gene.base_sequence.utr3.start_position:
            stop_codon_pos = -1
        else:
            stop_codon_pos = translation_start + (len(translated_result) - 1) * 3

        sequence = protein_domain.sequence[:((translation_start - gene.base_sequence.utr5.length) // 3) - protein_domain.end - 1] + translated_result

        # Находим позицию, с которой началась мутация
        diff_pos = (translation_start - gene.base_sequence.utr5.length) // 3
        while diff_pos < len(sequence) + protein_domain.start and sequence[diff_pos - protein_domain.start] == gene.protein.sequence[diff_pos]:
            diff_pos += 1


        # Создаем новый домен
        new_domain = ProteinDomain(
            name=f"{protein_domain.name}_mutated",
            start=protein_domain.start,
            end=protein_domain.start + len(sequence) - 1,
            sequence=sequence,
            type=protein_domain.type
        )
        
        return new_domain, diff_pos, stop_codon_pos


class SubstitutionStrategy(MutationStrategy):
    """Стратегия для замены нуклеотида"""
    
    def _update_full_sequence(self, original_sequence: str, global_position: int, new_nucleotide: str) -> str:
        """Обновить полную последовательность гена"""
        seq_list = list(original_sequence)
        seq_list[global_position] = new_nucleotide
        return ''.join(seq_list)
    
    def execute(self, mutation: SubstitutionMutation, gene: Gene) -> BaseMutationResult:        
        new_nucleotide = mutation.new_nucleotide
        nucleotide_position = mutation.position_nucleotide

        # Переводим позицию с учетом UTR5
        global_position = self._translate_nucleotide_position(nucleotide_position, gene.base_sequence.utr5)
        
        # Строим мутированную последовательность
        original_sequence = gene.base_sequence.full_sequence
        mutated_sequence = self._update_full_sequence(
            original_sequence, global_position, new_nucleotide
        )
        
        # Получаем новый кодон и аминокислоту
        codon = self._get_codon_by_nucleotide(mutated_sequence, global_position)
        new_aminoacid = self.translation_service.get_aminoacid(codon)

        return SubstitutionResult(new_aminoacid=new_aminoacid)


class InsertionStrategy(SequenceMutationStrategy):
    """Стратегия для вставки нуклеотидов"""
    
    def _build_mutated_sequence(self, original_sequence: str, 
                              position: int, inserted_sequence: str, utr3: UTR) -> str:
        """Построить мутированную последовательность с вставкой"""
        return original_sequence[:position + 1] + inserted_sequence + original_sequence[position + 1:utr3.start_position]
    
    def execute(self, mutation: InsertionMutation, gene: Gene) -> BaseMutationResult:
        inserted_sequence = mutation.inserted_sequence
        start_position = mutation.start_position

        # Переводим позицию с учетом UTR5
        global_position = self._translate_nucleotide_position(start_position, gene.base_sequence.utr5)
        
        # Строим мутированную последовательность
        original_sequence = gene.base_sequence.full_sequence
        mutated_sequence = self._build_mutated_sequence(
            original_sequence, global_position, inserted_sequence, gene.base_sequence.utr3
        )
        
        # Получаем затронутый белковый домен
        protein_domain = self._get_protein_domain_at_position(gene, start_position)
        
        # Для затронутого домена строим результат
        new_domain, diff_pos, stop_codon = self._calculate_protein_result(
            mutated_sequence,
            start_position,
            protein_domain,
            gene.base_sequence.utr5,
            gene
        )

        return InsertionResult(
            new_domain=new_domain,
            different_position=diff_pos,
            stop_codon_position=stop_codon
        )


class DeletionStrategy(SequenceMutationStrategy):
    """Стратегия для удаления нуклеотидов"""
    
    def _build_mutated_sequence(self, original_sequence: str, 
                              start_pos: int, end_pos: int, utr3: UTR) -> str:
        """Построить мутированную последовательность с удалением"""
        return original_sequence[:start_pos] + original_sequence[end_pos + 1:utr3.start_position]
    
    def execute(self, mutation: DeletionMutation, gene: Gene) -> BaseMutationResult:
        start_position = mutation.start_position
        end_position = mutation.end_position

        # Переводим позицию с учетом UTR5
        global_position = self._translate_nucleotide_position(start_position, gene.base_sequence.utr5)

        # Строим мутированную последовательность
        original_sequence = gene.base_sequence.full_sequence
        mutated_sequence = self._build_mutated_sequence(
            original_sequence, global_position, global_position + end_position - start_position, gene.base_sequence.utr3
        )
        
        # Получаем затронутый белковый домен
        protein_domain = self._get_protein_domain_at_position(gene, start_position)
        
        # Для затронутого домена строим результат
        new_domain, diff_pos, stop_codon = self._calculate_protein_result(
            mutated_sequence,
            start_position,
            protein_domain,
            gene.base_sequence.utr5,
            gene
        )

        return DeletionResult(
            new_domain=new_domain,
            different_position=diff_pos,
            stop_codon_position=stop_codon
        )


class ExonDeletionStrategy(SequenceMutationStrategy):
    """Стратегия для удаления экзона"""
    
    def _is_first_exon(self, exon: Exon, gene: Gene) -> bool:
        return exon == self._find_exon_by_position(self._translate_nucleotide_position(1, gene.base_sequence.utr5), gene)
    
    def _calculate_start_position(self, gene: Gene, exon_to_delete: Exon) -> int:
        if exon_to_delete.number == 1:
            return 0
        elif self._is_first_exon(exon_to_delete, gene):
            return exon_to_delete.start_position
        else:
            exon = gene.base_sequence.exons[exon_to_delete.number - 2]
            return exon.end_position - exon.end_phase + 1

    def _build_mutated_sequence(self, original_sequence: str, exon_to_delete: Exon, utr3: UTR) -> str:
        """Построить мутированную последовательность с вставкой"""
        return original_sequence[:exon_to_delete.start_position] + original_sequence[exon_to_delete.end_position + 1:utr3.start_position]

    def _calculate_protein_result(self, mutated_sequence: str,
                                translation_start: int, protein_domain: ProteinDomain, 
                                gene: Gene) -> Tuple[ProteinDomain, int, int]:
        """Рассчитать результат мутации для домена белка"""

        # Транслируем до стоп-кодона или конца
        translated_result = self.translation_service.translation_sequence(
            mutated_sequence, 
            translation_start, 
            (len(mutated_sequence) - translation_start) // 3 * 3 - 1
        )
        
        # Находим стоп-кодон в транслированной последовательности
        if translation_start + len(translated_result) * 3 >= gene.base_sequence.utr3.start_position:
            stop_codon_pos = -1
        else:
            stop_codon_pos = translation_start + (len(translated_result) - 1) * 3

        sequence=protein_domain.sequence[:((translation_start - gene.base_sequence.utr5.length) // 3) - protein_domain.end - 1] + translated_result

        # Находим позицию, с которой началась мутация
        diff_pos = (translation_start - gene.base_sequence.utr5.length) // 3
        while diff_pos < len(sequence) + protein_domain.start and sequence[diff_pos - protein_domain.start] == gene.protein.sequence[diff_pos]:
            diff_pos += 1

        # Создаем новый домен
        new_domain = ProteinDomain(
            name=f"{protein_domain.name}_mutated",
            start=0,
            end=len(translated_result) - 1,
            sequence=sequence,
            type=protein_domain.type
        )
        
        return new_domain, diff_pos, stop_codon_pos

    def execute(self, mutation: ExonDeletionMutation, gene: Gene) -> BaseMutationResult:
        nucleotide_position = mutation.nucleotide_position

        # Переводим позицию с учетом UTR5
        global_position = self._translate_nucleotide_position(nucleotide_position, gene.base_sequence.utr5)

        # Находим экзон для удаления
        exon_to_delete = self._find_exon_by_position(global_position, gene)

        # Строим мутированную последовательность
        original_sequence = gene.base_sequence.full_sequence
        mutated_sequence = self._build_mutated_sequence(
            original_sequence, exon_to_delete, gene.base_sequence.utr3
        )

        # Считаем стартовую позицию для мутации
        start_position = self._calculate_start_position(gene, exon_to_delete)
        
        # Получаем затронутые белковые домены
        protein_domain = self._get_protein_domain_at_position(gene, start_position - gene.base_sequence.utr5.length)
        
        # Для каждого затронутого домена строим результат
        new_domain, diff_pos, stop_codon = self._calculate_protein_result(
            mutated_sequence,
            start_position,
            protein_domain,
            gene
        )

        return ExonDeletionResult(
            new_domain=new_domain,
            different_position=diff_pos,
            stop_codon_position=stop_codon
        )


@dataclass
class MutationService:
    """Сервис для обработки мутаций с использованием паттерна Стратегия"""
    
    strategies: Dict[MutationType, MutationStrategy] = None
    
    def __post_init__(self):
        if self.strategies is None:
            self.strategies = {
                MutationType.SUBSTITUTION: SubstitutionStrategy(),
                MutationType.INSERTION: InsertionStrategy(),
                MutationType.DELETION: DeletionStrategy(),
                MutationType.EXON_DELETION: ExonDeletionStrategy()
            }
    
    def apply_mutation(self, mutation: Mutation, gene: Gene) -> BaseMutationResult:
        """Применить мутацию к гену"""
        strategy = self.strategies.get(mutation.mutation_type)
        
        if not strategy:
            raise ValueError(f"No strategy found for mutation type: {mutation.mutation_type}")
        
        return strategy.execute(mutation, gene)