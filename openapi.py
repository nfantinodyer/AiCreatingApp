import openai
import json
import os
import sys
import re

def safe_print(text):
    try:
        sys.stdout.buffer.write(text.encode('utf-8', errors='replace'))
        sys.stdout.buffer.write(b'\n')
        sys.stdout.buffer.flush()
    except Exception as e:
        print(text)

def extract_json(text):
    """
    Extract the JSON object from the GPT response.
    This helps if the model adds extra commentary.
    """
    match = re.search(r'(\{.*\})', text, re.DOTALL)
    if match:
        return match.group(1)
    return text

def scan_website_files(directory):
    """
    Scan the given directory and return a JSON string where each key is a filename
    and each value is the file content.
    """
    code_dict = {}
    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)
        if os.path.isfile(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                code_dict[filename] = f.read()
    return json.dumps(code_dict)

# Load configuration (e.g. API key) from config.json
with open('config.json', 'r') as config_file:
    config_data = json.load(config_file)
openai.api_key = config_data['api_key']

# Define directories for JSON outputs and website files, and ensure they exist.
JSON_DIR = "json_outputs"
os.makedirs(JSON_DIR, exist_ok=True)

WEBSITE_DIR = "website_files"
os.makedirs(WEBSITE_DIR, exist_ok=True)

# Define paths for intermediate JSON outputs (in JSON_DIR)
initial_file_path = os.path.join(JSON_DIR, "initial_code.json")
reviewer1_file_path = os.path.join(JSON_DIR, "reviewer1.json")
reviewer2_file_path = os.path.join(JSON_DIR, "reviewer2.json")
aggregated_file_path = os.path.join(JSON_DIR, "aggregated_final_code.json")
gap_analysis_file_path = os.path.join(JSON_DIR, "gap_analysis.txt")

def generate_initial_code(prompt):
    full_prompt = (
        prompt + "\n\n"
        "Return your output as a JSON object where each key is a filename (e.g., index.html, style.css, script.js) "
        "and the corresponding value is the file content. Do not include any commentary or additional text."
    )
    response = openai.chat.completions.create(
        model="gpt-4o-mini",  # Original generator model
        messages=[
            {"role": "system", "content": "You are an expert developer."},
            {"role": "user", "content": full_prompt}
        ],
        temperature=0.8,
    )
    return response.choices[0].message.content

def review_code(code, reviewer_prompt, model="gpt-4"):
    full_prompt = (
        reviewer_prompt + "\n\n"
        "Please return the corrected code in the same JSON format (with the same file names) as provided, "
        "without any additional commentary.\n\nHere is the code:\n" + code
    )
    response = openai.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "You are an expert code reviewer and fixer."},
            {"role": "user", "content": full_prompt}
        ],
        temperature=0.3,
    )
    return response.choices[0].message.content

def aggregate_reviews(original_code, review1, review2):
    aggregator_prompt = (
        "I have an original piece of code and two revised versions provided by independent reviewers. "
        "Each is formatted as a JSON object where the keys are filenames and the values are code. "
        "Please compare the code from both reviewers and merge the best improvements. "
        "Return a final version as a JSON object with the same file names, containing only code and no additional commentary."
        "\n\nOriginal Code:\n" + original_code +
        "\n\nReviewer 1 Revised Code:\n" + review1 +
        "\n\nReviewer 2 Revised Code:\n" + review2
    )
    response = openai.chat.completions.create(
        model="gpt-4",  # Aggregator model with high reasoning
        messages=[
            {"role": "system", "content": "You are an expert code aggregator."},
            {"role": "user", "content": aggregator_prompt}
        ],
        temperature=0.3,
    )
    return response.choices[0].message.content

def gap_analysis(code_json):
    analysis_prompt = (
        "Please review the following code for a website for selling bananas. "
        "Identify any missing features or improvements, and provide suggestions on what to add or fix.\n\n"
        + code_json
    )
    response = openai.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are an expert quality assurance and improvement assistant."},
            {"role": "user", "content": analysis_prompt}
        ],
        temperature=0.3,
    )
    return response.choices[0].message.content

def write_code_files_from_json(json_str, output_directory):
    """
    Parse the JSON string and write each file to the output_directory.
    """
    try:
        json_content = extract_json(json_str)
        code_dict = json.loads(json_content)
        for filename, content in code_dict.items():
            file_path = os.path.join(output_directory, filename)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
        return code_dict
    except Exception as e:
        safe_print(f"Error writing code files: {e}")
        return None

# === Main orchestration ===

# Define the base original prompt.
original_prompt = (
    "Create a website in HTML, CSS, and JavaScript for selling bananas. "
    "Include a homepage, product listing, and a contact form."
)

