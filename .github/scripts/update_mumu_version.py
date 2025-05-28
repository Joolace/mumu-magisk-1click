import re
import requests
# from bs4 import BeautifulSoup # No longer needed for parsing/XPath
import datetime
import lxml.html # Import lxml for XPath

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

# --- Regular Expressions for parsing extracted text ---
# Refined regex to extract version number (e.g., V 4.1.29 -> 4.1.29) from the found element text
VERSION_TEXT_PATTERN = re.compile(r"V\s*([\d.]+)", re.IGNORECASE)

# Existing patterns for date scraping (as no specific date XPath/selector provided)
DATE_PATTERNS = [
    re.compile(r"(?:Last updated|最后更新)[:：\s]*(\d{4}-\d{2}-\d{2})", re.IGNORECASE),
    re.compile(r"(\d{4}-\d{2}-\d{2})") # More generic date pattern
]

# --- XPath for version element ---
VERSION_XPATH = "/html/body/div[2]/div/section/div[1]/a/div[2]/div[2]/div[4]/font/font"

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
    """Parses HTML to find version and date using XPath and regex."""
    if not html_content:
        return None, None

    # Use lxml to parse HTML
    try:
        tree = lxml.html.fromstring(html_content)
    except Exception as e:
        print(f"Error parsing HTML with lxml: {e}")
        return None, None

    found_version = None
    found_date = None

    # --- Search for version using XPath ---
    print(f"Attempting to find version using XPath: {VERSION_XPATH}")
    version_elements = tree.xpath(VERSION_XPATH)
    
    if version_elements:
        # XPath can return a list; we expect only one element for this specific path
        version_element = version_elements[0]
        element_text = version_element.text_content().strip()
        print(f"Found potential version text using XPath: '{element_text}'")
        
        # Use regex to extract the version number from the text
        version_match = VERSION_TEXT_PATTERN.search(element_text)
        if version_match:
            found_version = "V" + version_match.group(1) # Ensure 'V' prefix
            print(f"Extracted version: {found_version}")
        else:
            print(f"Could not extract version number from text: '{element_text}'")
    else:
        print(f"Version element not found using XPath: {VERSION_XPATH}")

    # --- Search for date using existing patterns (no specific selector/XPath provided) ---
    # Convert lxml tree back to string to use existing date patterns that search text content
    text_content = lxml.html.tostring(tree, encoding='unicode', method='text')

    for pattern in DATE_PATTERNS:
        match = pattern.search(text_content)
        if match:
            found_date = match.group(1)
            print(f"Found date: {found_date} using pattern: {pattern.pattern}")
            break

    if not found_version:
        print("Version string not found using XPath or text patterns.")
    if not found_date:
        print("Update date string not found using text patterns.")

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
        print(f"Attempting to update main version to: {version_str}")

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
            print("Could not find version or date in the webpage. README not updated based on scrape results.")
            # Update with current date even if version/date isn't found, to show the script ran
            print(f"Attempting to update {README_PATH} with current date as fallback...")
            # Call update_readme with None for version, it will still update the date
            if update_readme(README_PATH, None, None): 
                 print("README update process completed with current date fallback (changes made).")
            else:
                print("README update process completed with current date fallback (no changes or failed to write).")
    else:
        print("Failed to fetch webpage content. README not updated.")
        # Update with current date even if page fetch fails
        print(f"Attempting to update {README_PATH} with current date as fallback...")
        # Call update_readme with None for version, it will still update the date
        if update_readme(README_PATH, None, None): 
            print("README update process completed with current date fallback (changes made).")
        else:
            print("README update process completed with current date fallback (no changes or failed to write).") 