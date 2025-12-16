from collections import Counter

# Define the lottery draw numbers for each date
draws = [
    [55, 21, 2, 19, 28, 15],  # 12/27/2024
    [37, 45, 5, 3, 30, 56],   # 12/29/2024
    [11, 40, 20, 12, 19, 1],  # 12/31/2024
    [3, 15, 36, 22, 58, 46],  # 01/03/2025
    [36, 46, 16, 19, 23, 27], # 01/05/2025
    [41, 31, 25, 12, 40, 33], # 01/07/2025
]

# Flatten the list of draws
all_numbers = [num for draw in draws for num in draw]

# Count how many times each number appears
number_counts = Counter(all_numbers)

# Identify repeat numbers (appear more than once)
repeat_numbers = [num for num, count in number_counts.items() if count > 1]

# Identify non-repeating numbers (appear only once)
non_repeat_numbers = [num for num, count in number_counts.items() if count == 1]

# Output the results
print("Repeat Numbers:", repeat_numbers)
print("Non-Repeat Numbers:", non_repeat_numbers)