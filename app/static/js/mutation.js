// Открытие/закрытие меню мутаций
document.addEventListener('DOMContentLoaded', function() {
    const menuToggle = document.getElementById('mutationMenuToggle');
    const mutationMenu = document.getElementById('mutationMenu');
    const closeBtn = document.getElementById('closeMutationMenu');
    const overlay = document.getElementById('mutationMenuOverlay');
    
    // Открытие меню
    menuToggle.addEventListener('click', () => {
        mutationMenu.classList.add('active');
        overlay.classList.add('active');
    });
    
    // Закрытие меню через кнопку X
    closeBtn.addEventListener('click', () => {
        mutationMenu.classList.remove('active');
        overlay.classList.remove('active');
    });
    
    // Закрытие меню через клик по фону
    overlay.addEventListener('click', () => {
        mutationMenu.classList.remove('active');
        overlay.classList.remove('active');
    });
    
    // Закрытие меню через Escape
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && mutationMenu.classList.contains('active')) {
            mutationMenu.classList.remove('active');
            overlay.classList.remove('active');
        }
    });
    
    // Переключение типа мутации
    const mutationTypes = document.querySelectorAll('.mutation-type-option');
    mutationTypes.forEach(type => {
        type.addEventListener('click', function() {
            // Снимаем активный класс со всех типов
            mutationTypes.forEach(t => t.classList.remove('active'));
            // Добавляем активный класс к выбранному типу
            this.classList.add('active');
            // Обновляем форму в зависимости от выбранного типа
            updateMutationForm(this.dataset.type);
        });
    });
    
    // Обработка полей ввода
    setupInputHandlers();
    
    // Инициализируем форму с первым типом мутации (Поиск)
    const defaultType = document.querySelector('.mutation-type-option.active');
    if (defaultType) {
        updateMutationForm(defaultType.dataset.type);
    }
});

// Настройка обработчиков полей ввода
function setupInputHandlers() {
    // Для диапазона удаления
    const mutationStart = document.getElementById('mutationStart');
    const mutationEnd = document.getElementById('mutationEnd');
    
    if (mutationStart && mutationEnd) {
        mutationStart.addEventListener('input', function() {
            if (this.value && !mutationEnd.value) {
                mutationEnd.value = parseInt(this.value) + 1;
            }
        });
        
        mutationEnd.addEventListener('blur', function() {
            if (mutationStart.value && this.value && parseInt(this.value) < parseInt(mutationStart.value)) {
                this.value = parseInt(mutationStart.value) + 1;
            }
        });
    }
    
    // Для вставки между позициями
    const insertPosition = document.getElementById('insertPosition');
    if (insertPosition) {
        insertPosition.addEventListener('input', function() {
            const before = this.value ? parseInt(this.value) : 'X';
            const after = this.value ? (parseInt(this.value) + 1) : 'X + 1';
            document.getElementById('insertBefore').textContent = before;
            document.getElementById('insertAfter').textContent = after;
            
            // Обновляем основное поле позиции
            const mainPosition = document.getElementById('mutationPosition');
            if (mainPosition && this.value) {
                mainPosition.value = this.value;
            }
        });
    }
    
    // Для поиска позиции
    const mutationPosition = document.getElementById('mutationPosition');
    if (mutationPosition) {
        mutationPosition.addEventListener('input', function() {
            // Обновляем поле вставки между позициями
            const insertPos = document.getElementById('insertPosition');
            if (insertPos && this.value) {
                insertPos.value = this.value;
                insertPos.dispatchEvent(new Event('input'));
            }
            
            // Обновляем начальную позицию для диапазона
            const startPos = document.getElementById('mutationStart');
            if (startPos && this.value) {
                startPos.value = this.value;
            }
        });
    }
}

