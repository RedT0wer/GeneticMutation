with open('tests/test_data/ensembl_seq_460472.json', 'r', encoding='utf-8-sig') as f:
    s = f.read()
with open('tests/test_data/ensembl_seq_460472.json', 'w', encoding='utf-8') as f:
    f.write(s)
