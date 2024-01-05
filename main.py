import requests
import re
import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import json
import time

# Load the original CSV
data = pd.read_csv('test.csv', encoding='windows-1252')


# Add a new column for website year if it doesn't exist
if 'Website Year' not in data.columns:
    data['Website Year'] = None

# Setup Selenium WebDriver with Service
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
service = Service(executable_path='chromedriver.exe')
driver = webdriver.Chrome(service=service, options=chrome_options)


# Function to scrape copyright year using requests


def scrape_with_requests(url):
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            text = soup.get_text()
            match = re.search(r'©\s*(20[0-2]\d)', text)
            if match:
                return match.group(1)  # Returns only the year part
            else:
                return "No year found"  # No match found
    except Exception as e:
        print(f"Error with URL {url}: {str(e)}")
    return "error"  # Error occurred


def scrape_with_selenium(url):
    try:
        driver.get(url)
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        driver.execute_script(
            "window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(5)  # Wait for any lazy-loaded elements to load
        body_text = driver.find_element(By.TAG_NAME, "body").text
        match = re.search(r'©\s*(20[0-2]\d)', body_text)
        if match:
            return match.group(1)  # Returns only the year part
        else:
            return "No year found"
    except Exception as e:
        print(f"Error with Selenium for URL {url}: {str(e)}")
    return "error"


# Dictionary to store results
results = {}
failed_attempts = {}

# Process each URL and update DataFrame
for index, row in data.iterrows():
    url = row['organization_primary_domain']
    if not isinstance(url, str) or pd.isna(url):
        continue

    full_url = 'https://' + url if not url.startswith('http') else url
    print(f"Processing URL: {full_url}")

    year = scrape_with_requests(full_url)
    if year == "No year found" or year == "error":
        print(f"Using Selenium for URL: {full_url}")
        year = scrape_with_selenium(full_url)

    # Update DataFrame with the year
    data.at[index, 'Website Year'] = year if year not in [
        "error", "No year found"] else None

    # Save the updated DataFrame to the CSV file after each URL is processed
    data.to_csv('test.csv', index=False)
    print(f"CSV file updated for {full_url}")

driver.quit()
print("All URLs processed. CSV file is fully updated.")
