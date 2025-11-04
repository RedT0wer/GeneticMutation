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

// Загрузка гена
async function loadGene() {
    const geneId = document.getElementById('gene_id').value.trim();

    if (!geneId) {
        updateStatus('Please enter a Gene ID', 'error');
        return;
    }

    updateStatus('Loading gene data...', 'loading');

    try {
        const response = await fetch(`/api/genes/${geneId}?species=human`);
        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Failed to load gene');
        }

        currentGene = data;
        displayExons(data.exons);
        updateStatus(`Gene ${geneId} loaded successfully`, 'success');

    } catch (error) {
        updateStatus(`Error: ${error.message}`, 'error');
        console.error('Gene loading error:', error);
    }
}

// Загрузка белка
async function loadProtein() {
    const proteinId = document.getElementById('protein_id').value.trim();

    if (!proteinId) {
        updateStatus('Please enter a Protein ID', 'error');
        return;
    }

    updateStatus('Loading protein data...', 'loading');

    try {
        // В реальном приложении здесь будет вызов API
        // Для демо создаем mock данные
        const mockDomains = [
            { name: 'DNA-binding', start: 100, end: 300, sequence: 'MOCKSEQ1' },
            { name: 'Transactivation', start: 400, end: 500, sequence: 'MOCKSEQ2' },
            { name: 'Tetramerization', start: 600, end: 700, sequence: 'MOCKSEQ3' }
        ];

        currentProtein = { domains: mockDomains };
        displayDomains(mockDomains, 'original-domains');
        updateStatus(`Protein ${proteinId} domains loaded`, 'success');

    } catch (error) {
        updateStatus(`Error: ${error.message}`, 'error');
        console.error('Protein loading error:', error);
    }
}

// Применение мутации
function applyMutation() {
    if (!currentGene && !currentProtein) {
        updateStatus('Please load gene and protein data first', 'error');
        return;
    }

    const type = document.getElementById('mutation_type').value;
    const position = parseInt(document.getElementById('mutation_position').value);
    const sequence = document.getElementById('mutation_sequence').value;

    if (!position || position < 0) {
        updateStatus('Please enter a valid position', 'error');
        return;
    }

    if ((type === 'substitution' || type === 'insertion') && !sequence) {
        updateStatus('Please enter sequence for this mutation type', 'error');
        return;
    }

    const mutation = { type, position, sequence, id: Date.now() };
    mutations.push(mutation);

    // Обновляем отображение
    updateDisplayWithMutations();
    updateStatus(`Applied ${type} mutation at position ${position}`, 'success');
}

// Очистка мутаций
function clearMutations() {
    mutations = [];
    updateDisplayWithMutations();
    updateStatus('All mutations cleared', 'success');
}

// Отображение экзонов
function displayExons(exons) {
    const container = document.getElementById('exons-display');

    if (!exons || exons.length === 0) {
        container.innerHTML = '<div class="placeholder">No exons data available</div>';
        return;
    }

    let html = '<div class="exons-container">';

    exons.forEach((exon, index) => {
        const isModified = mutations.some(m =>
            m.position >= exon.start_position && m.position <= exon.end_position
        );

        const isHighlighted = mutations.some(m => m.position === exon.start_position);

        let className = 'exon-block';
        if (isModified) className += ' modified';
        if (isHighlighted) className += ' highlight';

        html += `
            <div class="${className}" title="Exon ${exon.number}: ${exon.start_position}-${exon.end_position}">
                Exon ${exon.number}
            </div>
        `;
    });

    html += '</div>';
    container.innerHTML = html;
}

// Отображение доменов
function displayDomains(domains, containerId) {
    const container = document.getElementById(containerId);

    if (!domains || domains.length === 0) {
        container.innerHTML = '<div class="placeholder">No domains data available</div>';
        return;
    }

    let html = '<div class="domains-container">';

    domains.forEach((domain, index) => {
        const isModified = containerId === 'modified-domains' && mutations.length > 0;
        const isChanged = isModified && mutations.some(m =>
            m.position >= domain.start * 3 && m.position <= domain.end * 3
        );

        let className = 'domain-block';
        if (isModified) className += ' modified';
        if (isChanged) className += ' changed';

        html += `
            <div class="${className}" 
                 data-positions="${domain.start}-${domain.end}"
                 title="${domain.name}: ${domain.start}-${domain.end}">
                ${domain.name}
            </div>
        `;
    });

    html += '</div>';
    container.innerHTML = html;
}

// Обновление отображения с учетом мутаций
function updateDisplayWithMutations() {
    if (currentGene) {
        displayExons(currentGene.exons);
    }

    if (currentProtein) {
        displayDomains(currentProtein.domains, 'original-domains');

        // Для модифицированных доменов создаем копию с изменениями
        const modifiedDomains = currentProtein.domains.map(domain => ({
            ...domain,
            name: domain.name + (mutations.length > 0 ? ' (modified)' : '')
        }));

        displayDomains(modifiedDomains, 'modified-domains');
    }
}

// Mock данные для демонстрации
function loadDemoData() {
    // Mock экзоны
    const mockExons = [
        { number: 1, start_position: 0, end_position: 149, sequence: 'ATG...' },
        { number: 2, start_position: 150, end_position: 299, sequence: 'GCT...' },
        { number: 3, start_position: 300, end_position: 449, sequence: 'TAC...' },
        { number: 4, start_position: 450, end_position: 599, sequence: 'GGA...' },
        { number: 5, start_position: 600, end_position: 749, sequence: 'CTT...' }
    ];

    // Mock домены
    const mockDomains = [
        { name: 'DNA-binding', start: 100, end: 300, sequence: 'MOCKSEQ1' },
        { name: 'Transactivation', start: 400, end: 500, sequence: 'MOCKSEQ2' },
        { name: 'Tetramerization', start: 600, end: 700, sequence: 'MOCKSEQ3' }
    ];

    currentGene = { exons: mockExons };
    currentProtein = { domains: mockDomains };

    displayExons(mockExons);
    displayDomains(mockDomains, 'original-domains');
    displayDomains(mockDomains, 'modified-domains');

    updateStatus('Demo data loaded. Try applying mutations!', 'success');
}

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', function () {
    updateStatus('Application ready. Load demo data or enter your own IDs.');

    // Автозагрузка демо данных для удобства
    setTimeout(loadDemoData, 1000);
});

// Обработчики клавиш
document.addEventListener('keypress', function (e) {
    if (e.key === 'Enter') {
        if (document.activeElement.id === 'gene_id') {
            loadGene();
        } else if (document.activeElement.id === 'protein_id') {
            loadProtein();
        }
    }
});