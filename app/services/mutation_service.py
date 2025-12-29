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

    def _find_exon_by_position(self, nucleotide_position: int, gene: Gene) -> Optional[Exon]:
        """Найти экзон по позиции нуклеотида"""
        for exon in gene.base_sequence.exons:
            if exon.start_position <= nucleotide_position <= exon.end_position:
                return exon
        return None

    def _get_codon_by_nucleotide(self, sequence: str, nucleotide_position: int) -> str:
        """Получить кодон по номеру нуклеотида"""
        index = (nucleotide_position // 3) * 3
        return sequence[index:index + 3]
    
    def _get_protein_domain_at_position(self, gene: Gene, nucleotide_position: int) -> List[ProteinDomain]:
        """Получить белковые домены по позиции нуклеотида"""
        aminoacid_position = nucleotide_position // 3
        
        # Проверяем домены в транслированном белке
        for domain in gene.translated_protein.domains:
            if domain.start <= aminoacid_position <= domain.end:
                return domain


class SequenceMutationStrategy(MutationStrategy):
    """Базовый класс для стратегий, работающих с последовательностями"""
    
    def _calculate_protein_result(self, original_sequence: str, mutated_sequence: str,
                                mutation_position: int, protein_domain: ProteinDomain, 
                                utr5: UTR, gene: Gene) -> Tuple[ProteinDomain, int, int]:
        """Рассчитать результат мутации для домена белка"""
        
        # 1. Определяем стартовую позицию для трансляции:
        # Максимум из начала домена и начала экзона, содержащего мутацию
        domain_start_nucleotide = utr5.length + protein_domain.start * 3
        
        # Находим экзон, содержащий мутацию
        mutation_global_pos = self._translate_nucleotide_position(mutation_position, utr5)
        exon_with_mutation = self._find_exon_by_position(mutation_global_pos, gene)
        
        if not exon_with_mutation:
            raise ValueError(f"No exon found at mutation position {mutation_global_pos}")
        
        # Стартовая позиция трансляции - либо начало домена, либо начало экзона (что раньше)
        translation_start = max(domain_start_nucleotide, exon_with_mutation.start_position + exon_with_mutation.start_phase)
        
        # Транслируем до стоп-кодона или конца
        translated_result = self.translation_service.translation_sequence(
            mutated_sequence, 
            translation_start, 
            len(mutated_sequence) - 1
        )
        
        # Находим стоп-кодон в транслированной последовательности
        if translation_start + len(translated_result) * 3 >= gene.base_sequence.utr3.start_position:
            stop_codon_pos = -1
        else:
            stop_codon_pos = translation_start + (len(translated_result) - 1) * 3
        
        # Находим позицию, с которой началась мутация
        diff_pos = (translation_start - gene.base_sequence.utr5.length) // 3
        while diff_pos < len(translated_result) and translated_result[diff_pos] == gene.protein.sequence[diff_pos]:
            diff_pos += 1

        # Создаем новый домен
        new_domain = ProteinDomain(
            name=f"{protein_domain.name}_mutated",
            start=0,
            end=len(translated_result) - 1,
            sequence=protein_domain.sequence[:((translation_start - gene.base_sequence.utr5.length) // 3) - protein_domain.end - 1] + translated_result,
            type=protein_domain.type
        )
        
        return new_domain, diff_pos, stop_codon_pos
    
    def _find_stop_codon_in_sequence(self, aminoacid_sequence: str) -> int:
        """Найти позицию первого стоп-кодона в аминокислотной последовательности"""
        for i, aa in enumerate(aminoacid_sequence):
            if aa == '*':  # Символ стоп-кодона
                return i
        return -1
    
    def _calculate_difference_position(self, original: str, mutated: str) -> int:
        """Вычислить позицию первого различия между аминокислотными последовательностями"""
        min_len = min(len(original), len(mutated))
        for i in range(min_len):
            if original[i] != mutated[i]:
                return i
        return min_len if len(original) != len(mutated) else -1
    
    def _create_default_result(self, mutated_sequence: str, start_position: int,
                             mutation_type: str) -> Tuple[ProteinDomain, int, int]:
        """Создать результат по умолчанию, если мутация не затронула домены"""
        seq = mutated_sequence[start_position:]
        protein_sequence = self.translation_service.translation_sequence(seq, start_position, len(seq) - 1)
        new_domain = ProteinDomain(
            name=f"{mutation_type}_domain",
            start=0,
            end=len(protein_sequence) - 1,
            sequence=protein_sequence,
            type=mutation_type
        )
        return new_domain, 0, -1
    
    def _update_gene_sequences(self, gene: Gene, mutated_full_sequence: str):
        """Обновить полную последовательность в гене"""
        gene.base_sequence.full_sequence = mutated_full_sequence
        
        # Пересчитываем длину
        gene.base_sequence.length = len(mutated_full_sequence)


class SubstitutionStrategy(MutationStrategy):
    """Стратегия для замены нуклеотида"""
    
    def _translate_position_in_exon(self, exon: Exon, nucleotide_position: int) -> int:
        """Перевести глобальную позицию в позицию внутри экзона"""
        return nucleotide_position - exon.start_position

    def _substitute_nucleotide_in_exon(self, exon: Exon, position_in_exon: int, new_nucleotide: str):
        """Заменить нуклеотид в экзоне"""
        sequence = list(exon.sequence)
        sequence[position_in_exon] = new_nucleotide
        exon.sequence = ''.join(sequence)
        # Обновляем длину экзона
        exon.length = len(exon.sequence)
    
    def _update_full_sequence(self, gene: Gene, global_position: int, new_nucleotide: str):
        """Обновить полную последовательность гена"""
        seq_list = list(gene.base_sequence.full_sequence)
        seq_list[global_position] = new_nucleotide
        gene.base_sequence.full_sequence = ''.join(seq_list)
    
    def execute(self, mutation: SubstitutionMutation, gene: Gene) -> BaseMutationResult:        
        new_nucleotide = mutation.new_nucleotide
        nucleotide_position = mutation.position_nucleotide

        # Переводим позицию с учетом UTR5
        global_position = self._translate_nucleotide_position(nucleotide_position, gene.base_sequence.utr5)
        
        # Находим экзон
        exon = self._find_exon_by_position(global_position, gene)
        if not exon:
            raise ValueError(f"No exon found at position {global_position}")
            
        # Заменяем нуклеотид в экзоне
        position_in_exon = self._translate_position_in_exon(exon, global_position)
        self._substitute_nucleotide_in_exon(exon, position_in_exon, new_nucleotide)
        
        # Обновляем полную последовательность
        self._update_full_sequence(gene, global_position, new_nucleotide)
        
        # Получаем новый кодон и аминокислоту
        codon = self._get_codon_by_nucleotide(gene.base_sequence.full_sequence, global_position)
        new_aminoacid = self.translation_service.get_aminoacid(codon)

        return SubstitutionResult(new_aminoacid=new_aminoacid)


class InsertionStrategy(SequenceMutationStrategy):
    """Стратегия для вставки нуклеотидов"""
    
    def _build_mutated_sequence(self, original_sequence: str, 
                              position: int, inserted_sequence: str) -> str:
        """Построить мутированную последовательность с вставкой"""
        return original_sequence[:position + 1] + inserted_sequence + original_sequence[position + 1:]
    
    def execute(self, mutation: InsertionMutation, gene: Gene) -> BaseMutationResult:
        inserted_sequence = mutation.inserted_sequence
        start_position = mutation.start_position

        # Переводим позицию с учетом UTR5
        global_position = self._translate_nucleotide_position(start_position, gene.base_sequence.utr5)
        
        # Строим мутированную последовательность
        original_sequence = gene.base_sequence.full_sequence
        mutated_sequence = self._build_mutated_sequence(
            original_sequence, global_position, inserted_sequence
        )
        
        # Обновляем полную последовательность гена
        self._update_gene_sequences(gene, mutated_sequence)
        
        # Получаем затронутый белковый домен
        protein_domain = self._get_protein_domain_at_position(gene, start_position)
        
        # Для затронутого домена строим результат
        new_domain, diff_pos, stop_codon = self._calculate_protein_result(
            original_sequence,
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
    
    def _update_gene_sequences(self, gene: Gene, mutated_full_sequence: str):
        """Обновить полную последовательность в гене"""
        gene.base_sequence.full_sequence = mutated_full_sequence
        
        # Пересчитываем длину
        gene.base_sequence.length = len(mutated_full_sequence)


class DeletionStrategy(SequenceMutationStrategy):
    """Стратегия для удаления нуклеотидов"""
    
    def _build_mutated_sequence(self, original_sequence: str, 
                              start_pos: int, end_pos: int) -> str:
        """Построить мутированную последовательность с удалением"""
        return original_sequence[:start_pos] + original_sequence[end_pos + 1:]
    
    def _update_exon_after_deletion(self, exon: Exon, start_in_exon: int, 
                                  end_in_exon: int, deleted_length: int):
        """Обновить экзон после удаления"""
        # Удаляем последовательность из экзона
        exon.sequence = (exon.sequence[:start_in_exon] + 
                        exon.sequence[end_in_exon + 1:])
        # Обновляем длину экзона
        exon.length = len(exon.sequence)
        # Обновляем конечную позицию экзона
        exon.end_position -= deleted_length
    
    def execute(self, mutation: DeletionMutation, gene: Gene) -> BaseMutationResult:
        start_position = mutation.start_position
        end_position = mutation.end_position

        # Переводим позицию с учетом UTR5
        global_position = self._translate_nucleotide_position(start_position, gene.base_sequence.utr5)

        # Строим мутированную последовательность
        original_sequence = gene.base_sequence.full_sequence
        mutated_sequence = self._build_mutated_sequence(
            original_sequence, global_position, global_position + end_position - start_position
        )
        
        # Обновляем полную последовательность гена
        self._update_gene_sequences(gene, mutated_sequence)
        
        # Получаем затронутый белковый домен
        protein_domain = self._get_protein_domain_at_position(gene, start_position)
        
        # Для затронутого домена строим результат
        new_domain, diff_pos, stop_codon = self._calculate_protein_result(
            original_sequence,
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
    
    def _rebuild_full_sequence(self, gene: Gene) -> str:
        """Перестроить полную последовательность после удаления экзона"""
        # Собираем последовательности всех экзонов
        sequence_parts = []
        for exon in sorted(gene.base_sequence.exons, key=lambda x: x.number):
            sequence_parts.append(exon.sequence)
        
        return ''.join(sequence_parts)
    
    def execute(self, mutation: ExonDeletionMutation, gene: Gene) -> BaseMutationResult:
        exon_number = mutation.number_exon
        
        # Находим экзон для удаления
        exon_to_delete = None
        for exon in gene.base_sequence.exons:
            if exon.number == exon_number:
                exon_to_delete = exon
                break
        
        if not exon_to_delete:
            raise ValueError(f"Exon with number {exon_number} not found")
        
        # Удаляем экзон из списка
        gene.base_sequence.exons = [exon for exon in gene.base_sequence.exons 
                                  if exon.number != exon_number]
        
        start_position = exon_to_delete.start_position
        
        # Перестраиваем полную последовательность
        mutated_sequence = self._rebuild_full_sequence(gene)
        
        # Обновляем полную последовательность в гене
        self._update_gene_sequences(gene, mutated_sequence)
        
        # Пересчитываем позиции оставшихся экзонов
        current_position = 0
        for exon in sorted(gene.base_sequence.exons, key=lambda x: x.number):
            exon.start_position = current_position
            exon.end_position = current_position + exon.length - 1
            current_position += exon.length
        
        # Получаем затронутые белковые домены
        affected_domains = self._get_protein_domains_at_position(gene, start_position)
        
        # Для каждого затронутого домена строим результат
        if affected_domains:
            # Используем первый домен для результата
            protein_domain = affected_domains[0]
            new_domain, diff_pos, stop_codon = self._calculate_protein_result(
                gene.base_sequence.full_sequence,
                mutated_sequence,
                start_position,
                protein_domain
            )
        else:
            # Если не затронут ни один домен, создаем результат по умолчанию
            new_domain, diff_pos, stop_codon = self._create_default_result(
                mutated_sequence, start_position, "exon_deletion"
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