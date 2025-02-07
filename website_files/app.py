import os
import sqlite3
import uuid
from flask import Flask, render_template, request, redirect, url_for, session, flash, send_file, abort, g
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from functools import wraps
from cryptography.fernet import Fernet
import logging
from io import BytesIO
from flask_wtf import CSRFProtect

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', os.urandom(24))
DATABASE = 'database.db'
UPLOAD_FOLDER = 'uploads'
ENCRYPTION_KEY_FILE = 'secret.key'

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # Limit upload size to 16MB
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

csrf = CSRFProtect(app)

logging.basicConfig(
    filename='app.log',
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(name)s %(message)s'
)

ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(exc):
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db():
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                original_filename TEXT NOT NULL,
                stored_filename TEXT NOT NULL,
                user_id INTEGER NOT NULL,
                upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                file_size INTEGER,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS shared_links (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_id INTEGER NOT NULL,
                shared_link TEXT UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(file_id) REFERENCES files(id)
            )
        ''')
        db.commit()

def generate_encryption_key():
    if not os.path.exists(ENCRYPTION_KEY_FILE):
        key = Fernet.generate_key()
        with open(ENCRYPTION_KEY_FILE, 'wb') as key_file:
            key_file.write(key)
        logging.info('Encryption key generated and saved.')

def load_encryption_key():
    if 'encryption_key' not in g:
        if os.path.exists(ENCRYPTION_KEY_FILE):
            with open(ENCRYPTION_KEY_FILE, 'rb') as key_file:
                g.encryption_key = key_file.read()
        else:
            logging.error('Encryption key file not found.')
            raise FileNotFoundError('Encryption key file not found.')
    return g.encryption_key

def generate_shared_link():
    while True:
        shared_link = os.urandom(16).hex()
        db = get_db()
        cursor = db.cursor()
        cursor.execute('SELECT 1 FROM shared_links WHERE shared_link = ?', (shared_link,))
        if not cursor.fetchone():
            return shared_link

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('You need to be logged in to access this page.')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('files'))
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']
        if not username or not password:
            flash('Username and password are required.')
            return redirect(url_for('register'))
        hashed_password = generate_password_hash(password)
        try:
            db = get_db()
            cursor = db.cursor()
            cursor.execute('INSERT INTO users (username, password) VALUES (?, ?)',
                           (username, hashed_password))
            db.commit()
            flash('Registration successful! Please log in.')
            logging.info(f'New user registered: {username}')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Username already exists.')
            logging.warning(f'Registration failed: Username {username} already exists.')
            return redirect(url_for('register'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']
        if not username or not password:
            flash('Username and password are required.')
            return redirect(url_for('login'))
        db = get_db()
        cursor = db.cursor()
        cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
        user = cursor.fetchone()
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            flash('Login successful!')
            logging.info(f'User logged in: {username}')
            return redirect(url_for('files'))
        else:
            flash('Invalid credentials.')
            logging.warning(f'Failed login attempt for username: {username}')
            return redirect(url_for('login'))
    return render_template('login.html')

@app.route('/logout')
def logout():
    username = session.get('username', 'Unknown User')
    session.clear()
    flash('You have been logged out.')
    logging.info(f'User logged out: {username}')
    return redirect(url_for('login'))

@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part.')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash('No selected file.')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            original_filename = secure_filename(file.filename)
            stored_filename = f"{uuid.uuid4().hex}_{original_filename}"
            try:
                key = load_encryption_key()
                fernet = Fernet(key)
            except FileNotFoundError:
                flash('Encryption key not found.')
                return redirect(request.url)
            raw_data = file.read()
            encrypted_data = fernet.encrypt(raw_data)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], stored_filename)
            try:
                with open(file_path, 'wb') as encrypted_file:
                    encrypted_file.write(encrypted_data)
                file_size = len(encrypted_data)
                logging.info(f'File saved: {stored_filename} (Size: {file_size} bytes)')
            except Exception as e:
                logging.error(f'Error saving file {stored_filename}: {e}')
                flash('An error occurred while saving the file.')
                return redirect(request.url)
            try:
                db = get_db()
                cursor = db.cursor()
                cursor.execute('INSERT INTO files (original_filename, stored_filename, user_id, file_size) VALUES (?, ?, ?, ?)',
                               (original_filename, stored_filename, session['user_id'], file_size))
                db.commit()
                file_id = cursor.lastrowid
            except Exception as e:
                logging.error(f'Error inserting file record into the database: {e}')
                flash('An error occurred while saving the file information.')
                return redirect(request.url)
            flash('File uploaded successfully.')
            logging.info(f'File uploaded: {original_filename} by user {session["username"]} (User ID: {session["user_id"]})')
            return redirect(url_for('files'))
        else:
            flash('File type is not allowed.')
            return redirect(request.url)
    return render_template('upload.html')

@app.route('/files')
@login_required
def files():
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT * FROM files WHERE user_id = ?', (session['user_id'],))
    files = cursor.fetchall()
    return render_template('files.html', files=files)

@app.route('/download/<int:file_id>')
@login_required
def download(file_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT * FROM files WHERE id = ? AND user_id = ?', (file_id, session['user_id']))
    file = cursor.fetchone()
    if file:
        original_filename = file['original_filename']
        stored_filename = file['stored_filename']
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], stored_filename)
        if os.path.exists(file_path):
            try:
                key = load_encryption_key()
                fernet = Fernet(key)
            except FileNotFoundError:
                flash('Encryption key not found.')
                abort(500)
            try:
                with open(file_path, 'rb') as encrypted_file:
                    encrypted_data = encrypted_file.read()
                decrypted_data = fernet.decrypt(encrypted_data)
                logging.info(f'File downloaded: {original_filename} by user {session["username"]} (User ID: {session["user_id"]})')
                return send_file(
                    BytesIO(decrypted_data),
                    as_attachment=True,
                    download_name=original_filename,
                    mimetype='application/octet-stream'
                )
            except Exception as e:
                logging.error(f'Decryption failed for file {original_filename}: {e}')
                flash('An error occurred while decrypting the file.')
                abort(500)
        else:
            flash('File not found.')
            logging.error(f'File not found: {stored_filename}')
            abort(404)
    else:
        flash('You do not have permission to download this file.')
        logging.warning(f'Unauthorized download attempt by user {session.get("username", "Unknown")} for file ID {file_id}')
        abort(403)

@app.route('/share/<int:file_id>', methods=['GET'])
@login_required
def share(file_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT * FROM files WHERE id = ? AND user_id = ?', (file_id, session['user_id']))
    file = cursor.fetchone()
    if file:
        cursor.execute('SELECT shared_link FROM shared_links WHERE file_id = ?', (file_id,))
        existing_link = cursor.fetchone()
        if existing_link:
            shared_link = existing_link['shared_link']
        else:
            shared_link = generate_shared_link()
            try:
                cursor.execute('INSERT INTO shared_links (file_id, shared_link) VALUES (?, ?)', (file_id, shared_link))
                db.commit()
                logging.info(f'Shareable link created for file {file["original_filename"]} by user {session["username"]} (User ID: {session["user_id"]})')
            except Exception as e:
                logging.error(f'Error creating shared link for file ID {file_id}: {e}')
                flash('An error occurred while creating the shareable link.')
                return redirect(url_for('files'))
        link = url_for('share_link', shared_link=shared_link, _external=True)
        flash('Shareable link generated successfully.')
        return render_template('share.html', link=link)
    else:
        flash('You do not have permission to share this file.')
        logging.warning(f'Unauthorized share attempt by user {session.get("username", "Unknown")} for file ID {file_id}')
        abort(403)

@app.route('/share_link/<shared_link>')
def share_link(shared_link):
    db = get_db()
    cursor = db.cursor()
    cursor.execute('''
        SELECT files.original_filename, files.stored_filename 
        FROM files 
        JOIN shared_links ON files.id = shared_links.file_id 
        WHERE shared_links.shared_link = ?
    ''', (shared_link,))
    file = cursor.fetchone()
    if file:
        original_filename = file['original_filename']
        stored_filename = file['stored_filename']
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], stored_filename)
        if os.path.exists(file_path):
            try:
                key = load_encryption_key()
                fernet = Fernet(key)
            except FileNotFoundError:
                flash('Encryption key not found.')
                abort(500)
            try:
                with open(file_path, 'rb') as encrypted_file:
                    encrypted_data = encrypted_file.read()
                decrypted_data = fernet.decrypt(encrypted_data)
                logging.info(f'File downloaded via shared link: {original_filename} (Link: {shared_link})')
                return send_file(
                    BytesIO(decrypted_data),
                    as_attachment=True,
                    download_name=original_filename,
                    mimetype='application/octet-stream'
                )
            except Exception as e:
                logging.error(f'Decryption failed for shared link {shared_link}: {e}')
                flash('An error occurred while decrypting the file.')
                abort(500)
        else:
            flash('File not found.')
            logging.error(f'File not found for shared link: {shared_link}')
            abort(404)
    else:
        flash('Invalid shared link.')
        logging.warning(f'Invalid shared link accessed: {shared_link}')
        abort(404)

@app.route('/delete/<int:file_id>', methods=['POST'])
@login_required
def delete_file(file_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT * FROM files WHERE id = ? AND user_id = ?', (file_id, session['user_id']))
    file = cursor.fetchone()
    if file:
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], file['stored_filename'])
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
            cursor.execute('DELETE FROM shared_links WHERE file_id = ?', (file_id,))
            cursor.execute('DELETE FROM files WHERE id = ?', (file_id,))
            db.commit()
            flash('File deleted successfully.')
            logging.info(f'File deleted: {file["original_filename"]} by user {session["username"]} (User ID: {session["user_id"]})')
        except Exception as e:
            logging.error(f'Error deleting file {file["stored_filename"]}: {e}')
            flash('An error occurred while deleting the file.')
    else:
        flash('You do not have permission to delete this file.')
        logging.warning(f'Unauthorized delete attempt by user {session.get("username", "Unknown")} for file ID {file_id}')
    return redirect(url_for('files'))

@app.errorhandler(403)
def forbidden(e):
    return render_template('403.html'), 403

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500

if __name__ == '__main__':
    init_db()
    generate_encryption_key()
    DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'
    app.run(debug=DEBUG)
