import logging
from typing import List, Dict, Optional, Tuple
from ..models.gene_models import Gene, Exon
from ..models.mutation_models import Mutation, MutationResult, MutationType, AminoAcidChange, ImpactSeverity
from ..core.mutation_analyzer import MutationAnalyzer
from ..core.biopython_utils import BiopythonUtils

class MutationService:
    """Сервис для анализа мутаций"""
    
    def __init__(self):
        self.analyzer = MutationAnalyzer()
        self.bp_utils = BiopythonUtils()
        self.logger = logging.getLogger(__name__)
    
    def analyze_single_mutation(self, gene: Gene, mutation: Mutation) -> MutationResult:
        """
        Проанализировать одиночную мутацию
        """
        try:
            self.logger.info(f"Analyzing mutation: {mutation.type.value} at position {mutation.position}")
            
            # Выбираем анализатор в зависимости от типа мутации
            if mutation.type == MutationType.SUBSTITUTION:
                result = self._analyze_substitution(gene, mutation)
            elif mutation.type == MutationType.DELETION:
                result = self._analyze_deletion(gene, mutation)
            elif mutation.type == MutationType.INSERTION:
                result = self._analyze_insertion(gene, mutation)
            elif mutation.type == MutationType.EXON_DELETION:
                result = self._analyze_exon_deletion(gene, mutation)
            else:
                raise ValueError(f"Unsupported mutation type: {mutation.type}")
            
            # Оцениваем серьезность воздействия
            result.impact_severity = self._assess_impact_severity(result)
            
            self.logger.info(f"Mutation analysis completed. Impact: {result.impact_severity.value}")
            return result
            
        except Exception as e:
            self.logger.error(f"Mutation analysis failed: {e}")
            raise
    
    def analyze_multiple_mutations(self, gene: Gene, mutations: List[Mutation]) -> List[MutationResult]:
        """
        Проанализировать несколько мутаций последовательно
        """
        results = []
        current_gene = gene
        
        for mutation in mutations:
            try:
                result = self.analyze_single_mutation(current_gene, mutation)
                results.append(result)
                # Следующая мутация применяется к уже модифицированному гену
                current_gene = result.modified_gene
            except Exception as e:
                self.logger.error(f"Failed to analyze mutation {mutation}: {e}")
                # Продолжаем с другими мутациями
                continue
        
        return results
    
    def _analyze_substitution(self, gene: Gene, mutation: Mutation) -> MutationResult:
        """Анализ замены нуклеотида"""
        # Находим экзон и позицию в экзоне
        target_exon, exon_position = gene.find_exon_by_position(mutation.position)
        
        if not target_exon:
            raise ValueError(f"Position {mutation.position} not found in any exon")
        
        # Выполняем замену в последовательности экзона
        modified_exon_sequence = (
            target_exon.sequence[:exon_position] +
            mutation.new_sequence +
            target_exon.sequence[exon_position + 1:]
        )
        
        # Создаем модифицированный экзон
        modified_exon = Exon(
            number=target_exon.number,
            sequence=modified_exon_sequence,
            start_position=target_exon.start_position,
            end_position=target_exon.start_position + len(modified_exon_sequence) - 1,
            length=len(modified_exon_sequence),
            is_modified=True,
            modifications=[{
                'type': 'substitution',
                'position': exon_position,
                'original': target_exon.sequence[exon_position],
                'new': mutation.new_sequence
            }]
        )
        
        # Создаем модифицированный ген
        modified_gene = self._create_modified_gene(gene, [modified_exon])
        
        # Находим изменения аминокислот
        amino_acid_changes = self._find_amino_acid_changes(
            gene.protein.sequence,
            modified_gene.protein.sequence
        )
        
        return MutationResult(
            mutation=mutation,
            original_gene=gene,
            modified_gene=modified_gene,
            amino_acid_changes=amino_acid_changes,
            impact_severity=ImpactSeverity.LOW,  # Временно, оценим позже
            domain_changes=self._find_domain_changes(gene.protein.domains, amino_acid_changes)
        )
    
    def _analyze_deletion(self, gene: Gene, mutation: Mutation) -> MutationResult:
        """Анализ делеции"""
        # Получаем полную нуклеотидную последовательность
        full_sequence = gene.full_sequence
        
        # Создаем делецию
        modified_sequence = (
            full_sequence[:mutation.position] +
            full_sequence[mutation.position + mutation.length:]
        )
        
        # Транслируем последовательности
        original_protein = self.bp_utils.translate_sequence(full_sequence)
        modified_protein = self.bp_utils.translate_sequence(modified_sequence)
        
        # Находим изменения
        amino_acid_changes = self._find_amino_acid_changes(original_protein, modified_protein)
        
        # Создаем модифицированный ген
        modified_gene = self._create_gene_with_modified_sequence(gene, modified_sequence)
        
        # Проверяем на frameshift
        is_frameshift = mutation.length % 3 != 0
        stop_codon_position = self._find_stop_codon_position(modified_sequence) if is_frameshift else None
        
        return MutationResult(
            mutation=mutation,
            original_gene=gene,
            modified_gene=modified_gene,
            amino_acid_changes=amino_acid_changes,
            impact_severity=ImpactSeverity.LOW,
            is_frameshift=is_frameshift,
            stop_codon_position=stop_codon_position,
            domain_changes=self._find_domain_changes(gene.protein.domains, amino_acid_changes)
        )
    
    def _analyze_insertion(self, gene: Gene, mutation: Mutation) -> MutationResult:
        """Анализ вставки"""
        full_sequence = gene.full_sequence
        
        # Создаем вставку
        modified_sequence = (
            full_sequence[:mutation.position] +
            mutation.new_sequence +
            full_sequence[mutation.position:]
        )
        
        # Транслируем
        original_protein = self.bp_utils.translate_sequence(full_sequence)
        modified_protein = self.bp_utils.translate_sequence(modified_sequence)
        
        # Находим изменения
        amino_acid_changes = self._find_amino_acid_changes(original_protein, modified_protein)
        
        # Создаем модифицированный ген
        modified_gene = self._create_gene_with_modified_sequence(gene, modified_sequence)
        
        # Проверяем на frameshift
        is_frameshift = len(mutation.new_sequence) % 3 != 0
        stop_codon_position = self._find_stop_codon_position(modified_sequence) if is_frameshift else None
        
        return MutationResult(
            mutation=mutation,
            original_gene=gene,
            modified_gene=modified_gene,
            amino_acid_changes=amino_acid_changes,
            impact_severity=ImpactSeverity.LOW,
            is_frameshift=is_frameshift,
            stop_codon_position=stop_codon_position,
            domain_changes=self._find_domain_changes(gene.protein.domains, amino_acid_changes)
        )
    
    def _analyze_exon_deletion(self, gene: Gene, mutation: Mutation) -> MutationResult:
        """Анализ делеции экзона"""
        # Находим экзон для удаления
        exon_to_delete = next((e for e in gene.exons if e.number == mutation.position), None)
        if not exon_to_delete:
            raise ValueError(f"Exon {mutation.position} not found")
        
        # Создаем список экзонов без удаленного
        remaining_exons = [e for e in gene.exons if e.number != mutation.position]
        
        # Пересчитываем позиции оставшихся экзонов
        current_position = 0
        for exon in remaining_exons:
            exon.start_position = current_position
            exon.end_position = current_position + exon.length - 1
            current_position += exon.length
        
        # Создаем модифицированный ген
        modified_gene = Gene(
            id=gene.id + "_modified",
            name=gene.name,
            species=gene.species,
            chromosome=gene.chromosome,
            strand=gene.strand,
            protein=gene.protein,  # Белок будет пересчитан позже
            exons=remaining_exons,
            transcript_id=gene.transcript_id
        )
        
        # Пересчитываем белковую последовательность
        modified_sequence = modified_gene.full_sequence
        modified_protein_sequence = self.bp_utils.translate_sequence(modified_sequence)
        
        # Обновляем белок
        modified_gene.protein.sequence = modified_protein_sequence
        modified_gene.protein.length = len(modified_protein_sequence)
        
        # Находим изменения аминокислот
        amino_acid_changes = self._find_amino_acid_changes(
            gene.protein.sequence,
            modified_gene.protein.sequence
        )
        
        return MutationResult(
            mutation=mutation,
            original_gene=gene,
            modified_gene=modified_gene,
            amino_acid_changes=amino_acid_changes,
            impact_severity=ImpactSeverity.LOW,
            domain_changes=self._find_domain_changes(gene.protein.domains, amino_acid_changes)
        )
    
    def _create_modified_gene(self, original_gene: Gene, modified_exons: List[Exon]) -> Gene:
        """Создать модифицированный ген с обновленными экзонами"""
        # Заменяем модифицированные экзоны
        exons_map = {exon.number: exon for exon in original_gene.exons}
        for modified_exon in modified_exons:
            exons_map[modified_exon.number] = modified_exon
        
        # Собираем экзоны в правильном порядке
        new_exons = sorted([exons_map[num] for num in exons_map.keys()], key=lambda x: x.number)
        
        # Пересчитываем последовательность и белок
        new_sequence = ''.join(exon.sequence for exon in new_exons)
        new_protein_sequence = self.bp_utils.translate_sequence(new_sequence)
        
        # Создаем модифицированный белок
        modified_protein = Protein(
            id=original_gene.protein.id + "_modified",
            name=original_gene.protein.name,
            sequence=new_protein_sequence,
            length=len(new_protein_sequence),
            domains=original_gene.protein.domains,  # Домены будут обновлены позже
            molecular_weight=self.bp_utils.calculate_molecular_weight(new_protein_sequence)
        )
        
        return Gene(
            id=original_gene.id + "_modified",
            name=original_gene.name,
            species=original_gene.species,
            chromosome=original_gene.chromosome,
            strand=original_gene.strand,
            protein=modified_protein,
            exons=new_exons,
            transcript_id=original_gene.transcript_id
        )
    
    def _create_gene_with_modified_sequence(self, original_gene: Gene, new_sequence: str) -> Gene:
        """Создать ген с модифицированной последовательностью"""
        # Пока упрощенная реализация - в реальности нужно перераспределить по экзонам
        mock_exon = Exon(
            number=1,
            sequence=new_sequence,
            start_position=0,
            end_position=len(new_sequence) - 1,
            length=len(new_sequence),
            is_modified=True
        )
        
        new_protein_sequence = self.bp_utils.translate_sequence(new_sequence)
        
        modified_protein = Protein(
            id=original_gene.protein.id + "_modified",
            name=original_gene.protein.name,
            sequence=new_protein_sequence,
            length=len(new_protein_sequence),
            domains=original_gene.protein.domains,
            molecular_weight=self.bp_utils.calculate_molecular_weight(new_protein_sequence)
        )
        
        return Gene(
            id=original_gene.id + "_modified",
            name=original_gene.name,
            species=original_gene.species,
            chromosome=original_gene.chromosome,
            strand=original_gene.strand,
            protein=modified_protein,
            exons=[mock_exon],
            transcript_id=original_gene.transcript_id
        )
    
    def _find_amino_acid_changes(self, original_aa: str, modified_aa: str) -> List[AminoAcidChange]:
        """Найти изменения в аминокислотных последовательностях"""
        changes = []
        min_len = min(len(original_aa), len(modified_aa))
        
        for i in range(min_len):
            if original_aa[i] != modified_aa[i]:
                changes.append(AminoAcidChange(
                    position=i,
                    original=original_aa[i],
                    new=modified_aa[i],
                    type='substitution'
                ))
        
        # Обработка разных длин
        if len(original_aa) > len(modified_aa):
            for i in range(len(modified_aa), len(original_aa)):
                changes.append(AminoAcidChange(
                    position=i,
                    original=original_aa[i],
                    new='-',
                    type='deletion'
                ))
        elif len(original_aa) < len(modified_aa):
            for i in range(len(original_aa), len(modified_aa)):
                changes.append(AminoAcidChange(
                    position=i,
                    original='-',
                    new=modified_aa[i],
                    type='insertion'
                ))
        
        return changes
    
    def _find_domain_changes(self, domains: List[ProteinDomain], aa_changes: List[AminoAcidChange]) -> List[Dict]:
        """Найти изменения в доменах"""
        domain_changes = []
        
        for domain in domains:
            changes_in_domain = [
                change for change in aa_changes
                if domain.start <= change.position <= domain.end
            ]
            
            if changes_in_domain:
                domain_changes.append({
                    'domain_name': domain.name,
                    'domain_type': domain.type,
                    'changes_count': len(changes_in_domain),
                    'changes': [change.to_dict() for change in changes_in_domain]
                })
        
        return domain_changes
    
    def _find_stop_codon_position(self, sequence: str) -> Optional[int]:
        """Найти позицию стоп-кодона в последовательности"""
        stops = self.bp_utils.find_stop_codons(sequence)
        return stops[0] if stops else None
    
    def _assess_impact_severity(self, result: MutationResult) -> ImpactSeverity:
        """Оценить серьезность воздействия мутации"""
        if result.stop_codon_position is not None:
            return ImpactSeverity.HIGH
        
        if result.is_frameshift:
            return ImpactSeverity.HIGH
        
        if any(change.type in ['deletion', 'insertion'] for change in result.amino_acid_changes):
            return ImpactSeverity.HIGH
        
        domain_changes_count = sum(domain['changes_count'] for domain in result.domain_changes)
        if domain_changes_count > 0:
            return ImpactSeverity.MODERATE
        
        if result.amino_acid_changes:
            return ImpactSeverity.LOW
        
        return ImpactSeverity.LOW