import pandas as pd
from bs4 import BeautifulSoup
import os

def parse_saved_html(html_file_path):
    """
    Parse PCSO lottery results from a manually saved HTML file
    
    Instructions:
    1. Go to https://www.pcso.gov.ph/SearchLottoResult.aspx
    2. Set your search parameters (dates, game type)
    3. Click Search
    4. Save the results page as HTML (Ctrl+S or Cmd+S)
    5. Run this script with the saved HTML file
    """
    
    if not os.path.exists(html_file_path):
        print(f"HTML file not found: {html_file_path}")
        print("\nTo use this script:")
        print("1. Visit https://www.pcso.gov.ph/SearchLottoResult.aspx")
        print("2. Set your search parameters")
        print("3. Click Search")
        print("4. Save the page as 'pcso_results.html'")
        print("5. Run this script again")
        return False
    
    try:
        # Read the HTML file
        with open(html_file_path, 'r', encoding='utf-8') as file:
            html_content = file.read()
        
        # Parse with BeautifulSoup
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Find the results table
        lotto_table = soup.find('table', {'class': 'Grid search-lotto-result-table'})
        
        if not lotto_table:
            print("Could not find results table in the HTML file.")
            print("Make sure you saved the results page after clicking Search.")
            return False
        
        # Extract data
        data = []
        headers = ['LOTTO GAME', 'COMBINATIONS', 'DRAW DATE', 'JACKPOT (PHP)', 'WINNERS']
        
        rows = lotto_table.find_all('tr')[1:]  # Skip header row
        
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
            print("No data found in the HTML file.")
            return False
        
        # Save to files
        df = pd.DataFrame(data, columns=headers)
        df.to_csv('658.txt', index=False)
        df.to_json('658.json', orient='records', indent=4)
        
        print(f"Success! Extracted {len(data)} records")
        print("Data saved to 658.txt and 658.json")
        
        # Show first few records
        print("\nFirst 5 records:")
        print(df.head().to_string(index=False))
        
        return True
        
    except Exception as e:
        print(f"Error parsing HTML file: {e}")
        return False

if __name__ == "__main__":
    # Try to parse a saved HTML file
    html_file = "pcso_results.html"
    parse_saved_html(html_file)
