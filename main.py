import time
import re
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
USERS = [
    {"name": "Sajid", "postcode": "BL9 0RS", "house": "70"},
    {"name": "Shabaz", "postcode": "BL9 9HS", "house": "108"}
]


def clean_date_string(date_str):
    return re.sub(r'(\d+)(st|nd|rd|th)', r'\1', date_str)


def get_bin_dates(postcode, house_number):
    print(f"--- Starting Scraper for {postcode} ---")

    # 1. OPTIMISATION: Setup Chrome to be minimal and fast
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")

    # Block images, CSS, and fonts to save bandwidth and time
    prefs = {
        "profile.managed_default_content_settings.images": 2,
        "profile.managed_default_content_settings.stylesheets": 2,
        "profile.managed_default_content_settings.fonts": 2
    }
    chrome_options.add_experimental_option("prefs", prefs)

    # 'eager' means: "Don't wait for the whole page to load, just give me the HTML"
    chrome_options.page_load_strategy = 'eager'

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)

    found_events = []

    try:
        url = "https://www.bury.gov.uk/waste-and-recycling/bin-collection-days-and-alerts"
        driver.get(url)
        wait = WebDriverWait(driver, 10)  # Reduced timeout since we are moving faster

        # 2. Handle Cookie Banner (Fast Check)
        try:
            # Wait a max of 3 seconds for the banner, if not there, move on immediately
            accept_btn = WebDriverWait(driver, 3).until(EC.element_to_be_clickable(
                (By.XPATH,
                 "//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'accept')]")
            ))
            driver.execute_script("arguments[0].click();", accept_btn)
        except:
            pass  # No banner? Great, faster for us.

        # 3. Enter Postcode
        postcode_input = wait.until(EC.visibility_of_element_located((By.ID, "postcode")))
        postcode_input.send_keys(postcode)

        # 4. Click Search
        search_btn = driver.find_element(By.CSS_SELECTOR, "div.form-buttons button[type='submit']")
        driver.execute_script("arguments[0].click();", search_btn)

        # 5. Select Address (Fast Loop)
        # We assume the address list loads quickly.
        buttons = wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, "address__listButton")))

        address_found = False
        # Create a lower-case version of house number once for speed
        target_house = house_number.lower()

        for btn in buttons:
            if target_house in btn.text.lower():
                driver.execute_script("arguments[0].click();", btn)
                address_found = True
                break

        if not address_found:
            print("Address not found!")
            return []

        # 6. Get Results
        date_elements = wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, "bin__date")))

        for date_el in date_elements:
            # Use JS to get parent text instantly (faster than Selenium object navigation)
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

                    found_events.append({
                        "name": bin_name,
                        "date": dt_object
                    })
                    print(f"Found: {bin_name} on {dt_object.date()}")
                except ValueError:
                    continue

    except Exception as e:
        print(f"Error: {e}")
    finally:
        driver.quit()

    return found_events

def get_emoji(bin_name):
    """Returns a colored square based on the bin name."""
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
        # We call the helper function here
        e.name = f"{get_emoji(item['name'])} {item['name']}"
        e.begin = item['date']
        e.make_all_day()
        e.description = "Generated by my Python Robot."
        c.events.add(e)
        
    # Save to the specific filename passed to the function (e.g., 'ahmed.ics')
    with open(filename, 'w', encoding='utf-8') as f:
        f.writelines(c)
    print(f"Calendar saved to {filename}")

if __name__ == "__main__":
    # We loop through the list of friends
    for user in USERS:
        print(f"Processing {user['name']}...")
        
        # Run the scraper for this specific friend
        events = get_bin_dates(user['postcode'], user['house'])
        
        if events:
            # Create a unique filename for them (e.g., 'ahmed.ics')
            filename = f"{user['name']}.ics"
            
            # Generate their specific calendar
            # Note: We need to modify generate_calendar to accept a filename now
            c = Calendar()
            for item in events:
                e = Event()
                e.name = f"🚮 {item['name']}"
                e.begin = item['date']
                e.make_all_day()
                c.events.add(e)
                
            with open(filename, 'w', encoding='utf-8') as f:
                f.writelines(c)
            print(f"Saved {filename}")
            
        # IMPORTANT: Wait 30 seconds between people so we don't crash the council website
        time.sleep(30)
