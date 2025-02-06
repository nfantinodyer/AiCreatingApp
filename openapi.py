import openai
import json  # Only used to load the API key.
import os
import re
import sys

# Load the OpenAI API key from a config file.
with open("config.json", "r") as config_file:
    config = json.load(config_file)
openai.api_key = config["api_key"]


# Reconfigure sys.stdout to use UTF-8 (available in Python 3.7+)
try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

def remove_triple_backtick_lines(directory):
    """
    Walk through the given directory and all its subdirectories.
    For each .html, .js, or .css file found, remove any lines
    that contain triple backticks ('```'), then overwrite the file
    with the filtered content.
    """
    for root, dirs, files in os.walk(directory):
        for filename in files:
            # Check if the file has one of the desired extensions
            if filename.endswith(('.html', '.js', '.css')):
                file_path = os.path.join(root, filename)
                
                # Read all lines from the file
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()

                # Keep only the lines that do NOT contain triple backticks
                filtered_lines = [line for line in lines if '```' not in line]

                # Overwrite the file with filtered lines
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.writelines(filtered_lines)

def safe_print(text):
    """
    Print text using UTF-8 encoding. If a UnicodeEncodeError occurs, replace invalid characters.
    """
    try:
        print(text)
    except UnicodeEncodeError:
        print(text.encode('utf-8', errors='replace').decode('utf-8'))

def parse_files(text):
    """
    Parse a string in the custom file format.
    Expected format for each file:
    
    ### filename: <filename> ###
    <file content>
    ### end ###
    
    Returns a dictionary mapping filenames to their content.
    If the first and last lines of the file's content consist solely of triple backticks (```),
    they are removed.
    """
    pattern = r"### filename: (.*?) ###\s*(.*?)\s*### end ###"
    matches = re.findall(pattern, text, flags=re.DOTALL)
    result = {}
    for filename, content in matches:
        lines = content.splitlines()
        # Check if there are at least two lines and both the first and last lines are exactly "```"
        if len(lines) >= 2 and lines[0].strip() == "```" and lines[-1].strip() == "```":
            content = "\n".join(lines[1:-1])
        else:
            content = "\n".join(lines)
        result[filename.strip()] = content.strip()
    return result

def assemble_files(directory):
    """
    Assemble the contents of all files in the given directory into a single string
    in the custom format.
    """
    result = ""
    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)
        if os.path.isfile(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read().strip()
            result += f"### filename: {filename} ###\n{content}\n### end ###\n"
    return result

def write_files(file_dict, output_directory):
    """
    Given a dictionary mapping filenames to file contents, write each file to the output_directory.
    """
    for filename, content in file_dict.items():
        file_path = os.path.join(output_directory, filename)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

# --- Model Call Functions (using o1-mini or o1-preview) ---
# Set the default model to use. Change this to "o1-preview" if desired.
DEFAULT_MODEL = "o1-mini"

def generate_initial_code(prompt, model=DEFAULT_MODEL):
    full_prompt = (
        prompt + "\n\n"
        "Return your output in the following format:\n"
        "For each file, output a line:\n"
        "### filename: <filename> ###\n"
        "Then on subsequent lines, output the file content, and then output a line:\n"
        "### end ###\n"
        "Do not include any additional commentary."
    )
    # Use only a user message (no system message)
    response = openai.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": full_prompt}],
    )
    return response.choices[0].message.content

def review_code(code, reviewer_prompt, model=DEFAULT_MODEL):
    full_prompt = (
        reviewer_prompt + "\n\n"
        "Return the corrected code in the same format as provided below. Do not include any commentary.\n\n"
        "Here is the code:\n" + code + "\n\n"
        "Use the same format: each file begins with a line '### filename: <filename> ###', then its content, then '### end ###'."
    )
    response = openai.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": full_prompt}],
    )
    return response.choices[0].message.content

