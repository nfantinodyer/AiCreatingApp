import os
import json
import uuid
import logging
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from datetime import datetime
import requests
from werkzeug.utils import secure_filename

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Load configuration
try:
    with open("config.json", "r") as config_file:
        config = json.load(config_file)
    app.secret_key = config.get("secret_key", os.urandom(24))
    openai_api_key = config.get("api_key", "")
    PINTEREST_API_KEY = config.get("pinterest_api_key", "")
    UNSPLASH_API_KEY = config.get("unsplash_api_key", "")
    logger.info("Configuration loaded successfully.")
except Exception as e:
    logger.error(f"Error loading configuration: {e}")
    app.secret_key = os.urandom(24)
    openai_api_key = ""
    PINTEREST_API_KEY = ""
    UNSPLASH_API_KEY = ""

# Configuration
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(BASE_DIR, 'database.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB

db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Models
class Clothes(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    image_filename = db.Column(db.String(300), nullable=False)
    description = db.Column(db.Text, nullable=False)
    upload_time = db.Column(db.DateTime, default=datetime.utcnow)

class Preference(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    style_text = db.Column(db.Text, nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)

class Recommendation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    outfit_description = db.Column(db.Text, nullable=False)
    reason = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

# Initialize DB
with app.app_context():
    db.create_all()

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def analyze_image(image_path):
    if not openai_api_key:
        logger.error("OpenAI API key is missing.")
        return "Image analysis service is unavailable."
    try:
        description = f"Clothing item: {os.path.basename(image_path).split('.')[0].replace('_', ' ').title()}"
        logger.info(f"Image analyzed successfully: {image_path}")
    except Exception as e:
        logger.error(f"Error analyzing image {image_path}: {e}")
        description = "Could not analyze image."
    return description

# Context processor to make config available in all templates
@app.context_processor
def inject_config():
    return dict(config=config)

# Routes
@app.route('/')
def index():
    return redirect(url_for('dashboard'))

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        if 'image' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['image']
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            original_filename = secure_filename(file.filename)
            filename, ext = os.path.splitext(original_filename)
            unique_id = uuid.uuid4().hex
            unique_filename = f"{filename}_{unique_id}{ext}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
            try:
                file.save(filepath)
                logger.info(f"File saved: {filepath}")
            except Exception as e:
                logger.error(f"Error saving file {filepath}: {e}")
                flash('Error saving file.')
                return redirect(request.url)
            # Analyze image
            description = analyze_image(os.path.join('uploads', unique_filename))
            if description == "Image analysis service is unavailable.":
                flash(description)
            # Save to database
            new_cloth = Clothes(image_filename=unique_filename, description=description)
            try:
                db.session.add(new_cloth)
                db.session.commit()
                logger.info(f"Cloth added to database: {unique_filename}")
                flash('Image successfully uploaded and analyzed')
            except Exception as e:
                logger.error(f"Error saving to database: {e}")
                flash('Error saving to database.')
                return redirect(request.url)
            return redirect(url_for('my_clothes'))
        else:
            flash('Allowed image types are - png, jpg, jpeg, gif')
            return redirect(request.url)
    return render_template('upload.html')

@app.route('/my_clothes')
def my_clothes():
    try:
        clothes = Clothes.query.order_by(Clothes.upload_time.desc()).all()
    except Exception as e:
        logger.error(f"Error fetching clothes from database: {e}")
        flash('Error fetching clothes from database.')
        clothes = []
    return render_template('my_clothes.html', clothes=clothes)

@app.route('/pick_outfit', methods=['GET', 'POST'])
def pick_outfit():
    recommendation = None
    explanation = None
    if request.method == 'POST':
        style_pref = request.form.get('style', '').strip()
        if not style_pref:
            flash('Please enter your style preference.')
            return redirect(request.url)
        # Save style preference
        new_pref = Preference(style_text=style_pref)
        try:
            db.session.add(new_pref)
            db.session.commit()
            logger.info(f"Style preference saved: {style_pref}")
        except Exception as e:
            logger.error(f"Error saving style preference: {e}")
            flash('Error saving style preference.')
            return redirect(request.url)
        # Fetch all clothing descriptions
        try:
            descriptions = Clothes.query.with_entities(Clothes.description).all()
            descriptions_text = " ".join([desc[0] for desc in descriptions if desc[0]])
        except Exception as e:
            logger.error(f"Error fetching clothing descriptions: {e}")
            descriptions_text = ""
        # Generate outfit recommendation
        prompt = f"Based on the following clothing items: {descriptions_text} and the user's style preference: {style_pref}, suggest an outfit for today and explain why it is recommended."
        try:
            headers = {
                "Authorization": f"Bearer {openai_api_key}",
                "Content-Type": "application/json"
            }
            data = {
                "model": "gpt-4",
                "messages": [
                    {"role": "system", "content": "You are a fashion assistant."},
                    {"role": "user", "content": prompt}
                ]
            }
            response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=data)
            if response.status_code == 200:
                completion = response.json()
                recommendation_full = completion['choices'][0]['message']['content'].strip()
                recommendation = recommendation_full
                explanation = "Automatically generated based on uploaded clothes and style preferences."
                logger.info("Outfit recommendation generated successfully.")
            else:
                logger.error(f"OpenAI API error: {response.status_code} - {response.text}")
                recommendation = "Error generating recommendation."
                explanation = ""
                flash('Error generating outfit recommendation.')
        except Exception as e:
            logger.error(f"Error generating outfit recommendation: {e}")
            recommendation = "Error generating recommendation."
            explanation = ""
            flash('Error generating outfit recommendation.')
        # Save recommendation
        new_rec = Recommendation(outfit_description=recommendation, reason=explanation)
        try:
            db.session.add(new_rec)
            db.session.commit()
            logger.info("Recommendation saved to database.")
        except Exception as e:
            logger.error(f"Error saving recommendation to database: {e}")
    # Fetch latest recommendation if exists
    try:
        latest_rec = Recommendation.query.order_by(Recommendation.timestamp.desc()).first()
        if latest_rec:
            recommendation = latest_rec.outfit_description
            explanation = latest_rec.reason
    except Exception as e:
        logger.error(f"Error fetching latest recommendation: {e}")
    return render_template('pick_outfit.html', recommendation=recommendation, explanation=explanation)

@app.route('/api/search_images', methods=['GET'])
def api_search_images():
    query = request.args.get('query', '').strip()
    source = request.args.get('source', 'pinterest').lower()
    images = []
    if not query:
        return jsonify({"results": images})
    if source == 'pinterest' and PINTEREST_API_KEY:
        headers = {
            "Authorization": f"Bearer {PINTEREST_API_KEY}",
            "Content-Type": "application/json"
        }
        params = {
            "query": query,
            "page_size": 10
        }
        try:
            response = requests.get("https://api.pinterest.com/v5/search/pins", headers=headers, params=params)
            if response.status_code == 200:
                data = response.json()
                images = [pin['images']['orig']['url'] for pin in data.get('data', []) if 'images' in pin and 'orig' in pin['images']]
                logger.info(f"Pinterest images fetched for query: {query}")
            else:
                logger.error(f"Pinterest API error: {response.status_code} - {response.text}")
        except Exception as e:
            logger.error(f"Error fetching Pinterest images: {e}")
    elif source == 'unsplash' and UNSPLASH_API_KEY:
        headers = {
            "Authorization": f"Client-ID {UNSPLASH_API_KEY}"
        }
        params = {
            "query": query,
            "per_page": 10
        }
        try:
            response = requests.get("https://api.unsplash.com/search/photos", headers=headers, params=params)
            if response.status_code == 200:
                data = response.json()
                images = [img['urls']['small'] for img in data.get('results', []) if 'urls' in img and 'small' in img['urls']]
                logger.info(f"Unsplash images fetched for query: {query}")
            else:
                logger.error(f"Unsplash API error: {response.status_code} - {response.text}")
        except Exception as e:
            logger.error(f"Error fetching Unsplash images: {e}")
    else:
        logger.warning("Invalid source or API key missing.")
    return jsonify({"results": images})

@app.route('/search_images_page')
def search_images_page():
    if not (PINTEREST_API_KEY or UNSPLASH_API_KEY):
        flash('Image search functionality is unavailable. Please provide the necessary API keys.')
        return redirect(url_for('dashboard'))
    return render_template('search_images.html')

if __name__ == '__main__':
    app.run(debug=True)
