import openai
import json  # Only used to load the API key.
import os
import re
import sys
import time  # For optional delays on retry

# ================= Global Configuration =================

# OUTPUT_DIR can be adjusted to point to your desired application output directory.
OUTPUT_DIR = "spreadsheet_app"  

# Load API key from configuration file.
with open("config.json", "r") as config_file:
    config = json.load(config_file)
openai.api_key = config["api_key"]

# Configure candidate models (order matters: try first then fall back)
CANDIDATE_MODELS = ["o1-mini", "gpt-4o"]
DEFAULT_MODEL = CANDIDATE_MODELS[0]

# Parameters to control generation scaling.
INITIAL_VARIANT_COUNT = 8  # Change this to any number to scale the initial generation.

# ================= Utility Functions =================

def safe_print(text):
    """
    Print text using UTF-8 encoding. If a UnicodeEncodeError occurs,
    replace invalid characters.
    """
    try:
        print(text)
    except UnicodeEncodeError:
        print(text.encode('utf-8', errors='replace').decode('utf-8'))

def remove_triple_backtick_lines(directory):
    """
    Walk through the given directory and its subdirectories.
    For each .html, .js, .css, .py, .txt, or .log file found,
    remove any lines that contain triple backticks ('```'),
    then overwrite the file with the filtered content.
    """
    for root, dirs, files in os.walk(directory):
        for filename in files:
            file_path = os.path.join(root, filename)
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            filtered_lines = [line for line in lines if '```' not in line]
            with open(file_path, 'w', encoding='utf-8') as f:
                f.writelines(filtered_lines)

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

# ================= API Wrapper Functions =================

def call_openai_api(prompt, model=DEFAULT_MODEL, max_retries=3):
    """
    Wrapper for calling the OpenAI API.
    It tries the candidate models in order if an error occurs (e.g. usage limit reached).
    """
    for candidate in CANDIDATE_MODELS:
        current_model = candidate
        for attempt in range(max_retries):
            try:
                response = openai.chat.completions.create(
                    model=current_model,
                    messages=[{"role": "user", "content": prompt}],
                )
                return response.choices[0].message.content
            except openai.error.OpenAIError as e:
                safe_print(f"API call using model {current_model} failed on attempt {attempt + 1}: {e}")
                time.sleep(1)  # Optional: pause briefly before retrying.
        safe_print(f"Switching from model {current_model} due to repeated errors.")
    raise Exception("All candidate models failed to process the prompt.")

# ================= Generation and Review Functions =================

def generate_initial_code(prompt, model=DEFAULT_MODEL):
    """
    Generate complete, working code based on the given prompt.
    The output must strictly follow the required header/footer format.
    """
    full_prompt = (
        prompt + "\n\n"
        "Return your output in the following format:\n"
        "For each file, output a header line as follows:\n"
        "### filename: <filename> ###\n"
        "Then output the complete file content, and finally output a footer line:\n"
        "### end ###\n"
        "The code must be complete, self-contained, and ready-to-run immediately. Do not include any extra commentary."
    )
    return call_openai_api(full_prompt, model=model)

def double_check_pair(code_a, code_b, model=DEFAULT_MODEL):
    """
    Compare two versions of code and merge the best improvements from both.
    The final output must be complete, self-contained, and fully functional.
    """
    double_prompt = (
        "You are a master integrator. Compare the two versions of code below and produce a final merged version that incorporates the best improvements from both. "
        "The final output must be complete, self-contained, and fully functional, with no placeholder text or commentary.\n\n"
        "Version A:\n" + code_a + "\n\n"
        "Version B:\n" + code_b + "\n\n"
        "Return the merged code in the following format:\n"
        "### filename: <filename> ###\n"
        "<complete file content>\n"
        "### end ###"
    )
    return call_openai_api(double_prompt, model=model)

