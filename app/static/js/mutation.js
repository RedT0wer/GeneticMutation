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
document.getElementById('applyMutation').addEventListener('click', handleApplyMutationWithApi);

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

function Find(position) {
    nucleotide = findNucleotideAtPosition(position);
    nucleotide.classList.add("find");
    sequence_content = nucleotide.parentNode;
    exon = sequence_content.parentNode;
    exon_number = exon.getAttribute("data-exon-number");

    aminoacid = FindAminoacid(position);
    aminoacid.classList.add("find");
    sequence_content = aminoacid.parentNode;
    domain = sequence_content.parentNode;
    domain_name = domain.getAttribute("data-domain-name");

    result = {
        "nucleotide": nucleotide.innerText,
        "aminoacid": aminoacid.innerText,
        "exon_number": exon_number,
        "domain_name": domain_name,
    };

    return {
        success: true,
        data: result,
        type: "FIND"
    };
}

function findNucleotideAtPosition(position) {
    return document.querySelector(`[data-position-nucleotide="${position}"]`);
}

function FindAminoacid(position) {
    position = parseInt((parseInt(position) - 1) / 3) + 1;
    return document.querySelector(`[data-position-aminoacid="${position}"]`);
}

function Substitution(position, new_nucleotide, new_aminoacid) {
    nucleotide = findNucleotideAtPosition(position);
    nucleotide.classList.add("substitution");
    new_nucleotide_element = nucleotide.cloneNode(true);
    new_nucleotide_element.innerText = "(" + new_nucleotide + ")";
    nucleotide.after(new_nucleotide_element);

    aminoacid = FindAminoacid(position);
    aminoacid.classList.add("substitution");
    new_aminoacid_element = aminoacid.cloneNode(true);
    new_aminoacid_element.innerText = "(" + new_aminoacid + ")";
    aminoacid.after(new_aminoacid_element);
}

function Insertion(insertPos, sequence, stop_codon_pos, new_domain, different_position) {
    // 1. Находим нуклеотид в позиции вставки
    const insertionNucleotide = findNucleotideAtPosition(insertPos);
    if (!insertionNucleotide) {
        console.error(`Нуклеотид в позиции ${insertPos} не найден`);
        return;
    }

    stop_codon_pos = stop_codon_pos - (sequence.length - 1);

    // 2. Обновляем нуклеотиды и данные экзона после позиции вставки
    const r = updateNucleotidesAfterInsertion(insertPos, sequence.length, stop_codon_pos);
    last_pos = r.newPos; 
    last_nucleotide = r.element;

    // 3. Обновляем позиции экзонов
    updatePositionExon(insertPos, last_pos);

    // 4. Вставляем новые нуклеотиды
    insertNewNucleotides(insertPos, sequence, insertionNucleotide);

    // 5. Скрываем все после стоп-кодона
    hideExonsAndNucleotidesAfterStopCodon(last_nucleotide);

    // 6. Скрыть все домены после
    hideDomain(insertPos);

    // 7. Вставить новый домен
    number = insertNewDomain(insertPos, new_domain);

    // 8. Присвоить стиль разным аминокислотым
    updateStyleAminoacid(number, different_position);
}

function Deletion(startPos, endPos, stop_codon_pos, new_domain, different_position) {
    // 1. Обновляем нуклеотиды и данные экзона после позиции вставки
    const r = updateNucleotidesAfterInsertion(endPos, -(endPos - startPos + 1), stop_codon_pos + 3);
    
    last_pos = r.newPos; 
    last_nucleotide = r.element;

    // 2. Обновляем позиции экзонов
    updatePositionExon(startPos, last_pos);

    // 3. Обновляем стиль для удаленных
    updateStyleNucleotide(startPos, endPos);

    // 4. Скрываем все после стоп-кодона
    hideExonsAndNucleotidesAfterStopCodon(last_nucleotide);
    
    // 5. Скрыть все домены после
    hideDomain(endPos);

    // 6. Вставить новый домен
    number = insertNewDomain(startPos, new_domain);

    // 7. Присвоить стиль разным аминокислотым
    updateStyleAminoacid(number, different_position);
}

