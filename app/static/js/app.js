// Основные переменные
let currentGene = null;

// Функция для компиляции шаблонов
function compileTemplate(templateId, data) {
    const template = document.getElementById(templateId).innerHTML;
    const compiled = _.template(template);
    return compiled(data);
}

// Отображение статуса
function showStatus(message, type = 'info') {
    const statusEl = document.getElementById('buildStatus');
    statusEl.innerHTML = `
        <div class="status-message status-${type}">
            <i class="fas fa-${type === 'error' ? 'exclamation-circle' : type === 'success' ? 'check-circle' : 'info-circle'}"></i>
            ${message}
        </div>
    `;
}

// Отображение ошибки
function showError(message) {
    const errorEl = document.getElementById('errorMessage');
    errorEl.innerHTML = `
        <i class="fas fa-exclamation-triangle"></i>
        ${message}
    `;
    errorEl.style.display = 'block';
    
    setTimeout(() => {
        errorEl.style.display = 'none';
    }, 5000);
}

// Отображение информации о гене
function displayGeneInfo(gene) {
    const geneInfoEl = document.getElementById('geneInfo');
    
    const totalExonLength = gene.base_sequence.exons.reduce((sum, exon) => sum + exon.length, 0);
    const totalDomainLength = gene.protein.domains.reduce((sum, domain) => sum + (domain.end - domain.start + 1), 0);
    
    geneInfoEl.innerHTML = `
        <div class="gene-info-grid">
            <div class="info-item-gene">
                <span class="info-label"><i class="fas fa-shapes"></i> Количество доменов:</span>
                <span class="info-value">${gene.protein.domains.length}</span>
            </div>
            <div class="info-item-gene">
                <span class="info-label"><i class="fas fa-layer-group"></i> Количество экзонов:</span>
                <span class="info-value">${gene.base_sequence.exons.length}</span>
            </div>
            <div class="info-item-gene">
                <span class="info-label"><i class="fas fa-code"></i> Длина всех экзонов:</span>
                <span class="info-value">${totalExonLength} нуклеотидов</span>
            </div>
            <div class="info-item-gene">
                <span class="info-label"><i class="fas fa-ruler-combined"></i> Общая длина доменов:</span>
                <span class="info-value">${totalDomainLength} аминокислот</span>
            </div>
            <div class="info-item-gene">
                <span class="info-label"><i class="fas fa-file-code"></i> Последовательность 5' UTR:</span>
                <span class="info-value">${gene.base_sequence.utr5.length}</span>
            </div>
            <div class="info-item-gene">
                <span class="info-label"><i class="fas fa-file-code"></i> Последовательность 3' UTR:</span>
                <span class="info-value">${gene.base_sequence.utr3.length}</span>
            </div>
        </div>
    `;
}

function createExonData(exon, full_sequence, utr5, utr3) {
    const exonSequence = full_sequence.slice(exon.start_position, exon.end_position + 1);
    
    return {
        ...exon,
        identifier: currentGene.base_sequence.identifier,
        sequence: exonSequence,
        length: exonSequence.length,
        utr5: utr5.end_position,
        utr3: utr3.start_position
    };
}

function calculateNucleotideProperties(startPosition, index, utr5End, utr3Start) {
    const globalPosition = startPosition + index - utr5End;
    const numberCodon = Math.floor((globalPosition - 1) / 3) + 1;
    const isUtr = startPosition + index <= utr5End || startPosition + index >= utr3Start;
    const isCoding = !isUtr;
    const region = isCoding ? "кодирующая" : "utr";

    return { globalPosition, numberCodon, isUtr, isCoding, region };
}

function createNucleotideElement(nucleotideData) {
    const nucleotideHtml = compileTemplate('nucleotideTemplate', nucleotideData);
    const tempSpan = document.createElement('span');
    tempSpan.innerHTML = nucleotideHtml;
    
    return tempSpan.firstElementChild;
}

async function createExonElementAsync(exonData) {
    // Создаем элемент экзона без нуклеотидов
    const exonHtml = compileTemplate('exonTemplate', exonData);
    const tempDiv = document.createElement('div');
    tempDiv.innerHTML = exonHtml;
    return tempDiv.firstElementChild;
}

