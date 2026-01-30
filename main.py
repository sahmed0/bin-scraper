import time
import re
import os
import json
from datetime import datetime
from ics import Calendar, Event
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options

# --- CONFIGURATION ---
# Load users from GitHub Environment Variables (Secrets)
# If running on laptop, use a dummy list.
users_env = os.environ.get('BIN_USERS')

if users_env:
    try:
        USERS = json.loads(users_env)
        print("Successfully loaded USERS from Secret.")
    except json.JSONDecodeError:
        print("Error: Could not decode BIN_USERS secret. Check your JSON format.")
        USERS = []
else:
    print("Warning: No BIN_USERS secret found. Using dummy data.")
    USERS = [{"name": "test_user", "postcode": "BL9 0RS", "house": "1"}]

# --- BROWSER SETUP ---
def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")

    prefs = {
        "profile.managed_default_content_settings.images": 2,
        "profile.managed_default_content_settings.stylesheets": 2,
        "profile.managed_default_content_settings.fonts": 2
    }
    chrome_options.add_experimental_option("prefs", prefs)
    chrome_options.page_load_strategy = 'eager'

    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=chrome_options)

def clean_date_string(date_str):
    return re.sub(r'(\d+)(st|nd|rd|th)', r'\1', date_str)

def get_bin_dates(driver, postcode, house_number):
    print(f"--- Searching for {postcode}, House {house_number} ---")
    found_events = []

    try:
        url = "https://www.bury.gov.uk/waste-and-recycling/bin-collection-days-and-alerts"
        driver.get(url)
        wait = WebDriverWait(driver, 10)

        # 1. Reject Cookies
        try:
            # We target the reject button directly by its ID
            reject_btn = WebDriverWait(driver, 2).until(EC.element_to_be_clickable(
                (By.ID, "ccc-reject-settings")
            ))
            driver.execute_script("arguments[0].click();", reject_btn)
        except:
            pass

        # 2. Postcode
        postcode_input = wait.until(EC.visibility_of_element_located((By.ID, "postcode")))
        postcode_input.clear()
        postcode_input.send_keys(postcode)

        # 3. Search
        search_btn = driver.find_element(By.CSS_SELECTOR, "div.form-buttons button[type='submit']")
        driver.execute_script("arguments[0].click();", search_btn)

        # 4. Address Selection
        buttons = wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, "address__listButton")))

        address_found = False
        target_house = house_number.lower()

        for btn in buttons:
            if target_house in btn.text.lower():
                driver.execute_script("arguments[0].click();", btn)
                address_found = True
                break

        if not address_found:
            print(f"Address '{house_number}' not found for {postcode}!")
            return []

        # 5. Results
        date_elements = wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, "bin__date")))

        for date_el in date_elements:
            full_text = driver.execute_script("return arguments[0].parentNode.innerText;", date_el)
            lines = full_text.split('\n')
            bin_name = "Bin Collection"
            date_text = ""

            for line in lines:
                if "bin" in line.lower():
                    bin_name = line.strip()
                elif any(char.isdigit() for char in line):
                    date_text = line.strip()

            if date_text:
                try:
                    clean_date = clean_date_string(date_text)
                    dt_object = datetime.strptime(clean_date, "%A %d %B %Y")
                    found_events.append({"name": bin_name, "date": dt_object})
                    print(f"Found: {bin_name} on {dt_object.date()}")
                except ValueError:
                    continue

    except Exception as e:
        print(f"Error scraping {postcode}: {e}")
        
    return found_events

def get_emoji(bin_name):
    name = bin_name.lower()
    if "grey" in name: return "⬛"
    if "blue" in name: return "🟦"
    if "brown" in name: return "🟫"
    if "green" in name: return "🟩"
    return "🗑️"

def generate_calendar(events, filename):
    c = Calendar()
    for item in events:
        e = Event()
        e.name = f"{get_emoji(item['name'])} {item['name']}"
        e.begin = item['date']
        e.make_all_day()
        e.description = "Generated by Sajid's code."
        c.events.add(e)
        
    with open(filename, 'w', encoding='utf-8') as f:
        f.writelines(c)
    print(f"Calendar saved to {filename}")

if __name__ == "__main__":
    if not USERS:
        print("No users configured. Exiting.")
        exit()

    print("Starting Browser...")
    driver = setup_driver()

    try:
        for user in USERS:
            print(f"\nProcessing {user['name']}...")
            events = get_bin_dates(driver, user['postcode'], user['house'])
            
            if events:
                filename = f"{user['name']}.ics"
                generate_calendar(events, filename)
            
            time.sleep(2)
    finally:
        print("\nClosing Browser...")
        driver.quit()