function updateStyleNucleotide(startPos, endPos) {
    nucleotide = document.querySelector(`span[data-position-nucleotide="${startPos}"]`);
    while (startPos <= endPos) {
        nucleotide.classList.add("deletion");
        nucleotide = nucleotide.nextElementSibling;
        startPos++;
    }
}

function hideDomain(insertPos) {
    aminoacid = FindAminoacid(insertPos);
    domain_card = aminoacid.parentNode.parentNode;

    domains = document.querySelectorAll("div[class='domain-card']");
    for(let i = parseInt(domain_card.getAttribute("data-domain-number")) + 1; i < domains.length; i++) {
        domain = domains[i];
        domain.style.display = 'none';
    }
}

function insertNewDomain(insertPos, domain) {
    aminoacid = FindAminoacid(insertPos);
    prev_domain = aminoacid.parentNode.parentNode;
    prev_number = parseInt(prev_domain.getAttribute("data-domain-number"));

    const domainData = {
        ...domain,
        number: prev_number,
    };

    domainElement = createDomainElement(domainData);

    prev_domain.after(domainElement);

    return prev_number;
}

function updateStyleAminoacid(number, different_position) { 
    domains = document.querySelectorAll(`div[data-domain-number="${number}"]`);
    domains.forEach(domain => {
        aminoacids = domain.querySelectorAll("span[data-position-aminoacid]");
        aminoacids.forEach(aminoacid => {
            pos = parseInt(aminoacid.getAttribute("data-position-aminoacid"));
            if (pos > different_position) {
                aminoacid.classList.add("different");
            }
        });
    });
}

function updatePositionExon(insertPos, last_pos) {
    exons = document.querySelectorAll("div[class='exon-card']");
    st_exon = findNucleotideAtPosition(insertPos).parentNode.parentNode;
    st = parseInt(st_exon.getAttribute("data-exon-number")) - 1;
    end_exon = findNucleotideAtPosition(last_pos).parentNode.parentNode;
    end = parseInt(end_exon.getAttribute("data-exon-number")) - 1;
    for(let i = st; i <= end; i++) {
        exon = exons[i];
        nucleotides = exon.querySelectorAll("span[data-position-nucleotide]");
        first = nucleotides[0];
        last = nucleotides[nucleotides.length - 1];
        exon.setAttribute("data-exon-start-pos", Math.max(1, parseInt(first.getAttribute("data-position-nucleotide"))));

        if (end_exon != exon) {
            exon.setAttribute("data-exon-end-pos", parseInt(last.getAttribute("data-position-nucleotide")));
        } else {
            exon.setAttribute("data-exon-end-pos", parseInt(last_pos));
        }

        exon_meta = exon.querySelectorAll("span[class='position-badge']");
        exon_meta_pos = exon_meta[0];
        exon_meta_pos.textContent = `Позиция: ${exon.getAttribute("data-exon-start-pos")}-${exon.getAttribute("data-exon-end-pos")}`;
        exon_meta_pos = exon_meta[1];
        exon_meta_pos.textContent = `Длина: ${exon.getAttribute("data-exon-end-pos") - exon.getAttribute("data-exon-start-pos") + 1}`;
    }
}

function updateNucleotidesAfterInsertion(insertPos, insertLength, stopCodonPos) {
    const nucleotides = document.querySelectorAll("span[data-position-nucleotide]");
    
    for(let i = 0; i < nucleotides.length; i++) {
        element = nucleotides[i];
        const currentPos = parseInt(element.getAttribute("data-position-nucleotide"));
        
        if (currentPos > insertPos) {
            // Обновляем позицию
            const newPos = currentPos + insertLength;
            element.setAttribute("data-position-nucleotide", newPos);

            // Обновляем номер кодона
            const codonNumber = parseInt((newPos - 1) / 3) + 1;
            element.setAttribute("data-codon", codonNumber);
            
            // Обновляем title
            element.setAttribute("title", 
                `Номер нуклеотида: ${newPos}\nНомер кодона: ${codonNumber}\nОбласть: кодирующая`
            );
            
            // Обновляем классы кодона
            updateCodonClass(element, codonNumber);
            
            // Помечаем стоп-кодон если необходимо
            if (i - 1 > stopCodonPos - 3 && i - 1 <= stopCodonPos) {
                element.classList.add("stop_codon");
            } else if (i - 1 > stopCodonPos) {
                return { newPos: newPos - 1, element: element };
            }
        }
    }
}

