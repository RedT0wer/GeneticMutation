import pytest
import json

from app.api.ensembl_client import EnsemblClient
from app.api.ncbi_client import NCBIClient
from app.api.uniprot_client import UniProtClient

@pytest.mark.api
@pytest.mark.ensembl
class TestApiEnsembl:
    def test_ensembl_sequence(self):
        ensembl_obj = EnsemblClient()
        identifier = "ENST00000460472"
        data_ensembl = ensembl_obj._get_sequence(identifier)

        with open('tests/test_data/ensembl/ensembl_seq_460472.json', 'r', encoding='utf-8') as f:
            data = json.load(f)

        assert data == data_ensembl, "Последовательность не верная"

    def test_ensembl_exons(self):
        ensembl_obj = EnsemblClient()
        identifier = "ENST00000460472"
        data_ensembl = ensembl_obj._get_gene_with_exons(identifier)

        with open('tests/test_data/ensembl/ensembl_exons_460472.json', 'r', encoding='utf-8') as f:
            data = json.load(f)

        assert data == data_ensembl, "Данные экзонов не верные"

    def test_ensembl_process_sequence(self):
        ensembl_obj = EnsemblClient()
        identifier = "ENST00000460472"
        data_ensembl = ensembl_obj.get_sequence_legacy(identifier)

        with open('tests/test_data/ensembl/ensembl_procces_seq_460472.txt', 'r', encoding='utf-8') as f:
            data = f.readline().strip()

        assert data == str(data_ensembl), "Неверно обработана последовательность"

    def test_ensembl_process_exons(self):
        ensembl_obj = EnsemblClient()
        identifier = "ENST00000460472"
        data_ensembl = ensembl_obj.get_exons_legacy(identifier)

        with open('tests/test_data/ensembl/ensembl_procces_exons_460472.txt', 'r', encoding='utf-8') as f:
            data = f.readline().strip()

        assert data == str(data_ensembl), "Неверно обработаны данные экзонов"

@pytest.mark.api
@pytest.mark.ncbi
class TestApiNcbi:
    def test_ncbi_process_sequense(self):
        ncbi_obj = NCBIClient()
        identifier = "NM_003319"
        data_ncbi = ncbi_obj.get_sequence_legacy(identifier)

        with open(f'tests/test_data/ncbi/ncbi_procces_seq_{identifier}.txt', 'r', encoding='utf-8') as f:
            data = f.readline().strip()

        assert data == str(data_ncbi), "Неверно обработана последовательность"

    def test_ncbi_process_exons(self):
        ncbi_obj = NCBIClient()
        identifier = "NM_003319"
        data_ncbi = ncbi_obj.get_exons_legacy(identifier)

        with open(f'tests/test_data/ncbi/ncbi_procces_exons_{identifier}.txt', 'r', encoding='utf-8') as f:
            data = f.readline().strip()

        assert data == str(data_ncbi), "Неверно обработаны данные экзонов"

@pytest.mark.api
@pytest.mark.uniprot
class TestApiUniProt:
    def test_uniprot_process_sequense(self):
        uniProtClient_obj = UniProtClient()
        identifier = "Q8WZ42"
        data_uniprot = uniProtClient_obj.get_sequence_legacy(identifier)

        with open(f'tests/test_data/uniprot/uniprot_procces_seq_{identifier}.txt', 'r', encoding='utf-8') as f:
            data = f.readline().strip()

        assert data == str(data_uniprot), "Неверно обработана последовательность"

    def test_uniprot_process_exons(self):
        uniProtClient_obj = UniProtClient()
        identifier = "Q8WZ42"
        data_uniprot = uniProtClient_obj.get_domains_legacy(identifier)

        with open(f'tests/test_data/uniprot/uniprot_procces_domains_{identifier}.txt', 'r', encoding='utf-8') as f:
            data = f.readline().strip()

        assert data == str(data_uniprot), "Неверно обработаны домены"