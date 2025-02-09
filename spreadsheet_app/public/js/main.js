const getColumnLabel = (index) => {
    let label = '';
    while (index >= 0) {
        label = String.fromCharCode((index % 26) + 65) + label;
        index = Math.floor(index / 26) - 1;
    }
    return label;
};

document.addEventListener('DOMContentLoaded', () => {
    const currentPath = window.location.pathname;
    const isSpreadsheetPage = currentPath.startsWith('/spreadsheet/') && currentPath.split('/').length === 3;

    if (isSpreadsheetPage) {
        const pathSegments = currentPath.split('/').filter(segment => segment);
        const spreadsheetId = pathSegments[pathSegments.length - 1];
        initializeSpreadsheet(spreadsheetId);
    } else {
        initializeHome();
    }

    // Global Back to Home Button Handler
    const backHomeBtn = document.getElementById('backHomeBtn');
    if (backHomeBtn) {
        backHomeBtn.onclick = () => {
            window.location.href = '/';
        };
    }
});

// Toast Notification
const showToast = (message, type = 'success') => {
    let toast = document.getElementById('toast');
    if (!toast) {
        toast = document.createElement('div');
        toast.id = 'toast';
        toast.className = 'toast';
        document.body.appendChild(toast);
    }
    toast.innerText = message;
    toast.style.backgroundColor = type === 'success' ? '#4CAF50' : '#f44336';
    toast.className = 'toast show';
    setTimeout(() => {
        toast.className = toast.className.replace('show', '');
    }, 3000);
};

// Notification
const showNotification = (message) => {
    const notification = document.createElement('div');
    notification.className = 'notification show';
    notification.textContent = message;
    document.body.appendChild(notification);
    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => {
            document.body.removeChild(notification);
        }, 500);
    }, 3000);
};

