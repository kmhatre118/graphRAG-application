from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd
import time

# Search results page for list of races
search_url = "[Input URL to search]"

# Setup Selenium WebDriver
options = webdriver.ChromeOptions()
options.add_argument("--headless")  # Run without opening a browser (remove for debugging)
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36")

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=options)

# Load the search results page
driver.get(search_url)
time.sleep(5)  # Allow time for JavaScript to load content

# Dynamically find and click "Load More" link until all results are loaded
while True:
    try:
        # Locate "Load More" div
        load_more_link = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.ID, "load-more-link"))
        )

        # Scroll to the "Load More" div before clicking
        driver.execute_script("arguments[0].scrollIntoView();", load_more_link)
        time.sleep(1)

        # Click "Load More" using JavaScript to avoid interception issues
        driver.execute_script("arguments[0].click();", load_more_link)

        time.sleep(3)  # Wait for results to load
        print("✅ Clicked 'Load More' link.")

    except:
        print("✅ No more 'Load More' link found. All results loaded.")
        break  # Exit loop when no more "Load More" exists

# Extract 2024 race result links
race_results_links = []
year_links = driver.find_elements(By.XPATH, "//a[contains(@class, 'year-link')]")

for link in year_links:
    link_text = link.text.strip()
    
    if "2024" in link_text:  # Ensure it's for the year 2024 (even if extra text exists)
        race_results_links.append(link.get_attribute("href"))
        print(f"✅ Found 2024 results: {link.get_attribute('href')}")

# Convert race results links to DataFrame
df = pd.DataFrame(race_results_links, columns=["Race Results URL"])

# Save to CSV
df.to_csv("race_links_2024.csv", index=False)

# Display results
print(f"🚀 Total 2024 race results extracted: {len(race_results_links)}")
print(df.head())

# Close browser
driver.quit()
