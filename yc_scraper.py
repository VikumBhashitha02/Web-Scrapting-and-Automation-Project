from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
import time
import pandas as pd
from tqdm import tqdm
from urllib.parse import urlparse

# === Setup Selenium ===
CHROMEDRIVER_PATH = "D:/Assignment/chromedriver.exe"
service = Service(CHROMEDRIVER_PATH)
driver = webdriver.Chrome(service=service)

# === Load the YC company directory ===
driver.get("https://www.ycombinator.com/companies")
time.sleep(5)

# === Scroll to load more startups ===
for _ in range(15):  # Scroll 15 times to load ~500 companies
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(3)

# === Get startup cards inside the main container ===
container = driver.find_element(By.CSS_SELECTOR, 'div._section_i9oky_163._results_i9oky_343')
cards = container.find_elements(By.CSS_SELECTOR, 'a._company_i9oky_355')

startup_data = []

# === Extract basic info from each card ===
print(f"Extracting data from {len(cards)} startup cards...")

for card in tqdm(cards[:500]):
    try:
        name = card.find_element(By.CLASS_NAME, "_coName_i9oky_470").text
        desc = card.find_element(By.CLASS_NAME, "_coDescription_i9oky_495").text

        pill_elements = card.find_elements(By.CLASS_NAME, "pill")
        batch = pill_elements[0].text if pill_elements else ""

        link = card.get_attribute("href")  # Already a full link, no need to append domain

        # Validate URL
        if not link or not link.startswith("http"):
            raise ValueError("Invalid link found!")

        startup_data.append({
            "Company Name": name,
            "Batch": batch,
            "Description": desc,
            "Link": link
        })

    except Exception as e:
        print("Error reading card:", e)

# === Visit each startup detail page for founders and LinkedIn ===
print("Visiting each startup detail page to get founders...")
for startup in tqdm(startup_data):
    try:
        driver.get(startup["Link"])
    except Exception as e:
        print("❌ Could not open link:", startup["Link"])
        print("Error:", e)
        startup["Founders"] = ""
        startup["LinkedIn URLs"] = ""
        continue

    time.sleep(2)

    try:
        founder_blocks = driver.find_elements(By.CSS_SELECTOR, 'div.ycdc-card-new')
        founder_names = []
        linkedin_urls = []

        for block in founder_blocks:
            try:
                name = block.find_element(By.CSS_SELECTOR, 'div.text-xl.font-bold').text
                founder_names.append(name)

                linkedin_link = block.find_element(By.CSS_SELECTOR, 'a[href*="linkedin.com"]')
                linkedin_url = linkedin_link.get_attribute("href")
                linkedin_urls.append(linkedin_url)
            except:
                continue

        startup["Founders"] = ", ".join(founder_names)
        startup["LinkedIn URLs"] = ", ".join(linkedin_urls)

    except Exception as e:
        startup["Founders"] = ""
        startup["LinkedIn URLs"] = ""
        print("Error getting founders:", e)

# === Save to CSV ===
df = pd.DataFrame(startup_data)
df.to_csv("yc_startups.csv", index=False)
print("✅ Data saved to yc_startups.csv")

# Close the browser
driver.quit()