function updateCodonClass(element, codonNumber) {
    element.classList.remove("first_codon", "second_codon");
    
    if (codonNumber % 2) {
        element.classList.add("first_codon");
    } else {
        element.classList.add("second_codon");
    }
}

function insertNewNucleotides(insertPos, sequence, referenceElement) {
    let currentElement = referenceElement;
    
    for(let i = 0; i < sequence.length; i++) {
        position_nucleotide = insertPos + 1 + i;
        codonNumber = parseInt((position_nucleotide - 1) / 3) + 1;
        const nucleotideData = {
            classes: '',
            position_nucleotide: position_nucleotide,
            number_codon: codonNumber,
            isUtr: false,
            isCoding: true,
            region: "кодирующая",
            nucleotide: sequence[i],
        };
        
        const nucleotideElement = createNucleotideElement(nucleotideData);
        
        // Добавляем классы
        nucleotideElement.classList.add('coding', 'insertion');
        updateCodonClass(nucleotideElement, codonNumber);
        
        // Вставляем после текущего элемента
        currentElement.parentNode.insertBefore(nucleotideElement, currentElement.nextSibling);
        currentElement = nucleotideElement;
    }
}

function hideExonsAndNucleotidesAfterStopCodon(last_nucleotide) {
    // Находим текущий экзон
    const currentExon = last_nucleotide.parentNode.parentNode;
    if (!currentExon) return;

    const nucleotides = currentExon.querySelectorAll("span[data-position-nucleotide]");
    index = -1;
    for(let i = 0; i < nucleotides.length; i++) {
        if (nucleotides[i] == last_nucleotide) {
            index = i;
            break;
        }   
    }

    for(let i = index; i < nucleotides.length; i++) {
        element = nucleotides[i];
        element.style.display = 'none';
    }

    // Скрываем все последующие экзоны
    let nextExon = currentExon.nextElementSibling;
    while (nextExon && nextExon.classList.contains('exon-card')) {
        nextExon.style.display = 'none';
        nextExon = nextExon.nextElementSibling;
    }
}

// 3
function prepareMutationData(type, data) {
    const baseData = {
        mutation_type: type.toUpperCase()
    };

    switch(type) {
        case 'find':
            return {
                ...baseData,
                position_nucleotide: parseInt(data.position),
            };

        case 'substitution':
            return {
                ...baseData,
                position_nucleotide: parseInt(data.position),
                new_nucleotide: data.sequence.toUpperCase()
            };
            
        case 'insertion':
            return {
                ...baseData,
                start_position: parseInt(data.insertPos),
                end_position: parseInt(data.insertPos) + 1,
                inserted_sequence: data.sequence.toUpperCase()
            };
            
        case 'deletion':
            return {
                ...baseData,
                start_position: parseInt(data.startPos),
                end_position: parseInt(data.endPos)
            };
            
        case 'exon_deletion':
            return {
                ...baseData,
                nucleotide_position: parseInt(data.position),
            };
            
        default:
            throw new Error(`Unknown mutation type: ${type}`);
    }
}

// 2.1)
function getMutationFormData(type) {
    return {
        position: document.getElementById('mutationPosition')?.value,
        sequence: document.getElementById('mutationSequence')?.value,
        startPos: document.getElementById('mutationStart')?.value,
        endPos: document.getElementById('mutationEnd')?.value,
        insertPos: document.getElementById('insertPosition')?.value,
    };
}

// 2.2)
async function applyMutation(type, data) {
    try {
        restorePage();
        backupPage();

        // Подготавливаем данные для API
        const mutationData = prepareMutationData(type, data);

        if (type == "find") return Find(mutationData.position_nucleotide);
        
        // Отправляем запрос к API
        const response = await fetch(`/api/gene/mutate`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                gene: currentGene,
                mutation: mutationData
            })
        });

        if (!response.ok) {
            throw new Error(`API error: ${response.status}`);
        }

        const result = await response.json();
        
        if (!result.success) {
            throw new Error(result.error || 'Unknown API error');
        }
        
        return result;

    } catch (error) {
        console.error('Mutation API error:', error);
        throw error;
    }
}

