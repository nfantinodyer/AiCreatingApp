import openai
import json
import os
import re

# Load the OpenAI API key from a config file.
config = {}
with open("config.json", "r") as config_file:
    config = json.load(config_file)
openai.api_key = config["api_key"]

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
    
    Returns a dictionary mapping filenames to their content.
    """
    pattern = r"### filename: (.*?) ###\s*(.*?)\s*### end ###"
    matches = re.findall(pattern, text, flags=re.DOTALL)
    result = {}
    for filename, content in matches:
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

def generate_initial_code(prompt):
    full_prompt = (
        prompt + "\n\n"
        "Return your output in the following format:\n"
        "For each file, output a line:\n"
        "### filename: <filename> ###\n"
        "Then on subsequent lines, output the file content, and then output a line:\n"
        "### end ###\n"
        "Do not include any additional commentary."
    )
    response = openai.chat.completions.create(
        model="gpt-4o",  # Using a GPT-4 variant
        messages=[
            {"role": "system", "content": "You are an expert developer."},
            {"role": "user", "content": full_prompt}
        ],
        temperature=0.8,
    )
    return response.choices[0].message.content

def review_code(code, reviewer_prompt, model="gpt-4o"):
    full_prompt = (
        reviewer_prompt + "\n\n"
        "Return the corrected code in the same format as provided below. Do not include any commentary.\n\n"
        "Here is the code:\n" + code + "\n\n"
        "Use the same format: each file begins with a line '### filename: <filename> ###', then its content, then '### end ###'."
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

def aggregate_reviews(original_code, review1, review2, model="gpt-4o"):
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
        messages=[
            {"role": "system", "content": "You are an expert code aggregator."},
            {"role": "user", "content": aggregator_prompt}
        ],
        temperature=0.3,
    )
    return response.choices[0].message.content

def gap_analysis(code_text, model="gpt-4o"):
    analysis_prompt = (
        "Please review the following code for a website for selling bananas. "
        "Identify any missing features or improvements, and provide suggestions on what to add or fix.\n\n"
        + code_text
    )
    response = openai.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "You are an expert quality assurance and improvement assistant."},
            {"role": "user", "content": analysis_prompt}
        ],
        temperature=0.3,
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
