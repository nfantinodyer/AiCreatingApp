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
import openai
from PIL import Image
from io import BytesIO
from sqlalchemy.sql import func

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
    OPENAI_MODEL = config.get("openai_model", "gpt-4")
    logger.info("Configuration loaded successfully.")
except Exception as e:
    logger.error(f"Error loading configuration: {e}")
    app.secret_key = os.urandom(24)
    openai_api_key = ""
    PINTEREST_API_KEY = ""
    UNSPLASH_API_KEY = ""
    OPENAI_MODEL = "gpt-4"

# Set OpenAI API key
openai.api_key = openai_api_key

# Configuration
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')
OUTFIT_IMAGES_FOLDER = os.path.join(BASE_DIR, 'static', 'outfits')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTFIT_IMAGES_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['OUTFIT_IMAGES_FOLDER'] = OUTFIT_IMAGES_FOLDER
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(BASE_DIR, 'database.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Models
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, server_default=func.now(), nullable=False)

class Clothes(db.Model):
    __tablename__ = 'clothes'
    id = db.Column(db.Integer, primary_key=True)
    image_filename = db.Column(db.String(300), nullable=False)
    description = db.Column(db.Text, nullable=False)
    upload_time = db.Column(db.DateTime, server_default=func.now(), nullable=False)

class Preference(db.Model):
    __tablename__ = 'preference'
    id = db.Column(db.Integer, primary_key=True)
    style_text = db.Column(db.Text, nullable=False)
    date = db.Column(db.DateTime, server_default=func.now(), nullable=False)

class Recommendation(db.Model):
    __tablename__ = 'recommendation'
    id = db.Column(db.Integer, primary_key=True)
    outfit_description = db.Column(db.Text, nullable=False)
    reason = db.Column(db.Text, nullable=False)
    generated_image = db.Column(db.String(300), nullable=True)
    timestamp = db.Column(db.DateTime, server_default=func.now(), nullable=False)

# Context processor to make specific config keys available in all templates
@app.context_processor
def inject_config():
    return dict(
        pinterest_api_key=PINTEREST_API_KEY,
        unsplash_api_key=UNSPLASH_API_KEY
    )

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def analyze_image(image_path):
    if not openai_api_key:
        logger.error("OpenAI API key is missing.")
        return "Image analysis service is unavailable."
    try:
        with app.app_context():
            image_url = url_for('static', filename='uploads/' + os.path.basename(image_path), _external=True)
        messages = [
            {"role": "system", "content": "Analyze the following image and provide a detailed description of the clothing items present."},
            {"role": "user", "content": f"What’s in this image?\n{image_url}"}
        ]
        response = openai.ChatCompletion.create(
            model=OPENAI_MODEL,
            messages=messages
        )
        description = response['choices'][0]['message']['content'].strip()
        logger.info(f"Image analyzed successfully: {image_path}")
    except Exception as e:
        logger.error(f"Error analyzing image {image_path}: {e}")
        description = "Could not analyze image."
    return description

def generate_outfit_image(description):
    if not openai_api_key:
        logger.error("OpenAI API key is missing for image generation.")
        return None
    try:
        prompt = f"Create a stylish outfit image based on the following description: {description}"
        response = openai.Image.create(
            prompt=prompt,
            n=1,
            size="512x512"
        )
        image_url = response['data'][0]['url']
        image_response = requests.get(image_url)
        if image_response.status_code == 200:
            image = Image.open(BytesIO(image_response.content))
            image_format = image.format.lower()
            if image_format not in ALLOWED_EXTENSIONS:
                image_format = 'png'
            unique_id = uuid.uuid4().hex
            image_filename = f"outfit_{unique_id}.{image_format}"
            image_path = os.path.join(app.config['OUTFIT_IMAGES_FOLDER'], image_filename)
            image.save(image_path)
            logger.info(f"Outfit image generated and saved: {image_path}")
            return image_filename
        else:
            logger.error(f"Failed to fetch generated image: {image_response.status_code}")
            return None
    except Exception as e:
        logger.error(f"Error generating outfit image: {e}")
        return None

def reanalyze_all_images():
    try:
        clothes = Clothes.query.all()
        for cloth in clothes:
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], cloth.image_filename)
            if os.path.exists(image_path):
                new_description = analyze_image(image_path)
                cloth.description = new_description
            else:
                logger.warning(f"Image file does not exist: {cloth.image_filename}")
        db.session.commit()
        logger.info("All images reanalyzed successfully.")
    except Exception as e:
        logger.error(f"Error reanalyzing images: {e}")

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
            description = analyze_image(filepath)
            if description in ["Image analysis service is unavailable.", "Could not analyze image."]:
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

