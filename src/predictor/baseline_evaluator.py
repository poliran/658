"""Random baseline evaluator for fair comparison with ML models.

This module generates random lottery predictions and compares them against
ML model predictions. The core insight: if ML models cannot beat a random
baseline (adjusted for statistical variance), then they have no real
predictive power.

This is the most important reality check in the system.
"""

import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from scipy import stats
from scipy.special import comb

log = logging.getLogger(__name__)


class RandomBaselineEvaluator:
    """Generates and evaluates random lottery predictions as baseline."""

    def __init__(
        self,
        min_number: int = 1,
        max_number: int = 58,
        numbers_per_draw: int = 6,
        num_simulations: int = 10000,
    ):
        """Initialize random baseline evaluator.

        Args:
            min_number: Minimum lottery number
            max_number: Maximum lottery number
            numbers_per_draw: Numbers drawn per draw
            num_simulations: Number of random predictions to generate (for confidence intervals)
        """
        self.min_number = min_number
        self.max_number = max_number
        self.numbers_per_draw = numbers_per_draw
        self.num_simulations = num_simulations
        self.total_numbers = max_number - min_number + 1

    def generate_random_prediction(self) -> np.ndarray:
        """Generate a single random lottery prediction.

        Returns:
            Array of `numbers_per_draw` unique random numbers in range.
        """
        return np.random.choice(
            range(self.min_number, self.max_number + 1),
            size=self.numbers_per_draw,
            replace=False,
        )

    def generate_random_predictions(self, count: int) -> List[np.ndarray]:
        """Generate multiple random predictions.

        Args:
            count: Number of predictions to generate

        Returns:
            List of random prediction arrays
        """
        return [self.generate_random_prediction() for _ in range(count)]

    def evaluate_prediction(
        self, actual: np.ndarray, predicted: np.ndarray
    ) -> Dict[str, float]:
        """Evaluate a single prediction against actual draw.

        Args:
            actual: Array of actual lottery numbers drawn
            predicted: Array of predicted lottery numbers

        Returns:
            Dictionary with multiple accuracy metrics
        """
        metrics = {}

        # Exact matches (predicted numbers in actual draw, regardless of position)
        exact_matches = len(np.intersect1d(predicted, actual))
        metrics["exact_matches"] = exact_matches
        metrics["exact_match_rate"] = exact_matches / len(actual)

        # Position-wise matches (same number in same position)
        position_matches = np.sum(actual == predicted)
        metrics["position_matches"] = position_matches
        metrics["position_accuracy"] = position_matches / len(actual)

        # Partial match rates
        metrics["rate_6_of_6"] = 1.0 if exact_matches == 6 else 0.0
        metrics["rate_5_of_6"] = 1.0 if exact_matches >= 5 else 0.0
        metrics["rate_4_of_6"] = 1.0 if exact_matches >= 4 else 0.0
        metrics["rate_3_of_6"] = 1.0 if exact_matches >= 3 else 0.0

        # Distance-based metrics
        if len(actual) > 0 and len(predicted) > 0:
            # Mean absolute error between predicted and actual (treating as ordered)
            sorted_actual = np.sort(actual)
            sorted_predicted = np.sort(predicted)
            metrics["mae"] = np.mean(np.abs(sorted_actual - sorted_predicted))
            metrics["mse"] = np.mean((sorted_actual - sorted_predicted) ** 2)
        else:
            metrics["mae"] = 0.0
            metrics["mse"] = 0.0

        return metrics

    def generate_random_baseline_statistics(self, num_draws: int = 100) -> Dict:
        """Generate expected statistics for random predictions over many draws.

        This provides confidence intervals for what we expect from pure randomness.

        Args:
            num_draws: Number of simulated draws to test against random predictions

        Returns:
            Dictionary with expected distributions and confidence intervals
        """
        log.info(
            f"Generating random baseline statistics over {self.num_simulations} "
            f"simulations × {num_draws} draws..."
        )

        # Store metrics across all simulations
        exact_match_rates = []
        position_accuracies = []
        mae_values = []
        partial_3_rates = []
        partial_4_rates = []
        partial_5_rates = []
        partial_6_rates = []

        for sim in range(self.num_simulations):
            sim_exact_matches = 0
            sim_position_matches = 0
            sim_mae = 0
            sim_3_of_6 = 0
            sim_4_of_6 = 0
            sim_5_of_6 = 0
            sim_6_of_6 = 0

            for draw in range(num_draws):
                # Random "actual" draw
                actual = self.generate_random_prediction()
                # Random "predicted" draw
                predicted = self.generate_random_prediction()

                metrics = self.evaluate_prediction(actual, predicted)
                sim_exact_matches += metrics["exact_matches"]
                sim_position_matches += metrics["position_matches"]
                sim_mae += metrics["mae"]
                sim_3_of_6 += metrics["rate_3_of_6"]
                sim_4_of_6 += metrics["rate_4_of_6"]
                sim_5_of_6 += metrics["rate_5_of_6"]
                sim_6_of_6 += metrics["rate_6_of_6"]

            # Average over draws
            exact_match_rates.append(sim_exact_matches / (num_draws * self.numbers_per_draw))
            position_accuracies.append(sim_position_matches / (num_draws * self.numbers_per_draw))
            mae_values.append(sim_mae / num_draws)
            partial_3_rates.append(sim_3_of_6 / num_draws)
            partial_4_rates.append(sim_4_of_6 / num_draws)
            partial_5_rates.append(sim_5_of_6 / num_draws)
            partial_6_rates.append(sim_6_of_6 / num_draws)

        # Compute confidence intervals
        exact_match_rates = np.array(exact_match_rates)
        position_accuracies = np.array(position_accuracies)
        mae_values = np.array(mae_values)

        return {
            "num_simulations": self.num_simulations,
            "num_draws_per_simulation": num_draws,
            "exact_match_rate": {
                "mean": float(np.mean(exact_match_rates)),
                "std": float(np.std(exact_match_rates)),
                "ci_95_lower": float(np.percentile(exact_match_rates, 2.5)),
                "ci_95_upper": float(np.percentile(exact_match_rates, 97.5)),
                "interpretation": "Expected rate for random prediction",
            },
            "position_accuracy": {
                "mean": float(np.mean(position_accuracies)),
                "std": float(np.std(position_accuracies)),
                "ci_95_lower": float(np.percentile(position_accuracies, 2.5)),
                "ci_95_upper": float(np.percentile(position_accuracies, 97.5)),
                "interpretation": "Expected position-wise accuracy for random prediction",
            },
            "mae": {
                "mean": float(np.mean(mae_values)),
                "std": float(np.std(mae_values)),
                "ci_95_lower": float(np.percentile(mae_values, 2.5)),
                "ci_95_upper": float(np.percentile(mae_values, 97.5)),
                "interpretation": "Expected mean absolute error for random prediction",
            },
            "partial_matches": {
                "3_of_6_rate": float(np.mean(partial_3_rates)),
                "4_of_6_rate": float(np.mean(partial_4_rates)),
                "5_of_6_rate": float(np.mean(partial_5_rates)),
                "6_of_6_rate": float(np.mean(partial_6_rates)),
            },
        }

    def compare_model_vs_random(
        self,
        model_metrics: List[Dict],
        random_baseline: Optional[Dict] = None,
        num_baseline_draws: int = 100,
    ) -> Dict:
        """Compare ML model performance against random baseline with statistical tests.

        This is the critical test: if the model doesn't beat the baseline by a
        statistically significant margin, it has no predictive value.

        Args:
            model_metrics: List of evaluation metrics from ML model predictions
            random_baseline: Pre-computed baseline (if None, computed on the fly)
            num_baseline_draws: Number of draws for baseline simulation

        Returns:
            Dictionary with comparison results and statistical significance tests
        """
        if random_baseline is None:
            random_baseline = self.generate_random_baseline_statistics(num_baseline_draws)

        # Extract model metrics
        model_exact_match_rates = [m.get("exact_match_rate", 0) for m in model_metrics]
        model_position_accuracies = [m.get("position_accuracy", 0) for m in model_metrics]
        model_mae_values = [m.get("mae", 0) for m in model_metrics]

        model_exact_mean = np.mean(model_exact_match_rates)
        model_position_mean = np.mean(model_position_accuracies)
        model_mae_mean = np.mean(model_mae_values)

        # Get random baseline means
        random_exact_mean = random_baseline["exact_match_rate"]["mean"]
        random_exact_std = random_baseline["exact_match_rate"]["std"]
        random_position_mean = random_baseline["position_accuracy"]["mean"]
        random_position_std = random_baseline["position_accuracy"]["std"]
        random_mae_mean = random_baseline["mae"]["mean"]
        random_mae_std = random_baseline["mae"]["std"]

        # Perform t-tests
        # Null hypothesis: model performance = random performance
        # Alternative: model is better than random

        t_stat_exact, p_value_exact = stats.ttest_ind(
            model_exact_match_rates,
            np.random.normal(random_exact_mean, random_exact_std, len(model_exact_match_rates)),
        )

        t_stat_position, p_value_position = stats.ttest_ind(
            model_position_accuracies,
            np.random.normal(random_position_mean, random_position_std, len(model_position_accuracies)),
        )

        # For MAE, lower is better, so flip the test direction
        t_stat_mae, p_value_mae = stats.ttest_ind(
            model_mae_values,
            np.random.normal(random_mae_mean, random_mae_std, len(model_mae_values)),
        )

        # Effect size (Cohen's d)
        cohens_d_exact = (model_exact_mean - random_exact_mean) / np.sqrt(
            (np.std(model_exact_match_rates) ** 2 + random_exact_std**2) / 2
        )

        cohens_d_position = (model_position_mean - random_position_mean) / np.sqrt(
            (np.std(model_position_accuracies) ** 2 + random_position_std**2) / 2
        )

        return {
            "comparison": "ML Model vs. Random Baseline",
            "num_model_predictions": len(model_metrics),
            "exact_match_comparison": {
                "model_mean": float(model_exact_mean),
                "random_mean": float(random_exact_mean),
                "difference": float(model_exact_mean - random_exact_mean),
                "t_statistic": float(t_stat_exact),
                "p_value": float(p_value_exact),
                "cohens_d": float(cohens_d_exact),
                "significantly_better": (
                    p_value_exact < 0.05 and model_exact_mean > random_exact_mean
                ),
                "interpretation": (
                    "✓ Model significantly outperforms random (p < 0.05)"
                    if p_value_exact < 0.05 and model_exact_mean > random_exact_mean
                    else "✗ No significant improvement over random baseline"
                ),
            },
            "position_accuracy_comparison": {
                "model_mean": float(model_position_mean),
                "random_mean": float(random_position_mean),
                "difference": float(model_position_mean - random_position_mean),
                "t_statistic": float(t_stat_position),
                "p_value": float(p_value_position),
                "cohens_d": float(cohens_d_position),
                "significantly_better": (
                    p_value_position < 0.05 and model_position_mean > random_position_mean
                ),
                "interpretation": (
                    "✓ Model significantly outperforms random (p < 0.05)"
                    if p_value_position < 0.05 and model_position_mean > random_position_mean
                    else "✗ No significant improvement over random baseline"
                ),
            },
            "mae_comparison": {
                "model_mean": float(model_mae_mean),
                "random_mean": float(random_mae_mean),
                "difference": float(model_mae_mean - random_mae_mean),
                "t_statistic": float(t_stat_mae),
                "p_value": float(p_value_mae),
                "significantly_better": (
                    p_value_mae < 0.05 and model_mae_mean < random_mae_mean
                ),
                "interpretation": (
                    "✓ Model errors significantly smaller than random (p < 0.05)"
                    if p_value_mae < 0.05 and model_mae_mean < random_mae_mean
                    else "✗ Model errors not significantly better than random"
                ),
            },
            "overall_conclusion": (
                "✗ CRITICAL: Model does not beat random baseline. "
                "This suggests no real predictive power. Check for overfitting or data leakage."
                if not (
                    p_value_exact < 0.05
                    and model_exact_mean > random_exact_mean
                )
                else "⚠ Model marginally better than random; effect size may be small."
            ),
            "significance_threshold": 0.05,
        }

    def theoretical_probabilities(self) -> Dict:
        """Return theoretical probabilities for random selection.

        These are the hard limits of what random chance alone can achieve.

        Returns:
            Dictionary with theoretical metrics
        """
        # For a 6/58 lottery
        total_combinations = comb(self.total_numbers, self.numbers_per_draw)

        # Probability of matching exactly k of 6 numbers
        # P(k) = C(6, k) * C(52, 6-k) / C(58, 6)

        prob_6_of_6 = 1.0 / total_combinations
        prob_5_of_6 = (
            comb(6, 5) * comb(self.total_numbers - 6, 1) / total_combinations
        )
        prob_4_of_6 = (
            comb(6, 4) * comb(self.total_numbers - 6, 2) / total_combinations
        )
        prob_3_of_6 = (
            comb(6, 3) * comb(self.total_numbers - 6, 3) / total_combinations
        )

        # Expected number of exact matches per draw
        expected_exact = (
            sum(
                comb(6, k)
                * comb(self.total_numbers - 6, self.numbers_per_draw - k)
                / total_combinations
                * k
                for k in range(self.numbers_per_draw + 1)
            )
            / self.numbers_per_draw
        )

        return {
            "lottery_type": f"{self.numbers_per_draw}/{self.total_numbers}",
            "total_possible_combinations": int(total_combinations),
            "probabilities": {
                "6_of_6": float(prob_6_of_6),
                "5_of_6": float(prob_5_of_6),
                "4_of_6": float(prob_4_of_6),
                "3_of_6": float(prob_3_of_6),
            },
            "odds": {
                "6_of_6": f"1 in {int(total_combinations):,}",
                "5_of_6": f"1 in {int(1 / prob_5_of_6):,}",
                "4_of_6": f"1 in {int(1 / prob_4_of_6):,}",
                "3_of_6": f"1 in {int(1 / prob_3_of_6):,}",
            },
            "expected_matches_per_draw": float(expected_exact),
            "note": "These are theoretical limits; no model can beat them consistently",
        }