// Обновление формы в зависимости от типа мутации
function updateMutationForm(type) {
    // Получаем все элементы параметров
    const positionParam = document.getElementById('positionParam');
    const sequenceParam = document.getElementById('sequenceParam');
    const rangeParam = document.getElementById('rangeParam');
    const insertBetweenParam = document.getElementById('insertBetweenParam');
    const exonParam = document.getElementById('exonParam');
    
    const sequenceInput = document.getElementById('mutationSequence');
    const positionInput = document.getElementById('mutationPosition');
    const titleElement = document.getElementById('mutationParamsTitle');
    
    // Очищаем все поля
    clearAllFields();
    
    // Скрыть все поля
    positionParam.style.display = 'none';
    sequenceParam.style.display = 'none';
    rangeParam.style.display = 'none';
    insertBetweenParam.style.display = 'none';
    exonParam.style.display = 'none';
    
    // Обновляем заголовок раздела
    const titles = {
        'find': 'Параметры поиска',
        'substitution': 'Параметры замены',
        'insertion': 'Параметры вставки',
        'deletion': 'Параметры удаления',
        'exon_deletion': 'Параметры удаления экзона'
    };
    
    if (titleElement) {
        titleElement.innerHTML = `<i class="fas fa-sliders-h"></i> ${titles[type] || 'Параметры'}`;
    }
    
    // Настраиваем поля для каждого типа
    switch(type) {
        case 'find':
            positionParam.style.display = 'block';
            updateLabel('positionLabel', '<i class="fas fa-map-marker-alt"></i> Позиция для поиска:');
            positionInput.placeholder = 'Введите номер нуклеотида';
            break;
            
        case 'substitution':
            positionParam.style.display = 'block';
            sequenceParam.style.display = 'block';
            updateLabel('positionLabel', '<i class="fas fa-map-marker-alt"></i> Позиция замены:');
            positionInput.placeholder = 'Позиция заменяемого нуклеотида';
            if (sequenceInput) {
                sequenceInput.placeholder = 'Новый нуклеотид (A, T, C, G)';
                sequenceInput.maxLength = 1;
            }
            break;
            
        case 'insertion':
            positionParam.style.display = 'none'; // Скрываем основное поле позиции
            insertBetweenParam.style.display = 'block';
            sequenceParam.style.display = 'block';
            if (sequenceInput) {
                sequenceInput.placeholder = 'Последовательность для вставки';
                sequenceInput.maxLength = 20;
            }
            break;
            
        case 'deletion':
            rangeParam.style.display = 'block';
            updateLabel('positionLabel', '<i class="fas fa-map-marker-alt"></i> Позиция удаления:');
            break;
            
        case 'exon_deletion':
            positionParam.style.display = 'block';
            updateLabel('positionLabel', '<i class="fas fa-map-marker-alt"></i> Позиция для удаления:');
            positionInput.placeholder = 'Введите номер нуклеотида';
            
            // Заполняем список экзонов
            const exonSelect = document.getElementById('exonSelect');
            if (exonSelect) {
                exonSelect.innerHTML = '<option value="">-- Выберите экзон --</option>';
                // Добавляем экзоны из DOM если они есть
                const exonCards = document.querySelectorAll('.exon-card');
                if (exonCards.length > 0) {
                    exonCards.forEach(card => {
                        const exonNum = card.dataset.exonNumber;
                        const option = document.createElement('option');
                        option.value = exonNum;
                        option.textContent = `Экзон ${exonNum}`;
                        exonSelect.appendChild(option);
                    });
                } else {
                    // Демо экзоны
                    for (let i = 1; i <= 5; i++) {
                        const option = document.createElement('option');
                        option.value = i;
                        option.textContent = `Экзон ${i}`;
                        exonSelect.appendChild(option);
                    }
                }
            }
            break;
    }
    
    // Обновляем текст кнопки применения
    const applyBtn = document.getElementById('applyMutation');
    if (applyBtn) {
        const buttonTexts = {
            'find': '<i class="fas fa-search"></i> Найти',
            'substitution': '<i class="fas fa-exchange-alt"></i> Заменить',
            'insertion': '<i class="fas fa-plus"></i> Вставить',
            'deletion': '<i class="fas fa-minus"></i> Удалить',
            'exon_deletion': '<i class="fas fa-trash-alt"></i> Удалить экзон'
        };
        applyBtn.innerHTML = buttonTexts[type] || '<i class="fas fa-play"></i> Выполнить';
    }
}

// Обновление текста метки
function updateLabel(elementId, newText) {
    const element = document.getElementById(elementId);
    if (element) {
        element.innerHTML = newText;
    }
}

// Очистка всех полей
function clearAllFields() {
    // Очищаем основные поля
    document.querySelectorAll('.mutation-input').forEach(input => {
        if (input.type !== 'select-one') { // Не очищаем select
            input.value = '';
        }
    });
    
    // Сбрасываем select
    const exonSelect = document.getElementById('exonSelect');
    if (exonSelect) {
        exonSelect.selectedIndex = 0;
    }
    
    // Сбрасываем поле вставки между позициями
    document.getElementById('insertBefore').textContent = 'X ';
    document.getElementById('insertAfter').textContent = 'X + 1';
    
    // Сбрасываем результат
    const resultDiv = document.getElementById('mutationResult');
    if (resultDiv) {
        resultDiv.innerHTML = '<p>Действие не выполнено</p>';
        resultDiv.style.borderLeftColor = '#4a90e2';
    }
}

