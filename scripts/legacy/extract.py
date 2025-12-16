import json

# Load data from 655.json
with open('658.json', 'r') as file:
    data = json.load(file)

# Extract "COMBINATIONS" and "DRAW DATE", convert combinations to tuples
filtered_data = [
    {
        "COMBINATIONS": tuple(map(int, entry["COMBINATIONS"].split('-'))),
        "DRAW DATE": entry["DRAW DATE"]
    }
    for entry in data
]

# Print the filtered data
print(filtered_data)

# Optionally, save the filtered data to a new JSON file
with open('combinations_date.json', 'w') as file:
    json.dump(filtered_data, file, indent=4)

print("Filtered data saved to combinations_date.json")