// 2.3)
function showResult(type, data, apiResult) {
    const resultDiv = document.getElementById('mutationResult');
    
    let resultHTML = '';

    switch(type) {
        case 'find':
            resultHTML = `
                <p><strong>Результат поиска</strong></p>
                <p>Найдено в экзоне: <strong>Экзон ${apiResult.exon_number}</strong></p>
                <p>Нуклеотид: <strong>${apiResult.nucleotide}</strong></p>
                <p>Найдено в домене: <strong>Домен ${apiResult.domain_name}</strong></p>
                <p>Аминокислота: <strong>${apiResult.aminoacid}</strong></p>
                <p class="success"><i class="fas fa-check-circle"></i> Поиск завершен</p>
            `;
            break;

        case 'substitution':
            Substitution(parseInt(data.position), data.sequence.toUpperCase(), apiResult.new_aminoacid);
            resultHTML = `
                <p><strong>Замена выполнена</strong></p>
                <p>Позиция: <strong>${data.position}</strong></p>
                <p>Новый нуклеотид: <strong>${data.sequence}</strong></p>
                <p>Новая аминокислота: <strong>${apiResult.new_aminoacid}</strong></p>
                <p>Статус: <strong>Успешно</strong></p>
                <p class="success"><i class="fas fa-check-circle"></i> Замена применена</p>
            `;
            break;
            
        case 'insertion':
            Insertion(parseInt(data.insertPos), data.sequence.toUpperCase(), apiResult.stop_codon_position, apiResult.new_domain, apiResult.different_position);
            resultHTML = `
                <p><strong>Вставка выполнена</strong></p>
                <p>Между позициями: <strong>${data.insertPos} и ${parseInt(data.insertPos) + 1}</strong></p>
                <p>Вставленная последовательность: <strong>${data.sequence}</strong></p>
                <p>Длина: <strong>${data.sequence.length} нуклеотидов</strong></p>
                <p class="success"><i class="fas fa-check-circle"></i> Вставка применена</p>
            `;
            break;
            
        case 'deletion':
            Deletion(parseInt(data.startPos), parseInt(data.endPos), apiResult.stop_codon_position, apiResult.new_domain, apiResult.different_position)
            resultHTML = `
                <p><strong>Удаление выполнено</strong></p>
                <p>Диапазон: <strong>${data.startPos} - ${data.endPos}</strong></p>
                <p>Удалены нуклеотиды: <strong>${1}</strong></p>
                <p>Статус: <strong>Успешно</strong></p>
                <p class="success"><i class="fas fa-check-circle"></i> Удаление применено</p>
            `;
            break;
            
        case 'exon_deletion':
            resultHTML = `
                <p><strong>Экзон удален</strong></p>
                <p>Удаленный экзон: <strong>Экзон ${apiResult.number_exon}</strong></p>
                <p>Статус: <strong>Успешно</strong></p>
                <p class="success"><i class="fas fa-check-circle"></i> Экзон удален</p>
            `;
            break;
    }
    
    resultDiv.innerHTML = resultHTML;
    resultDiv.style.borderLeftColor = '#28a745';
}

// 1)
async function handleApplyMutationWithApi() {
    const activeType = document.querySelector('.mutation-type-option.active')?.dataset.type;
    const resultDiv = document.getElementById('mutationResult');
    
    // Получаем значения полей
    const data = getMutationFormData(activeType);
    
    // Валидация
    // if (!validateInputs(activeType, data)) {
    //    return;
    // }
    
    // Показываем сообщение о начале обработки
    resultDiv.innerHTML = `
        <p><strong>Обработка...</strong></p>
        <p><i class="fas fa-spinner fa-spin"></i> Выполняется ${getTypeName(activeType)}</p>
    `;
    resultDiv.style.borderLeftColor = '#ff9800';
    
    try {
        // Вызываем API
        const apiResult = await applyMutation(activeType, data);

        if (apiResult.success) {
            // Отображаем результат от API
            showResult(activeType, data, apiResult.data);
        } else {
            // Показываем ошибку
            showError(apiResult.error);
        }
        
    } catch (error) {
        showError(error.message);
    }
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