// Функция для кнопки "Выполнить"
document.getElementById('applyMutation')?.addEventListener('click', function() {
    const activeType = document.querySelector('.mutation-type-option.active')?.dataset.type;
    const resultDiv = document.getElementById('mutationResult');
    
    if (!resultDiv) return;
    
    // Получаем значения полей
    const position = document.getElementById('mutationPosition')?.value;
    const sequence = document.getElementById('mutationSequence')?.value;
    const startPos = document.getElementById('mutationStart')?.value;
    const endPos = document.getElementById('mutationEnd')?.value;
    const insertPos = document.getElementById('insertPosition')?.value;
    const exonSelect = document.getElementById('exonSelect')?.value;
    
    // Валидация
    if (!validateInputs(activeType, position, sequence, startPos, endPos, insertPos, exonSelect)) {
        return;
    }
    
    // Отображаем результат
    showResult(activeType, {
        position,
        sequence,
        startPos,
        endPos,
        insertPos,
        exon: exonSelect
    });
});

// Валидация ввода
function validateInputs(type, position, sequence, startPos, endPos, insertPos, exon) {
    switch(type) {
        case 'find':
            if (!position) {
                showError('Введите позицию для поиска');
                return false;
            }
            break;
            
        case 'substitution':
            if (!position || !sequence) {
                showError('Заполните позицию и новый нуклеотид');
                return false;
            }
            if (!['A', 'T', 'C', 'G'].includes(sequence.toUpperCase())) {
                showError('Новый нуклеотид должен быть A, T, C или G');
                return false;
            }
            break;
            
        case 'insertion':
            if (!insertPos || !sequence) {
                showError('Заполните позицию и последовательность для вставки');
                return false;
            }
            break;
            
        case 'deletion':
            if (!startPos || !endPos) {
                showError('Заполните начальную и конечную позиции');
                return false;
            }
            if (parseInt(endPos) <= parseInt(startPos)) {
                showError('Конечная позиция должна быть больше начальной');
                return false;
            }
            break;
            
        case 'exon_deletion':
            if (!exon) {
                showError('Выберите экзон для удаления');
                return false;
            }
            break;
    }
    return true;
}

// Показать ошибку
function showError(message) {
    const resultDiv = document.getElementById('mutationResult');
    if (resultDiv) {
        resultDiv.innerHTML = `
            <p style="color: #dc3545;"><i class="fas fa-exclamation-triangle"></i> Ошибка: ${message}</p>
        `;
        resultDiv.style.borderLeftColor = '#dc3545';
    }
}

function FindExon(position) {
    const element = document.querySelector(`[data-position="${position}"]`);
    element.classList.add("find");
}

function FindDomain(position) {
    const current_domains = currentGene.protein.domains;
    positon = parseInt((parseInt(position) - 1) / 3);

    for(const domain of current_domains) {
        console.log(domain.name);
        if (domain.start <= position && position <= domain.end) {            
            return [domain.name, position - domain.start];
        }
    }
}

function ShowFindExon(exon_number, position) {
    element = document.querySelector(`[data-exon-number="${exon_number}"]`);
    element = element.getElementsByClassName('sequence-content')[0];
    if (element.childElementCount == 2) {
        element_utr = element.getElementsByClassName('utr')[0];
        position = position - element_utr.textContent.trim().length;
    }
    codingSequenceElement = element.getElementsByClassName('coding')[0];
    sequence = codingSequenceElement.textContent.trim();
    
    // Разделяем последовательность
    before = sequence.slice(0, position);
    atPosition = sequence.charAt(position);
    after = sequence.slice(position + 1);

    // Создаем новые spans
    beforeSpan = document.createElement('span');
    atPositionSpan = document.createElement('span');
    afterSpan = document.createElement('span');

    beforeSpan.textContent = before;
    atPositionSpan.textContent = atPosition;
    atPositionSpan.classList.add("find");
    afterSpan.textContent = after;

    // Очищаем оригинальный элемент и добавляем новые
    codingSequenceElement.innerHTML = ''; // Очищаем содержимое
    codingSequenceElement.appendChild(beforeSpan);
    codingSequenceElement.appendChild(atPositionSpan);
    codingSequenceElement.appendChild(afterSpan);

    // Эмулируем нажатие клавиши Escape
    const escapeEvent = new KeyboardEvent('keydown', {
        key: 'Escape',
        keyCode: 27,
        code: 'Escape',
        which: 27,
        bubbles: true,
    });
    document.dispatchEvent(escapeEvent);

    // Прокручиваем страницу к созданному элементу
    const rect = codingSequenceElement.getBoundingClientRect();
    const windowHeight = window.innerHeight;
    const scrollTop = window.scrollY;

    // Вычисляем новую позицию для прокрутки
    const newScrollTop = scrollTop + rect.top - (windowHeight / 2 - rect.height / 2);
    window.scrollTo({ top: newScrollTop, behavior: 'smooth' });

    return atPosition;
}

