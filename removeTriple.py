import os

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

if __name__ == "__main__":
    # Replace this with the path to the directory you want to process
    directory_to_clean = "website_files"
    remove_triple_backtick_lines(directory_to_clean)
    print(f"Finished removing lines containing triple backticks in {directory_to_clean}")
