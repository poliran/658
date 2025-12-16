import csv

# Open the input file (assuming it's a text file with the given format)
with open('658.txt', 'r') as infile:
    # Read the content using a CSV reader
    reader = csv.DictReader(infile)
    
    # Prepare data to write to output CSV
    extracted_data = [(row['DRAW DATE'], row['COMBINATIONS']) for row in reader]

# Write the extracted data to a new CSV file
with open('combinations.csv', 'w', newline='') as outfile:
    writer = csv.writer(outfile)
    # Write header
    writer.writerow(['DRAW DATE', 'COMBINATIONS'])
    # Write data rows
    writer.writerows(extracted_data)

print("Extraction complete. Data saved to 'combinations.csv'.")