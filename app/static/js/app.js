// Глобальные переменные
let currentGene = null;
let currentProtein = null;
let mutations = [];

// Обновление статуса
function updateStatus(message, type = 'info') {
    const statusBar = document.getElementById('status');
    statusBar.textContent = message;
    statusBar.className = 'status-bar';

    if (type === 'success') {
        statusBar.classList.add('success');
    } else if (type === 'error') {
        statusBar.classList.add('error');
    } else if (type === 'loading') {
        statusBar.classList.add('loading');
    }
}

// Загрузка гена из API
async function loadGene() {
    const geneId = document.getElementById('gene_id').value.trim();
    const proteinId = document.getElementById('protein_id').value.trim();

    if (!geneId) {
        updateStatus('Please enter a Gene ID', 'error');
        return;
    }

    if (!proteinId) {
        updateStatus('Please enter a Protein ID', 'error');
        return;
    }

    updateStatus('Building gene structure...', 'loading');

    try {
        const response = await fetch('/api/gene/build', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                source: 'ensembl',
                gene_id: geneId,
                protein_id: proteinId
            })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Failed to build gene structure');
        }

        if (!data.success) {
            throw new Error('Failed to build gene structure');
        }

        currentGene = data.gene;
        
        // Отображаем данные гена
        displayGeneData(currentGene);
        
        updateStatus(`Gene ${geneId} built successfully`, 'success');

    } catch (error) {
        updateStatus(`Error: ${error.message}`, 'error');
        console.error('Gene building error:', error);
    }
}

// Загрузка белка (теперь часть общего запроса гена)
async function loadProtein() {
    // Теперь белок загружается вместе с геном
    const geneId = document.getElementById('gene_id').value.trim();
    
    if (!geneId) {
        updateStatus('Please load gene first to get protein data', 'error');
        return;
    }
    
    if (currentGene && currentGene.protein) {
        displayProteinData(currentGene.protein);
        updateStatus('Protein data displayed from gene', 'success');
    } else {
        updateStatus('Load gene first to get protein data', 'error');
    }
}

// Отображение данных гена
function displayGeneData(gene) {
    if (!gene) {
        console.error('No gene data provided');
        return;
    }

    // 1. Отображаем экзоны
    displayExons(gene.base_sequence.exons);
    
    // 2. Отображаем информацию о гене
    displayGeneInfo(gene);
    
    // 3. Отображаем последовательности
    displaySequences(gene);
    
    // 4. Отображаем белок (если есть)
    if (gene.protein) {
        displayProteinData(gene.protein);
    }
}

// Отображение информации о гене
function displayGeneInfo(gene) {
    const infoContainer = document.getElementById('gene-info-display');
    if (!infoContainer) {
        // Создаем контейнер если его нет
        const contentDiv = document.querySelector('.content');
        const infoSection = document.createElement('div');
        infoSection.className = 'section';
        infoSection.id = 'gene-info-section';
        infoSection.innerHTML = `
            <h2>Gene Information</h2>
            <div id="gene-info-display" class="info-display"></div>
        `;
        contentDiv.insertBefore(infoSection, contentDiv.firstChild);
    }

    const infoDiv = document.getElementById('gene-info-display');
    const info = gene.base_sequence;
    
    let html = `
        <div class="info-grid">
            <div class="info-item">
                <span class="info-label">Identifier:</span>
                <span class="info-value">${info.identifier}</span>
            </div>
            <div class="info-item">
                <span class="info-label">Length:</span>
                <span class="info-value">${info.length} nucleotides</span>
            </div>
            <div class="info-item">
                <span class="info-label">Number of exons:</span>
                <span class="info-value">${info.exons.length}</span>
            </div>
            <div class="info-item">
                <span class="info-label">5' UTR length:</span>
                <span class="info-value">${info.utr5.length}</span>
            </div>
            <div class="info-item">
                <span class="info-label">3' UTR length:</span>
                <span class="info-value">${info.utr3.length}</span>
            </div>
        </div>
    `;
    
    infoDiv.innerHTML = html;
}

// Отображение последовательностей
function displaySequences(gene) {
    const sequencesContainer = document.getElementById('sequences-display');
    if (!sequencesContainer) {
        const contentDiv = document.querySelector('.content');
        const sequenceSection = document.createElement('div');
        sequenceSection.className = 'section';
        sequenceSection.id = 'sequences-section';
        sequenceSection.innerHTML = `
            <h2>Sequences</h2>
            <div id="sequences-display" class="sequences-display"></div>
        `;
        contentDiv.insertBefore(sequenceSection, document.querySelector('.domains-section'));
    }

    const seqDiv = document.getElementById('sequences-display');
    const seq = gene.base_sequence;
    
    let html = `
        <div class="sequence-tabs">
            <button class="seq-tab active" onclick="showSequence('nucleotide-full')">Full Nucleotide</button>
            <button class="seq-tab" onclick="showSequence('nucleotide-coding')">Coding Region</button>
            <button class="seq-tab" onclick="showSequence('protein')">Protein</button>
        </div>
        <div class="sequence-content">
            <div id="nucleotide-full" class="sequence-text active">
                <h3>Full Nucleotide Sequence (${seq.length} bp)</h3>
                <textarea readonly class="sequence-textarea">${seq.full_sequence || 'No sequence available'}</textarea>
            </div>
            <div id="nucleotide-coding" class="sequence-text">
                <h3>Coding Region</h3>
                <textarea readonly class="sequence-textarea">${getCodingSequence(seq) || 'No coding sequence available'}</textarea>
            </div>
            <div id="protein" class="sequence-text">
                <h3>Protein Sequence</h3>
                <textarea readonly class="sequence-textarea">${gene.protein?.sequence || 'No protein sequence available'}</textarea>
            </div>
        </div>
    `;
    
    seqDiv.innerHTML = html;
}

