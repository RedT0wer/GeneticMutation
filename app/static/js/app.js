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

function displayExons(exons, totalLength) {
    const container = document.getElementById('exonsContainer');
    const countEl = document.getElementById('exonCount');
    const full_sequence = currentGene.base_sequence.full_sequence;
    
    // Получаем UTR области из base_sequence
    const utr5 = currentGene.base_sequence.utr5;
    const utr3 = currentGene.base_sequence.utr3;
    
    // Очищаем контейнер
    container.innerHTML = '';
    
    // Обновляем статистику сразу
    countEl.innerHTML = `<i class="fas fa-layer-group"></i> ${exons.length} экзонов`;
    
    // Создаем DocumentFragment для более эффективного добавления
    const fragment = document.createDocumentFragment();
    
    for(const exon of exons) {
        // Получаем полную последовательность экзона
        const exonSequence = full_sequence.slice(exon.start_position, exon.end_position + 1);
        
        const exonData = {
            ...exon,
            identifier: currentGene.base_sequence.identifier,
            sequence: exonSequence,
            utr5: utr5.end_position,
            utr3: utr3.start_position
        };
        
        // Создаем HTML экзона
        const exonHtml = compileTemplate('exonTemplate', exonData);
        
        // Создаем временный контейнер для парсинга HTML
        const tempDiv = document.createElement('div');
        tempDiv.innerHTML = exonHtml;
        const exonElement = tempDiv.firstElementChild;
        
        // Находим контейнер для последовательности
        const sequenceContent = exonElement.querySelector('.sequence-content');
        
        // Создаем DocumentFragment для нуклеотидов
        const nucleotidesFragment = document.createDocumentFragment();
        
        // Создаем элементы для каждого нуклеотида
        for (let i = 0; i < exonSequence.length; i++) {
            const nucleotide = exonSequence[i];
            const globalPosition = exon.start_position + i + 1;
            
            // Вычисления для нуклеотида
            const positionNucleotide = globalPosition;
            const numberCodon = Math.floor(i / 3);
            const isUtr = globalPosition < utr5.end_position || globalPosition >= utr3.start_position;
            
            // Определяем классы для нуклеотида
            let classes = 'coding';
            if (isUtr) {
                classes = 'utr';
            }
            
            // Создаем данные для шаблона нуклеотида
            const nucleotideData = {
                classes: classes,
                position_nucleotide: positionNucleotide,
                number_codon: numberCodon,
                isUtr: isUtr,
                nucleotide: nucleotide
            };
            
            // Создаем элемент нуклеотида
            const nucleotideHtml = compileTemplate('nucleotideTemplate', nucleotideData);
            
            // Создаем временный элемент для нуклеотида
            const tempSpan = document.createElement('span');
            tempSpan.innerHTML = nucleotideHtml;
            const nucleotideElement = tempSpan.firstElementChild;
            
            // Добавляем нуклеотид во фрагмент
            nucleotidesFragment.appendChild(nucleotideElement);
        }
        
        // Добавляем все нуклеотиды в контейнер последовательности
        sequenceContent.appendChild(nucleotidesFragment);
        
        // Добавляем экзон во фрагмент
        fragment.appendChild(exonElement);
    }
    
    // Добавляем все экзоны на страницу за одну операцию
    container.appendChild(fragment);
}

// Отображение доменов
function displayDomains(domains, totalLength) {
    const container = document.getElementById('domainsContainer');
    const countEl = document.getElementById('domainCount');
    
    container.innerHTML = '';
    
    domains.forEach(domain => {
        const domainLength = domain.end - domain.start + 1;
        
        const domainData = {
            ...domain,
            total_length: totalLength,
            sequence: domain.sequence
        };
        
        const html = compileTemplate('domainTemplate', domainData);
        container.innerHTML += html;
    });
    
    // Обновляем статистику
    countEl.innerHTML = `<i class="fas fa-shapes"></i> ${domains.length} доменов`;
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
        
        // Отображаем информацию
        displayGeneInfo(currentGene);
        displayExons(currentGene.base_sequence.exons, currentGene.base_sequence.length);
        displayDomains(currentGene.protein.domains, currentGene.protein.length);
        
        // Показываем содержимое
        document.getElementById('geneContent').style.display = 'flex';
        
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