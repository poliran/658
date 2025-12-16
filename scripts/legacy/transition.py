import itertools
import random

def generate_combinations(base_sequence, additional_numbers, num_combinations=10):
    """
    Generate combinations by replacing some numbers in the base sequence
    
    Args:
    - base_sequence: List of base numbers to start with
    - additional_numbers: Pool of numbers to use for replacements
    - num_combinations: Number of combinations to generate
    
    Returns:
    List of generated combinations
    """
    combinations = []
    
    for _ in range(num_combinations):
        # Create a copy of the base sequence to modify
        new_combination = base_sequence.copy()
        
        # Randomly select indices to replace
        replace_indices = random.sample(range(len(new_combination)), 
                                        k=random.randint(1, min(3, len(new_combination))))
        
        # Replace selected indices with unique numbers from additional pool
        for idx in replace_indices:
            replacement = random.choice(additional_numbers)
            while replacement in new_combination:
                replacement = random.choice(additional_numbers)
            new_combination[idx] = replacement
        
        # Sort the combination
        new_combination.sort()
        
        # Convert to string format and add to combinations
        combinations.append('-'.join(map(str, new_combination)))
    
    return combinations

# Base sequence from previous analysis
base_sequence = [31, 25, 13, 5, 26, 10]

# All possible lottery numbers (assuming 1-58 range)
all_numbers = list(range(1, 59))

# Remove base sequence numbers from additional pool
additional_numbers = [num for num in all_numbers if num not in base_sequence]

# Generate combinations
combinations_list = generate_combinations(base_sequence, additional_numbers)

print("Generated Combinations:")
for combo in combinations_list:
    print(combo)