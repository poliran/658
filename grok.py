import random
import time

# Define high-frequency numbers and their weights from historical data
numbers = list(range(1, 59))
frequencies = {
    1: 103, 2: 105, 3: 95, 4: 104, 5: 108, 6: 108, 7: 108, 8: 108, 9: 100,
    10: 107, 11: 105, 12: 105, 13: 112, 14: 107, 15: 104, 16: 102, 17: 104,
    18: 102, 19: 102, 20: 108, 21: 96, 22: 108, 23: 111, 24: 100, 25: 107,
    26: 98, 27: 108, 28: 97, 29: 98, 30: 103, 31: 95, 32: 102, 33: 104,
    34: 102, 35: 97, 36: 103, 37: 99, 38: 111, 39: 102, 40: 105, 41: 104,
    42: 102, 43: 103, 44: 97, 45: 100, 46: 103, 47: 103, 48: 103, 49: 95,
    50: 102, 51: 103, 52: 103, 53: 101, 54: 100, 55: 97, 56: 99, 57: 99, 58: 101
}
weights = [frequencies[i] for i in numbers]

# Define common consecutive pairs
consecutive_pairs = [(12, 13), (13, 14), (22, 23), (1, 2), (38, 39)]

# Define clusters
clusters = [
    list(range(1, 11)),   # 1–10
    list(range(11, 21)),  # 11–20
    list(range(21, 31)),  # 21–30
    list(range(31, 41)),  # 31–40
    list(range(41, 51)),  # 41–50
    list(range(51, 59))   # 51–58
]
cluster_names = ["1–10", "11–20", "21–30", "31–40", "41–50", "51–58"]

# Define target cluster distributions
target_distributions = [
    [1, 2, 1, 1, 0, 0],  # 1-2-1-1-0-0
    [1, 1, 2, 2, 0, 0],  # 1-1-2-2-0-0
    [0, 2, 2, 1, 1, 0]   # 0-2-2-1-1-0
]

def get_consecutive_pairs(combo):
    """Return list of consecutive pairs in the combination."""
    combo = sorted(combo)
    pairs = []
    for i in range(len(combo) - 1):
        if combo[i] + 1 == combo[i + 1]:
            pairs.append((combo[i], combo[i + 1]))
    return pairs

def get_statistics(combo):
    """Calculate statistics for a combination."""
    odd_count = sum(1 for n in combo if n % 2 == 1)
    low_count = sum(1 for n in combo if n <= 29)
    combo_sum = sum(combo)
    cluster_counts = [sum(1 for n in combo if n in cluster) for cluster in clusters]
    consecutive_pairs_found = get_consecutive_pairs(combo)
    
    return {
        "odd_count": odd_count,
        "even_count": 6 - odd_count,
        "low_count": low_count,
        "high_count": 6 - low_count,
        "sum": combo_sum,
        "cluster_counts": cluster_counts,
        "consecutive_pairs": consecutive_pairs_found
    }

def is_valid_combination(combo, target_distribution):
    """Check if combination meets all criteria."""
    stats = get_statistics(combo)
    
    # Check odd/even (3 odd, 3 even)
    if stats["odd_count"] != 3:
        return False
    
    # Check high/low (3 low: 1–29, 3 high: 30–58)
    if stats["low_count"] != 3:
        return False
    
    # Check sum (170–190)
    if not (170 <= stats["sum"] <= 190):
        return False
    
    # Check consecutive pair
    if not stats["consecutive_pairs"]:
        return False
    
    # Check cluster distribution
    if stats["cluster_counts"] != target_distribution:
        return False
    
    return True

def generate_combination(target_distribution, max_attempts=10000):
    """Generate a combination meeting all criteria."""
    print(f"Generating combination for cluster distribution {target_distribution}...")
    start_time = time.time()
    
    try:
        for attempt in range(1, max_attempts + 1):
            # Start with a consecutive pair
            pair = random.choice(consecutive_pairs)
            combo = list(pair)
            
            # Add remaining numbers with protection against infinite loops
            available_numbers = [n for n in numbers if n not in combo]
            available_weights = [frequencies[n] for n in available_numbers]
            max_fill_attempts = len(available_numbers) * 2  # Limit fill attempts
            fill_attempt = 0
            
            while len(combo) < 6 and fill_attempt < max_fill_attempts:
                if not available_numbers:  # No more numbers available
                    break
                num = random.choices(available_numbers, available_weights, k=1)[0]
                combo.append(num)
                # Update available numbers and weights
                idx = available_numbers.index(num)
                available_numbers.pop(idx)
                available_weights.pop(idx)
                fill_attempt += 1
            
            # Check if combination has 6 numbers
            if len(combo) != 6:
                continue
            
            # Sort combination
            combo.sort()
            
            # Check if combination meets all criteria
            if is_valid_combination(combo, target_distribution):
                elapsed_time = time.time() - start_time
                print(f"Success: Generated combination in {attempt} attempts ({elapsed_time:.2f} seconds)")
                return combo, True
            
            if attempt % 1000 == 0:
                print(f"Progress: Attempt {attempt}/{max_attempts}")
        
        elapsed_time = time.time() - start_time
        print(f"Failure: Could not generate combination in {max_attempts} attempts ({elapsed_time:.2f} seconds)")
        return None, False
    
    except Exception as e:
        print(f"Error during generation: {e}")
        return None, False

# Generate three combinations and collect statistics
combinations = []
stats_list = []
successful = 0

for i, dist in enumerate(target_distributions, 1):
    print(f"\n--- Generating Combination {i} ---")
    combo, success = generate_combination(dist)
    if success:
        successful += 1
        combinations.append(combo)
        stats = get_statistics(combo)
        stats_list.append(stats)
        
        # Print detailed statistics
        print(f"Combination {i}: {'-'.join(f'{n:02d}' for n in combo)}")
        print(f"Status: Success")
        print(f"Sum: {stats['sum']}")
        print(f"Odd/Even: {stats['odd_count']} odd, {stats['even_count']} even")
        print(f"High/Low: {stats['low_count']} low (1–29), {stats['high_count']} high (30–58)")
        print(f"Consecutive Pairs: {stats['consecutive_pairs']}")
        print(f"Cluster Distribution: {', '.join(f'{name}: {count}' for name, count in zip(cluster_names, stats['cluster_counts']))}")
    else:
        print(f"Combination {i}: Failed to generate")
        print(f"Status: Failure")

# Print summary statistics
if stats_list:
    print("\n--- Summary Statistics ---")
    avg_sum = sum(stats["sum"] for stats in stats_list) / len(stats_list)
    avg_odd = sum(stats["odd_count"] for stats in stats_list) / len(stats_list)
    avg_low = sum(stats["low_count"] for stats in stats_list) / len(stats_list)
    total_pairs = sum(len(stats["consecutive_pairs"]) for stats in stats_list)
    print(f"Successful Combinations: {successful}/{len(target_distributions)}")
    print(f"Average Sum: {avg_sum:.2f}")
    print(f"Average Odd Numbers: {avg_odd:.2f}")
    print(f"Average Low Numbers (1–29): {avg_low:.2f}")
    print(f"Total Consecutive Pairs Found: {total_pairs}")
else:
    print("\n--- Summary Statistics ---")
    print("No combinations generated successfully")