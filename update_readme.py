import requests
import re
from urllib.parse import urlparse # Added for URL parsing

API_URL = "https://poridhi-tesk.vercel.app/get_tasks" # Make sure this is your deployed API URL if not running locally
README_PATH = "readme.md" # Use relative path for GitHub Actions

# Placeholder comments in your README
README_TABLE_START_COMMENT = "<!-- DYNAMIC_TABLE_START -->"
README_TABLE_END_COMMENT = "<!-- DYNAMIC_TABLE_END -->"

def fetch_tasks_from_api():
    """Fetches task data from the Flask API."""
    try:
        response = requests.get(API_URL)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching tasks from API: {e}")
        return None

def format_updates(updates):
    """Formats a list of update objects into a numbered HTML string for Markdown table."""
    if not updates:
        return "No updates yet."
    if isinstance(updates, list):
        if not updates: # Handle empty list case
            return "No updates yet."
        
        formatted_list = []
        for i, update_obj in enumerate(updates):
            if isinstance(update_obj, dict) and 'text' in update_obj and 'link' in update_obj:
                text = update_obj['text']
                link = update_obj['link']
                if link: # Only add link if it's not empty
                    formatted_list.append(f"{i+1}. [{text}]({link})")
                else:
                    formatted_list.append(f"{i+1}. {text} (No link provided)")
            elif isinstance(update_obj, dict) and 'text' in update_obj: # Handle if link is missing
                 formatted_list.append(f"{i+1}. {update_obj['text']} (Link missing)")
            else: # Fallback for old string format or malformed objects
                formatted_list.append(f"{i+1}. {str(update_obj)}")

        return "<br>".join(formatted_list)
    return str(updates) # Fallback if it's not a list (e.g. old data format)

def shorten_repo_link(url_string):
    """Shortens a repository URL for display, preferring username/repo for GitHub."""
    if not url_string or url_string == '[Repository URL]' or not url_string.startswith(('http://', 'https://')):
        return '[Link]' # Default text if no valid URL

    try:
        parsed_url = urlparse(url_string)
        if parsed_url.netloc.lower() == 'github.com':
            path_parts = parsed_url.path.strip('/').split('/')
            if len(path_parts) >= 2:
                # Ensure no empty strings from multiple slashes, e.g. /user//repo
                user_repo = [part for part in path_parts[:2] if part]
                if len(user_repo) == 2:
                    return f"{user_repo[0]}/{user_repo[1]}"
        # Fallback for other URLs or if GitHub parsing fails to get two parts
        if parsed_url.netloc:
            return parsed_url.netloc # e.g., gitlab.com
        return url_string[:30] + "..." if len(url_string) > 30 else url_string # Basic truncation
    except Exception:
        # Catch any parsing errors and return a simple truncation
        return url_string[:30] + "..." if len(url_string) > 30 else url_string

def generate_markdown_table(tasks):
    """Generates a Markdown table from the task data."""
    if not tasks:
        return "| Name | Task | Update | Repo Link |\n| --- | --- | --- | --- |\n| (No tasks to display) |  |  |  |\n"

    header = "| Name | Task | Update | Repo Link |\n| --- | --- | --- | --- |"
    rows = []
    for task_entry in tasks: # Renamed variable to avoid conflict with 'tasks' module if ever imported
        name = task_entry.get('name', 'N/A')
        task_name = task_entry.get('task_name', 'N/A')
        task_updates_list = task_entry.get('task_updates', []) # This is now a list of dicts
        repo_link_full = task_entry.get('repo_link', '')

        formatted_updates = format_updates(task_updates_list)
        
        # Ensure repo_link_full is a string before passing to shorten_repo_link
        if not isinstance(repo_link_full, str):
            repo_link_full = str(repo_link_full)

        short_link_text = shorten_repo_link(repo_link_full)
        
        # If repo_link_full is empty or just a placeholder, don't make it a clickable link
        if not repo_link_full or repo_link_full == '[Repository URL]':
            repo_link_markdown = short_link_text # Or simply '[No Link]'
        else:
            repo_link_markdown = f"[{short_link_text}]({repo_link_full})"
            
        rows.append(f"| {name} | {task_name} | {formatted_updates} | {repo_link_markdown} |")
    
    return f"{header}\n" + "\n".join(rows)

def update_readme(markdown_table):
    """Updates the README.md file with the new Markdown table."""
    try:
        with open(README_PATH, 'r', encoding='utf-8') as f:
            readme_content = f.read()

        pattern = re.compile(f"{re.escape(README_TABLE_START_COMMENT)}.*?{re.escape(README_TABLE_END_COMMENT)}", re.DOTALL)
        
        # Ensure the new content for replacement is correctly formatted
        new_dynamic_block = f"{README_TABLE_START_COMMENT}\n{markdown_table}\n{README_TABLE_END_COMMENT}"
        
        updated_readme_content, num_replacements = pattern.subn(new_dynamic_block, readme_content)
        
        if num_replacements == 0:
            print(f"Error: Could not find placeholder comments in README.md.\n"
                  f"Make sure your README.md contains:\n{README_TABLE_START_COMMENT}\n...some content...\n{README_TABLE_END_COMMENT}")
            return

        with open(README_PATH, 'w', encoding='utf-8') as f:
            f.write(updated_readme_content)
        print("README.md updated successfully.")

    except FileNotFoundError:
        print(f"Error: README.md not found at {README_PATH}")
    except Exception as e:
        print(f"An error occurred while updating README.md: {e}")

if __name__ == "__main__":
    tasks = fetch_tasks_from_api()
    if tasks is not None:
        # Example: Pad with placeholder rows if you want a fixed number of total rows
        # current_task_count = len(tasks)
        # desired_total_rows = 20 
        # if current_task_count < desired_total_rows:
        #     for _ in range(desired_total_rows - current_task_count):
        #         tasks.append({
        #             'name': '[Your Name]', 
        #             'task_name': '[Task Name]', 
        #             'task_updates': ['[Status/Progress]'], 
        #             'repo_link': '[Repository URL]'
        #         })
        
        markdown_table = generate_markdown_table(tasks)
        update_readme(markdown_table)
