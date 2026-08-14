import unittest
import random
from src.predictor.eval.randomness import (
    analyze_draws,
    chi_squared_uniformity,
    runs_test_median,
    serial_correlation,
    compression_audit,
)


class TestRandomnessModule(unittest.TestCase):

    def setUp(self):
        # Create deterministic draws: 100 draws of numbers 1..6 repeated
        self.repetitive_draws = [[(i % 6) + 1 for _ in range(6)] for i in range(100)]
        # Create random draws in range 1..58
        rnd = random.Random(42)
        self.random_draws = [[rnd.randint(1, 58) for _ in range(6)] for _ in range(100)]

    def test_chi2_returns_stats(self):
        res = chi_squared_uniformity(self.random_draws, num_bins=58)
        self.assertIn("chi2", res)
        self.assertIn("dof", res)

    def test_runs_test_median(self):
        # flattened repetitive sequence will have low variability
        flat = [n for draw in self.repetitive_draws for n in draw]
        r = runs_test_median(flat)
        self.assertIn("z", r)
        self.assertIn("p_value", r)

    def test_serial_correlation(self):
        flat = [n for draw in self.random_draws for n in draw]
        sc = serial_correlation(flat, lag=1)
        self.assertIn("autocorr", sc)

    def test_compression_ratio_smaller_for_repetitive(self):
        c_rep = compression_audit(self.repetitive_draws)
        c_rnd = compression_audit(self.random_draws)
        # repetitive data should compress better (smaller ratio)
        self.assertLess(c_rep["ratio"], c_rnd["ratio"])

    def test_analyze_draws_struct(self):
        out = analyze_draws(self.random_draws, num_bins=58)
        self.assertIn("chi2", out)
        self.assertIn("runs", out)
        self.assertIn("serial_corr_lag1", out)
        self.assertIn("compression", out)


if __name__ == "__main__":
    unittest.main()