// Initialize Home Page
const initializeHome = () => {
    const createBtn = document.getElementById('createBtn');
    const spreadsheetsList = document.getElementById('spreadsheetsList');
    const searchInput = document.getElementById('searchInput');
    const loading = document.getElementById('loading');
    const errorModal = document.getElementById('errorModal');
    const errorMessage = document.getElementById('errorMessage');
    const closeModal = document.getElementById('closeModal');
    const sortName = document.getElementById('sortName');
    const sortDate = document.getElementById('sortDate');
    const selectAll = document.getElementById('selectAll');
    const deleteSelected = document.getElementById('deleteSelected');

    if (closeModal) {
        closeModal.onclick = () => {
            errorModal.style.display = 'none';
        };
    }

    window.onclick = (event) => {
        if (event.target == errorModal) {
            errorModal.style.display = 'none';
        }
    };

    const showLoadingFunc = () => {
        if (loading) {
            loading.style.display = 'block';
        }
    };

    const hideLoadingFunc = () => {
        if (loading) {
            loading.style.display = 'none';
        }
    };

    const showError = (message) => {
        if (errorMessage && errorModal) {
            errorMessage.textContent = message;
            errorModal.style.display = 'flex';
        }
    };

    let spreadsheetsData = [];

    const fetchSpreadsheets = () => {
        showLoadingFunc();
        fetch('/api/spreadsheets')
            .then(response => {
                if (!response.ok) {
                    throw new Error('Failed to fetch spreadsheets.');
                }
                return response.json();
            })
            .then(data => {
                hideLoadingFunc();
                spreadsheetsData = data;
                renderSpreadsheets(data);
            })
            .catch(error => {
                hideLoadingFunc();
                showError(error.message);
            });
    };

    const renderSpreadsheets = (spreadsheets) => {
        if (!spreadsheetsList) return;
        spreadsheetsList.innerHTML = '';
        spreadsheets.forEach(sheet => {
            const tr = document.createElement('tr');

            const selectTd = document.createElement('td');
            const checkbox = document.createElement('input');
            checkbox.type = 'checkbox';
            checkbox.className = 'selectItem';
            checkbox.dataset.id = sheet.id;
            selectTd.appendChild(checkbox);
            tr.appendChild(selectTd);

            const nameTd = document.createElement('td');
            const link = document.createElement('a');
            link.href = `/spreadsheet/${sheet.id}`;
            link.textContent = sheet.name;
            link.className = 'spreadsheetLink';
            nameTd.appendChild(link);
            tr.appendChild(nameTd);

            const createdAtTd = document.createElement('td');
            createdAtTd.textContent = new Date(sheet.createdAt).toLocaleString();
            tr.appendChild(createdAtTd);

            const updatedAtTd = document.createElement('td');
            updatedAtTd.textContent = new Date(sheet.updatedAt).toLocaleString();
            tr.appendChild(updatedAtTd);

            spreadsheetsList.appendChild(tr);
        });
    };

    const createSpreadsheet = () => {
        const name = prompt('Enter spreadsheet name:', `Untitled Spreadsheet ${spreadsheetsData.length + 1}`);
        if (name === null) return; // User cancelled
        if (!name.trim()) {
            showToast('Spreadsheet name cannot be empty.', 'error');
            return;
        }
        showLoadingFunc();
        fetch('/api/spreadsheets', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ name, rows: 20, columns: 10 })
        })
        .then(response => {
            hideLoadingFunc();
            if (!response.ok) {
                return response.json().then(data => { throw new Error(data.error || 'Failed to create spreadsheet.') });
            }
            return response.json();
        })
        .then(data => {
            window.location.href = `/spreadsheet/${data.id}`;
        })
        .catch(error => {
            showToast(error.message, 'error');
        });
    };

    const deleteSelectedSpreadsheets = () => {
        const checkboxes = document.querySelectorAll('.selectItem:checked');
        if (checkboxes.length === 0) {
            showToast('No spreadsheets selected for deletion.', 'error');
            return;
        }
        if (!confirm(`Are you sure you want to delete ${checkboxes.length} selected spreadsheet(s)?`)) {
            return;
        }
        showLoadingFunc();
        const deletePromises = Array.from(checkboxes).map(cb => {
            const id = cb.dataset.id;
            return fetch(`/api/spreadsheets/${id}`, {
                method: 'DELETE'
            })
            .then(response => {
                if (!response.ok) {
                    return response.json().then(data => { throw new Error(data.error || 'Failed to delete spreadsheet.') });
                }
                return response.json();
            });
        });
        Promise.all(deletePromises)
            .then(results => {
                hideLoadingFunc();
                showToast('Selected spreadsheets deleted successfully.', 'success');
                fetchSpreadsheets();
            })
            .catch(error => {
                hideLoadingFunc();
                showToast(error.message, 'error');
            });
    };

    const sortSpreadsheetsByName = () => {
        const sorted = [...spreadsheetsData].sort((a, b) => a.name.localeCompare(b.name));
        renderSpreadsheets(sorted);
    };

    const sortSpreadsheetsByDate = () => {
        const sorted = [...spreadsheetsData].sort((a, b) => new Date(b.updatedAt) - new Date(a.updatedAt));
        renderSpreadsheets(sorted);
    };

    const toggleSelectAll = () => {
        const checkboxes = document.querySelectorAll('.selectItem');
        checkboxes.forEach(cb => cb.checked = selectAll.checked);
    };

    const debounce = (func, delay) => {
        let debounceTimer;
        return function () {
            const context = this;
            const args = arguments;
            clearTimeout(debounceTimer);
            debounceTimer = setTimeout(() => func.apply(context, args), delay);
        }
    };

    const filterSpreadsheets = debounce(() => {
        const query = searchInput.value.toLowerCase();
        const filtered = spreadsheetsData.filter(sheet => sheet.name.toLowerCase().includes(query));
        renderSpreadsheets(filtered);
    }, 300);

    if (createBtn) {
        createBtn.onclick = createSpreadsheet;
    }

    if (deleteSelected) {
        deleteSelected.onclick = deleteSelectedSpreadsheets;
    }

    if (sortName) {
        sortName.onclick = sortSpreadsheetsByName;
    }

    if (sortDate) {
        sortDate.onclick = sortSpreadsheetsByDate;
    }

    if (selectAll) {
        selectAll.onchange = toggleSelectAll;
    }

    if (searchInput) {
        searchInput.oninput = filterSpreadsheets;
    }

    fetchSpreadsheets();
};