def merge_variants(variants, model=DEFAULT_MODEL):
    """
    Repeatedly merge a list of code variants pairwise until only one variant remains.
    If the list length is odd, the last variant is carried over to the next round.
    Returns the final merged variant.
    """
    current_variants = variants[:]
    round_number = 1
    while len(current_variants) > 1:
        safe_print(f"Merging round {round_number}: {len(current_variants)} variants to merge.")
        merged_variants = []
        # Merge in pairs.
        for i in range(0, len(current_variants) - 1, 2):
            merged = double_check_pair(current_variants[i], current_variants[i+1], model=model)
            merged_variants.append(merged)
        # If odd number of variants, carry the last one over.
        if len(current_variants) % 2 == 1:
            merged_variants.append(current_variants[-1])
        current_variants = merged_variants
        round_number += 1
    return current_variants[0]

def review_code(code, reviewer_prompt, model=DEFAULT_MODEL):
    """
    Review the provided code and produce a corrected, fully integrated version.
    The output must use the header/footer format, with no placeholder text or extra commentary.
    """
    full_prompt = (
        reviewer_prompt + "\n\n"
        "Return the corrected code in the following format:\n"
        "For each file, begin with a header line: '### filename: <filename> ###'\n"
        "Follow with the complete file content, then end with: '### end ###'\n"
        "Do not include any extra commentary.\n\n"
        "Here is the code:\n" + code + "\n\n"
        "Ensure the final output is complete and fully functional."
    )
    return call_openai_api(full_prompt, model=model)

def aggregate_reviews(original_code, review1, review2, model=DEFAULT_MODEL):
    """
    Compare the original code with two reviewed versions and merge the best improvements into a final version.
    The output must be complete and fully functional using the specified header/footer format.
    """
    aggregator_prompt = (
        "You are a master integrator of code revisions. Your task is to compare two reviewed versions of the code along with the original version, "
        "and produce a final merged version that incorporates the best improvements from all versions. "
        "The final output must be complete, self-contained, and immediately runnable. "
        "Do not include any placeholder text or commentary. Every file must be output in full.\n\n"
        "Original Code:\n" + original_code +
        "\n\nReviewer 1 Revised Code:\n" + review1 +
        "\n\nReviewer 2 Revised Code:\n" + review2 +
        "\n\nReturn the final merged version in the following format:\n"
        "### filename: <filename> ###\n"
        "<complete file content>\n"
        "### end ###"
    )
    return call_openai_api(aggregator_prompt, model=model)

def gap_analysis(code_text, model=DEFAULT_MODEL):
    """
    Analyze the given code for missing components, errors, or improvements to ensure full functionality.
    Do not propose security features or placeholder instructions.
    Return only the essential suggestions in plain text.
    """
    analysis_prompt = (
        "Analyze the following code for a web-based application. "
        "Identify any missing components, errors, or areas for improvement that would ensure the code is fully complete and ready-to-run. "
        "Do not propose any security features or placeholder instructions. "
        "Provide only the essential suggestions in plain text.\n\n"
        + code_text
    )
    return call_openai_api(analysis_prompt, model=model)

def audit_file(original_code, new_code, model=DEFAULT_MODEL):
    """
    Merge modifications into the original file so that the final output is complete and fully functional.
    Any partial changes or instructions like 'do the same as before' must be fully integrated.
    No placeholder text is allowed.
    """
    audit_prompt = (
        "You are a highly experienced code integrator. Your task is to merge any modifications into the original file so that the final output is complete, self-contained, and fully functional. "
        "If the revised version contains only partial changes or instructions like 'do the same as before', integrate those changes into the full file. "
        "Under no circumstances should any placeholder text remain. Provide actual, working code that runs out-of-the-box. "
        "Do not include any commentary or explanation.\n\n"
        "Original file content:\n"
        "----------------------\n"
        f"{original_code}\n"
        "----------------------\n\n"
        "Revised file content:\n"
        "----------------------\n"
        f"{new_code}\n"
        "----------------------\n"
    )
    return call_openai_api(audit_prompt, model=model)

