from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd
import time
import re

#Load event URLs collected using race_link_collector
event_urls_df = pd.read_csv("race_links_2024.csv")
event_urls = event_urls_df["Race Results URL"].tolist()


# Setup Selenium WebDriver
options = webdriver.ChromeOptions()
options.add_argument("--headless")  # Run without opening a browser (remove for debugging)
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36")

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=options)

# Storage for all extracted athlete results
all_athlete_results = []

# Function to extract athlete names and results from the current page
def extract_athlete_data(race_name, race_date):
    athlete_rows = driver.find_elements(By.XPATH, "//div[contains(@class, 'row mx-0 link-to-irp')]")
    
    for row in athlete_rows:
        try:
            # Extract athlete name
            name_element = row.find_element(By.XPATH, ".//a[contains(@class, 'athName athName-display')]")
            athlete_name = name_element.text.strip() if name_element else "Unknown"

            # Extract result time
            time_element = row.find_element(By.XPATH, ".//div[contains(@class, 'col-2 px-0')]")
            result_time = time_element.text.strip() if time_element else "N/A"

            # Store result
            all_athlete_results.append({
                "Race Name": race_name,
                "Race Date" : race_date,
                "Athlete Name": athlete_name,
                "Result Time": result_time
            })

        except Exception as e:
            print(f"⚠ Error extracting data for an athlete: {e}")

# Function to extract race name from the title tag
def extract_race_name():
    try:
        race_name = driver.title  # Get the page title
        return race_name
    except Exception as e:
        print(f"⚠ Error extracting race name: {e}")
        return "Unknown Race"

def extract_race_date():
    try:
        # Find all elements with the class "MuiChip-label"
        date_elements = driver.find_elements(By.CLASS_NAME, "MuiChip-label")
        
        for element in date_elements:
            text = element.text.strip()
            # Regex pattern for Month Day, Year format
            if re.match(r"^[A-Za-z]+\s\d{1,2},\s\d{4}$", text):
                return text  # Return the first match found
                
        return "2024"
    except Exception as e:
        print(f"⚠ Error extracting race date: {e}")
        return "2024"

# Function to handle pagination within each "View All" section
def handle_pagination(race_name, race_date):
    while True:
        try:
            next_button = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.XPATH, "//button[contains(text(), '>')]"))
            )

            # Scroll to and click the "Next" button
            driver.execute_script("arguments[0].scrollIntoView();", next_button)
            time.sleep(1)
            driver.execute_script("arguments[0].click();", next_button)

            time.sleep(3)  # Wait for next page to load
            extract_athlete_data(race_name, race_date)  # Extract athlete data from the new page

        except:
            print("✅ No more pages left for this section.")
            break  # Exit loop when no "Next" button is found

# Function to process an event page and extract athlete results
def extract_athlete_results(event_url):
    driver.get(event_url)
    time.sleep(5)  # Allow JavaScript to load

    print(f"🔍 Collecting event: {event_url}")

    # Click each "View All" button, extract athlete names/results, and handle pagination
    view_all_buttons = driver.find_elements(By.CLASS_NAME, "view-all-results")
    num_buttons = len(view_all_buttons)

    if num_buttons > 0:
        for index in range(num_buttons):
            try:
                # Reload event results page before each "View All" click
                driver.get(event_url)
                time.sleep(5)

                # Re-fetch all "View All" buttons
                view_all_buttons = driver.find_elements(By.CLASS_NAME, "view-all-results")

                if index < len(view_all_buttons):
                    view_all_button = view_all_buttons[index]

                    print(f"✅ Clicking 'View All' button {index + 1} of {num_buttons}")

                    # Scroll to and click the button
                    driver.execute_script("arguments[0].scrollIntoView();", view_all_button)
                    time.sleep(1)
                    driver.execute_script("arguments[0].click();", view_all_button)
                    time.sleep(3)

                    # Extract race name after clicking "View All"
                    race_name = extract_race_name()
                    race_date = extract_race_date()
                    print(f"🏁 Extracted Race Name: {race_name}")

                    # Extract athlete names and results after clicking "View All"
                    extract_athlete_data(race_name, race_date)

                    # Handle pagination for this "View All" section before returning to main event page
                    handle_pagination(race_name, race_date)

                else:
                    print(f"⚠ 'View All' button {index + 1} not found after reload.")

            except Exception as e:
                print(f"⚠ Unable to click 'View All' button {index + 1}. Error: {e}")

    else:
        print("⚠ No 'View All' buttons found.")

# Iterate through all event URLs
for event_url in event_urls:
    extract_athlete_results(event_url)

# Convert results to DataFrame
df = pd.DataFrame(all_athlete_results)

# Save to CSV
df.to_csv("2024_Triathlon_Results.csv", index=False)

# Display results
print(f"🚀 Total athletes extracted: {len(all_athlete_results)}")
print(df.head())

# Close browser
driver.quit()