async function fillExonWithNucleotidesAsync(exonElement, exonData) {
    const sequenceContent = exonElement.querySelector('.sequence-content');
    
    // Параллельно создаем все нуклеотиды для этого экзона
    const nucleotidePromises = Array.from(exonData.sequence).map((nucleotide, i) => {
        return new Promise(resolve => {
            const { globalPosition, numberCodon, isUtr, isCoding, region } = 
                calculateNucleotideProperties(exonData.start_position, i, exonData.utr5, exonData.utr3);
            const classCodon = (numberCodon % 2) ? 'first_codon' : 'second_codon';
            
            const nucleotideData = {
                classes: isUtr ? 'utr' : 'coding' + ' ' + classCodon,
                position_nucleotide: isUtr ? -1 : globalPosition,
                number_codon: isUtr ? -1 : numberCodon,
                isUtr: isUtr,
                isCoding: isCoding,
                region: region,
                nucleotide: nucleotide
            };
            
            const nucleotideElement = createNucleotideElement(nucleotideData);
            resolve({ element: nucleotideElement, position: i });
        });
    });
    
    const nucleotideResults = await Promise.all(nucleotidePromises);
    
    // Сортируем по позиции и добавляем в правильном порядке
    nucleotideResults.sort((a, b) => a.position - b.position);
    
    const fragment = document.createDocumentFragment();
    nucleotideResults.forEach(result => fragment.appendChild(result.element));
    sequenceContent.appendChild(fragment);
    
    return exonElement;
}

async function createDomainElementAsync(domainData) {
    // Создаем элемент домена без аминокислот
    const domainHtml = compileTemplate('domainTemplate', domainData);
    const tempDiv = document.createElement('div');
    tempDiv.innerHTML = domainHtml;
    return tempDiv.firstElementChild;
}

async function fillDomainWithAminoacidsAsync(domainElement, domainData) {
    const sequenceContent = domainElement.querySelector('.sequence-content');
    
    // Параллельно создаем все аминокислоты для этого домена
    const aminoacidPromises = Array.from(domainData.sequence).map((aminoacid, i) => {
        return new Promise(resolve => {
            const positionAminoacid = domainData.start + i;
            
            const aminoacidData = {
                position_aminoacid: positionAminoacid,
                aminoacid: aminoacid
            };
            
            const aminoacidHtml = compileTemplate('aminoacidTemplate', aminoacidData);
            const tempSpan = document.createElement('span');
            tempSpan.innerHTML = aminoacidHtml;
            const aminoacidElement = tempSpan.firstElementChild;
            
            resolve({ element: aminoacidElement, position: i });
        });
    });
    
    const aminoacidResults = await Promise.all(aminoacidPromises);
    
    // Сортируем по позиции и добавляем в правильном порядке
    aminoacidResults.sort((a, b) => a.position - b.position);
    
    const fragment = document.createDocumentFragment();
    aminoacidResults.forEach(result => fragment.appendChild(result.element));
    sequenceContent.appendChild(fragment);
    
    return domainElement;
}

// Вспомогательные функции для максимального параллелизма
async function createAllExonsParallel(exons) {
    const full_sequence = currentGene.base_sequence.full_sequence;
    const utr5 = currentGene.base_sequence.utr5;
    const utr3 = currentGene.base_sequence.utr3;
    
    // Параллельно создаем данные для всех экзонов
    const exonDataPromises = exons.map(exon => 
        Promise.resolve(createExonData(exon, full_sequence, utr5, utr3))
    );
    
    const exonDatas = await Promise.all(exonDataPromises);
    
    // Параллельно создаем элементы всех экзонов (без нуклеотидов)
    const exonElementPromises = exonDatas.map(exonData => 
        createExonElementAsync(exonData)
    );
    
    const exonElements = await Promise.all(exonElementPromises);
    
    return { exonDatas, exonElements };
}

