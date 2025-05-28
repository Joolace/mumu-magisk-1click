import re
import requests
from bs4 import BeautifulSoup
import datetime

# --- Configuration ---
README_PATH = "README.md"
MUMU_DOWNLOAD_URL = "https://mumu.163.com/download/"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"

# --- HTML Markers in README.md ---
VERSION_START_MARKER = "<!-- MUMU_VERSION_START -->"
VERSION_END_MARKER = "<!-- MUMU_VERSION_END -->"
DATE_START_MARKER = "<!-- MUMU_UPDATE_DATE_START -->"
DATE_END_MARKER = "<!-- MUMU_UPDATE_DATE_END -->"

# --- New Marker for Compatible Version ---
COMPATIBLE_VERSION_START_MARKER = "<!-- MUMU_COMPATIBLE_VERSION_START -->"
COMPATIBLE_VERSION_END_MARKER = "<!-- MUMU_COMPATIBLE_VERSION_END -->"

# --- Regular Expressions to find version and date ---
# Regex patterns to find the version and date.
# Added Chinese character equivalents for broader matching.
VERSION_PATTERNS = [
    re.compile(r"(?:Current version|当前版本)[:：\s]*V\s*([\d.]+)", re.IGNORECASE),
    re.compile(r"V\s*([\d.]+)", re.IGNORECASE) # More generic version pattern
]
DATE_PATTERNS = [
    re.compile(r"(?:Last updated|最后更新)[:：\s]*(\d{4}-\d{2}-\d{2})", re.IGNORECASE),
    re.compile(r"(\d{4}-\d{2}-\d{2})") # More generic date pattern
]

def fetch_page_content(url):
    """Fetches content from the given URL."""
    try:
        headers = {'User-Agent': USER_AGENT}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()  # Raise an exception for HTTP errors
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"Error fetching URL {url}: {e}")
        return None

def parse_content(html_content):
    """Parses HTML to find version and date using BeautifulSoup and regex."""
    if not html_content:
        return None, None

    soup = BeautifulSoup(html_content, 'html.parser')
    text_content = soup.get_text(separator='\\n') # Get all text, preserving line breaks for context

    found_version = None
    found_date = None

    # Search for version
    for pattern in VERSION_PATTERNS:
        match = pattern.search(text_content)
        if match:
            found_version = "V" + match.group(1) # Ensure 'V' prefix
            print(f"Found version: {found_version} using pattern: {pattern.pattern}")
            break
        else:
            # Try finding within <font> tags specifically if primary patterns fail
            font_tags = soup.find_all('font')
            for tag in font_tags:
                tag_text = tag.get_text()
                match = pattern.search(tag_text)
                if match:
                    found_version = "V" + match.group(1)
                    print(f"Found version in <font>: {found_version} using pattern: {pattern.pattern}")
                    break
            if found_version:
                break

    # Search for date
    for pattern in DATE_PATTERNS:
        match = pattern.search(text_content)
        if match:
            found_date = match.group(1)
            print(f"Found date: {found_date} using pattern: {pattern.pattern}")
            break
        else:
            # Try finding within <font> tags specifically
            font_tags = soup.find_all('font')
            for tag in font_tags:
                tag_text = tag.get_text()
                match = pattern.search(tag_text)
                if match:
                    found_date = match.group(1)
                    print(f"Found date in <font>: {found_date} using pattern: {pattern.pattern}")
                    break
            if found_date:
                break
                
    if not found_version:
        print("Version string not found.")
    if not found_date:
        print("Update date string not found.")

    return found_version, found_date

def update_readme(readme_path, version_str, date_str):
    """Updates the README file with the new version and date."""
    try:
        with open(readme_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        print(f"Error: README.md not found at {readme_path}")
        return False

    original_content = content
    
    # Update version
    if version_str:
        version_regex = re.compile(f"({re.escape(VERSION_START_MARKER)})(.*?)({re.escape(VERSION_END_MARKER)})", re.DOTALL)
        content = version_regex.sub(f"\\1 {version_str} \\3", content)
        print(f"Attempting to update version to: {version_str}")

    # Update compatible version line
    if version_str:
        compatible_version_regex = re.compile(f"({re.escape(COMPATIBLE_VERSION_START_MARKER)})(.*?)({re.escape(COMPATIBLE_VERSION_END_MARKER)})", re.DOTALL)
        content = compatible_version_regex.sub(f"\\1 {version_str}\\3", content) # No space needed before closing marker
        print(f"Attempting to update compatible version line to: {version_str}")

    # Update date
    if date_str:
        date_regex = re.compile(f"({re.escape(DATE_START_MARKER)})(.*?)({re.escape(DATE_END_MARKER)})", re.DOTALL)
        content = date_regex.sub(f"\\1 {date_str} \\3", content)
        print(f"Attempting to update date to: {date_str}")
    else: # If no date scraped, use current date
        current_date_str = datetime.datetime.now().strftime("%Y-%m-%d")
        date_regex = re.compile(f"({re.escape(DATE_START_MARKER)})(.*?)({re.escape(DATE_END_MARKER)})", re.DOTALL)
        content = date_regex.sub(f"\\1 {current_date_str} \\3", content)
        print(f"Scraped date not found. Using current date: {current_date_str}")


    if content == original_content:
        print("No changes made to README.md content.")
        return False # No changes were made

    try:
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"README.md updated successfully at {readme_path}")
        return True # Changes were made
    except IOError as e:
        print(f"Error writing to README.md: {e}")
        return False

if __name__ == "__main__":
    print(f"Fetching content from {MUMU_DOWNLOAD_URL}...")
    html = fetch_page_content(MUMU_DOWNLOAD_URL)

    if html:
        print("Parsing content...")
        version, date = parse_content(html)
        
        if version or date: # Proceed if at least one piece of info was found
            print(f"Attempting to update {README_PATH}...")
            if update_readme(README_PATH, version, date):
                print("README update process completed (changes made).")
            else:
                print("README update process completed (no changes or failed to write).")
        else:
            print("Could not find version or date in the webpage. README not updated.")
            # Update with current date even if version isn't found, to show the script ran
            print(f"Attempting to update {README_PATH} with current date as fallback...")
            if update_readme(README_PATH, None, None): # Pass None for version, script handles current date
                 print("README update process completed with current date (changes made).")
            else:
                print("README update process completed with current date (no changes or failed to write).")
    else:
        print("Failed to fetch webpage content. README not updated.")
        # Update with current date even if page fetch fails
        print(f"Attempting to update {README_PATH} with current date as fallback...")
        if update_readme(README_PATH, None, None): # Pass None for version, script handles current date
            print("README update process completed with current date (changes made).")
        else:
            print("README update process completed with current date (no changes or failed to write).") 