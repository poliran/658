import requests
import pandas as pd
from bs4 import BeautifulSoup

# URL of the website to scrape
url = "https://www.pcso.gov.ph/SearchLottoResult.aspx"

# Set up headers to mimic a browser
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
    "Referer": url,
}

# Create a session
session = requests.Session()

# Send a GET request with headers to see if we can get the initial page
response = session.get(url, headers=headers)
response.raise_for_status()  # Check for request errors

# Parse the HTML content using BeautifulSoup
soup = BeautifulSoup(response.text, 'html.parser')

# Find the form and extract hidden fields (like __VIEWSTATE)
viewstate = soup.find('input', {'id': '__VIEWSTATE'})['value']
eventvalidation = soup.find('input', {'id': '__EVENTVALIDATION'})['value']

# Prepare the form data for the POST request (with hidden fields)
form_data = {
    "ctl00$ctl00$cphContainer$cpContent$ddlStartMonth": "January",
    "ctl00$ctl00$cphContainer$cpContent$ddlStartDate": "1",
    "ctl00$ctl00$cphContainer$cpContent$ddlStartYear": "2015",
    "ctl00$ctl00$cphContainer$cpContent$ddlEndMonth": "August",
    "ctl00$ctl00$cphContainer$cpContent$ddlEndDay": "15",
    "ctl00$ctl00$cphContainer$cpContent$ddlEndYear": "2025",
    "ctl00$ctl00$cphContainer$cpContent$ddlSelectGame": "18",  # change for games played
    "__EVENTTARGET": "ctl00$ctl00$cphContainer$cpContent$btnSearch",
    "__VIEWSTATE": viewstate,
    "__EVENTVALIDATION": eventvalidation,
}

# Send a POST request with the form data and headers
response = session.post(url, data=form_data, headers=headers)
response.raise_for_status()  # Check for request errors

# Parse the HTML content using BeautifulSoup
soup = BeautifulSoup(response.text, 'html.parser')

# Find the table containing the lotto results
lotto_table = soup.find('table', {'class': 'Grid search-lotto-result-table'})

# Initialize a list to store the data
data = []

# Extract the headers you want to save in the CSV
headers = ['LOTTO GAME', 'COMBINATIONS', 'DRAW DATE', 'JACKPOT (PHP)', 'WINNERS']

# Loop through each row in the table (skip the header row)
for row in lotto_table.find_all('tr')[1:]:
    cols = row.find_all('td')
    lotto_game = cols[0].text.strip()
    combinations = cols[1].text.strip()
    draw_date = cols[2].text.strip()
    jackpot = cols[3].text.strip()
    winners = cols[4].text.strip()
    # Append the extracted data to the list
    data.append([lotto_game, combinations, draw_date, jackpot, winners])

# Convert the data into a pandas DataFrame
df = pd.DataFrame(data, columns=headers)

# Save the DataFrame to a CSV file
df.to_csv('658.txt', index=False)
df.to_json('658.json', orient='records', indent=4)

print("Data has been saved to 658.txt & 658.json")
