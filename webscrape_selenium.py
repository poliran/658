from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd
import time

# Set up Chrome options
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

# Initialize the driver with webdriver-manager
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)

try:
    # Navigate to the website
    url = "https://www.pcso.gov.ph/SearchLottoResult.aspx"
    driver.get(url)
    
    # Wait for page to load
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "ctl00_ctl00_cphContainer_cpContent_ddlSelectGame"))
    )
    
    # Select the game (18 for 6/58)
    game_dropdown = Select(driver.find_element(By.ID, "ctl00_ctl00_cphContainer_cpContent_ddlSelectGame"))
    game_dropdown.select_by_value("18")
    
    # Set date range
    start_month = Select(driver.find_element(By.ID, "ctl00_ctl00_cphContainer_cpContent_ddlStartMonth"))
    start_month.select_by_visible_text("January")
    
    start_date = Select(driver.find_element(By.ID, "ctl00_ctl00_cphContainer_cpContent_ddlStartDate"))
    start_date.select_by_visible_text("1")
    
    start_year = Select(driver.find_element(By.ID, "ctl00_ctl00_cphContainer_cpContent_ddlStartYear"))
    start_year.select_by_visible_text("2015")
    
    end_month = Select(driver.find_element(By.ID, "ctl00_ctl00_cphContainer_cpContent_ddlEndMonth"))
    end_month.select_by_visible_text("October")
    
    end_day = Select(driver.find_element(By.ID, "ctl00_ctl00_cphContainer_cpContent_ddlEndDay"))
    end_day.select_by_visible_text("6")
    
    end_year = Select(driver.find_element(By.ID, "ctl00_ctl00_cphContainer_cpContent_ddlEndYear"))
    end_year.select_by_visible_text("2025")
    
    # Click search button
    search_button = driver.find_element(By.ID, "ctl00_ctl00_cphContainer_cpContent_btnSearch")
    search_button.click()
    
    # Wait for results to load
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME, "search-lotto-result-table"))
    )
    
    # Find the results table
    table = driver.find_element(By.CLASS_NAME, "search-lotto-result-table")
    rows = table.find_elements(By.TAG_NAME, "tr")
    
    # Extract data
    data = []
    headers = ['LOTTO GAME', 'COMBINATIONS', 'DRAW DATE', 'JACKPOT (PHP)', 'WINNERS']
    
    for row in rows[1:]:  # Skip header row
        cols = row.find_elements(By.TAG_NAME, "td")
        if len(cols) >= 5:
            data.append([
                cols[0].text.strip(),
                cols[1].text.strip(),
                cols[2].text.strip(),
                cols[3].text.strip(),
                cols[4].text.strip()
            ])
    
    # Create DataFrame and save
    df = pd.DataFrame(data, columns=headers)
    df.to_csv('658.txt', index=False)
    df.to_json('658.json', orient='records', indent=4)
    
    print(f"Data has been saved to 658.txt & 658.json")
    print(f"Total records: {len(data)}")
    
except Exception as e:
    print(f"Error: {e}")
    
finally:
    driver.quit()
