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

// ПАРАЛЛЕЛЬНОЕ СОЗДАНИЕ ЭКЗОНОВ
async function displayExons(exons) {
    const container = document.getElementById('exonsContainer');
    const countEl = document.getElementById('exonCount');
    const full_sequence = currentGene.base_sequence.full_sequence;
    
    const utr5 = currentGene.base_sequence.utr5;
    const utr3 = currentGene.base_sequence.utr3;

    container.innerHTML = '';
    
    countEl.innerHTML = `<i class="fas fa-layer-group"></i> ${exons.length} экзонов`;
    
    // Создаем все экзоны параллельно
    const exonPromises = exons.map(exon => 
        createExonElementAsync(exon, full_sequence, utr5, utr3)
    );
    
    try {
        // Ждем завершения всех промисов
        const exonElements = await Promise.all(exonPromises);
        
        // Добавляем все разом
        const fragment = document.createDocumentFragment();
        exonElements.forEach(element => fragment.appendChild(element));
        container.appendChild(fragment);
    } catch (error) {
        console.error('Ошибка при создании экзонов:', error);
        showError('Ошибка при создании экзонов');
    }
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

async function createExonElementAsync(exon, full_sequence, utr5, utr3) {
    const exonData = createExonData(exon, full_sequence, utr5, utr3);
    
    // Создаем нуклеотиды параллельно
    const nucleotidesPromises = Array.from(exonData.sequence).map((nucleotide, i) => {
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
            resolve(nucleotideElement);
        });
    });
    
    const nucleotideElements = await Promise.all(nucleotidesPromises);
    
    // Собираем экзон
    const exonHtml = compileTemplate('exonTemplate', exonData);
    const tempDiv = document.createElement('div');
    tempDiv.innerHTML = exonHtml;
    const exonElement = tempDiv.firstElementChild;
    
    const sequenceContent = exonElement.querySelector('.sequence-content');
    
    // Добавляем все нуклеотиды
    const fragment = document.createDocumentFragment();
    nucleotideElements.forEach(element => fragment.appendChild(element));
    sequenceContent.appendChild(fragment);
    
    return exonElement;
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

// ПАРАЛЛЕЛЬНОЕ СОЗДАНИЕ ДОМЕНОВ
async function displayDomains(domains) {
    const container = document.getElementById('domainsContainer');
    const countEl = document.getElementById('domainCount');
    
    // Очищаем контейнер
    container.innerHTML = '';
    
    // Обновляем статистику сразу
    countEl.innerHTML = `<i class="fas fa-shapes"></i> ${domains.length} доменов`;
    
    // Если нет доменов, выходим
    if (domains.length === 0) return;
    
    try {
        // Создаем все домены параллельно
        const domainPromises = domains.map((domain, index) => 
            createDomainElementAsync(domain, index)
        );
        
        // Ждем завершения всех промисов
        const domainElements = await Promise.all(domainPromises);
        
        // Добавляем все разом
        const fragment = document.createDocumentFragment();
        domainElements.forEach(element => fragment.appendChild(element));
        container.appendChild(fragment);
    } catch (error) {
        console.error('Ошибка при создании доменов:', error);
        showError('Ошибка при создании доменов');
    }
}

async function createDomainElementAsync(domain, index) {
    const domainData = {
        ...domain,
        number: index + 1,
    };
    
    // Создаем аминокислоты параллельно
    const aminoacidPromises = Array.from(domainData.sequence).map((aminoacid, i) => {
        return new Promise(resolve => {
            // Позиция аминокислоты в белке (от 1)
            const positionAminoacid = domainData.start + i;
            
            // Создаем данные для шаблона аминокислоты
            const aminoacidData = {
                position_aminoacid: positionAminoacid,
                aminoacid: aminoacid
            };
            
            // Создаем элемент аминокислоты
            const aminoacidHtml = compileTemplate('aminoacidTemplate', aminoacidData);
            
            // Создаем временный элемент для аминокислоты
            const tempSpan = document.createElement('span');
            tempSpan.innerHTML = aminoacidHtml;
            const aminoacidElement = tempSpan.firstElementChild;
            
            resolve(aminoacidElement);
        });
    });
    
    const aminoacidElements = await Promise.all(aminoacidPromises);
    
    // Собираем домен
    const domainHtml = compileTemplate('domainTemplate', domainData);
    const tempDiv = document.createElement('div');
    tempDiv.innerHTML = domainHtml;
    const domainElement = tempDiv.firstElementChild;
    
    // Находим контейнер для последовательности
    const sequenceContent = domainElement.querySelector('.sequence-content');
    
    // Добавляем все аминокислоты
    const fragment = document.createDocumentFragment();
    aminoacidElements.forEach(element => fragment.appendChild(element));
    sequenceContent.appendChild(fragment);
    
    return domainElement;
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
        
        // ПАРАЛЛЕЛЬНОЕ ОТОБРАЖЕНИЕ ИНФОРМАЦИИ, ЭКЗОНОВ И ДОМЕНОВ
        try {
            // Запускаем все задачи параллельно
            await Promise.all([
                displayGeneInfo(currentGene),
                displayExons(currentGene.base_sequence.exons),
                displayDomains(currentGene.protein.domains)
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