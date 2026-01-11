import pytest
import time

from app.models.mutation_models import *
from app.services.gene_service import GeneService
from app.services.mutation_service import MutationService

@pytest.mark.services
@pytest.mark.gene_service
class TestGeneServices:
    def test_create_gene_ensembl(self):
        gene_service = GeneService()
        gene_id = "ENST00000460472"
        protein_id = "Q8WZ42"
        gene = gene_service.build_gene_from_ensembl(gene_id=gene_id, protein_id=protein_id)
        assert not gene is None, "Объект Гена не создался"

    def test_create_gene_ncbi(self):
        gene_service = GeneService()
        ncbi_id = "NM_003319"
        protein_id = "Q8WZ42"
        gene = gene_service.build_gene_from_ncbi(ncbi_id=ncbi_id, protein_id=protein_id)
        assert not gene is None, "Объект Гена не создался"

@pytest.mark.services
@pytest.mark.mutation_service
class TestMutationServices:
    @pytest.mark.substitution
    def test_substitution_one(self):
        gene_service = GeneService()
        mutation_service = MutationService()

        ncbi_id = "NM_003319"
        protein_id = "Q8WZ42"
        gene = gene_service.build_gene_from_ncbi(ncbi_id=ncbi_id, protein_id=protein_id)

        mutation = SubstitutionMutation(MutationType.SUBSTITUTION, "T", 1)
        substitution_result = mutation_service.apply_mutation(mutation, gene)       
        new_aminoacid = substitution_result.new_aminoacid
        assert new_aminoacid == "L", f"Вернулась не та аминокислота: {new_aminoacid}"
    
    @pytest.mark.substitution
    def test_substitution_two(self):
        gene_service = GeneService()
        mutation_service = MutationService()

        ncbi_id = "NM_003319"
        protein_id = "Q8WZ42"
        gene = gene_service.build_gene_from_ncbi(ncbi_id=ncbi_id, protein_id=protein_id)

        mutation = SubstitutionMutation(MutationType.SUBSTITUTION, "T", 5)
        substitution_result = mutation_service.apply_mutation(mutation, gene)       
        new_aminoacid = substitution_result.new_aminoacid
        assert new_aminoacid == "I", f"Вернулась не та аминокислота: {new_aminoacid}"
    
    @pytest.mark.substitution
    def test_substitution_three(self):
        gene_service = GeneService()
        mutation_service = MutationService()

        ncbi_id = "NM_003319"
        protein_id = "Q8WZ42"
        gene = gene_service.build_gene_from_ncbi(ncbi_id=ncbi_id, protein_id=protein_id)

        mutation = SubstitutionMutation(MutationType.SUBSTITUTION, "C", 5569)
        substitution_result = mutation_service.apply_mutation(mutation, gene)       
        new_aminoacid = substitution_result.new_aminoacid
        assert new_aminoacid == "Q", f"Вернулась не та аминокислота: {new_aminoacid}"

    @pytest.mark.insertion
    def test_inserted_one(self):
        gene_service = GeneService()
        mutation_service = MutationService()

        ncbi_id = "NM_003319"
        protein_id = "Q8WZ42"
        gene = gene_service.build_gene_from_ncbi(ncbi_id=ncbi_id, protein_id=protein_id)

        mutation = InsertionMutation(MutationType.INSERTION, "A", 10, 90)
        insertion_result = mutation_service.apply_mutation(mutation, gene) 
        new_domain = insertion_result.new_domain
        print(insertion_result)
        assert gene.base_sequence.full_sequence[insertion_result.stop_codon_position - 2:insertion_result.stop_codon_position + 1] == "TAG"

    @pytest.mark.deletion
    def test_deletion_one(self):
        gene_service = GeneService()
        mutation_service = MutationService()
        ncbi_id = "NM_003319"
        protein_id = "Q8WZ42"
        gene = gene_service.build_gene_from_ncbi(ncbi_id=ncbi_id, protein_id=protein_id)

        mutation = DeletionMutation(MutationType.DELETION, 1, 3)
        deletion_result = mutation_service.apply_mutation(mutation, gene) 
        new_domain = deletion_result.new_domain
        print(deletion_result)
        assert not new_domain is None, f"sdf"

    @pytest.mark.exon_deletion
    def test_exon_deletion_one(self):
        gene_service = GeneService()
        mutation_service = MutationService()

        ncbi_id = "NM_003319"
        protein_id = "Q8WZ42"
        gene = gene_service.build_gene_from_ncbi(ncbi_id=ncbi_id, protein_id=protein_id)

        mutation = ExonDeletionMutation(MutationType.EXON_DELETION, 1)
        exon_deletion_result = mutation_service.apply_mutation(mutation, gene) 
        print(exon_deletion_result)
        assert not exon_deletion_result is None, f"sdf"