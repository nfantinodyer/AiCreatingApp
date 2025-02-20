import openai
import json  # Only used to load the API key.
import os
import re
import sys
import time  # For optional delays on retry
import requests  # Used to download generated images
from concurrent.futures import ThreadPoolExecutor, as_completed

# ================= Global Configuration =================

# OUTPUT_DIR can be adjusted to point to your desired application output directory.
OUTPUT_DIR = "testingTestingCapability"  

# Load API key from configuration file.
with open("config.json", "r") as config_file:
    config = json.load(config_file)
openai.api_key = config["api_key"]

# Configure candidate models (order matters: try first then fall back)
CANDIDATE_MODELS = ["gpt-4o-mini", "o1-mini"]
DEFAULT_MODEL = CANDIDATE_MODELS[0]

# Parameters to control generation scaling.
INITIAL_VARIANT_COUNT = 4  # Change this to any number to scale the initial generation.

# Global variable for file extensions that should NOT be opened as text.
DISALLOWED_EXTENSIONS = {
    # Image extensions
    '.png', '.jpg', '.jpeg', '.gif', '.bmp', '.svg', '.ico',
    # Video extensions
    '.mp4', '.mkv', '.avi', '.mov', '.webm',
    # Audio extensions
    '.mp3', '.wav', '.flac', '.ogg', '.aac', '.m4a',
    # Other
    '.db', '.ini'
}

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
    For each file that is not of a disallowed type (e.g. image, video, audio),
    remove any lines that contain triple backticks (```),
    then overwrite the file with the filtered content.
    """
    for root, dirs, files in os.walk(directory):
        for filename in files:
            ext = os.path.splitext(filename)[1].lower()
            if ext in DISALLOWED_EXTENSIONS:
                continue  # Skip files that should not be opened as text.
            file_path = os.path.join(root, filename)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
            except UnicodeDecodeError:
                safe_print(f"Skipping file due to decoding error: {file_path}")
                continue
            filtered_lines = [line for line in lines if "```" not in line]
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
    
    For files with extensions in DISALLOWED_EXTENSIONS (e.g., images, videos, audio) a placeholder
    is inserted. For all other files, an attempt is made to read the content as text.
    """
    result = ""
    for root, dirs, files in os.walk(directory):
        for filename in files:
            file_path = os.path.join(root, filename)
            relative_path = os.path.relpath(file_path, directory)
            ext = os.path.splitext(filename)[1].lower()
            if os.path.isfile(file_path):
                if ext in DISALLOWED_EXTENSIONS:
                    content = "<binary file not included>"
                else:
                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            content = f.read().strip()
                    except UnicodeDecodeError:
                        content = "<Unable to decode file content>"
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

# ================= New Functions for Image Generation =================

def find_image_references_in_text(text):
    """
    Search the provided text for any references to image files.
    It looks for common patterns in HTML (src=, href=), CSS (url(...)) and Markdown (![...](...)).
    Returns a set of image file paths (relative paths as written in the code).
    """
    image_refs = set()
    patterns = [
        r'(?i)(?:src|href)=["\']([^"\']+\.(?:png|jpg|jpeg|gif|bmp|svg|ico))["\']',
        r'(?i)url\(\s*["\']?([^"\'\s)]+\.(?:png|jpg|jpeg|gif|bmp|svg|ico))["\']?\s*\)',
        r'(?i)!\[[^\]]*\]\(([^)]+\.(?:png|jpg|jpeg|gif|bmp|svg|ico))\)'
    ]
    for pat in patterns:
        matches = re.findall(pat, text)
        for m in matches:
            image_refs.add(m)
    return image_refs

def generate_image(image_full_path, model="gpt-4o"):
    """
    Generate an image using OpenAI’s image-generation API and save it to image_full_path.
    The prompt is based on the image file's name.
    """
    os.makedirs(os.path.dirname(image_full_path), exist_ok=True)
    image_filename = os.path.basename(image_full_path)
    prompt = (f"Generate a visually appealing placeholder image for a modern web application. "
              f"The image should be relevant to the design element named '{image_filename}'.")
    try:
        response = openai.Image.create(
            prompt=prompt,
            n=1,
            size="512x512",  # You can adjust the size as needed.
            response_format="url"
        )
        image_url = response['data'][0]['url']
        r = requests.get(image_url)
        if r.status_code == 200:
            with open(image_full_path, "wb") as f:
                f.write(r.content)
            safe_print(f"Generated image: {image_full_path}")
        else:
            safe_print(f"Failed to download image for {image_full_path}. HTTP status: {r.status_code}")
    except Exception as e:
        safe_print(f"Error generating image for {image_full_path}: {e}")

def generate_missing_images(directory):
    """
    Walk through text-based files in the directory (and its subdirectories) to find references
    to images. For any referenced image that does not exist, generate it using generate_image().
    """
    tasks = []
    with ThreadPoolExecutor(max_workers=10) as executor:
        for root, dirs, files in os.walk(directory):
            for filename in files:
                ext = os.path.splitext(filename)[1].lower()
                if ext in DISALLOWED_EXTENSIONS:
                    continue  # Skip binary files.
                file_path = os.path.join(root, filename)
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()
                except UnicodeDecodeError:
                    continue
                image_refs = find_image_references_in_text(content)
                for image_ref in image_refs:
                    image_full_path = os.path.join(directory, image_ref)
                    if not os.path.exists(image_full_path):
                        safe_print(f"Image reference '{image_ref}' not found. Generating image...")
                        tasks.append(executor.submit(generate_image, image_full_path))
        # Wait for all image generation tasks to complete.
        for task in tasks:
            task.result()

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
            except Exception as e:
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
        "While merging, evaluate which version more closely adheres to the original base prompt's guidelines and project vision. "
        "Favor changes that bring the code in closer alignment with the base prompt, and be willing to let through additional modifications if they add beneficial functionality.\n\n"
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
        tasks = []
        with ThreadPoolExecutor(max_workers=max(1, len(current_variants)//2)) as executor:
            for i in range(0, len(current_variants) - 1, 2):
                tasks.append(executor.submit(double_check_pair, current_variants[i], current_variants[i+1], model))
            for task in tasks:
                merged_variants.append(task.result())
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
        "Review the code thoroughly, checking for errors, inconsistencies, or deviations from the original base prompt requirements. "
        "If the code already closely matches the base prompt, allow enhancements that extend its functionality while preserving the core design. "
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
        "Give special weight to changes that improve adherence to the base prompt. If one version is closer to the original project requirements, favor its changes. "
        "Allow additional beneficial modifications to pass through if they extend functionality while staying true to the base prompt.\n\n"
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
        "Also assess how well the code aligns with the original base prompt requirements. "
        "If the code already closely follows the base prompt, favor suggestions that allow additional beneficial changes rather than removing existing functionality. "
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
        "When merging, carefully evaluate which modifications align best with the original base prompt's guidelines. "
        "Favor changes that improve adherence to the project requirements, and allow more modifications to pass through if they extend functionality in a beneficial way. "
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

def process_audit_file(filename, new_content, output_directory, model=DEFAULT_MODEL):
    """
    Helper function to audit and write a single file.
    """
    file_path = os.path.join(output_directory, filename)
    
    # If the filename indicates a directory or the path exists as a directory, create it and skip further processing.
    if filename.endswith('/') or (os.path.exists(file_path) and os.path.isdir(file_path)):
        os.makedirs(file_path, exist_ok=True)
        safe_print(f"Ensured directory exists: {file_path}")
        return

    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    
    # For image files: if content is the placeholder, generate the image.
    if os.path.splitext(filename)[1].lower() in {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.svg', '.ico'}:
        if new_content.strip() == "<binary file not included>":
            safe_print(f"Generating missing image file: {filename}")
            generate_image(file_path)
            return

    # Read the existing file content if it exists and is not a directory.
    if os.path.exists(file_path) and not os.path.isdir(file_path):
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

def audited_write_files(new_file_dict, output_directory, model=DEFAULT_MODEL):
    """
    For each file to be written, if an original version exists in the output directory,
    merge the new content with the existing file using the auditor function, then write the audited content to disk.
    Additionally, for files intended to be images (with image extensions) whose content is just the placeholder text,
    generate a real image instead.
    If the aggregated file entry represents a directory (e.g. ends with a '/' or the path is already a directory),
    ensure the directory exists and skip file writing.
    """
    tasks = []
    with ThreadPoolExecutor(max_workers=10) as executor:
        for filename, new_content in new_file_dict.items():
            tasks.append(executor.submit(process_audit_file, filename, new_content, output_directory, model))
        for task in tasks:
            task.result()

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

        # --- Step 1: Initial Code Generation (Tree Leaves) ---
        safe_print("Initial Code Generation Begins")
        initial_variants = []
        # Use concurrent generators to produce multiple independent variants.
        with ThreadPoolExecutor(max_workers=INITIAL_VARIANT_COUNT) as executor:
            futures = [executor.submit(generate_initial_code, updated_prompt, DEFAULT_MODEL)
                       for _ in range(INITIAL_VARIANT_COUNT)]
            for i, future in enumerate(as_completed(futures)):
                variant = future.result()
                initial_variants.append(variant)
                safe_print(f"Initial generator variant {i+1} produced.")
        safe_print(f"Generated {len(initial_variants)} initial code variants.")

        # --- Step 2: Independent Review Trees ---
        # For each initial variant, run two reviewers concurrently.
        tree_aggregated_outputs = []
        for idx, initial_variant in enumerate(initial_variants):
            safe_print(f"\nProcessing review tree for variant {idx+1}.")
            with ThreadPoolExecutor(max_workers=2) as executor:
                future_rev1 = executor.submit(
                    review_code,
                    initial_variant,
                    "Please review the code and correct any errors or omissions so that the output is fully complete and immediately functional. "
                    "Ensure that any modifications maintain or enhance the alignment with the original base prompt.",
                    DEFAULT_MODEL
                )
                future_rev2 = executor.submit(
                    review_code,
                    initial_variant,
                    "Please inspect the code for bugs, inconsistencies, and deviations from the base prompt, and return a fully integrated, corrected version that is ready-to-run. "
                    "Allow additional beneficial changes if they bring the code closer to the base prompt.",
                    DEFAULT_MODEL
                )
                rev1_output = future_rev1.result()
                rev2_output = future_rev2.result()
            safe_print(f"Reviews completed for variant {idx+1}.")

            # Aggregate the outputs from the initial variant and its two reviews.
            aggregated_tree = aggregate_reviews(initial_variant, rev1_output, rev2_output, model=DEFAULT_MODEL)
            tree_aggregated_outputs.append(aggregated_tree)
            safe_print(f"Aggregation complete for variant {idx+1} tree.")

        # --- Step 3: Hierarchical Aggregation ---
        # If more than one aggregated tree exists, merge them pairwise.
        if len(tree_aggregated_outputs) > 1:
            safe_print("\nMerging aggregated outputs from individual review trees into a final aggregated output.")
            final_aggregated_output = merge_variants(tree_aggregated_outputs, model=DEFAULT_MODEL)
        else:
            final_aggregated_output = tree_aggregated_outputs[0]
        safe_print("Final aggregated code output produced for this iteration.")

        # Write aggregated files to disk using the auditing process.
        aggregated_files = parse_files(final_aggregated_output)
        audited_write_files(aggregated_files, OUTPUT_DIR, model=DEFAULT_MODEL)
        remove_triple_backtick_lines(OUTPUT_DIR)
        safe_print("Files written to disk and audited.")

        # --- Generate Missing Images ---
        safe_print("Scanning for missing image references and generating images if needed...")
        generate_missing_images(OUTPUT_DIR)

        # --- Step 4: Post-run Gap Analysis ---
        safe_print("Performing post-run gap analysis.")
        post_analysis = gap_analysis(final_aggregated_output, model=DEFAULT_MODEL)
        safe_print("Post-run Gap Analysis suggestions:")
        safe_print(post_analysis)

        # --- Update Base Prompt for next iteration ---
        base_prompt = (
            load_base_prompt("BasePrompt.txt") +  # Reload in case of external updates.
            "\n\nIncorporate all of the following improvements:\n" + post_analysis
        )
        safe_print("Base prompt updated for next iteration:")
        safe_print(base_prompt)

        # Double-check: Terminate if no changes are detected between iterations.
        if final_aggregated_output.strip() == previous_aggregated_code.strip():
            safe_print("No changes detected in aggregated code. Terminating loop.")
            break
        else:
            previous_aggregated_code = final_aggregated_output

        iteration += 1

    safe_print(f"\nAll iterations complete. Application files are in '{OUTPUT_DIR}'.")

if __name__ == '__main__':
    main()