def aggregate_reviews(original_code, review1, review2, model=DEFAULT_MODEL):
    aggregator_prompt = (
        "I have an original piece of code and two revised versions provided by independent reviewers. "
        "Each is in the following format:\n"
        "### filename: <filename> ###\n"
        "<file content>\n"
        "### end ###\n\n"
        "Please compare the code from both reviewers and merge the best improvements. "
        "Return a final version in the same format, containing only the code and no additional commentary."
        "\n\nOriginal Code:\n" + original_code +
        "\n\nReviewer 1 Revised Code:\n" + review1 +
        "\n\nReviewer 2 Revised Code:\n" + review2
    )
    response = openai.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": aggregator_prompt}],
    )
    return response.choices[0].message.content

def gap_analysis(code_text, model=DEFAULT_MODEL):
    analysis_prompt = (
        "Please review the following code for a website for selling bananas. "
        "Identify any missing features or improvements, and provide suggestions on what to add or fix.\n\n"
        + code_text
    )
    response = openai.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": analysis_prompt}],
    )
    return response.choices[0].message.content

# --- MAIN ORCHESTRATION (All intermediate data kept in memory) ---

# Final website files will be written to the 'website_files' directory.
WEBSITE_DIR = "website_files"
os.makedirs(WEBSITE_DIR, exist_ok=True)

base_prompt = (
    "Create a website in HTML, CSS, and JavaScript for selling bananas. "
    "Include a homepage, product listing, and a contact form."
)

max_iterations = 5
iteration = 0
previous_aggregated_code = ""

while iteration < max_iterations:
    safe_print(f"\n===== Iteration {iteration+1} =====\n")
    
    # --- Pre-run Gap Analysis & Prompt Update ---
    if os.listdir(WEBSITE_DIR):
        safe_print("Scanning current website files for pre-run gap analysis...")
        current_files_str = assemble_files(WEBSITE_DIR)
        pre_analysis = gap_analysis(current_files_str)
        safe_print("Pre-run Gap Analysis suggestions:")
        safe_print(pre_analysis)
        updated_prompt = (
            base_prompt +
            "\n\nCurrent website files:\n" + current_files_str +
            "\n\nIncorporate all of the following improvements:\n" + pre_analysis
        )
    else:
        updated_prompt = base_prompt

    safe_print("Updated prompt for code generation:")
    safe_print(updated_prompt)

    # --- Step 1: Initial Code Generation ---
    print("Initial Code Generation Begins")
    initial_code_output = generate_initial_code(updated_prompt)
    initial_files = parse_files(initial_code_output)
    write_files(initial_files, WEBSITE_DIR)
    remove_triple_backtick_lines(WEBSITE_DIR)
    print("Initial Code Generation Ends")

    # --- Step 2: Reviews ---
    print("Review Begins")
    review1_output = review_code(initial_code_output, "Please review the code and fix any errors or issues you see.")
    safe_print("Reviewer 1 complete")

    review2_output = review_code(initial_code_output, "Please inspect the code for any bugs or improvements and return a corrected version.")
    safe_print("Reviewer 2 complete")

    # --- Step 3: Aggregation ---
    print("Aggregation Begins")
    aggregated_code_output = aggregate_reviews(initial_code_output, review1_output, review2_output)
    aggregated_files = parse_files(aggregated_code_output)
    write_files(aggregated_files, WEBSITE_DIR)
    remove_triple_backtick_lines(WEBSITE_DIR)
    print("Aggregation Ends")

    # --- Step 4: Post-run Gap Analysis ---
    print("Post-run Gap Analysis Begins")
    post_analysis = gap_analysis(aggregated_code_output)
    safe_print("Post-run Gap Analysis suggestions:")
    safe_print(post_analysis)

    # --- Update Base Prompt with Latest Analysis ---
    base_prompt = (
        "Create a website in HTML, CSS, and JavaScript for selling bananas. "
        "Include a homepage, product listing, and a contact form."
        "\n\nIncorporate all of the following improvements:\n" + post_analysis
    )
    safe_print("Base prompt updated for next iteration:")
    safe_print(base_prompt)

    if aggregated_code_output.strip() == previous_aggregated_code.strip():
        safe_print("No changes detected in aggregated code. Terminating loop.")
        break
    else:
        previous_aggregated_code = aggregated_code_output

    iteration += 1

safe_print(f"\nAll iterations complete. Website files are in '{WEBSITE_DIR}'.")