# --- Pre-run Gap Analysis ---
# Check if the website_files folder contains any files.
website_files_list = os.listdir(WEBSITE_DIR)
if website_files_list:
    safe_print("Scanning current website files for pre-run gap analysis...")
    website_code_json = scan_website_files(WEBSITE_DIR)
    pre_analysis = gap_analysis(website_code_json)
    pre_gap_analysis_file_path = os.path.join(JSON_DIR, "pre_gap_analysis.txt")
    with open(pre_gap_analysis_file_path, "w", encoding="utf-8") as f:
        f.write(pre_analysis)
    safe_print("Pre-run Gap Analysis suggestions:")
    safe_print(pre_analysis)
    # Update the original prompt with current website files and gap analysis suggestions.
    original_prompt += (
        "\n\nThe current website files are as follows (in JSON format):\n" + website_code_json +
        "\n\nPlease incorporate the following improvements based on the above gap analysis suggestions:\n" + pre_analysis
    )
    safe_print("Updated original prompt with pre-run gap analysis:")
    safe_print(original_prompt)
elif os.path.exists(aggregated_file_path):
    # Fallback: if no website files exist but a previous aggregated JSON does, use it.
    with open(aggregated_file_path, "r", encoding="utf-8") as f:
        previous_final_code = f.read().strip()
    if previous_final_code:
        safe_print("Performing pre-run gap analysis on previous aggregated code...")
        pre_analysis = gap_analysis(previous_final_code)
        pre_gap_analysis_file_path = os.path.join(JSON_DIR, "pre_gap_analysis.txt")
        with open(pre_gap_analysis_file_path, "w", encoding="utf-8") as f:
            f.write(pre_analysis)
        safe_print("Pre-run Gap Analysis suggestions:")
        safe_print(pre_analysis)
        original_prompt += (
            "\n\nPlease incorporate the following improvements based on previous gap analysis:\n" + pre_analysis
        )
        safe_print("Updated original prompt with pre-run gap analysis:")
        safe_print(original_prompt)

# --- Step 1: Initial Code Generation ---
if os.path.exists(initial_file_path):
    with open(initial_file_path, "r", encoding="utf-8") as src_file:
        initial_code = src_file.read().strip()
    if not initial_code:
        safe_print("Initial code file is empty. Generating initial code...")
        initial_code = generate_initial_code(original_prompt)
        with open(initial_file_path, "w", encoding="utf-8") as src_file:
            src_file.write(initial_code)
        safe_print("Initial code generated and saved in JSON format.")
    else:
        safe_print("Loaded initial code from file.")
else:
    safe_print("Initial code file does not exist. Generating initial code...")
    initial_code = generate_initial_code(original_prompt)
    with open(initial_file_path, "w", encoding="utf-8") as src_file:
        src_file.write(initial_code)
    safe_print("Initial code generated and saved in JSON format.")

# Write initial code to website files
initial_code_files = write_code_files_from_json(initial_code, WEBSITE_DIR)
if initial_code_files:
    safe_print("Initial website files have been created:")
    for fname in initial_code_files.keys():
        safe_print(f" - {fname}")

# --- Step 2: Reviews ---
safe_print("\nReviewing code with Reviewer 1...")
review1 = review_code(initial_code, "Please review the code and fix any errors or issues you see.")
with open(reviewer1_file_path, "w", encoding="utf-8") as f:
    f.write(review1)
safe_print("Reviewer 1 output saved in JSON format.")

safe_print("\nReviewing code with Reviewer 2...")
review2 = review_code(initial_code, "Please inspect the code for any bugs or improvements and return a corrected version.")
with open(reviewer2_file_path, "w", encoding="utf-8") as f:
    f.write(review2)
safe_print("Reviewer 2 output saved in JSON format.")

# --- Step 3: Aggregation ---
safe_print("\nAggregating the two reviews...")
final_code = aggregate_reviews(initial_code, review1, review2)
with open(aggregated_file_path, "w", encoding="utf-8") as f:
    f.write(final_code)
safe_print("Aggregated final code saved in JSON format.")

# Write aggregated final code to website files
final_code_files = write_code_files_from_json(final_code, WEBSITE_DIR)
if final_code_files:
    safe_print("Final aggregated website files have been created:")
    for fname in final_code_files.keys():
        safe_print(f" - {fname}")

# --- Step 4: Gap Analysis (Post-run) ---
safe_print("\nPerforming post-run gap analysis on final code...")
analysis = gap_analysis(final_code)
with open(gap_analysis_file_path, "w", encoding="utf-8") as f:
    f.write(analysis)
safe_print("Post-run Gap Analysis suggestions saved to file:")
safe_print(analysis)

safe_print(f"\nAll generated files have been saved. JSON outputs are in '{JSON_DIR}', website files are in '{WEBSITE_DIR}'.")