// Initialize Spreadsheet Page
const initializeSpreadsheet = (spreadsheetId) => {
    const spreadsheetEditor = document.getElementById('spreadsheetEditor');
    const saveBtn = document.getElementById('saveBtn');
    const sheetNameInput = document.getElementById('sheetName');
    const backBtn = document.getElementById('backHomeBtn');
    const rowsInput = document.getElementById('rows');
    const columnsInput = document.getElementById('columns');
    const resizeBtn = document.getElementById('resizeBtn');
    const loading = document.getElementById('loading');
    const errorModal = document.getElementById('errorModal');
    const errorMessage = document.getElementById('errorMessage');
    const closeModal = document.getElementById('closeModal');

    if (closeModal) {
        closeModal.onclick = () => {
            errorModal.style.display = 'none';
        };
    }

    window.onclick = (event) => {
        if (event.target == errorModal) {
            errorModal.style.display = 'none';
        }
    };

    const showLoading = () => {
        if (loading) {
            loading.style.display = 'block';
        }
    };
    
    const hideLoading = () => {
        if (loading) {
            loading.style.display = 'none';
        }
    };
    
    const showError = (message) => {
        if (errorMessage && errorModal) {
            errorMessage.textContent = message;
            errorModal.style.display = 'flex';
        }
    };

    let cellsData = {};
    let rows = 20;
    let columns = 10;
    let hasUnsavedChanges = false;

    const fetchSpreadsheet = () => {
        showLoading();
        fetch(`/api/spreadsheets/${spreadsheetId}`)
            .then(response => {
                if (!response.ok) {
                    throw new Error('Failed to fetch spreadsheet.');
                }
                return response.json();
            })
            .then(data => {
                hideLoading();
                sheetNameInput.value = data.name;
                rows = data.rows;
                columns = data.columns;
                rowsInput.value = rows;
                columnsInput.value = columns;
                cellsData = data.data || {};
                renderGrid(rows, columns);
            })
            .catch(error => {
                hideLoading();
                showError(error.message);
            });
    };

    const renderGrid = (rowsCount, colsCount) => {
        if (!spreadsheetEditor) return;
        spreadsheetEditor.innerHTML = '';
        const table = document.createElement('table');
        table.style.borderCollapse = 'collapse';
        table.style.width = '100%';

        const thead = document.createElement('thead');
        const headerRow = document.createElement('tr');

        // Top-left empty cell
        const emptyTh = document.createElement('th');
        headerRow.appendChild(emptyTh);

        // Column headers
        for (let c = 0; c < colsCount; c++) {
            const th = document.createElement('th');
            th.textContent = getColumnLabel(c);
            th.style.border = '1px solid #ddd';
            th.style.padding = '8px';
            headerRow.appendChild(th);
        }
        thead.appendChild(headerRow);
        table.appendChild(thead);

        const tbody = document.createElement('tbody');

        for (let r = 1; r <= rowsCount; r++) {
            const tr = document.createElement('tr');
            
            const rowHeader = document.createElement('th');
            rowHeader.textContent = r;
            rowHeader.style.border = '1px solid #ddd';
            rowHeader.style.padding = '8px';
            tr.appendChild(rowHeader);
            
            for (let c = 0; c < colsCount; c++) {
                const td = document.createElement('td');
                td.style.border = '1px solid #ddd';
                td.style.padding = '8px';
                
                const input = document.createElement('input');
                input.type = 'text';
                input.className = 'cell-input';
                input.style.width = '100%';
                input.style.boxSizing = 'border-box';
                const cellId = `${getColumnLabel(c)}${r}`;
                input.value = cellsData[cellId] || '';
                input.dataset.cellId = cellId;
                input.addEventListener('input', handleCellInput);
                tr.appendChild(td).appendChild(input);
            }
            tbody.appendChild(tr);
        }

        table.appendChild(tbody);
        spreadsheetEditor.appendChild(table);
    };

    const handleCellInput = (e) => {
        const input = e.target;
        const cellId = input.dataset.cellId;
        let value = input.value;
        if (value.startsWith('=')) {
            try {
                const result = evaluateExpression(value.substring(1));
                input.style.backgroundColor = '#e0ffe0';
                cellsData[cellId] = result;
                input.value = result;
            } catch (err) {
                input.style.backgroundColor = '#ffe0e0';
                cellsData[cellId] = value;
            }
        } else {
            cellsData[cellId] = value;
            input.style.backgroundColor = '';
        }
        hasUnsavedChanges = true;
    };

    const evaluateExpression = (expr) => {
        expr = expr.replace(/\s+/g, '').toUpperCase();
        if (expr.startsWith('SUM(') && expr.endsWith(')')) {
            const range = expr.substring(4, expr.length - 1);
            return sumRange(range);
        } else if (expr.startsWith('AVERAGE(') && expr.endsWith(')')) {
            const range = expr.substring(8, expr.length - 1);
            return averageRange(range);
        } else {
            // Implement basic arithmetic or throw error
            // For safety, avoid using eval
            const sanitizedExpr = expr.replace(/[^0-9+\-*/().A-Z]/g, '');
            try {
                // Replace cell references with their values
                const exprWithValues = sanitizedExpr.replace(/[A-Z]+\d+/g, (match) => {
                    const val = parseFloat(cellsData[match]);
                    return isNaN(val) ? 0 : val;
                });
                // eslint-disable-next-line no-new-func
                return Function(`'use strict'; return (${exprWithValues})`)();
            } catch {
                throw new Error('Invalid Expression');
            }
        }
    };

    const sumRange = (range) => {
        const cells = getCellsFromRange(range);
        let sum = 0;
        cells.forEach(cell => {
            const val = parseFloat(cellsData[cell]);
            if (!isNaN(val)) {
                sum += val;
            }
        });
        return sum;
    };

    const averageRange = (range) => {
        const cells = getCellsFromRange(range);
        let sum = 0;
        let count = 0;
        cells.forEach(cell => {
            const val = parseFloat(cellsData[cell]);
            if (!isNaN(val)) {
                sum += val;
                count++;
            }
        });
        return count === 0 ? 0 : parseFloat((sum / count).toFixed(2));
    };

    const getCellsFromRange = (range) => {
        const [start, end] = range.split(':');
        const startColMatch = start.match(/[A-Z]+/);
        const startRowMatch = start.match(/\d+/);
        const endColMatch = end.match(/[A-Z]+/);
        const endRowMatch = end.match(/\d+/);

        if (!startColMatch || !startRowMatch || !endColMatch || !endRowMatch) {
            throw new Error('Invalid Range');
        }

        const startCol = getColumnIndex(startColMatch[0]);
        const startRow = parseInt(startRowMatch[0], 10);
        const endCol = getColumnIndex(endColMatch[0]);
        const endRow = parseInt(endRowMatch[0], 10);

        if (isNaN(startCol) || isNaN(startRow) || isNaN(endCol) || isNaN(endRow)) {
            throw new Error('Invalid Range');
        }

        const cells = [];
        for (let c = startCol; c <= endCol; c++) {
            for (let r = startRow; r <= endRow; r++) {
                cells.push(`${getColumnLabel(c)}${r}`);
            }
        }
        return cells;
    };

    const getColumnIndex = (label) => {
        let index = 0;
        for (let i = 0; i < label.length; i++) {
            index *= 26;
            index += label.charCodeAt(i) - 64;
        }
        return index - 1;
    };

    const saveSpreadsheet = () => {
        const name = sheetNameInput.value.trim() || 'Untitled Spreadsheet';
        const payload = { name, rows, columns, cellData: cellsData };
        showLoading();
        fetch(`/api/spreadsheets/${spreadsheetId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        })
        .then(response => {
            hideLoading();
            if (!response.ok) {
                return response.json().then(data => { throw new Error(data.error || 'Failed to save spreadsheet.') });
            }
            return response.json();
        })
        .then(result => {
            showToast('Spreadsheet saved successfully.', 'success');
            hasUnsavedChanges = false;
        })
        .catch(error => {
            hideLoading();
            showToast(error.message, 'error');
        });
    };

    const resizeGrid = () => {
        const newRows = parseInt(rowsInput.value, 10);
        const newColumns = parseInt(columnsInput.value, 10);
        if (isNaN(newRows) || isNaN(newColumns) || newRows <= 0 || newColumns <= 0) {
            showToast('Invalid rows or columns.', 'error');
            return;
        }
        showLoading();
        fetch(`/api/spreadsheets/${spreadsheetId}`)
            .then(response => {
                if (!response.ok) {
                    throw new Error('Failed to fetch spreadsheet for resizing.');
                }
                return response.json();
            })
            .then(data => {
                hideLoading();
                rows = newRows;
                columns = newColumns;
                rowsInput.value = rows;
                columnsInput.value = columns;
                renderGrid(rows, columns);
                hasUnsavedChanges = true;
                showToast('Spreadsheet resized successfully.', 'success');
            })
            .catch(error => {
                hideLoading();
                showToast(error.message, 'error');
            });
    };

    const handleBeforeUnload = (e) => {
        if (hasUnsavedChanges) {
            e.preventDefault();
            e.returnValue = '';
        }
    };

    if (saveBtn) {
        saveBtn.addEventListener('click', saveSpreadsheet);
    }

    if (backBtn) {
        backBtn.addEventListener('click', () => {
            window.location.href = '/';
        });
    }

    if (resizeBtn) {
        resizeBtn.addEventListener('click', resizeGrid);
    }

    window.addEventListener('beforeunload', handleBeforeUnload);

    fetchSpreadsheet();
};
