"""Statistical tests for randomness and independence.

This module implements formal statistical tests to demonstrate that lottery draws
are effectively random and independent. These tests serve as an educational tool
to show why ML models cannot improve upon random guessing.

Tests implemented:
- Chi-squared uniformity test: Verifies each number has equal probability
- Runs test: Checks independence of consecutive draws
- Serial correlation test: Detects patterns in number sequences
- Compression-based entropy (Lempel-Ziv): Measures algorithmic randomness
"""

import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple
from scipy import stats
from collections import Counter

log = logging.getLogger(__name__)


class RandomnessAnalyzer:
    """Analyzes lottery data for evidence of randomness and independence."""

    def __init__(self, min_number: int = 1, max_number: int = 58, numbers_per_draw: int = 6):
        """Initialize randomness analyzer.

        Args:
            min_number: Minimum lottery number (typically 1)
            max_number: Maximum lottery number (typically 58)
            numbers_per_draw: Numbers drawn per draw (typically 6)
        """
        self.min_number = min_number
        self.max_number = max_number
        self.numbers_per_draw = numbers_per_draw
        self.total_numbers = max_number - min_number + 1

    def extract_numbers_from_combinations(self, data: pd.DataFrame) -> List[int]:
        """Extract all numbers from draw history.

        Args:
            data: DataFrame with COMBINATIONS column (e.g., "1-5-12-35-42-58")

        Returns:
            Flattened list of all numbers drawn.
        """
        numbers = []
        for combo_str in data["COMBINATIONS"]:
            nums = [int(n.strip()) for n in str(combo_str).split("-")]
            numbers.extend(nums)
        return numbers

    def chi_squared_uniformity_test(self, data: pd.DataFrame) -> Dict:
        """Test if all numbers have equal probability of being drawn.

        Null hypothesis: Each number 1-58 has equal probability (1/58).
        If p-value > 0.05, we fail to reject the null (data is consistent with uniformity).

        Returns:
            Dictionary with chi2 statistic, p-value, interpretation.
        """
        numbers = self.extract_numbers_from_combinations(data)
        observed_counts = Counter(numbers)

        # Expected count for each number (uniform distribution)
        expected_count = len(numbers) / self.total_numbers

        # Build observed frequencies for all numbers
        observed_freq = np.array(
            [observed_counts.get(num, 0) for num in range(self.min_number, self.max_number + 1)]
        )
        expected_freq = np.full(self.total_numbers, expected_count)

        # Chi-squared test
        chi2_stat, p_value = stats.chisquare(observed_freq, expected_freq)

        # Degrees of freedom = number of categories - 1
        df = self.total_numbers - 1

        return {
            "test": "Chi-squared Uniformity",
            "null_hypothesis": f"All numbers (1-{self.max_number}) equally likely",
            "chi2_statistic": float(chi2_stat),
            "p_value": float(p_value),
            "degrees_of_freedom": df,
            "expected_count_per_number": float(expected_count),
            "total_numbers_observed": len(numbers),
            "interpretation": (
                "✓ PASS: Data consistent with uniform distribution"
                if p_value > 0.05
                else "✗ FAIL: Data significantly deviates from uniformity"
            ),
            "significance_level": 0.05,
        }

    def runs_test(self, data: pd.DataFrame) -> Dict:
        """Test independence of consecutive draws using Wald-Wolfowitz runs test.

        A "run" is a sequence of consecutive values on same side of median.
        Too few runs suggests positive correlation (clustering).
        Too many runs suggests negative correlation (alternation).

        Returns:
            Dictionary with runs test results and p-value.
        """
        numbers = self.extract_numbers_from_combinations(data)

        # Convert to binary: above/below median
        median = np.median(numbers)
        binary_sequence = (np.array(numbers) > median).astype(int)

        # Count runs
        runs = 1
        for i in range(1, len(binary_sequence)):
            if binary_sequence[i] != binary_sequence[i - 1]:
                runs += 1

        n1 = np.sum(binary_sequence)  # Count of 1s
        n2 = len(binary_sequence) - n1  # Count of 0s
        n = len(binary_sequence)

        # Expected number of runs and variance
        expected_runs = (2 * n1 * n2) / n + 1
        variance_runs = (2 * n1 * n2 * (2 * n1 * n2 - n)) / (n**2 * (n - 1))

        # Z-score for normal approximation
        z_score = (runs - expected_runs) / np.sqrt(variance_runs)
        p_value = 2 * (1 - stats.norm.cdf(abs(z_score)))

        return {
            "test": "Wald-Wolfowitz Runs Test",
            "null_hypothesis": "Numbers are independent (random distribution of above/below median)",
            "observed_runs": int(runs),
            "expected_runs": float(expected_runs),
            "z_score": float(z_score),
            "p_value": float(p_value),
            "total_observations": n,
            "above_median_count": n1,
            "below_median_count": n2,
            "interpretation": (
                "✓ PASS: No significant autocorrelation"
                if p_value > 0.05
                else "✗ FAIL: Significant autocorrelation detected"
            ),
            "significance_level": 0.05,
        }

    def serial_correlation_test(self, data: pd.DataFrame, lag: int = 1) -> Dict:
        """Test for autocorrelation in number sequences using Ljung-Box test.

        Null hypothesis: No autocorrelation at specified lag.

        Args:
            data: DataFrame with COMBINATIONS column
            lag: Number of lags to test (default 1 for immediate consecutive effect)

        Returns:
            Dictionary with autocorrelation test results.
        """
        numbers = np.array(self.extract_numbers_from_combinations(data))

        # Autocorrelation
        mean = np.mean(numbers)
        c0 = np.sum((numbers - mean) ** 2) / len(numbers)
        c_lag = np.sum((numbers[:-lag] - mean) * (numbers[lag:] - mean)) / len(numbers)
        autocorr = c_lag / c0

        # Ljung-Box test statistic
        ljung_box_stat = len(numbers) * (len(numbers) + 2) * (autocorr**2 / (len(numbers) - lag))

        # Chi-squared with 1 degree of freedom
        p_value = 1 - stats.chi2.cdf(ljung_box_stat, df=1)

        return {
            "test": f"Serial Correlation Test (Lag {lag})",
            "null_hypothesis": f"No autocorrelation at lag {lag}",
            "autocorrelation_coefficient": float(autocorr),
            "ljung_box_statistic": float(ljung_box_stat),
            "p_value": float(p_value),
            "lag": lag,
            "sample_size": len(numbers),
            "interpretation": (
                "✓ PASS: No significant autocorrelation"
                if p_value > 0.05
                else "✗ FAIL: Significant autocorrelation at this lag"
            ),
            "significance_level": 0.05,
        }

    def lempel_ziv_complexity(self, data: pd.DataFrame, max_complexity: int = 8) -> Dict:
        """Measure algorithmic complexity using Lempel-Ziv compression.

        The Lempel-Ziv complexity approximates the entropy of a sequence.
        Random sequences have high complexity; predictable patterns have low complexity.

        This is a data compression approach: simpler sequences compress better.
        Lottery data should have complexity close to log2(N) for uniform random.

        Args:
            data: DataFrame with COMBINATIONS column
            max_complexity: Maximum pattern size to consider (empirically ~6-8)

        Returns:
            Dictionary with compression analysis.
        """
        numbers = self.extract_numbers_from_combinations(data)

        # Normalize numbers to 0-57 range for binary representation
        normalized = np.array([n - self.min_number for n in numbers])

        # Convert to binary string
        binary_str = "".join(format(int(n), f"0{6}b") for n in normalized)

        # Lempel-Ziv complexity (number of distinct substrings)
        complexity = self._compute_lz_complexity(binary_str, max_complexity)

        # Theoretical maximum entropy for uniform random over N numbers
        theoretical_max = np.log2(self.total_numbers)

        # Normalized complexity (0 = completely predictable, 1 = maximum entropy)
        normalized_complexity = complexity / np.log2(len(binary_str) + 1)

        return {
            "test": "Lempel-Ziv Compression Complexity",
            "description": "Measures algorithmic randomness; higher = more random",
            "lz_complexity": float(complexity),
            "theoretical_entropy": float(theoretical_max),
            "normalized_complexity": float(normalized_complexity),
            "binary_string_length": len(binary_str),
            "interpretation": (
                "✓ Random-like: High complexity, difficult to compress"
                if normalized_complexity > 0.7
                else "⚠ Potentially patterned: Lower complexity suggests structure"
            ),
        }

    @staticmethod
    def _compute_lz_complexity(binary_str: str, max_pattern_size: int = 8) -> float:
        """Compute Lempel-Ziv complexity for a binary string.

        Args:
            binary_str: Binary representation of the sequence
            max_pattern_size: Maximum pattern length to search

        Returns:
            LZ complexity value
        """
        i, complexity = 0, 1
        sub_lengths = {1}

        while i < len(binary_str):
            max_len = min(max_pattern_size, len(binary_str) - i)
            match_found = False

            for length in range(max_len, 0, -1):
                if binary_str[i : i + length] in sub_lengths:
                    match_found = True
                    sub_lengths.add(binary_str[i : i + length])
                    i += length
                    break

            if not match_found:
                sub_lengths.add(binary_str[i])
                i += 1
                complexity += 1

        return complexity

    def theoretical_probability(self) -> Dict:
        """Calculate theoretical probability of perfect 6/6 match.

        Returns:
            Dictionary with theoretical probabilities.
        """
        # Exact match: must predict all 6 numbers in correct positions
        exact_match_prob = 1.0 / (
            np.math.factorial(self.total_numbers) / np.math.factorial(self.total_numbers - self.numbers_per_draw)
        )

        # Partial matches
        prob_6_of_6 = 1.0 / 45057474  # C(58,6) = 45,057,474 for 6/58 lottery

        # Any 5 of 6
        from scipy.special import comb

        prob_5_of_6 = (
            comb(6, 5) * comb(52, 1) / comb(58, 6)
        )  # Choose 5 from 6 correct, 1 from 52 wrong

        prob_4_of_6 = comb(6, 4) * comb(52, 2) / comb(58, 6)
        prob_3_of_6 = comb(6, 3) * comb(52, 3) / comb(58, 6)

        # Expected value per $1 ticket (roughly)
        # This is highly simplified; actual odds depend on prize structure
        ev_per_ticket = prob_6_of_6 * 1_000_000 - 1.0  # Assuming $1M jackpot

        return {
            "test": "Theoretical Probabilities (6/58 Lottery)",
            "probability_6_of_6": float(prob_6_of_6),
            "probability_5_of_6": float(prob_5_of_6),
            "probability_4_of_6": float(prob_4_of_6),
            "probability_3_of_6": float(prob_3_of_6),
            "odds_6_of_6": int(1 / prob_6_of_6),
            "odds_5_of_6": f"~1 in {int(1 / prob_5_of_6)}",
            "odds_4_of_6": f"~1 in {int(1 / prob_4_of_6)}",
            "expected_value_per_ticket": float(ev_per_ticket),
            "note": "Expected value is negative; house always wins over time",
        }

    def run_full_randomness_battery(self, data: pd.DataFrame) -> Dict:
        """Run complete statistical test suite on lottery data.

        Returns:
            Dictionary with all test results and summary.
        """
        log.info("Running comprehensive randomness test battery...")

        results = {
            "chi_squared": self.chi_squared_uniformity_test(data),
            "runs_test": self.runs_test(data),
            "serial_correlation": self.serial_correlation_test(data, lag=1),
            "lz_complexity": self.lempel_ziv_complexity(data),
            "theoretical": self.theoretical_probability(),
        }

        # Summary: count passes
        passes = sum(
            1 for test in ["chi_squared", "runs_test", "serial_correlation"]
            if "✓ PASS" in results[test].get("interpretation", "")
        )

        results["summary"] = {
            "total_tests": 3,  # Not counting theoretical or compression
            "tests_passed": passes,
            "overall_assessment": (
                "✓ Data is consistent with random, independent draws"
                if passes == 3
                else "⚠ Some randomness tests show anomalies; review results carefully"
            ),
            "implication_for_prediction": (
                "ML models should not outperform random baseline. "
                "If they do, check for data leakage or overfitting."
            ),
        }

        return results
