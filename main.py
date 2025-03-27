from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import json
import time

# Setup Chrome options
options = Options()
options.headless = False  # Set to True if you don't want the browser window to open

# Set path to chromedriver
driver_path = '/Users/parikshitsingh/Downloads/chromedriver-mac-arm64/chromedriver'

# Initialize WebDriver
driver = webdriver.Chrome(service=Service(driver_path), options=options)

# Visit the main website
url = 'https://m.freightbook.net/'
driver.get(url)

# Wait for the page to load
time.sleep(1)  # Adjust this sleep time based on your internet speed

# Prepare a list to store the scraped data
forwarder_data = []

# Function to close the GDPR banner if it exists
def close_gdpr_banner():
    try:
        gdpr_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Yes, Got It')]")
        gdpr_button.click()  # Close the GDPR banner
        time.sleep(0.5)  # Wait a bit after clicking the button
    except Exception as e:
        print("GDPR banner not found or already closed.")


# Function to wait for the page to load the forwarders
def wait_for_page_load():
    try:
        WebDriverWait(driver, 3).until(
            EC.presence_of_all_elements_located((By.XPATH, "//div[@class='business-card vcard']"))
        )
    except Exception as e:
        print("Error waiting for page to load:", e)


# Keep track of the countries we've already visited
visited_countries = set()

# Iterate through countries in the dropdown
while True:
    # Re-fetch the country dropdown in case the DOM has changed
    country_dropdown = driver.find_element(By.ID, 'company-search-country')
    countries = country_dropdown.find_elements(By.TAG_NAME, 'option')

    # Iterate through each country
    for country_option in countries:
        country_name = country_option.text
        country_value = country_option.get_attribute('value')

        # Skip the "Search by country..." option and countries we've already visited
        if country_value == "0" or country_name in visited_countries:
            continue

        print(f"Scraping forwarders for {country_name}...")

        # Mark this country as visited
        visited_countries.add(country_name)

        # Select the country and submit the form
        country_dropdown.send_keys(country_name)

        # Wait for the search results page to load
        wait_for_page_load()

        # Collect forwarder links on this page
        forwarders = driver.find_elements(By.XPATH, "//div[@class='search-results']//a[contains(@href, '/member/')]")

        unique_forwarders = set()
        for forwarder in forwarders:
            forwarder_url = forwarder.get_attribute('href')
            unique_forwarders.add(forwarder_url)

        print(f"Found {len(unique_forwarders)} unique forwarders for {country_name}.")  # Debugging line

        # Iterate through each forwarder and scrape details
        for forwarder_url in unique_forwarders:
            print(f"Scraping {forwarder_url}...")

            try:
                # Visit the forwarder's full profile page
                driver.get(forwarder_url)
                time.sleep(3)  # Wait for the profile page to load

                # Scrape forwarder details dynamically
                forwarder_details = {}
                forwarder_details['name'] = driver.find_element(By.XPATH, "//div[@class='col-sm-12 value fn org']/h2").text

                # Extract key-value pairs from the first table (address, country, phone, etc.)
                rows = driver.find_elements(By.XPATH, "//div[contains(@class, 'row')]")
                for row in rows:
                    try:
                        # Extract the label (key) and value dynamically
                        label = row.find_element(By.XPATH, ".//div[contains(@class, 'heading')]").text.strip()
                        value = row.find_element(By.XPATH, ".//div[contains(@class, 'value')]").text.strip()
                        forwarder_details[label] = value
                    except Exception as e:
                        continue  # Skip any row that doesn't contain both a key and value

                # Scrape additional data from the second table (year, owner, services, etc.)
                additional_rows = driver.find_elements(By.XPATH, "//div[@class='col-xs-12 more-info']//div[@class='row']")
                for row in additional_rows:
                    try:
                        label = row.find_element(By.XPATH, ".//div[contains(@class, 'heading')]").text.strip()
                        value = row.find_element(By.XPATH, ".//div[contains(@class, 'value')]").text.strip()
                        forwarder_details[label] = value
                    except Exception as e:
                        continue  # Skip any row that doesn't contain both a key and value

                # Append to forwarder data
                forwarder_data.append(forwarder_details)

            except Exception as e:
                print(f"Error scraping {forwarder_url}: {e}")
                continue

        # Navigate back to the search results page (or reload the homepage to process the next country)
        driver.get(url)
        time.sleep(3)  # Wait for the page to load again
        break

    # Stop if all countries have been processed
    if len(visited_countries) == len(countries) - 1:  # Exclude the "Search by country..." option
        break

# Save the collected data as JSON
with open('forwarders_data.json', 'w') as json_file:
    json.dump(forwarder_data, json_file, indent=4)

# Close the browser
driver.quit()

print("Data has been successfully scraped and saved to 'forwarders_data.json'")
