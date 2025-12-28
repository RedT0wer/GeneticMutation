import pytest

from app.services.gene_service import GeneService

@pytest.mark.services
@pytest.mark.gene_service
class TestGeneServices:
    # def test_create_gene_ensembl(self):
    #     gene_service = GeneService()
    #     gene_id = "ENST00000460472"
    #     protein_id = "Q8WZ42"
    #     gene = gene_service.build_gene_from_ensembl(gene_id=gene_id, protein_id=protein_id)
    #     assert not gene is None, "Объект Гена не создался"

    def test_create_gene_ncbi(self):
        gene_service = GeneService()
        ncbi_id = "NM_003319"
        protein_id = "Q8WZ42"
        gene = gene_service.build_gene_from_ncbi(ncbi_id=ncbi_id, protein_id=protein_id)
        print()
        print(gene.translated_protein.domains[0])
        print()
        print(gene.translated_protein.domains[1])
        assert not gene is None, "Объект Гена не создался"
