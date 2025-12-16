import requests
import pandas as pd
from bs4 import BeautifulSoup
import time
import urllib3

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def scrape_pcso_data():
    # URL of the website to scrape
    url = "https://www.pcso.gov.ph/SearchLottoResult.aspx"
    
    # Enhanced headers to better mimic a real browser
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Cache-Control": "max-age=0"
    }
    
    # Create a session with retry strategy
    session = requests.Session()
    session.headers.update(headers)
    
    try:
        print("Attempting to access PCSO website...")
        
        # First, try to get the initial page
        response = session.get(url, timeout=30, verify=False)
        
        if response.status_code == 403:
            print("Access denied (403). The website may be blocking automated requests.")
            print("This could be due to:")
            print("- Anti-bot protection")
            print("- Geographic restrictions")
            print("- Rate limiting")
            return False
            
        response.raise_for_status()
        print(f"Successfully accessed the website (Status: {response.status_code})")
        
        # Parse the HTML content
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Check if we can find the expected form elements
        viewstate_element = soup.find('input', {'id': '__VIEWSTATE'})
        eventvalidation_element = soup.find('input', {'id': '__EVENTVALIDATION'})
        
        if not viewstate_element or not eventvalidation_element:
            print("Could not find required form elements. The page structure may have changed.")
            return False
            
        viewstate = viewstate_element['value']
        eventvalidation = eventvalidation_element['value']
        
        print("Found required form elements, preparing search...")
        
        # Add delay before POST request
        time.sleep(3)
        
        # Prepare the form data for the POST request
        form_data = {
            "ctl00$ctl00$cphContainer$cpContent$ddlStartMonth": "January",
            "ctl00$ctl00$cphContainer$cpContent$ddlStartDate": "1",
            "ctl00$ctl00$cphContainer$cpContent$ddlStartYear": "2015",
            "ctl00$ctl00$cphContainer$cpContent$ddlEndMonth": "October",
            "ctl00$ctl00$cphContainer$cpContent$ddlEndDay": "6",
            "ctl00$ctl00$cphContainer$cpContent$ddlEndYear": "2025",
            "ctl00$ctl00$cphContainer$cpContent$ddlSelectGame": "18",
            "__EVENTTARGET": "ctl00$ctl00$cphContainer$cpContent$btnSearch",
            "__VIEWSTATE": viewstate,
            "__EVENTVALIDATION": eventvalidation,
        }
        
        # Update headers for POST request
        post_headers = headers.copy()
        post_headers.update({
            "Content-Type": "application/x-www-form-urlencoded",
            "Origin": "https://www.pcso.gov.ph",
            "Referer": url,
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "same-origin"
        })
        
        # Send POST request
        response = session.post(url, data=form_data, headers=post_headers, timeout=30, verify=False)
        response.raise_for_status()
        
        print("Search request successful, parsing results...")
        
        # Parse the results
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find the table containing the lotto results
        lotto_table = soup.find('table', {'class': 'Grid search-lotto-result-table'})
        
        if not lotto_table:
            print("Could not find results table. The search may have returned no results or the page structure changed.")
            return False
        
        # Extract data
        data = []
        headers_list = ['LOTTO GAME', 'COMBINATIONS', 'DRAW DATE', 'JACKPOT (PHP)', 'WINNERS']
        
        # Loop through each row in the table (skip the header row)
        rows = lotto_table.find_all('tr')[1:]
        
        for row in rows:
            cols = row.find_all('td')
            if len(cols) >= 5:
                data.append([
                    cols[0].text.strip(),
                    cols[1].text.strip(),
                    cols[2].text.strip(),
                    cols[3].text.strip(),
                    cols[4].text.strip()
                ])
        
        if not data:
            print("No data found in the results table.")
            return False
        
        # Convert to DataFrame and save
        df = pd.DataFrame(data, columns=headers_list)
        df.to_csv('658.txt', index=False)
        df.to_json('658.json', orient='records', indent=4)
        
        print(f"Success! Data has been saved to 658.txt & 658.json")
        print(f"Total records extracted: {len(data)}")
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"Network error: {e}")
        return False
    except Exception as e:
        print(f"Unexpected error: {e}")
        return False

if __name__ == "__main__":
    scrape_pcso_data()
