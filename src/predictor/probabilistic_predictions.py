"""Probabilistic lottery prediction with calibrated probability outputs.

Instead of hard predictions (e.g., "predict 5, 12, 23..."), this module
produces calibrated probability estimates for each number's likelihood
of being drawn. This enables proper scoring rules (Brier score, log-loss)
that better evaluate model quality than simple accuracy metrics.
"""

import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from scipy import stats
from sklearn.calibration import CalibratedClassifierCV
from sklearn.isotonic import IsotonicRegression

log = logging.getLogger(__name__)


class ProbabilisticPredictor:
    """Produces calibrated probability predictions instead of hard predictions."""

    def __init__(self, min_number: int = 1, max_number: int = 58, numbers_per_draw: int = 6):
        """Initialize probabilistic predictor.

        Args:
            min_number: Minimum lottery number
            max_number: Maximum lottery number
            numbers_per_draw: Numbers drawn per draw
        """
        self.min_number = min_number
        self.max_number = max_number
        self.numbers_per_draw = numbers_per_draw
        self.total_numbers = max_number - min_number + 1
        self.calibrators = {}  # Per-number calibrators

    def create_binary_targets(
        self, features_df: pd.DataFrame
    ) -> Tuple[pd.DataFrame, Dict[int, np.ndarray]]:
        """Convert lottery draws to binary targets for each number.

        Each number (1-58) gets a binary target: 1 if drawn, 0 if not.

        Args:
            features_df: DataFrame with lottery features including num_1, num_2, etc.

        Returns:
            Tuple of (features, dict mapping number to binary targets)
        """
        X = features_df.drop(
            columns=["COMBINATIONS", "DRAW DATE", "num_1", "num_2", "num_3", "num_4", "num_5", "num_6"],
            errors="ignore"
        )

        y_dict = {}
        for num in range(self.min_number, self.max_number + 1):
            # Binary target: 1 if this number was drawn, 0 otherwise
            target = np.zeros(len(features_df))
            for pos in range(1, self.numbers_per_draw + 1):
                col_name = f"num_{pos}"
                if col_name in features_df.columns:
                    target += (features_df[col_name].values == num).astype(int)

            y_dict[num] = (target > 0).astype(int)

        return X, y_dict

    def train_probability_model(
        self,
        X_train: pd.DataFrame,
        y_dict_train: Dict[int, np.ndarray],
        base_model,
        calibration_method: str = "sigmoid",
    ) -> Dict:
        """Train calibrated probability models for each number.

        Args:
            X_train: Training features
            y_dict_train: Dictionary of binary targets per number
            base_model: Sklearn model class (e.g., LogisticRegression, GradientBoostingClassifier)
            calibration_method: "sigmoid", "isotonic", or None for no calibration

        Returns:
            Dictionary mapping numbers to trained calibrated models
        """
        log.info(f"Training probability models for each number ({self.total_numbers} models)...")

        models = {}
        for num in range(self.min_number, self.max_number + 1):
            y = y_dict_train[num]

            # Skip if target is constant
            if len(np.unique(y)) < 2:
                log.warning(f"Skipping number {num}: constant target (no positive examples)")
                continue

            try:
                if calibration_method:
                    # Train with calibration
                    model = CalibratedClassifierCV(
                        base_model,
                        method=calibration_method,
                        cv=5,
                    )
                else:
                    # Train without calibration
                    model = base_model

                model.fit(X_train, y)
                models[num] = model

            except Exception as e:
                log.error(f"Error training model for number {num}: {e}")

        log.info(f"Successfully trained {len(models)}/{self.total_numbers} probability models")
        return models

    def predict_probabilities(
        self,
        X_test: pd.DataFrame,
        models: Dict[int, object],
    ) -> Dict[int, np.ndarray]:
        """Generate probability predictions for each number.

        Args:
            X_test: Test features
            models: Trained probability models per number

        Returns:
            Dictionary mapping numbers to probability arrays
        """
        probabilities = {}
        for num, model in models.items():
            try:
                # Get probability for class 1 (number is drawn)
                probs = model.predict_proba(X_test)[:, 1]
                probabilities[num] = probs
            except Exception as e:
                log.warning(f"Error predicting for number {num}: {e}")

        return probabilities

    def select_top_k_by_probability(
        self,
        probabilities: Dict[int, np.ndarray],
        k: int = 6,
        sample_idx: int = 0,
    ) -> Tuple[np.ndarray, Dict]:
        """Select top-k numbers by predicted probability for a single sample.

        Args:
            probabilities: Dict mapping numbers to probability arrays
            k: Number of numbers to select (typically 6)
            sample_idx: Index of sample to predict for

        Returns:
            Tuple of (selected numbers, probability values for selected)
        """
        # Get probabilities for this sample
        sample_probs = {}
        for num, prob_array in probabilities.items():
            sample_probs[num] = prob_array[sample_idx]

        # Sort by probability, descending
        sorted_nums = sorted(sample_probs.items(), key=lambda x: x[1], reverse=True)

        # Select top-k
        selected = np.array([num for num, _ in sorted_nums[:k]])
        selected_probs = np.array([prob for _, prob in sorted_nums[:k]])

        return selected, selected_probs

    def brier_score(
        self,
        y_true: Dict[int, np.ndarray],
        y_proba: Dict[int, np.ndarray],
    ) -> Tuple[float, Dict]:
        """Calculate Brier score: mean squared error of probability estimates.

        Brier score = mean((predicted_prob - actual)^2)
        Lower is better. Perfect predictions = 0. Random guessing = 0.25 for binary.

        For lottery: random baseline ~ 0.25 (50% chance drawn for each number).

        Args:
            y_true: Dictionary of binary true values per number
            y_proba: Dictionary of probability predictions per number

        Returns:
            Tuple of (overall Brier score, per-number scores)
        """
        per_number_scores = {}
        all_errors = []

        for num in y_true.keys():
            if num not in y_proba:
                continue

            true_vals = y_true[num]
            pred_probs = y_proba[num]

            # Clamp probabilities to [0, 1]
            pred_probs = np.clip(pred_probs, 0, 1)

            # Brier score for this number
            brier = np.mean((pred_probs - true_vals) ** 2)
            per_number_scores[num] = brier
            all_errors.extend((pred_probs - true_vals) ** 2)

        overall_brier = np.mean(all_errors) if all_errors else float("nan")

        return overall_brier, per_number_scores

    def log_loss(
        self,
        y_true: Dict[int, np.ndarray],
        y_proba: Dict[int, np.ndarray],
    ) -> Tuple[float, Dict]:
        """Calculate log loss (cross-entropy) for probability estimates.

        Log loss = -mean(y_true * log(y_proba) + (1 - y_true) * log(1 - y_proba))
        Lower is better. Perfect = 0. Random guessing = log(2) ≈ 0.693 for binary.

        Args:
            y_true: Dictionary of binary true values per number
            y_proba: Dictionary of probability predictions per number

        Returns:
            Tuple of (overall log loss, per-number scores)
        """
        per_number_scores = {}
        all_losses = []

        for num in y_true.keys():
            if num not in y_proba:
                continue

            true_vals = y_true[num]
            pred_probs = np.clip(y_proba[num], 1e-15, 1 - 1e-15)  # Avoid log(0)

            # Log loss for this number
            losses = -np.mean(
                true_vals * np.log(pred_probs)
                + (1 - true_vals) * np.log(1 - pred_probs)
            )
            per_number_scores[num] = losses
            all_losses.append(losses)

        overall_log_loss = np.mean(all_losses) if all_losses else float("nan")

        return overall_log_loss, per_number_scores

    def calibration_analysis(
        self,
        y_true: Dict[int, np.ndarray],
        y_proba: Dict[int, np.ndarray],
        num_bins: int = 10,
    ) -> Dict:
        """Analyze calibration: do predicted probabilities match actual frequencies?

        If model is well-calibrated, samples predicted with probability p should
        have actual frequency ≈ p.

        Args:
            y_true: Dictionary of binary true values per number
            y_proba: Dictionary of probability predictions per number
            num_bins: Number of probability bins to analyze

        Returns:
            Dictionary with calibration analysis
        """
        calibration_results = {}

        for num in y_true.keys():
            if num not in y_proba:
                continue

            true_vals = y_true[num]
            pred_probs = np.clip(y_proba[num], 0, 1)

            # Bin predictions by probability
            bins = np.linspace(0, 1, num_bins + 1)
            bin_indices = np.digitize(pred_probs, bins) - 1
            bin_indices = np.clip(bin_indices, 0, num_bins - 1)

            bin_calibration = []
            for bin_idx in range(num_bins):
                mask = bin_indices == bin_idx
                if np.sum(mask) > 0:
                    mean_pred_prob = np.mean(pred_probs[mask])
                    mean_actual = np.mean(true_vals[mask])
                    bin_calibration.append({
                        "bin": bin_idx,
                        "mean_predicted_prob": float(mean_pred_prob),
                        "actual_frequency": float(mean_actual),
                        "count": int(np.sum(mask)),
                        "calibration_error": float(abs(mean_pred_prob - mean_actual)),
                    })

            calibration_results[num] = bin_calibration

        # Overall calibration metric (expected calibration error)
        all_calibration_errors = []
        for num_results in calibration_results.values():
            for bin_result in num_results:
                all_calibration_errors.append(bin_result["calibration_error"])

        ece = np.mean(all_calibration_errors) if all_calibration_errors else float("nan")

        return {
            "expected_calibration_error": float(ece),
            "interpretation": (
                "✓ Well-calibrated: ECE < 0.05"
                if ece < 0.05
                else "⚠ Poorly calibrated: ECE >= 0.05. Probabilities don't match reality."
            ),
            "per_number_calibration": calibration_results,
        }

    def probability_summary(
        self,
        y_true: Dict[int, np.ndarray],
        y_proba: Dict[int, np.ndarray],
    ) -> Dict:
        """Generate comprehensive summary of probabilistic predictions.

        Args:
            y_true: Dictionary of binary true values per number
            y_proba: Dictionary of probability predictions per number

        Returns:
            Dictionary with complete probabilistic evaluation
        """
        brier, brier_per_num = self.brier_score(y_true, y_proba)
        log_loss_score, log_loss_per_num = self.log_loss(y_true, y_proba)
        calibration = self.calibration_analysis(y_true, y_proba)

        # Compare to random baseline
        random_brier = 0.25  # For uniform binary (50% of numbers drawn)
        random_log_loss = np.log(2)  # ≈ 0.693

        return {
            "brier_score": {
                "value": float(brier),
                "random_baseline": float(random_brier),
                "improvement": float(random_brier - brier) if not np.isnan(brier) else 0,
                "interpretation": (
                    "✓ Better than random"
                    if not np.isnan(brier) and brier < random_brier
                    else "✗ No improvement over random"
                ),
            },
            "log_loss": {
                "value": float(log_loss_score),
                "random_baseline": float(random_log_loss),
                "improvement": float(random_log_loss - log_loss_score) if not np.isnan(log_loss_score) else 0,
                "interpretation": (
                    "✓ Better than random"
                    if not np.isnan(log_loss_score) and log_loss_score < random_log_loss
                    else "✗ No improvement over random"
                ),
            },
            "calibration": calibration,
            "note": (
                "These proper scoring rules provide a more complete picture of model quality "
                "than simple accuracy metrics. Lottery predictions should approach random baseline."
            ),
        }
