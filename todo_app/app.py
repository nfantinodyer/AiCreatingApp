import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for
import logging

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database configuration
DATABASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'database.db')

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT
        )
    ''')
    # Insert initial data if table is empty
    cursor.execute('SELECT COUNT(*) FROM tasks')
    count = cursor.fetchone()[0]
    if count == 0:
        cursor.executemany('INSERT INTO tasks (title, description) VALUES (?, ?)', [
            ('Sample Task 1', 'This is the first sample task.'),
            ('Sample Task 2', 'This is the second sample task.')
        ])
        logger.info('Inserted initial sample tasks into the database.')
    conn.commit()
    conn.close()

@app.route('/', methods=['GET', 'POST'])
def index():
    conn = get_db_connection()
    cursor = conn.cursor()
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        cursor.execute('INSERT INTO tasks (title, description) VALUES (?, ?)', (title, description))
        conn.commit()
        logger.info(f'Added task: {title}')
        conn.close()
        return redirect(url_for('index'))
    
    cursor.execute('SELECT * FROM tasks')
    tasks = cursor.fetchall()
    conn.close()
    return render_template('index.html', tasks=tasks)

@app.route('/update/<int:task_id>', methods=['GET', 'POST'])
def update(task_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        cursor.execute('UPDATE tasks SET title = ?, description = ? WHERE id = ?', (title, description, task_id))
        conn.commit()
        logger.info(f'Updated task ID {task_id} to title: {title}')
        conn.close()
        return redirect(url_for('index'))
    
    cursor.execute('SELECT * FROM tasks WHERE id = ?', (task_id,))
    task = cursor.fetchone()
    conn.close()
    return render_template('update.html', task=task)

@app.route('/delete/<int:task_id>', methods=['POST'])
def delete(task_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM tasks WHERE id = ?', (task_id,))
    conn.commit()
    conn.close()
    logger.info(f'Deleted task ID {task_id}')
    return redirect(url_for('index'))

@app.teardown_appcontext
def close_connection(exception):
    if exception:
        logger.error(f'An exception occurred: {exception}')

if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5000)
