document.addEventListener('DOMContentLoaded', () => {
  const loadingIndicator = document.getElementById('loading');
  const errorModal = document.getElementById('errorModal');
  const errorMessage = document.getElementById('errorMessage');
  const closeModalBtn = document.getElementById('closeModal');

  closeModalBtn.addEventListener('click', () => {
    errorModal.style.display = 'none';
  });

  const showLoading = () => {
    loadingIndicator.style.display = 'flex';
  };

  const hideLoading = () => {
    loadingIndicator.style.display = 'none';
  };

  const showError = (message) => {
    errorMessage.textContent = message;
    errorModal.style.display = 'flex';
  };

  // Index Page Scripts
  if (document.getElementById('spreadsheetList')) {
    const spreadsheetList = document.getElementById('spreadsheetList');
    const searchInput = document.getElementById('searchInput');
    const selectAllCheckbox = document.getElementById('selectAll');
    const deleteSelectedBtn = document.getElementById('deleteSelected');
    const sortNameBtn = document.getElementById('sortName');
    const sortDateBtn = document.getElementById('sortDate');

    const fetchSpreadsheets = async () => {
      showLoading();
      try {
        const response = await fetch('/api/spreadsheets');
        if (!response.ok) {
          throw new Error('Failed to fetch spreadsheets.');
        }
        const data = await response.json();
        displaySpreadsheets(data);
      } catch (error) {
        showError(error.message);
      } finally {
        hideLoading();
      }
    };

    const displaySpreadsheets = (spreadsheets) => {
      spreadsheetList.innerHTML = '';
      spreadsheets.forEach((sheet) => {
        const tr = document.createElement('tr');

        const tdSelect = document.createElement('td');
        const checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        checkbox.className = 'selectBox';
        checkbox.value = sheet.id;
        tdSelect.appendChild(checkbox);
        tr.appendChild(tdSelect);

        const tdName = document.createElement('td');
        const link = document.createElement('a');
        link.href = `/spreadsheet/${sheet.id}`;
        link.textContent = sheet.name;
        tdName.appendChild(link);
        tr.appendChild(tdName);

        const tdCreated = document.createElement('td');
        tdCreated.textContent = new Date(sheet.createdAt).toLocaleString();
        tr.appendChild(tdCreated);

        const tdUpdated = document.createElement('td');
        tdUpdated.textContent = new Date(sheet.updatedAt).toLocaleString();
        tr.appendChild(tdUpdated);

        spreadsheetList.appendChild(tr);
      });
    };

    searchInput.addEventListener('input', () => {
      const filter = searchInput.value.toLowerCase();
      const rows = spreadsheetList.getElementsByTagName('tr');
      Array.from(rows).forEach((row) => {
        const name = row.getElementsByTagName('td')[1]?.textContent.toLowerCase() || '';
        if (name.includes(filter)) {
          row.style.display = '';
        } else {
          row.style.display = 'none';
        }
      });
    });

    selectAllCheckbox.addEventListener('change', () => {
      const checkboxes = document.querySelectorAll('.selectBox');
      checkboxes.forEach((cb) => {
        cb.checked = selectAllCheckbox.checked;
      });
    });

    deleteSelectedBtn.addEventListener('click', async () => {
      const checkboxes = document.querySelectorAll('.selectBox:checked');
      if (checkboxes.length === 0) {
        alert('No spreadsheets selected for deletion.');
        return;
      }
      if (!confirm('Are you sure you want to delete the selected spreadsheets?')) {
        return;
      }
      showLoading();
      try {
        for (let cb of checkboxes) {
          const response = await fetch(`/api/spreadsheets/${cb.value}`, {
            method: 'DELETE',
          });
          if (!response.ok) {
            throw new Error('Failed to delete some spreadsheets.');
          }
        }
        fetchSpreadsheets();
      } catch (error) {
        showError(error.message);
      } finally {
        hideLoading();
      }
    });

    let sortOrderName = true;
    sortNameBtn.addEventListener('click', () => {
      const rows = Array.from(spreadsheetList.getElementsByTagName('tr'));
      rows.sort((a, b) => {
        const nameA = a.getElementsByTagName('td')[1]?.textContent.toLowerCase() || '';
        const nameB = b.getElementsByTagName('td')[1]?.textContent.toLowerCase() || '';
        if (nameA < nameB) return sortOrderName ? -1 : 1;
        if (nameA > nameB) return sortOrderName ? 1 : -1;
        return 0;
      });
      sortOrderName = !sortOrderName;
      spreadsheetList.innerHTML = '';
      rows.forEach((row) => {
        spreadsheetList.appendChild(row);
      });
    });

    let sortOrderDate = true;
    sortDateBtn.addEventListener('click', () => {
      const rows = Array.from(spreadsheetList.getElementsByTagName('tr'));
      rows.sort((a, b) => {
        const dateA = new Date(a.getElementsByTagName('td')[2]?.textContent || 0);
        const dateB = new Date(b.getElementsByTagName('td')[2]?.textContent || 0);
        return sortOrderDate ? dateA - dateB : dateB - dateA;
      });
      sortOrderDate = !sortOrderDate;
      spreadsheetList.innerHTML = '';
      rows.forEach((row) => {
        spreadsheetList.appendChild(row);
      });
    });

    fetchSpreadsheets();
  }

  // Spreadsheet Page Scripts
  if (document.getElementById('spreadsheetEditor')) {
    const spreadsheetEditor = document.getElementById('spreadsheetEditor');
    const saveBtn = document.getElementById('saveBtn');
    const resizeBtn = document.getElementById('resizeBtn');
    const nameInput = document.getElementById('sheetName');
    const rowsInput = document.getElementById('rows');
    const columnsInput = document.getElementById('columns');
    const loadingIndicator = document.getElementById('loading');

    let spreadsheetId = window.location.pathname.split('/').pop();
    let originalData = null;
    let spreadsheetData = [];
    let hasUnsavedChanges = false;

    const fetchSpreadsheet = async () => {
      showLoading();
      try {
        const response = await fetch(`/api/spreadsheets/${spreadsheetId}`);
        if (!response.ok) {
          throw new Error('Failed to fetch spreadsheet.');
        }
        const data = await response.json();
        originalData = JSON.stringify(data);
        nameInput.value = data.name;
        rowsInput.value = data.rows;
        columnsInput.value = data.columns;
        spreadsheetData = data.data.map(row => [...row]);
        renderGrid();
      } catch (error) {
        showError(error.message);
      } finally {
        hideLoading();
      }
    };

    const renderGrid = () => {
      spreadsheetEditor.innerHTML = '';
      for (let i = 0; i < spreadsheetData.length; i++) {
        const row = document.createElement('div');
        row.className = 'row';
        for (let j = 0; j < spreadsheetData[i].length; j++) {
          const cell = document.createElement('input');
          cell.type = 'text';
          cell.value = spreadsheetData[i][j];
          cell.dataset.row = i;
          cell.dataset.col = j;
          cell.addEventListener('input', (e) => {
            spreadsheetData[e.target.dataset.row][e.target.dataset.col] = e.target.value;
            hasUnsavedChanges = true;
          });
          row.appendChild(cell);
        }
        spreadsheetEditor.appendChild(row);
      }
    };

    const saveSpreadsheet = async () => {
      showLoading();
      try {
        const name = nameInput.value.trim();
        const rows = parseInt(rowsInput.value, 10);
        const columns = parseInt(columnsInput.value, 10);
        const data = spreadsheetData;

        const response = await fetch(`/api/spreadsheets/${spreadsheetId}`, {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ name, rows, columns, data }),
        });

        if (!response.ok) {
          const err = await response.json();
          throw new Error(err.error || 'Failed to save spreadsheet.');
        }

        const savedData = await response.json();
        originalData = JSON.stringify(savedData);
        hasUnsavedChanges = false;
        alert('Spreadsheet saved successfully.');
      } catch (error) {
        showError(error.message);
      } finally {
        hideLoading();
      }
    };

    const resizeGrid = () => {
      const newRows = parseInt(rowsInput.value, 10);
      const newCols = parseInt(columnsInput.value, 10);

      if (newRows > spreadsheetData.length) {
        for (let i = spreadsheetData.length; i < newRows; i++) {
          const newRow = [];
          for (let j = 0; j < newCols; j++) {
            newRow.push('');
          }
          spreadsheetData.push(newRow);
        }
      } else if (newRows < spreadsheetData.length) {
        spreadsheetData = spreadsheetData.slice(0, newRows);
      }

      spreadsheetData.forEach((row, index) => {
        if (newCols > row.length) {
          for (let j = row.length; j < newCols; j++) {
            row.push('');
          }
        } else if (newCols < row.length) {
          spreadsheetData[index] = row.slice(0, newCols);
        }
      });

      renderGrid();
      hasUnsavedChanges = true;
    };

    resizeBtn.addEventListener('click', () => {
      resizeGrid();
      alert('Grid resized. Please save to persist changes.');
    });

    saveBtn.addEventListener('click', saveSpreadsheet);

    window.addEventListener('beforeunload', (e) => {
      if (hasUnsavedChanges) {
        e.preventDefault();
        e.returnValue = '';
      }
    });

    fetchSpreadsheet();
  }
});
