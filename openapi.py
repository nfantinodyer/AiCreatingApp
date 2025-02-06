import openai
import json
import os

# Load configuration (e.g. API key) from config.json
with open('config.json', 'r') as config_file:
    config_data = json.load(config_file)

openai.api_key = config_data['api_key']

# --- Define the functions for each step ---

def generate_initial_code(prompt):
    response = openai.chat.completions.create(
        model="gpt-4o-mini",  # Original generator model
        messages=[
            {"role": "system", "content": "You are an expert developer."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.8,
    )
    return response.choices[0].message.content

def review_code(code, reviewer_prompt, model="gpt-4"):  
    # Use a higher reasoning model for reviews
    full_prompt = f"{reviewer_prompt}\n\nHere is the code:\n{code}"
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
        "I have an original piece of code and two revised versions provided by independent reviewers. \n"
        "Please compare the following:\n\n"
        "Original Code:\n"
        "-----------------\n"
        f"{original_code}\n\n"
        "Reviewer 1 Revised Code:\n"
        "-----------------\n"
        f"{review1}\n\n"
        "Reviewer 2 Revised Code:\n"
        "-----------------\n"
        f"{review2}\n\n"
        "Merge the best improvements and provide a final version of the code. "
        "If one reviewer made a better change for a given section, choose that version. "
        "Explain your reasoning briefly in a summary before the code."
    )
    response = openai.chat.completions.create(
        model="gpt-4",  # aggregator model with high reasoning
        messages=[
            {"role": "system", "content": "You are an expert code aggregator."},
            {"role": "user", "content": aggregator_prompt}
        ],
        temperature=0.3,
    )
    return response.choices[0].message.content

def gap_analysis(final_code):
    analysis_prompt = (
        "Please review the following code for a website for selling bananas. "
        "Identify any missing features or improvements, and provide suggestions on what to add or fix. \n\n"
        f"{final_code}"
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

# --- Main orchestration ---

# File where the source code is stored.
SOURCE_FILE = "source_code.txt"

# Define the original prompt.
original_prompt = (
    "Create a website in HTML, CSS, and JavaScript for selling bananas. "
    "Include a homepage, product listing, and a contact form."
)

# Step 1: Read the source code from file if it exists; otherwise generate it.
if os.path.exists(SOURCE_FILE):
    with open(SOURCE_FILE, "r", encoding="utf-8") as src_file:
        initial_code = src_file.read()
    print("Loaded initial code from file:")
    print(initial_code)
else:
    print("Generating initial code...")
    initial_code = generate_initial_code(original_prompt)
    # Save the generated code to the file for future runs.
    with open(SOURCE_FILE, "w", encoding="utf-8") as src_file:
        src_file.write(initial_code)
    print("Initial Code Generated and saved to file:")
    print(initial_code)

# Step 2: Review the code using two separate reviewers.
print("\nReviewing code with Reviewer 1...")
review1 = review_code(initial_code, "Please review the code and fix any errors or issues you see.")
print("Reviewer 1 Output:\n", review1)

print("\nReviewing code with Reviewer 2...")
review2 = review_code(initial_code, "Please inspect the code for any bugs or improvements and return a corrected version.")
print("Reviewer 2 Output:\n", review2)

# Step 3: Aggregate the two reviews.
print("\nAggregating the two reviews...")
final_code = aggregate_reviews(initial_code, review1, review2)
print("Aggregated Final Code:\n", final_code)

# Step 4: Perform gap analysis on the final code.
print("\nPerforming gap analysis on final code...")
analysis = gap_analysis(final_code)
print("Gap Analysis Suggestions:\n", analysis)

# Step 5: Update the source file with the final aggregated code.
with open(SOURCE_FILE, "w", encoding="utf-8") as src_file:
    src_file.write(final_code)
print(f"\nThe source file '{SOURCE_FILE}' has been updated with the final code.")