@app.route('/delete_image/<int:cloth_id>', methods=['POST'])
def delete_image(cloth_id):
    try:
        cloth = Clothes.query.get_or_404(cloth_id)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], cloth.image_filename)
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"File removed: {file_path}")
        # Also remove associated outfit images if any
        recommendations = Recommendation.query.filter_by(outfit_description=cloth.description).all()
        for rec in recommendations:
            if rec.generated_image:
                outfit_path = os.path.join(app.config['OUTFIT_IMAGES_FOLDER'], rec.generated_image)
                if os.path.exists(outfit_path):
                    os.remove(outfit_path)
                    logger.info(f"Outfit image removed: {outfit_path}")
            db.session.delete(rec)
        db.session.delete(cloth)
        db.session.commit()
        flash('Image successfully removed.')
    except Exception as e:
        logger.error(f"Error removing cloth with ID {cloth_id}: {e}")
        flash('Error removing image.')
    return redirect(url_for('my_clothes'))

@app.route('/pick_outfit', methods=['GET', 'POST'])
def pick_outfit():
    recommendation = None
    explanation = None
    outfit_image = None
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
        if not descriptions_text:
            flash('No clothing descriptions available for recommendation.')
            return redirect(request.url)
        # Generate outfit recommendation using OpenAI API
        prompt = f"Based on the following clothing items: {descriptions_text} and the user's style preference: {style_pref}, suggest an outfit for today and explain why it is recommended."
        try:
            messages = [
                {"role": "system", "content": "You are a fashion assistant."},
                {"role": "user", "content": prompt}
            ]
            completion = openai.ChatCompletion.create(
                model=OPENAI_MODEL,
                messages=messages
            )
            recommendation_full = completion['choices'][0]['message']['content'].strip()
            # Parsing robustly
            outfit = ""
            explanation = ""
            try:
                outfit_marker = "outfit:"
                explanation_marker = "explanation:"
                recommendation_lower = recommendation_full.lower()
                outfit_index = recommendation_lower.find(outfit_marker)
                explanation_index = recommendation_lower.find(explanation_marker)
                if outfit_index != -1 and explanation_index != -1 and explanation_index > outfit_index:
                    outfit = recommendation_full[outfit_index + len(outfit_marker):explanation_index].strip()
                    explanation = recommendation_full[explanation_index + len(explanation_marker):].strip()
                else:
                    # If markers not found, assign entire text to outfit with default explanation
                    outfit = recommendation_full
                    explanation = "Automatically generated based on uploaded clothes and style preferences."
            except Exception as parse_e:
                logger.error(f"Error parsing OpenAI response: {parse_e}")
                outfit = recommendation_full
                explanation = "Automatically generated based on uploaded clothes and style preferences."
            recommendation = outfit
            if not explanation:
                explanation = "Automatically generated based on uploaded clothes and style preferences."
            # Generate outfit image
            outfit_image_filename = generate_outfit_image(recommendation)
            if outfit_image_filename:
                outfit_image = outfit_image_filename
                logger.info("Outfit image generated successfully.")
        except Exception as e:
            logger.error(f"Error generating outfit recommendation: {e}")
            recommendation = "Error generating recommendation."
            explanation = ""
            flash('Error generating outfit recommendation.')
        # Save recommendation
        if recommendation:
            new_rec = Recommendation(outfit_description=recommendation, reason=explanation, generated_image=outfit_image if outfit_image else None)
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
            if latest_rec.generated_image:
                outfit_image = latest_rec.generated_image
    except Exception as e:
        logger.error(f"Error fetching latest recommendation: {e}")
    return render_template('pick_outfit.html', recommendation=recommendation, explanation=explanation, outfit_image=outfit_image)

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
                images = [pin.get('images', {}).get('orig', {}).get('url') for pin in data.get('data', []) if pin.get('images') and pin['images'].get('orig') and pin['images']['orig'].get('url')]
                images = [url for url in images if url]
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
                images = [img.get('urls', {}).get('small') for img in data.get('results', []) if img.get('urls') and img['urls'].get('small')]
                images = [url for url in images if url]
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

@app.route('/reanalyze', methods=['POST'])
def reanalyze():
    try:
        reanalyze_all_images()
        flash('All images have been reanalyzed successfully.')
    except Exception as e:
        logger.error(f"Error during reanalysis: {e}")
        flash('An error occurred while reanalyzing images.')
    return redirect(url_for('my_clothes'))

# Error handling for file upload size
@app.errorhandler(413)
def request_entity_too_large(error):
    flash('File is too large. Maximum upload size is 16MB.')
    return redirect(request.url), 413

# Ensure debug mode is off for production
if __name__ == '__main__':
    app.run(debug=False)
