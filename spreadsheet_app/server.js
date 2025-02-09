const express = require('express');
const fs = require('fs');
const path = require('path');
const { v4: uuidv4 } = require('uuid');

const app = express();
const PORT = 3000;
const DATA_FILE = path.join(__dirname, 'data.json');

app.use(express.json());
app.use(express.static(path.join(__dirname, 'public')));
app.set('views', path.join(__dirname, 'views'));
app.set('view engine', 'html');

// Helper function to read data from JSON file
const readData = () => {
  if (!fs.existsSync(DATA_FILE)) {
    fs.writeFileSync(DATA_FILE, JSON.stringify({ spreadsheets: [] }, null, 2));
  }
  const data = fs.readFileSync(DATA_FILE);
  return JSON.parse(data);
};

// Helper function to write data to JSON file
const writeData = (data) => {
  fs.writeFileSync(DATA_FILE, JSON.stringify(data, null, 2));
};

// Validate spreadsheet data
const validateSpreadsheet = (spreadsheet, isUpdate = false) => {
  const { name, rows, columns, data } = spreadsheet;
  if (!name || typeof name !== 'string' || name.trim() === '') {
    return 'Name must be a non-empty string.';
  }
  if (!Number.isInteger(rows) || rows <= 0) {
    return 'Rows must be a positive integer.';
  }
  if (!Number.isInteger(columns) || columns <= 0) {
    return 'Columns must be a positive integer.';
  }
  if (!Array.isArray(data)) {
    return 'Data must be an array.';
  }
  if (data.length !== rows) {
    return 'Data rows do not match the specified number of rows.';
  }
  for (let row of data) {
    if (!Array.isArray(row) || row.length !== columns) {
      return 'Data columns do not match the specified number of columns.';
    }
  }
  return null;
};

// Routes
app.get('/', (req, res) => {
  res.sendFile(path.join(__dirname, 'views', 'index.html'));
});

app.get('/spreadsheet/:id', (req, res) => {
  res.sendFile(path.join(__dirname, 'views', 'spreadsheet.html'));
});

// Route to create a new spreadsheet and redirect to its editor
app.get('/spreadsheet/new', (req, res) => {
  try {
    const defaultName = 'Untitled Spreadsheet';
    let uniqueName = defaultName;
    let counter = 1;
    const data = readData();
    while (data.spreadsheets.find(s => s.name.toLowerCase() === uniqueName.toLowerCase())) {
      uniqueName = `${defaultName} (${counter++})`;
    }

    const newSpreadsheet = {
      id: uuidv4(),
      name: uniqueName,
      rows: 10,
      columns: 10,
      data: Array.from({ length: 10 }, () => Array(10).fill('')),
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };

    data.spreadsheets.push(newSpreadsheet);
    writeData(data);

    res.redirect(`/spreadsheet/${newSpreadsheet.id}`);
  } catch (error) {
    res.status(500).send('Failed to create a new spreadsheet.');
  }
});

// API Endpoints
app.get('/api/spreadsheets', (req, res) => {
  try {
    const data = readData();
    res.json(data.spreadsheets);
  } catch (error) {
    res.status(500).json({ error: 'Failed to retrieve spreadsheets.' });
  }
});

app.post('/api/spreadsheets', (req, res) => {
  try {
    const { name, rows, columns, data } = req.body;
    const validationError = validateSpreadsheet(req.body);
    if (validationError) {
      return res.status(400).json({ error: validationError });
    }

    const existing = readData().spreadsheets.find(
      (s) => s.name.toLowerCase() === name.toLowerCase()
    );
    if (existing) {
      return res.status(400).json({ error: 'Spreadsheet name must be unique.' });
    }

    const newSpreadsheet = {
      id: uuidv4(),
      name,
      rows,
      columns,
      data,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };

    const dataObj = readData();
    dataObj.spreadsheets.push(newSpreadsheet);
    writeData(dataObj);

    res.status(201).json(newSpreadsheet);
  } catch (error) {
    res.status(500).json({ error: 'Failed to create spreadsheet.' });
  }
});

app.get('/api/spreadsheets/:id', (req, res) => {
  try {
    const data = readData();
    const spreadsheet = data.spreadsheets.find((s) => s.id === req.params.id);
    if (!spreadsheet) {
      return res.status(404).json({ error: 'Spreadsheet not found.' });
    }
    res.json(spreadsheet);
  } catch (error) {
    res.status(500).json({ error: 'Failed to retrieve spreadsheet.' });
  }
});

app.put('/api/spreadsheets/:id', (req, res) => {
  try {
    const data = readData();
    const index = data.spreadsheets.findIndex((s) => s.id === req.params.id);
    if (index === -1) {
      return res.status(404).json({ error: 'Spreadsheet not found.' });
    }

    const { name, rows, columns, data: spreadsheetData } = req.body;
    const validationError = validateSpreadsheet(req.body, true);
    if (validationError) {
      return res.status(400).json({ error: validationError });
    }

    // Check for unique name excluding current spreadsheet
    const duplicate = data.spreadsheets.find(
      (s) => s.name.toLowerCase() === name.toLowerCase() && s.id !== req.params.id
    );
    if (duplicate) {
      return res.status(400).json({ error: 'Spreadsheet name must be unique.' });
    }

    data.spreadsheets[index] = {
      ...data.spreadsheets[index],
      name,
      rows,
      columns,
      data: spreadsheetData,
      updatedAt: new Date().toISOString(),
    };

    writeData(data);
    res.json(data.spreadsheets[index]);
  } catch (error) {
    res.status(500).json({ error: 'Failed to update spreadsheet.' });
  }
});

app.delete('/api/spreadsheets/:id', (req, res) => {
  try {
    const data = readData();
    const index = data.spreadsheets.findIndex((s) => s.id === req.params.id);
    if (index === -1) {
      return res.status(404).json({ error: 'Spreadsheet not found.' });
    }
    data.spreadsheets.splice(index, 1);
    writeData(data);
    res.json({ message: 'Spreadsheet deleted successfully.' });
  } catch (error) {
    res.status(500).json({ error: 'Failed to delete spreadsheet.' });
  }
});

app.listen(PORT, () => {
  console.log(`Server is running on http://localhost:${PORT}`);
});
