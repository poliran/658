import random
import unittest

# Define the range of numbers (1 to 58) and the repeat numbers
all_numbers = set(range(1, 59))  # All numbers from 1 to 58
repeat_numbers = {55, 21, 2, 28, 37, 45, 5, 30, 56, 11, 20, 1, 22, 58, 16, 23, 27, 41, 31, 25, 33}  # Set of numbers that are repeats
non_repeat_numbers = list(all_numbers - repeat_numbers)  # Numbers excluding repeats

# Step 2: Generate three sets of random combinations without repeat numbers
no_repeat_combinations = [random.sample(non_repeat_numbers, 6) for _ in range(2)]  # 6 numbers selected from non-repeat numbers

# Step 3: Generate two sets of random combinations including one repeat number
with_repeat_combinations = []
for _ in range(2):
    repeat_num = random.choice(list(repeat_numbers))  # Choose one repeat number randomly
    combination = [repeat_num] + random.sample(non_repeat_numbers, 5)  # Choose 5 non-repeated numbers
    with_repeat_combinations.append(combination)  # Store the combination

# Step 4: Generate two sets of random combinations including two repeat number
with_two_repeat_combinations = []
for _ in range(2):
    repeat_num = random.choice(list(repeat_numbers))  # Choose one repeat number randomly
    combination = [repeat_num] + random.sample(non_repeat_numbers, 5)  # Choose 5 non-repeated numbers
    with_two_repeat_combinations.append(combination)  # Store the combination

# Print the results
print("No Repeat Combinations:", no_repeat_combinations)
print("With Repeat Combinations:", with_repeat_combinations)
print("With Two Repeat Combinations:", with_two_repeat_combinations)

class TestCombinations(unittest.TestCase):
    def setUp(self):
        self.all_numbers = set(range(1, 59))
        self.repeat_numbers = {55, 21, 2, 28, 37, 45, 5, 30, 56, 11, 20, 1, 22, 58, 16, 23, 27, 41, 31, 25, 33}
        self.non_repeat_numbers = list(self.all_numbers - self.repeat_numbers)

    def test_no_repeat_combinations(self):
        no_repeat_combinations = [random.sample(self.non_repeat_numbers, 6) for _ in range(2)]
        for combination in no_repeat_combinations:
            self.assertEqual(len(combination), 6)
            self.assertTrue(all(num in self.non_repeat_numbers for num in combination))
            self.assertEqual(len(set(combination)), len(combination))  # Ensure no duplicates

    def test_with_repeat_combinations(self):
        with_repeat_combinations = []
        for _ in range(2):
            repeat_num = random.choice(list(self.repeat_numbers))
            combination = [repeat_num] + random.sample(self.non_repeat_numbers, 5)
            with_repeat_combinations.append(combination)
        for combination in with_repeat_combinations:
            self.assertEqual(len(combination), 6)
            self.assertTrue(any(num in self.repeat_numbers for num in combination))  # At least one repeat number
            self.assertTrue(all(num in self.non_repeat_numbers or num == combination[0] for num in combination))  # Valid numbers

    def test_with_two_repeat_combinations(self):
        with_two_repeat_combinations = []
        for _ in range(2):
            repeat_nums = random.sample(list(self.repeat_numbers), 2)  # Choose two repeat numbers
            combination = repeat_nums + random.sample(self.non_repeat_numbers, 4)
            with_two_repeat_combinations.append(combination)
        for combination in with_two_repeat_combinations:
            self.assertEqual(len(combination), 6)
            self.assertTrue(sum(num in self.repeat_numbers for num in combination) == 2)  # Exactly two repeat numbers
            self.assertTrue(all(num in self.non_repeat_numbers or num in combination[:2] for num in combination))  # Valid numbers

if __name__ == '__main__':
    unittest.main()