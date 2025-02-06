import os
import re

# ---------------------------
# CONFIGURATION (unchanged)
# ---------------------------
# For testing, we don't need the API key, so we can comment out the config JSON loading.
# import json
# with open("config.json", "r") as config_file:
#     config = json.load(config_file)
# openai.api_key = config["api_key"]

# ---------------------------
# Helper Functions (unchanged)
# ---------------------------
def safe_print(text):
    try:
        print(text)
    except Exception as e:
        print(text)

def parse_files(text):
    """
    Parse a string in the custom file format.
    Expected format for each file:
    
    ### filename: <filename> ###
    <file content>
    ### end ###
    
    Returns a dictionary mapping filenames to their content,
    with the first and last lines removed if they are exactly "```".
    """
    pattern = r"### filename: (.*?) ###\s*(.*?)\s*### end ###"
    matches = re.findall(pattern, text, flags=re.DOTALL)
    result = {}
    for filename, content in matches:
        lines = content.splitlines()
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

# ---------------------------
# Dummy Model Functions for Testing
# ---------------------------
# These functions simulate responses from the API. You can change the returned strings as needed.
def generate_initial_code(prompt, model="o1-mini"):
    # Return a sample output in the custom format.
    return (
        "### filename: index.html ###\n"
        "<html><body><h1>Banana Shop</h1></body></html>\n"
        "### end ###\n"
        "### filename: style.css ###\n"
        "body { background-color: yellow; }\n"
        "### end ###"
    )

def review_code(code, reviewer_prompt, model="o1-mini"):
    # For testing, just return the input code unmodified (or modify it slightly).
    return code.replace("Banana Shop", "The Banana Shop")

def aggregate_reviews(original_code, review1, review2, model="o1-mini"):
    # For testing, simply return the version from reviewer1.
    return review1

def gap_analysis(code_text, model="o1-mini"):
    # For testing, return a dummy analysis string.
    return "Consider adding a navigation bar and contact form validation."

# ---------------------------
# MAIN ORCHESTRATION (Intermediate data kept in memory)
# ---------------------------

# Directory to write website files.
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
            "\n\nIncorporate the following improvements:\n" + pre_analysis
        )
    else:
        updated_prompt = base_prompt

    safe_print("Updated prompt for code generation:")
    safe_print(updated_prompt)

    # --- Step 1: Initial Code Generation ---
    initial_code_output = generate_initial_code(updated_prompt)
    safe_print("Initial code generated:")
    safe_print(initial_code_output)
    initial_files = parse_files(initial_code_output)
    write_files(initial_files, WEBSITE_DIR)

    # --- Step 2: Reviews ---
    review1_output = review_code(initial_code_output, "Please review the code and fix any errors or issues you see.")
    safe_print("Reviewer 1 output:")
    safe_print(review1_output)
    review2_output = review_code(initial_code_output, "Please inspect the code for any bugs or improvements and return a corrected version.")
    safe_print("Reviewer 2 output:")
    safe_print(review2_output)

    # --- Step 3: Aggregation ---
    aggregated_code_output = aggregate_reviews(initial_code_output, review1_output, review2_output)
    safe_print("Aggregated final code:")
    safe_print(aggregated_code_output)
    aggregated_files = parse_files(aggregated_code_output)
    write_files(aggregated_files, WEBSITE_DIR)

    # --- Step 4: Post-run Gap Analysis ---
    post_analysis = gap_analysis(aggregated_code_output)
    safe_print("Post-run Gap Analysis suggestions:")
    safe_print(post_analysis)

    # --- Update Base Prompt with Latest Analysis ---
    base_prompt = (
        "Create a website in HTML, CSS, and JavaScript for selling bananas. "
        "Include a homepage, product listing, and a contact form."
        "\n\nIncorporate the following improvements based on the latest gap analysis:\n" + post_analysis
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