def audited_write_files(new_file_dict, output_directory, model=DEFAULT_MODEL):
    """
    For each file to be written, if an original version exists in the output directory,
    merge the new content with the existing file using the auditor function, then write the audited content to disk.
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

def load_base_prompt(prompt_file="BasePrompt.txt"):
    """
    Load the base prompt from the specified file.
    If the file is missing, return a default generic prompt.
    """
    if os.path.exists(prompt_file):
        with open(prompt_file, "r", encoding="utf-8") as f:
            return f.read()
    else:
        safe_print(f"Warning: {prompt_file} not found. Using a default prompt.")
        return (
            "I'm building a fully functional web-based application using Python and Flask. "
            "The application requirements will be provided in the base prompt. "
            "All files must be complete and ready-to-run out-of-the-box, with no placeholder text or insecure instructions. "
            "When modifying any file, include the entire file content. Do not include any commentary or instructions; output code only. "
            "Organize files into appropriate directories (e.g., templates, static/css)."
        )

# ================= Main Orchestration =================

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Load the base prompt.
    base_prompt = load_base_prompt("BasePrompt.txt")

    max_iterations = 5
    iteration = 0
    previous_aggregated_code = ""

    while iteration < max_iterations:
        safe_print(f"\n===== Iteration {iteration+1} =====\n")

        # --- Pre-run Gap Analysis & Prompt Update ---
        if os.listdir(OUTPUT_DIR):
            safe_print("Scanning current application files for pre-run gap analysis...")
            current_files_str = assemble_files(OUTPUT_DIR)
            pre_analysis = gap_analysis(current_files_str, model=DEFAULT_MODEL)
            safe_print("Pre-run Gap Analysis suggestions:")
            safe_print(pre_analysis)
            updated_prompt = (
                base_prompt +
                "\n\nCurrent files:\n" + current_files_str +
                "\n\nIncorporate all of the following improvements:\n" + pre_analysis
            )
        else:
            updated_prompt = base_prompt

        safe_print("Updated prompt for code generation:")
        safe_print(updated_prompt)

        additional_feedback = load_feedback()
        if additional_feedback:
            safe_print("Additional feedback loaded")
            updated_prompt += "\n\nAdditional Very Important Feedback to fix first:\n" + additional_feedback
        clear_feedback()

        # --- Step 1: Initial Code Generation (Files kept in memory only) ---
        safe_print("Initial Code Generation Begins")
        initial_variants = []
        for i in range(INITIAL_VARIANT_COUNT):
            variant = generate_initial_code(updated_prompt, model=DEFAULT_MODEL)
            initial_variants.append(variant)
            print(f"Variant {i+1} generated.")
        safe_print(f"Generated {INITIAL_VARIANT_COUNT} initial code variants.")

        # Merge variants pairwise until one final output remains.
        final_initial_code_output = merge_variants(initial_variants, model=DEFAULT_MODEL)
        safe_print("Final initial code output produced via multi-round merging.")
        initial_code_output = final_initial_code_output
        safe_print("Initial Code Generation Completed (files stored in memory)")
        # NOTE: Files are NOT written to disk at this stage.

        # --- Step 2: Reviews ---
        safe_print("Review Begins")
        review1_output = review_code(initial_code_output,
            "Please review the code and correct any errors or omissions so that the output is fully complete and immediately functional.",
            model=DEFAULT_MODEL)
        safe_print("Reviewer 1 complete")

        review2_output = review_code(initial_code_output,
            "Please inspect the code for bugs and inconsistencies, and return a fully integrated, corrected version that is ready-to-run.",
            model=DEFAULT_MODEL)
        safe_print("Reviewer 2 complete")

        # --- Step 3: Aggregation ---
        safe_print("Aggregation Begins")
        aggregated_code_output = aggregate_reviews(initial_code_output, review1_output, review2_output, model=DEFAULT_MODEL)
        aggregated_files = parse_files(aggregated_code_output)
        # Write files to disk using the auditor for final verification.
        audited_write_files(aggregated_files, OUTPUT_DIR, model=DEFAULT_MODEL)
        remove_triple_backtick_lines(OUTPUT_DIR)
        safe_print("Aggregation Ends")

        # --- Step 4: Post-run Gap Analysis ---
        safe_print("Post-run Gap Analysis Begins")
        post_analysis = gap_analysis(aggregated_code_output, model=DEFAULT_MODEL)
        safe_print("Post-run Gap Analysis suggestions:")
        safe_print(post_analysis)

        # --- Update Base Prompt for next iteration ---
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

    safe_print(f"\nAll iterations complete. Application files are in '{OUTPUT_DIR}'.")

if __name__ == '__main__':
    main()