async function displayAllExonsParallel({ exonDatas, exonElements }) {
    start = performance.now();
    const container = document.getElementById('exonsContainer');
    const countEl = document.getElementById('exonCount');
    
    container.innerHTML = '';
    countEl.innerHTML = `<i class="fas fa-layer-group"></i> ${exonElements.length} экзонов`;
    
    // Параллельно наполняем все экзоны нуклеотидами
    const fillPromises = exonElements.map((exonElement, index) => 
        fillExonWithNucleotidesAsync(exonElement, exonDatas[index])
    );
    
    await Promise.all(fillPromises);
    
    // Добавляем все экзоны разом
    const fragment = document.createDocumentFragment();
    exonElements.forEach(element => fragment.appendChild(element));
    container.appendChild(fragment);
    console.log(performance.now() - start);
}

async function createAllDomainsParallel(domains) {
    // Параллельно создаем данные для всех доменов
    const domainDataPromises = domains.map((domain, index) => 
        Promise.resolve({
            ...domain,
            number: index + 1,
        })
    );
    
    const domainDatas = await Promise.all(domainDataPromises);
    
    // Параллельно создаем элементы всех доменов (без аминокислот)
    const domainElementPromises = domainDatas.map(domainData => 
        createDomainElementAsync(domainData)
    );
    
    const domainElements = await Promise.all(domainElementPromises);
    
    return { domainDatas, domainElements };
}

async function displayAllDomainsParallel({ domainDatas, domainElements }) {
    const container = document.getElementById('domainsContainer');
    const countEl = document.getElementById('domainCount');
    
    container.innerHTML = '';
    countEl.innerHTML = `<i class="fas fa-shapes"></i> ${domainElements.length} доменов`;
    
    // Параллельно наполняем все домены аминокислотами
    const fillPromises = domainElements.map((domainElement, index) => 
        fillDomainWithAminoacidsAsync(domainElement, domainDatas[index])
    );
    
    await Promise.all(fillPromises);
    
    // Добавляем все домены разом
    const fragment = document.createDocumentFragment();
    domainElements.forEach(element => fragment.appendChild(element));
    container.appendChild(fragment);
}

// Построение гена через API
async function buildGene() {
    const source = document.getElementById('source').value;
    const geneId = document.getElementById('geneId').value.trim();
    const proteinId = document.getElementById('proteinId').value.trim();
    
    if (!geneId || !proteinId) {
        showStatus('Пожалуйста, заполните все поля', 'error');
        return;
    }
    
    showStatus('Построение гена...', 'loading');
    
    try {
        const response = await fetch('/api/gene/build', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                source,
                gene_id: geneId,
                protein_id: proteinId
            })
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || 'Ошибка при построении гена');
        }
        
        currentGene = data.gene;
        showStatus('Ген успешно построен!', 'success');
        
        // ПАРАЛЛЕЛЬНОЕ ОТОБРАЖЕНИЕ ВСЕГО КОНТЕНТА
        try {
            // Запускаем ВСЕ задачи параллельно на 4 уровнях:
            
            // Уровень 1: Основная информация гена
            const geneInfoPromise = Promise.resolve(displayGeneInfo(currentGene));

            // Уровень 2: Подготовка данных для экзонов и доменов (параллельно)
            const [exonsData, domainsData] = await Promise.all([
                Promise.resolve(currentGene.base_sequence.exons),
                Promise.resolve(currentGene.protein.domains)
            ]);
            
            // Уровень 3: Создание элементов экзонов и доменов (параллельно)
            const [exonsCreated, domainsCreated] = await Promise.all([
                createAllExonsParallel(exonsData),
                createAllDomainsParallel(domainsData)
            ]);
            
            // Уровень 4: Наполнение элементами и отображение (параллельно)
            await Promise.all([
                geneInfoPromise,
                displayAllExonsParallel(exonsCreated),
                displayAllDomainsParallel(domainsCreated)
            ]);
            
            // Показываем содержимое после завершения всех задач
            document.getElementById('geneContent').style.display = 'flex';
            
        } catch (displayError) {
            console.error('Ошибка при отображении:', displayError);
            showError('Ошибка при отображении данных гена');
        }
        
    } catch (error) {
        showStatus(error.message, 'error');
        showError(error.message);
    }
}

// Инициализация
document.addEventListener('DOMContentLoaded', function() {
    // Кнопка построения гена
    document.getElementById('buildGeneBtn').addEventListener('click', buildGene);
    
    // Обработка Enter в полях формы
    document.getElementById('geneId').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') buildGene();
    });
    
    document.getElementById('proteinId').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') buildGene();
    });
});