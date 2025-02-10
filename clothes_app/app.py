import os
import json
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import openai
import requests
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Replace with a secure key in production

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

# Load configuration
with open("config.json", "r") as config_file:
    config = json.load(config_file)
openai.api_key = config.get("api_key")
PINTEREST_API_KEY = config.get("pinterest_api_key", "")
UNSPLASH_API_KEY = config.get("unsplash_api_key", "")

def analyze_image(image_path):
    # Construct absolute URL for the image
    image_url = request.host_url.rstrip('/') + '/' + image_path
    messages = [
        {"role": "system", "content": "You are an assistant that can analyze and describe images based on their URLs."},
        {"role": "user", "content": f"Please describe the contents of this image: {image_url}"}
    ]

    try:
        response = openai.ChatCompletion.create(
            model='gpt-4',
            messages=messages
        )
        description = response.choices[0].message['content'].strip()
    except Exception:
        description = "Could not analyze image."
    return description

# Routes
@app.route('/')
def index():
    return render_template('index.html')

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
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            # Analyze image
            description = analyze_image(os.path.join('static', 'uploads', filename))
            # Save to database
            new_cloth = Clothes(image_filename=filename, description=description)
            db.session.add(new_cloth)
            db.session.commit()
            flash('Image successfully uploaded and analyzed')
            return redirect(url_for('my_clothes'))
        else:
            flash('Allowed image types are - png, jpg, jpeg, gif')
            return redirect(request.url)
    return render_template('upload.html')

@app.route('/my_clothes')
def my_clothes():
    clothes = Clothes.query.order_by(Clothes.upload_time.desc()).all()
    return render_template('my_clothes.html', clothes=clothes)

@app.route('/pick_outfit', methods=['GET', 'POST'])
def pick_outfit():
    recommendation = None
    explanation = None
    if request.method == 'POST':
        style_pref = request.form.get('style', '')
        if not style_pref:
            flash('Please enter your style preference.')
            return redirect(request.url)
        # Save style preference
        new_pref = Preference(style_text=style_pref)
        db.session.add(new_pref)
        db.session.commit()
        # Fetch all clothing descriptions
        descriptions = Clothes.query.with_entities(Clothes.description).all()
        descriptions_text = " ".join([desc[0] for desc in descriptions if desc[0]])
        # Generate outfit recommendation
        prompt = f"Based on the following clothing items: {descriptions_text} and the user's style preference: {style_pref}, suggest an outfit for today and explain why it is recommended."
        try:
            completion = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a fashion assistant."},
                    {"role": "user", "content": prompt}
                ]
            )
            recommendation_full = completion.choices[0].message['content'].strip()
            # Assign the full response to recommendation
            recommendation = recommendation_full
            explanation = "Automatically generated based on uploaded clothes and style preferences."
        except Exception:
            recommendation = "Error generating recommendation."
            explanation = ""
        # Save recommendation
        new_rec = Recommendation(outfit_description=recommendation, reason=explanation)
        db.session.add(new_rec)
        db.session.commit()
    return render_template('pick_outfit.html', recommendation=recommendation, explanation=explanation)

@app.route('/recommendation')
def recommendation_page():
    latest_rec = Recommendation.query.order_by(Recommendation.timestamp.desc()).first()
    if latest_rec:
        return render_template('recommendation.html', outfit=latest_rec.outfit_description, explanation=latest_rec.reason)
    else:
        flash('No recommendation available.')
        return redirect(url_for('pick_outfit'))

@app.route('/search_images', methods=['GET'])
def search_images():
    query = request.args.get('query', '')
    source = request.args.get('source', 'pinterest')
    images = []
    if not query:
        return jsonify({"results": images})
    if source == 'pinterest' and PINTEREST_API_KEY:
        headers = {
            "Authorization": f"Bearer {PINTEREST_API_KEY}"
        }
        params = {
            "query": query,
            "limit": 10
        }
        response = requests.get("https://api.pinterest.com/v5/search/pins", headers=headers, params=params)
        if response.status_code == 200:
            data = response.json()
            images = [pin['images']['orig']['url'] for pin in data.get('data', []) if 'images' in pin]
    elif source == 'unsplash' and UNSPLASH_API_KEY:
        response = requests.get("https://api.unsplash.com/search/photos", params={
            "query": query,
            "per_page": 10,
            "client_id": UNSPLASH_API_KEY
        })
        if response.status_code == 200:
            data = response.json()
            images = [img['urls']['small'] for img in data.get('results', [])]
    return jsonify({"results": images})

if __name__ == '__main__':
    app.run(debug=True)
