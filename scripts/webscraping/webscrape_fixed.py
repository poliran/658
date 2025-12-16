from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import sys

def scrape_latest():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    
    try:
        url = "https://www.pcso.gov.ph/SearchLottoResult.aspx"
        driver.get(url)
        print(f"Successfully accessed: {url}")
        print(f"Page title: {driver.title}")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "latest":
        scrape_latest()
    else:
        print("Usage: python webscrape_fixed.py latest")
