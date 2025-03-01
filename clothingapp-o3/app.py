import os
import sys
import time
import json
import sqlite3
import openai
import logging
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory, abort
from werkzeug.utils import secure_filename

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s in %(module)s: %(message)s')

app = Flask(__name__)
app.secret_key = "supersecretkey"

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Check if the base directory is writable early on
if not os.access(BASE_DIR, os.W_OK):
    logging.error("The base directory '%s' is not writable.", BASE_DIR)
    sys.exit("Base directory is not writable.")

UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["ALLOWED_EXTENSIONS"] = {"png", "jpg", "jpeg", "gif"}
app.config["MAX_CONTENT_LENGTH"] = 2 * 1024 * 1024

DATABASE = os.path.join(BASE_DIR, "database.db")

config_path = os.path.join(BASE_DIR, "config.json")
try:
    with open(config_path, "r") as config_file:
        config = json.load(config_file)
    if "api_key" not in config:
        logging.error("Required key 'api_key' not found in configuration.")
        sys.exit("Missing required configuration key.")
except FileNotFoundError:
    logging.error("Configuration file not found at %s", config_path)
    sys.exit("Missing configuration file.")
except json.JSONDecodeError as e:
    logging.error("Configuration file is malformed: %s", e)
    sys.exit("Malformed configuration file.")

openai.api_key = config["api_key"]

DEFAULT_MODEL = "o3-mini"
CANDIDATE_MODELS = [DEFAULT_MODEL]

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config["ALLOWED_EXTENSIONS"]

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS images (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL,
                analysis TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS recommendations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                style_preference TEXT,
                outfit_recommendation TEXT,
                explanation TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()

def call_openai_api(prompt, model=DEFAULT_MODEL, max_retries=3):
    for candidate in CANDIDATE_MODELS:
        current_model = candidate
        for attempt in range(max_retries):
            try:
                response = openai.chat.completions.create(
                    model=current_model,
                    messages=[{"role": "user", "content": prompt}],
                )
                return response['choices'][0]['message']['content']
            except Exception as e:
                logging.error("API call error using model '%s' on attempt %d: %s. Prompt: %s", current_model, attempt + 1, e, prompt)
                time.sleep(1)
        logging.error("Switching from model '%s' due to repeated errors.", current_model)
    raise Exception("All candidate models failed to process the prompt.")

def analyze_image(image_url):
    prompt = f"Please analyze the image located at the following URL and describe its contents in detail: {image_url}"
    messages = [
        {"role": "system", "content": "You are an expert image analyzer."},
        {"role": "user", "content": prompt}
    ]
    try:
        response = openai.chat.completions.create(
            model=DEFAULT_MODEL,
            messages=messages
        )
        analysis = response['choices'][0]['message']['content']
        return analysis
    except Exception as e:
        logging.error("Error analyzing image at URL '%s': %s", image_url, e)
        return "Image analysis failed."

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/upload", methods=["GET", "POST"])
def upload():
    if request.method == "POST":
        if "image" not in request.files:
            flash("No image part in the request.")
            return redirect(request.url)
        file = request.files["image"]
        if file.filename == "" or not allowed_file(file.filename):
            flash("No valid image file selected.")
            return redirect(request.url)
        filename = datetime.now().strftime("%Y%m%d%H%M%S_") + secure_filename(file.filename)
        filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        try:
            file.save(filepath)
        except Exception as e:
            logging.error("Error saving file '%s': %s", filename, e)
            flash("An error occurred while saving the image. Please try again.")
            return redirect(request.url)
        file_url = url_for("uploaded_file", filename=filename, _external=True)
        analysis = analyze_image(file_url)
        with get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute("INSERT INTO images (filename, analysis) VALUES (?, ?)", (filename, analysis))
            conn.commit()
        flash("Image uploaded and analyzed successfully!")
        return redirect(url_for("my_clothes"))
    return render_template("upload.html")

@app.route("/uploads/<filename>")
def uploaded_file(filename):
    file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    if not os.path.exists(file_path):
        logging.error("File %s not found.", filename)
        abort(404)
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

@app.route("/my_clothes")
def my_clothes():
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM images ORDER BY created_at DESC")
        images = cur.fetchall()
    return render_template("my_clothes.html", images=images)

@app.route("/pick_outfit", methods=["GET", "POST"])
def pick_outfit():
    if request.method == "POST":
        style_preference = request.form.get("style_preference", "").strip()
        if not style_preference:
            flash("Please provide a style preference.")
            return redirect(request.url)
        with get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT analysis FROM images")
            images = cur.fetchall()
        descriptions = "\n".join([img["analysis"] for img in images if img["analysis"]])
        prompt = (
            f"Based on the following clothes descriptions:\n{descriptions}\n"
            f"And given the style preference: {style_preference}, please recommend an outfit for today and explain why it is suitable."
        )
        result = call_openai_api(prompt)
        outfit_lines = result.split("\n")
        outfit = outfit_lines[0] if outfit_lines else "Outfit recommendation not generated."
        explanation = "\n".join(outfit_lines[1:]) if len(outfit_lines) > 1 else ""
        with get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO recommendations (style_preference, outfit_recommendation, explanation) VALUES (?, ?, ?)",
                (style_preference, outfit, explanation)
            )
            conn.commit()
        return render_template("outfit.html", outfit=outfit, explanation=explanation)
    return render_template("pick_outfit.html")

@app.route("/pinterest", methods=["GET", "POST"])
def pinterest():
    results = []
    if request.method == "POST":
        query = request.form.get("query", "").strip()
        if query:
            results = [
                {"img": url_for("static", filename="pinterest/result1.jpg"), "alt": f"{query} style 1"},
                {"img": url_for("static", filename="pinterest/result2.jpg"), "alt": f"{query} style 2"},
                {"img": url_for("static", filename="pinterest/result3.jpg"), "alt": f"{query} style 3"}
            ]
        else:
            flash("Please enter a search term.")
    return render_template("pinterest.html", results=results)

@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template("500.html"), 500

if __name__ == "__main__":
    init_db()
    app.run(debug=True)