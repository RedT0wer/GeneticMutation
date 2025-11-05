import pytest
import json

from app.api.ensembl_client import EnsemblClient

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
    def test_ncbi_sequense(self):
        pass

    def test_ncbi_exons(self):
        pass

@pytest.mark.api
@pytest.mark.uniprot
class TestApiUniProt:
    def test_uniprot_sequense(self):
        pass

    def test_uniprot_exons(self):
        pass