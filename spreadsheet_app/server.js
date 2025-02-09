const express = require('express');
const path = require('path');
const { v4: uuidv4, validate: uuidValidate, version: uuidVersion } = require('uuid');
const sqlite3 = require('sqlite3').verbose();
const { open } = require('sqlite');

const app = express();
const PORT = process.env.PORT || 3000;

// Initialize SQLite database
let db;
const initializeDatabase = async () => {
  db = await open({
    filename: path.join(__dirname, 'database.sqlite'),
    driver: sqlite3.Database
  });

  await db.run(`
    CREATE TABLE IF NOT EXISTS spreadsheets (
      id TEXT PRIMARY KEY,
      name TEXT UNIQUE NOT NULL,
      rows INTEGER NOT NULL,
      columns INTEGER NOT NULL,
      data TEXT,
      createdAt TEXT NOT NULL,
      updatedAt TEXT NOT NULL
    )
  `);
};

// Middleware
app.use(express.json());
app.use(express.static(path.join(__dirname, 'public')));

// Helper Functions
const isUUID = (id) => uuidValidate(id) && uuidVersion(id) === 4;

const validateSpreadsheet = (spreadsheet, isUpdate = false) => {
  const { name, rows, columns, data } = spreadsheet;
  if (!isUpdate || (isUpdate && name !== undefined)) {
    if (name !== undefined && (typeof name !== 'string' || name.trim() === '')) {
      return 'Name must be a non-empty string.';
    }
  }
  if (!isUpdate || (isUpdate && rows !== undefined)) {
    if (rows !== undefined && (!Number.isInteger(rows) || rows <= 0)) {
      return 'Rows must be a positive integer.';
    }
  }
  if (!isUpdate || (isUpdate && columns !== undefined)) {
    if (columns !== undefined && (!Number.isInteger(columns) || columns <= 0)) {
      return 'Columns must be a positive integer.';
    }
  }
  if (!isUpdate || (isUpdate && data !== undefined)) {
    if (data !== undefined && (typeof data !== 'object' || Array.isArray(data))) {
      return 'Data must be an object with cell keys.';
    }
  }
  return null;
};

// Routes
app.get('/', (req, res) => {
  res.sendFile(path.join(__dirname, 'views', 'index.html'));
});

app.get('/spreadsheet/:id', (req, res) => {
  const { id } = req.params;
  if (!isUUID(id)) {
    return res.status(400).sendFile(path.join(__dirname, 'views', 'error.html'));
  }
  res.sendFile(path.join(__dirname, 'views', 'spreadsheet.html'));
});

app.get('/spreadsheet/new', async (req, res) => {
  try {
    const defaultNameBase = 'Untitled Spreadsheet';
    let uniqueName = defaultNameBase;
    let counter = 1;
    const existingNames = await db.all('SELECT name FROM spreadsheets');
    const existingNamesLower = existingNames.map(s => s.name.toLowerCase());
    while (existingNamesLower.includes(uniqueName.toLowerCase())) {
      uniqueName = `${defaultNameBase} (${counter++})`;
    }

    const id = uuidv4();
    const now = new Date().toISOString();
    await db.run(
      `INSERT INTO spreadsheets (id, name, rows, columns, data, createdAt, updatedAt)
       VALUES (?, ?, ?, ?, ?, ?, ?)`,
      [id, uniqueName, 20, 10, JSON.stringify({}), now, now]
    );

    res.redirect(`/spreadsheet/${id}`);
  } catch (error) {
    res.status(500).sendFile(path.join(__dirname, 'views', 'error.html'));
  }
});

// API Endpoints
app.get('/api/spreadsheets', async (req, res) => {
  try {
    const spreadsheets = await db.all('SELECT id, name, rows, columns, createdAt, updatedAt FROM spreadsheets');
    res.json(spreadsheets);
  } catch (error) {
    res.status(500).json({ error: 'Failed to fetch spreadsheets.' });
  }
});