// Получение кодирующей последовательности
function getCodingSequence(seq) {
    if (!seq.full_sequence || seq.utr5.end_position < 0 || seq.utr3.start_position < 0) {
        return null;
    }
    const codingStart = seq.utr5.end_position + 1;
    const codingEnd = seq.utr3.start_position - 1;
    
    if (codingStart >= 0 && codingEnd > codingStart) {
        return seq.full_sequence.substring(codingStart, codingEnd + 1);
    }
    return null;
}

// Показ определенной последовательности
function showSequence(sequenceId) {
    // Убираем активный класс у всех табов
    document.querySelectorAll('.seq-tab').forEach(tab => {
        tab.classList.remove('active');
    });
    
    // Убираем активный класс у всех контентов
    document.querySelectorAll('.sequence-text').forEach(content => {
        content.classList.remove('active');
    });
    
    // Активируем выбранный таб и контент
    event.target.classList.add('active');
    document.getElementById(sequenceId).classList.add('active');
}

// Отображение экзонов
function displayExons(exons) {
    const container = document.getElementById('exons-display');

    if (!exons || exons.length === 0) {
        container.innerHTML = '<div class="placeholder">No exons data available</div>';
        return;
    }

    let html = `
        <div class="exons-info">
            <p>Total exons: ${exons.length}</p>
        </div>
        <div class="exons-container">
    `;

    exons.forEach((exon, index) => {
        const length = exon.end_position - exon.start_position + 1;
        const isCoding = exon.start_phase !== -1;
        
        let className = 'exon-block';
        if (isCoding) className += ' coding';
        if (exon.start_phase === -1) className += ' non-coding';
        
        html += `
            <div class="${className}" 
                 title="Exon ${exon.number}
Start: ${exon.start_position}
End: ${exon.end_position}
Length: ${length} bp
Phase: ${exon.start_phase !== -1 ? 'Start: ' + exon.start_phase + ', End: ' + exon.end_phase : 'Non-coding'}">
                <div class="exon-number">${exon.number}</div>
                <div class="exon-length">${length}bp</div>
                ${isCoding ? '<div class="exon-phase">Phase: ' + exon.start_phase + '</div>' : '<div class="exon-phase">UTR</div>'}
            </div>
        `;
    });

    html += '</div>';
    container.innerHTML = html;
}

// Отображение данных белка
function displayProteinData(protein) {
    const container = document.getElementById('original-domains');

    if (!protein || !protein.domains || protein.domains.length === 0) {
        container.innerHTML = '<div class="placeholder">No protein domains available</div>';
        return;
    }

    // Создаем информацию о белке
    const proteinInfo = document.getElementById('protein-info-display');
    if (!proteinInfo) {
        const domainsSection = document.querySelector('.domain-column:first-child');
        const infoDiv = document.createElement('div');
        infoDiv.id = 'protein-info-display';
        infoDiv.className = 'info-display';
        infoDiv.innerHTML = `
            <div class="protein-info">
                <p><strong>Protein ID:</strong> ${protein.identifier}</p>
                <p><strong>Length:</strong> ${protein.length} amino acids</p>
                <p><strong>Domains:</strong> ${protein.domains.length}</p>
            </div>
        `;
        domainsSection.insertBefore(infoDiv, container);
    }

    let html = '<div class="domains-container">';

    protein.domains.forEach((domain, index) => {
        const length = domain.end - domain.start + 1;
        const isConnection = domain.name === 'connection';
        
        let className = 'domain-block';
        if (isConnection) className += ' connection';
        
        html += `
            <div class="${className}" 
                 title="${domain.name}
Position: ${domain.start}-${domain.end}
Length: ${length} aa
Type: ${domain.type}">
                <div class="domain-name">${domain.name}</div>
                <div class="domain-position">${domain.start}-${domain.end}</div>
                <div class="domain-length">${length}aa</div>
            </div>
        `;
    });

    html += '</div>';
    container.innerHTML = html;
}

// Применение мутации (оставлено для совместимости)
function applyMutation() {
    updateStatus('Mutation functionality requires gene and protein data', 'info');
    // Реализация мутаций будет добавлена позже
}

// Очистка мутаций
function clearMutations() {
    mutations = [];
    if (currentGene) {
        displayGeneData(currentGene);
    }
    updateStatus('All mutations cleared', 'success');
}

// Загрузка демо данных
function loadDemoData() {
    // Устанавливаем демо значения
    document.getElementById('gene_id').value = 'ENST00000460472';
    document.getElementById('protein_id').value = 'Q8WZ42';
}

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', function () {
    updateStatus('Application ready. Enter Gene and Protein IDs or load demo data.');
    
    // Добавляем кнопку загрузки демо данных
    const inputPanel = document.querySelector('.input-panel');

    // Автозагрузка демо данных
    setTimeout(() => {
        loadDemoData();
    }, 500);
});