// Показать результат
function showResult(type, data) {
    const resultDiv = document.getElementById('mutationResult');
    
    let resultHTML = '';
    const processingHTML = `
        <p><strong>Обработка...</strong></p>
        <p><i class="fas fa-spinner fa-spin"></i> Выполняется ${getTypeName(type)}</p>
    `;
    
    resultDiv.innerHTML = processingHTML;
    resultDiv.style.borderLeftColor = '#ff9800';
    
    // Демонстрационный результат через 1.5 секунды
    setTimeout(() => {
        switch(type) {
            case 'find':
                restorePage();
                backupPage();
                FindExon(data.position);
                resultHTML = `
                    <p><strong>Результат поиска</strong></p>
                    <p>Найдено в экзоне: <strong>Экзон ${1}</strong></p>
                    <p>Нуклеотид: <strong>${1}</strong></p>
                    <p>Найдено в домене: <strong>Домен ${1}</strong></p>
                    <p class="success"><i class="fas fa-check-circle"></i> Поиск завершен</p>
                `;
                break;
                
            case 'substitution':
                resultHTML = `
                    <p><strong>Замена выполнена</strong></p>
                    <p>Позиция: <strong>${data.position}</strong></p>
                    <p>Новый нуклеотид: <strong>${data.sequence}</strong></p>
                    <p>Статус: <strong>Успешно</strong></p>
                    <p class="success"><i class="fas fa-check-circle"></i> Замена применена</p>
                `;
                break;
                
            case 'insertion':
                resultHTML = `
                    <p><strong>Вставка выполнена</strong></p>
                    <p>Между позициями: <strong>${data.insertPos} и ${parseInt(data.insertPos) + 1}</strong></p>
                    <p>Вставленная последовательность: <strong>${data.sequence}</strong></p>
                    <p>Длина: <strong>${data.sequence.length} нуклеотидов</strong></p>
                    <p class="success"><i class="fas fa-check-circle"></i> Вставка применена</p>
                `;
                break;
                
            case 'deletion':
                resultHTML = `
                    <p><strong>Удаление выполнено</strong></p>
                    <p>Диапазон: <strong>${data.startPos} - ${data.endPos}</strong></p>
                    <p>Удалено нуклеотидов: <strong>${parseInt(data.endPos) - parseInt(data.startPos) + 1}</strong></p>
                    <p>Статус: <strong>Успешно</strong></p>
                    <p class="success"><i class="fas fa-check-circle"></i> Удаление применено</p>
                `;
                break;
                
            case 'exon_deletion':
                resultHTML = `
                    <p><strong>Экзон удален</strong></p>
                    <p>Удаленный экзон: <strong>Экзон ${data.exon}</strong></p>
                    ${data.position ? `<p>Позиция в экзоне: <strong>${data.position}</strong></p>` : ''}
                    <p>Статус: <strong>Успешно</strong></p>
                    <p class="success"><i class="fas fa-check-circle"></i> Экзон удален</p>
                `;
                break;
        }
        
        resultDiv.innerHTML = resultHTML;
        resultDiv.style.borderLeftColor = '#28a745';
    }, 1500);
}

// Получить название типа
function getTypeName(type) {
    const names = {
        'find': 'поиск',
        'substitution': 'замена',
        'insertion': 'вставка',
        'deletion': 'удаление',
        'exon_deletion': 'удаление экзона'
    };
    return names[type] || 'действие';
}

// Функция для кнопки "Сбросить"
document.getElementById('resetMutation')?.addEventListener('click', function() {
    // Очищаем все поля
    clearAllFields();
    
    // Сбрасываем на тип "Поиск"
    const firstType = document.querySelector('.mutation-type-option[data-type="find"]');
    if (firstType) {
        document.querySelectorAll('.mutation-type-option').forEach(t => t.classList.remove('active'));
        firstType.classList.add('active');
        updateMutationForm('find');
    }
});

// Супер-мини версия
let pageBackup = null;

function backupPage() {
    pageBackup = {
        exons: document.getElementById('exonsContainer')?.innerHTML,
        domains: document.getElementById('domainsContainer')?.innerHTML,
        time: Date.now()
    };
}

function restorePage() {
    if (!pageBackup) return;
    
    const exons = document.getElementById('exonsContainer');
    const domains = document.getElementById('domainsContainer');
    
    if (exons && pageBackup.exons) exons.innerHTML = pageBackup.exons;
    if (domains && pageBackup.domains) domains.innerHTML = pageBackup.domains;
}