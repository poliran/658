import csv
from datetime import datetime

# Read data from swertres.txt
with open('658.txt', 'r', newline='') as infile:
    reader = csv.reader(infile, delimiter='\t')
    header = next(reader)  # Skip header
    data = list(reader)

# Sort data based on the draw date (index 2)
data_sorted = sorted(data, key=lambda x: datetime.strptime(x[2], '%m/%d/%Y'), reverse=True)

# Write sorted data back to a new file or overwrite the existing file
with open('sorted_658.txt', 'w', newline='') as outfile:
    writer = csv.writer(outfile, delimiter='\t')
    writer.writerow(header)
    writer.writerows(data_sorted)

print("File sorted_649.txt created with data sorted from latest to oldest draw date.")
