# GeneticMutation

Сервис для построения структуры гена и моделирования различных типов мутаций с использованием данных из внешних API (Ensembl, NCBI, UniProt).

## ✨ Основные возможности

Построение гена

    - Загрузка данных из Ensembl или NCBI

    - Получение экзонов, UTR-областей, полной нуклеотидной последовательности

    - Загрузка белковых доменов из UniProt

    - Автоматическая трансляция нуклеотидной последовательности в белок

    - Выравнивание доменов на транслированном белке

Моделирование мутаций

    - Замена (Substitution): замена одного нуклеотида
    
    - Вставка (Insertion): вставка последовательности нуклеотидов
    
    - Удаление (Deletion): удаление участка последовательности

## 📡 API Endpoints

### 1. Построение гена

```http
POST /api/gene/build
```
Тело запроса:
```json

{
    "source": "ensembl",  // или "ncbi"
    "gene_id": "ENST00000460472",
    "protein_id": "Q8WZ42"  // UniProt ID
}
```

Ответ:
```json
{
    "success": true,
    "gene": {
        "protein": {
            "identifier": "P04637",
            "sequence": "MEEPQSDPSV...",
            "length": 393,
            "domains": [...]
        },
        "base_sequence": {
            "identifier": "ENSG00000139618",
            "length": 1925,
            "full_sequence": "GAGCAGTCG...",
            "exons": [...],
            "utr5": {...},
            "utr3": {...}
        }
    }
}
```

### 2. Применение мутации

```http
POST /api/gene/mutate
```

**Тело запроса (SUBSTITUTION):**
```json
{
    "gene": { ... },  // структура гена из предыдущего запроса
    "mutation": {
        "mutation_type": "SUBSTITUTION",
        "new_nucleotide": "A",
        "position_nucleotide": 150
    }
}
```


**Тело ответа (SUBSTITUTION):**
```json
{
    "success": true,
    "data": {
        "new_aminoacid": "A"
    },
    "type": "SUBSTITUTION"
}
```

**Тело запроса (INSERTION):**
```json
{
    "gene": { ... },
    "mutation": {
        "mutation_type": "INSERTION",
        "inserted_sequence": "ATCG",
        "start_position": 150,
        "end_position": 150  // для вставки start=end
    }
}
```


**Тело ответа (INSERTION):**
```json
{
    "success": true,
    "data": {
        "new_domain": {
            "name": "DNA-binding domain_mutated",
            "start": 94,
            "end": 295,
            "sequence": "SVPSQKTYQGSYGFRLGFLHSGTAKSVTCTYSPALNKMFCQLAKTCPVQLWVDSTPPPGTRVRAMAIYKQSQHMTEVVRRCPHHERCSDSDGLAPPQHLIRVEGNLRVEYLDDRNTFRHSVVVPYEPPEVGSDCTTIHYNYMCNSSCMGGMNRRPILTIITLEDSSGNLLGRNSFEVRVCACPGRDRRTEEENFRAINSS",
            "type": "domain"
        },
        "different_position": 102,
        "stop_codon_position": 1620
    },
    "type": "INSERTION"
}
```


**Тело запроса (DELETION):**
```json
{
    "gene": { ... },
    "mutation": {
        "mutation_type": "DELETION",
        "start_position": 150,
        "end_position": 153
    }
}
```


**Тело ответа (DELETION):**
```json
{
    "success": true,
    "data": {
        "new_domain": {
            "name": "DNA-binding domain_mutated",
            "start": 94,
            "end": 280,
            "sequence": "SVPSQKTYQGSYGFRLGFLHSGTAKSVTCTYSPALNKMFCQLAKTCPVQLWVDSTPPPGTRVRAMAIYKQSQHMTEVVRRCPHHERCSDSDGLAPPQHLIRVEGNLRVEYLDDRNTFRHSVVVPYEPPEVGSDCTTIHYNYMCNSSCMGGMNRRPI",
            "type": "domain"
        },
        "different_position": 102,
        "stop_codon_position": 10
    },
    "type": "DELETION"
}
```

### 3. Получение типов мутаций
```http
GET /api/mutation/types
```
Ответ:
```json
{
    "success": true,
    "mutation_types": [
        {
            "type": "SUBSTITUTION",
            "description": "Замена одного нуклеотида на другой"
        },
        {
            "type": "INSERTION",
            "description": "Вставка последовательности нуклеотидов"
        },
        {
            "type": "DELETION",
            "description": "Удаление последовательности нуклеотидов"
        }
    ]
}
```

### 4. Ответы с ошибками

**400 Bad Request:**
```json
{
    "error": "Missing required parameters: source, gene_id, protein_id"
}
```

```json
{
    "error": "Invalid source. Must be \"ensembl\" or \"ncbi\""
}
```

```json
{
    "error": "No JSON data provided"
}
```

**500 Internal Server Error:**
```json
{
    "error": "Failed to build gene structure"
}
```

```json
{
    "error": "Error applying mutation: ..."
}
```

**404 Not Found:**
```json
{
    "error": "Endpoint not found"
}
```

## 📊 Модели данных

Gene
```python

@dataclass
class Gene:
    protein: Protein
    base_sequence: BaseSequence
```
Protein
```python

@dataclass
class Protein:
    identifier: str
    sequence: str
    length: int
    domains: List[ProteinDomain]
```
BaseSequence
```python

@dataclass
class BaseSequence:
    identifier: str
    length: int
    full_sequence: str
    exons: List[Exon]
    utr5: UTR
    utr3: UTR
```
Exon
```python

@dataclass
class Exon:
    number: int
    start_position: int
    end_position: int
    start_phase: int  # -1 для некодирующих, 0-2 для фазы
    end_phase: int
    length: int
```
