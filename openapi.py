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
    Walk through the given directory and its subdirectories.
    For each .html, .js, .css, .py, .txt, or .log file found,
    remove any lines that contain triple backticks ('```'),
    then overwrite the file with the filtered content.
    """
    for root, dirs, files in os.walk(directory):
        for filename in files:
            if filename.endswith(('.html', '.js', '.css', '.py', '.txt', '.log')):
                file_path = os.path.join(root, filename)
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                filtered_lines = [line for line in lines if '```' not in line]
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.writelines(filtered_lines)

def safe_print(text):
    """
    Print text using UTF-8 encoding. If a UnicodeEncodeError occurs,
    replace invalid characters.
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
    
    Returns a dictionary mapping filenames (which may include paths) to their content.
    """
    pattern = r"### filename: (.*?) ###\s*(.*?)\s*### end ###"
    matches = re.findall(pattern, text, flags=re.DOTALL)
    result = {}
    for filename, content in matches:
        result[filename.strip()] = content.strip()
    return result

def assemble_files(directory):
    """
    Recursively assemble the contents of all files in the given directory and its subdirectories
    into a single string in the custom format. Each file is represented with its relative path.
    """
    result = ""
    for root, dirs, files in os.walk(directory):
        for filename in files:
            file_path = os.path.join(root, filename)
            relative_path = os.path.relpath(file_path, directory)
            if os.path.isfile(file_path):
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read().strip()
                result += f"### filename: {relative_path} ###\n{content}\n### end ###\n"
    return result

def write_files(file_dict, output_directory):
    """
    Given a dictionary mapping filenames (which may include subdirectories) to file contents,
    write each file to the output_directory, creating subdirectories as needed.
    """
    for filename, content in file_dict.items():
        file_path = os.path.join(output_directory, filename)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

# --- New: Auditor Functions ---

def audit_file(original_code, new_code, model="o1-mini"):
    """
    You are an expert code integrator. Your task is to merge modifications into a full,
    complete, and ready-to-run file. If the revised version contains only partial changes 
    or instructions such as "do the same as before," incorporate these changes into the complete 
    original file. NEVER output placeholder text like "Replace with a secure key in production."
    Always provide fully working code. Do not include any commentary.
    """
    audit_prompt = (
        "You are an expert code integrator. Your task is to produce a complete, self-contained version of a file by merging any modifications into the original content. "
        "If the revised version is partial or contains instructions like 'do the same as before', integrate these changes so that the final file is complete and fully working. "
        "Ensure that no placeholder text (such as 'Replace with a secure key in production') remains; provide real, working code out-of-the-box. "
        "Do not include any commentary in your output.\n\n"
        "Original file content:\n"
        "----------------------\n"
        f"{original_code}\n"
        "----------------------\n\n"
        "Revised file content:\n"
        "----------------------\n"
        f"{new_code}\n"
        "----------------------\n"
    )
    response = openai.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": audit_prompt}],
    )
    return response.choices[0].message.content

def audited_write_files(new_file_dict, output_directory, model="o1-mini"):
    """
    For each file to be written, if an original version exists, call the auditor function 
    to merge the new content with the existing file to produce a complete and fully functional file.
    Then, write the audited content. This supports files in subdirectories.
    """
    for filename, new_content in new_file_dict.items():
        file_path = os.path.join(output_directory, filename)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                original_content = f.read()
        else:
            original_content = None

        if original_content:
            safe_print(f"Auditing file: {filename}")
            audited_content = audit_file(original_content, new_content, model=model)
        else:
            audited_content = new_content

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(audited_content)

# --- Helper: Load the Base Prompt from a file ---
def load_base_prompt(prompt_file="BasePrompt.txt"):
    """
    Load the base prompt from the specified file.
    If the file is not found, use a default prompt tailored for a to-do list application.
    The prompt instructs the AI to produce complete, ready-to-run code with no placeholder text.
    """
    if os.path.exists(prompt_file):
        with open(prompt_file, "r", encoding="utf-8") as f:
            return f.read()
    else:
        safe_print(f"Warning: {prompt_file} not found. Using a default prompt.")
        return (
            "I'm building a simple, fully functional web-based To-Do List application using Python and Flask. "
            "The application should allow users to add, view, update, and delete tasks, storing them in a SQLite database. "
            "All files must be complete and ready-to-run out-of-the-box, with no placeholder text or insecure instructions. "
            "When modifying any file, provide the entire file content. Do not include any commentary or instructions; output code only. "
            "Organize files into appropriate directories (e.g., templates, static/css)."
        )

# --- Model Call Functions (using o1-mini or o1-preview) ---
DEFAULT_MODEL = "o1-mini"

def generate_initial_code(prompt, model=DEFAULT_MODEL):
    """
    Generate complete, working code based on the given prompt.
    The output must follow the specified format: each file is preceded by a header line and followed by a footer line.
    Do not include any extra commentary or placeholder text.
    """
    full_prompt = (
        prompt + "\n\n"
        "Return your output in the following format:\n"
        "For each file, output a header line as:\n"
        "### filename: <filename> ###\n"
        "Then output the complete file content on subsequent lines, followed by a footer line:\n"
        "### end ###\n"
        "Ensure the code is fully complete, self-contained, and ready-to-run. Do not include any commentary."
    )
    response = openai.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": full_prompt}],
    )
    return response.choices[0].message.content

def load_feedback(feedback_path="feedback.txt"):
    """
    If the specified feedback file exists, return its content; otherwise, return an empty string.
    """
    if os.path.exists(feedback_path):
        with open(feedback_path, "r", encoding="utf-8") as f:
            return f.read().strip()
    return ""

def clear_feedback(feedback_path="feedback.txt"):
    """
    Clear all text from the feedback file.
    """
    if os.path.exists(feedback_path):
        with open(feedback_path, "w", encoding="utf-8") as f:
            f.write("")

def review_code(code, reviewer_prompt, model=DEFAULT_MODEL):
    """
    Review the provided code and produce a corrected, fully integrated version.
    Your output must contain the complete code for each file, with no partial updates or placeholder text.
    Do not include any commentary.
    """
    full_prompt = (
        reviewer_prompt + "\n\n"
        "Return the corrected code in the following format:\n"
        "For each file, begin with a header line: '### filename: <filename> ###'\n"
        "Follow with the complete file content, then end with: '### end ###'\n"
        "Do not include any additional commentary.\n\n"
        "Here is the code:\n" + code + "\n\n"
        "Ensure the final output is complete and working."
    )
    response = openai.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": full_prompt}],
    )
    return response.choices[0].message.content

def aggregate_reviews(original_code, review1, review2, model=DEFAULT_MODEL):
    """
    Compare the original code and two revised versions provided by independent reviewers.
    Merge the best improvements into a final, complete version of each file.
    Ensure that the final output is fully working and contains no placeholder text.
    Return the merged code in the same file format without any commentary.
    """
    aggregator_prompt = (
        "You are to merge two reviewed versions of code with the original version. "
        "Compare the changes, and integrate the best improvements into complete, self-contained files that are ready-to-run. "
        "Do not output any placeholder text or commentary. Every file must be provided in full.\n\n"
        "Original Code:\n" + original_code +
        "\n\nReviewer 1 Revised Code:\n" + review1 +
        "\n\nReviewer 2 Revised Code:\n" + review2 +
        "\n\nReturn the final merged version in the format:\n"
        "### filename: <filename> ###\n"
        "<complete file content>\n"
        "### end ###"
    )
    response = openai.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": aggregator_prompt}],
    )
    return response.choices[0].message.content

def gap_analysis(code_text, model=DEFAULT_MODEL):
    """
    Analyze the provided code for missing features or improvements.
    Identify issues and suggest modifications to ensure that the code is complete and ready-to-run.
    Do not include any security additions or placeholder text; focus on creating a working foundation.
    Return only the suggestions without additional commentary.
    """
    analysis_prompt = (
        "Review the following code for a simple web-based To-Do List application. "
        "Identify any missing features, errors, or areas for improvement to make the code fully complete and working out-of-the-box. "
        "Do not include any security-related additions or placeholder instructions. "
        "Provide only the necessary suggestions in plain text.\n\n"
        + code_text
    )
    response = openai.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": analysis_prompt}],
    )
    return response.choices[0].message.content

# --- MAIN ORCHESTRATION (All intermediate data kept in memory) ---

# Final website files will be written to the 'todo_app' directory.
DIR = "todo_app"
os.makedirs(DIR, exist_ok=True)

# Load the base prompt from BasePrompt.txt
base_prompt = load_base_prompt("BasePrompt.txt")

max_iterations = 5
iteration = 0
previous_aggregated_code = ""

while iteration < max_iterations:
    safe_print(f"\n===== Iteration {iteration+1} =====\n")
    
    if iteration == 0:
        # --- Pre-run Gap Analysis & Prompt Update ---
        if os.listdir(DIR):
            safe_print("Scanning current application files for pre-run gap analysis...")
            current_files_str = assemble_files(DIR)
            pre_analysis = gap_analysis(current_files_str)
            safe_print("Pre-run Gap Analysis suggestions:")
            safe_print(pre_analysis)
            updated_prompt = (
                base_prompt +
                "\n\nCurrent files:\n" + current_files_str +
                "\n\nIncorporate all of the following improvements:\n" + pre_analysis
            )
        else:
            updated_prompt = base_prompt
    else:
        updated_prompt = base_prompt

    safe_print("Updated prompt for code generation:")
    safe_print(updated_prompt)

    additional_feedback = load_feedback()
    if additional_feedback:
        safe_print("Additional feedback loaded")
        updated_prompt += "\n\nAdditional Very Important Feedback to fix first:\n" + additional_feedback
    clear_feedback()

    # --- Step 1: Initial Code Generation ---
    safe_print("Initial Code Generation Begins")
    initial_code_output = generate_initial_code(updated_prompt)
    initial_files = parse_files(initial_code_output)
    # For the initial generation, simply write the files.
    write_files(initial_files, DIR)
    remove_triple_backtick_lines(DIR)
    safe_print("Initial Code Generation Ends")

    # --- Step 2: Reviews ---
    safe_print("Review Begins")
    review1_output = review_code(initial_code_output, "Please review the code and fix any errors or omissions, ensuring that the output is complete and ready-to-run.")
    safe_print("Reviewer 1 complete")

    review2_output = review_code(initial_code_output, "Please inspect the code for bugs and inconsistencies, and return a fully integrated, corrected version that works out-of-the-box.")
    safe_print("Reviewer 2 complete")

    # --- Step 3: Aggregation ---
    safe_print("Aggregation Begins")
    aggregated_code_output = aggregate_reviews(initial_code_output, review1_output, review2_output)
    aggregated_files = parse_files(aggregated_code_output)
    # Use the auditor to check each file (supporting subdirectories)
    audited_write_files(aggregated_files, DIR, model=DEFAULT_MODEL)
    remove_triple_backtick_lines(DIR)
    safe_print("Aggregation Ends")

    # --- Step 4: Post-run Gap Analysis ---
    safe_print("Post-run Gap Analysis Begins")
    post_analysis = gap_analysis(aggregated_code_output)
    safe_print("Post-run Gap Analysis suggestions:")
    safe_print(post_analysis)

    # --- Update Base Prompt with Latest Analysis ---
    base_prompt = (
        load_base_prompt("BasePrompt.txt") +  # Reload the base prompt in case it has changed
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

safe_print(f"\nAll iterations complete. Application files are in '{DIR}'.")