app.post('/api/spreadsheets', async (req, res) => {
  const { name, rows, columns } = req.body;
  const validationError = validateSpreadsheet({ name, rows, columns, data: {} }, false);
  if (validationError) {
    return res.status(400).json({ error: validationError });
  }

  try {
    const finalName = name || 'Untitled Spreadsheet';
    const now = new Date().toISOString();
    const id = uuidv4();
    await db.run(
      `INSERT INTO spreadsheets (id, name, rows, columns, data, createdAt, updatedAt)
       VALUES (?, ?, ?, ?, ?, ?, ?)`,
      [id, finalName, rows || 20, columns || 10, JSON.stringify({}), now, now]
    );
    res.status(201).json({ id, name: finalName });
  } catch (error) {
    if (error.message.includes('UNIQUE constraint failed')) {
      res.status(400).json({ error: 'Spreadsheet name must be unique.' });
    } else {
      res.status(500).json({ error: 'Failed to create spreadsheet.' });
    }
  }
});

app.get('/api/spreadsheets/:id', async (req, res) => {
  const { id } = req.params;
  if (!isUUID(id)) {
    return res.status(400).json({ error: 'Invalid Spreadsheet ID' });
  }

  try {
    const spreadsheet = await db.get('SELECT * FROM spreadsheets WHERE id = ?', [id]);
    if (!spreadsheet) {
      return res.status(404).json({ error: 'Spreadsheet not found' });
    }
    spreadsheet.data = JSON.parse(spreadsheet.data || '{}');
    res.json(spreadsheet);
  } catch (error) {
    res.status(500).json({ error: 'Failed to retrieve spreadsheet.' });
  }
});

app.put('/api/spreadsheets/:id', async (req, res) => {
  const { id } = req.params;
  if (!isUUID(id)) {
    return res.status(400).json({ error: 'Invalid Spreadsheet ID' });
  }
  const { name, rows, columns, cellData } = req.body;
  const validationError = validateSpreadsheet({ name, rows, columns, data: cellData }, true);
  if (validationError) {
    return res.status(400).json({ error: validationError });
  }

  try {
    const spreadsheet = await db.get('SELECT * FROM spreadsheets WHERE id = ?', [id]);
    if (!spreadsheet) {
      return res.status(404).json({ error: 'Spreadsheet not found' });
    }

    const finalName = name !== undefined ? name : spreadsheet.name;
    const finalRows = rows !== undefined ? rows : spreadsheet.rows;
    const finalColumns = columns !== undefined ? columns : spreadsheet.columns;
    const finalData = cellData !== undefined ? JSON.stringify(cellData) : spreadsheet.data;
    const now = new Date().toISOString();

    await db.run(
      `UPDATE spreadsheets
       SET name = ?, rows = ?, columns = ?, data = ?, updatedAt = ?
       WHERE id = ?`,
      [finalName, finalRows, finalColumns, finalData, now, id]
    );

    res.json({ message: 'Spreadsheet updated successfully' });
  } catch (error) {
    if (error.message.includes('UNIQUE constraint failed')) {
      res.status(400).json({ error: 'Spreadsheet name must be unique.' });
    } else {
      res.status(500).json({ error: 'Failed to update spreadsheet.' });
    }
  }
});

app.delete('/api/spreadsheets/:id', async (req, res) => {
  const { id } = req.params;
  if (!isUUID(id)) {
    return res.status(400).json({ error: 'Invalid Spreadsheet ID' });
  }

  try {
    const result = await db.run('DELETE FROM spreadsheets WHERE id = ?', [id]);
    if (result.changes === 0) {
      return res.status(404).json({ error: 'Spreadsheet not found' });
    }
    res.json({ message: 'Spreadsheet deleted successfully' });
  } catch (error) {
    res.status(500).json({ error: 'Failed to delete spreadsheet.' });
  }
});

// Error Handling for Undefined Routes
app.use((req, res) => {
  res.status(404).sendFile(path.join(__dirname, 'views', '404.html'));
});

// Start Server
initializeDatabase()
  .then(() => {
    app.listen(PORT, () => {
      console.log(`Server is running on http://localhost:${PORT}`);
    });
  })
  .catch(err => {
    console.error('Failed to initialize database:', err);
  });
