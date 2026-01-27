# 🗑️ Bury Council Bin Automator

**Never miss bin day again.** This tool automatically scrapes the [Bury Council](https://www.bury.gov.uk) website and syncs the collection dates directly to your phone's calendar.

It runs entirely in the cloud (GitHub Actions) and updates weekly, so you never have to maintain it.

### ✨ Features

* **Zero Maintenance:** Runs automatically every Monday morning.
* **Smart Calendars:** Generates `.ics` files compatible with iPhone (iOS), Google Calendar, and Outlook.
* **Colour Coded:** Events are auto-tagged with emojis for quick recognition:
* ⬛ Grey Bin
* 🟦 Blue Bin
* 🟫 Brown Bin
* 🟩 Green Bin


* **Multi-User:** Supports tracking multiple addresses (great for friends & family).

---

### 🚀 How It Works

1. **Scrape:** A Python script (`main.py`) launches a headless browser to check the council website for specific addresses.
2. **Generate:** It creates an iCalendar (`.ics`) file for each user found.
3. **Host:** GitHub stores these files publicly.
4. **Sync:** Your phone subscribes to the file URL and updates automatically when the script runs.

---

### 🛠️ Configuration

To add yourself or friends, simply edit the `USERS` list in `main.py`:

```python
USERS = [
    {"name": "a", "postcode": "BL9 9BB", "house": "1"},
    {"name": "b",   "postcode": "BL9 5AB", "house": "24"}
]

```

### 📱 How to Subscribe

Once the script has run, find your file in the file list (e.g., `a.ics`), click **Raw**, and copy the URL.

* **iPhone:** Settings > Calendar > Accounts > Add Account > Subscribed Calendar > Paste URL.
* **Google Calendar:** "Other calendars" (+) > From URL > Paste URL.

---

### 💻 Tech Stack

* **Python 3.9**
* **Selenium** (Web Scraping)
* **ICS** (Calendar Generation)
* **GitHub Actions** (CI/CD Automation)
