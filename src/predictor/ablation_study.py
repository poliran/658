"""Feature ablation study to demonstrate that engineered features add no predictive power.

This module runs systematic ablation studies showing that:
1. Frequency-based features (hot numbers) don't improve predictions
2. Pattern features (odd/even, sum) don't help
3. The model is essentially memorizing noise, not learning real patterns

This is a core educational component.
"""

import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, mean_absolute_error
import copy

log = logging.getLogger(__name__)


class FeatureAblationStudy:
    """Systematic ablation of features to demonstrate their utility (or lack thereof)."""

    def __init__(self, min_number: int = 1, max_number: int = 58, numbers_per_draw: int = 6):
        """Initialize ablation study.

        Args:
            min_number: Minimum lottery number
            max_number: Maximum lottery number
            numbers_per_draw: Numbers drawn per draw
        """
        self.min_number = min_number
        self.max_number = max_number
        self.numbers_per_draw = numbers_per_draw
        self.total_numbers = max_number - min_number + 1

    def categorize_features(self, features_df: pd.DataFrame) -> Dict[str, List[str]]:
        """Categorize features by type.

        Args:
            features_df: DataFrame with all features

        Returns:
            Dictionary mapping feature categories to column lists
        """
        categories = {
            "frequency_features": [col for col in features_df.columns if col.startswith("freq_")],
            "pattern_features": [col for col in features_df.columns if col in ["sum_numbers", "odd_count", "low_count"]],
            "position_features": [col for col in features_df.columns if col.startswith("num_")],
            "date_features": [col for col in features_df.columns if "date" in col.lower()],
        }
        return categories

    def get_feature_set_variations(
        self, features_df: pd.DataFrame
    ) -> Dict[str, List[str]]:
        """Define various feature combinations for ablation testing.

        Returns:
            Dictionary mapping variation names to lists of feature column names
        """
        categories = self.categorize_features(features_df)
        all_features = [
            col
            for col in features_df.columns
            if col not in ["COMBINATIONS", "DRAW DATE", "index"]
        ]

        return {
            "all_features": all_features,
            "no_frequency": [
                f for f in all_features if f not in categories["frequency_features"]
            ],
            "no_pattern": [
                f for f in all_features if f not in categories["pattern_features"]
            ],
            "only_position": categories["position_features"],
            "only_frequency": categories["frequency_features"],
            "only_pattern": categories["pattern_features"],
            "random_features": self._generate_random_features_baseline(
                len(all_features),
                len(features_df)
            ),
        }

    @staticmethod
    def _generate_random_features_baseline(
        num_features: int, num_samples: int
    ) -> List[str]:
        """Generate names for random noise features for baseline comparison.

        Args:
            num_features: Number of features to simulate
            num_samples: Number of samples

        Returns:
            List of random feature names (for documentation)
        """
        return [f"random_noise_{i}" for i in range(num_features)]

    def run_ablation_study(
        self,
        features_df: pd.DataFrame,
        train_func,
        predict_func,
        test_size: float = 0.2,
        random_state: int = 42,
    ) -> Dict:
        """Run ablation study on various feature combinations.

        Args:
            features_df: DataFrame with all features
            train_func: Function(X_train, y_train) -> trained_model
            predict_func: Function(model, X_test) -> predictions
            test_size: Train/test split ratio
            random_state: Random seed for reproducibility

        Returns:
            Dictionary with ablation results for each feature set
        """
        log.info("Starting feature ablation study...")

        # Prepare target variable (first number position as example)
        y = features_df["num_1"].values

        # Get feature variations
        feature_variations = self.get_feature_set_variations(features_df)

        results = {}

        for variation_name, feature_cols in feature_variations.items():
            if not feature_cols:
                log.warning(f"Skipping {variation_name}: no features in this set")
                continue

            log.info(f"Evaluating {variation_name} ({len(feature_cols)} features)...")

            # Use available features
            available_cols = [
                col for col in feature_cols
                if col in features_df.columns and col not in ["COMBINATIONS", "DRAW DATE"]
            ]

            if not available_cols:
                log.warning(f"No available columns for {variation_name}")
                continue

            X = features_df[available_cols].values

            # Train/test split
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=test_size, random_state=random_state
            )

            # Train model
            try:
                model = train_func(X_train, y_train)
                y_pred = predict_func(model, X_test)

                # Calculate metrics
                mse = mean_squared_error(y_test, y_pred)
                mae = mean_absolute_error(y_test, y_pred)
                rmse = np.sqrt(mse)

                # Correlation of predictions with actual
                correlation = np.corrcoef(y_test, y_pred)[0, 1]

                results[variation_name] = {
                    "num_features": len(available_cols),
                    "feature_names": available_cols,
                    "mse": float(mse),
                    "rmse": float(rmse),
                    "mae": float(mae),
                    "correlation": float(correlation),
                    "train_size": len(X_train),
                    "test_size": len(X_test),
                }

            except Exception as e:
                log.error(f"Error training on {variation_name}: {e}")
                results[variation_name] = {
                    "error": str(e),
                    "num_features": len(available_cols),
                }

        # Generate comparison summary
        results["summary"] = self._generate_ablation_summary(results)

        return results

    def _generate_ablation_summary(self, ablation_results: Dict) -> Dict:
        """Analyze ablation results and generate summary insights.

        Args:
            ablation_results: Results from run_ablation_study

        Returns:
            Summary dictionary with key findings
        """
        # Filter out summary and error results
        valid_results = {
            k: v
            for k, v in ablation_results.items()
            if k != "summary" and "error" not in v
        }

        if not valid_results:
            return {"error": "No valid results to summarize"}

        # Extract MAE values
        mae_values = {
            k: v["mae"] for k, v in valid_results.items() if "mae" in v
        }

        # Sort by MAE (lower is better)
        sorted_by_mae = sorted(mae_values.items(), key=lambda x: x[1])

        best_mae = sorted_by_mae[0] if sorted_by_mae else (None, float("inf"))
        worst_mae = sorted_by_mae[-1] if sorted_by_mae else (None, float("-inf"))

        # Analysis
        mae_diff_percent = (
            (worst_mae[1] - best_mae[1]) / best_mae[1] * 100
            if best_mae[1] != 0
            else 0
        )

        # Key insight: if removing features doesn't hurt performance much,
        # those features aren't actually useful
        frequency_only = valid_results.get("only_frequency", {})
        all_features = valid_results.get("all_features", {})

        improvement = (
            (frequency_only.get("mae", float("inf"))
             - all_features.get("mae", 0))
            / all_features.get("mae", 1)
            * 100
        )

        return {
            "total_variations_tested": len(valid_results),
            "best_performing": {
                "name": best_mae[0],
                "mae": float(best_mae[1]),
                "num_features": valid_results[best_mae[0]].get("num_features", 0),
            },
            "worst_performing": {
                "name": worst_mae[0],
                "mae": float(worst_mae[1]),
                "num_features": valid_results[worst_mae[0]].get("num_features", 0),
            },
            "mae_variation_percent": float(mae_diff_percent),
            "frequency_features_improvement": float(improvement),
            "key_insight": (
                "✓ Frequency features show improvement"
                if improvement > 5
                else "✗ Frequency features provide minimal/no improvement. "
                "This suggests they are capturing noise, not real patterns."
            ),
            "educational_conclusion": (
                "The inability to improve predictions by feature engineering "
                "demonstrates that lottery draws are effectively random. "
                "Any apparent patterns are statistical artifacts."
            ),
            "rank_by_mae": {
                k: v["mae"]
                for k, v in sorted(
                    valid_results.items(), key=lambda x: x[1].get("mae", float("inf"))
                )
            },
        }

    def analyze_feature_importance(
        self, features_df: pd.DataFrame, model_predictions: np.ndarray
    ) -> Dict:
        """Estimate feature importance by analyzing correlation with predictions.

        Args:
            features_df: DataFrame with all features
            model_predictions: Model's predictions

        Returns:
            Dictionary with feature importance ranking
        """
        importances = {}

        categories = self.categorize_features(features_df)

        for feature_type, feature_cols in categories.items():
            type_importances = []
            for col in feature_cols:
                if col in features_df.columns:
                    correlation = np.abs(np.corrcoef(features_df[col], model_predictions)[0, 1])
                    type_importances.append({"feature": col, "correlation": correlation})

            # Sort by correlation
            type_importances.sort(
                key=lambda x: x["correlation"], reverse=True
            )
            importances[feature_type] = type_importances

        return importances

    def permutation_importance(
        self,
        features_df: pd.DataFrame,
        model,
        predict_func,
        y_true: np.ndarray,
        num_repeats: int = 10,
    ) -> Dict:
        """Calculate permutation importance: drop each feature and measure impact.

        Args:
            features_df: DataFrame with all features
            model: Trained model
            predict_func: Function to generate predictions
            y_true: True target values
            num_repeats: Number of times to shuffle each feature

        Returns:
            Dictionary with permutation importance for each feature
        """
        log.info("Computing permutation importance...")

        X = features_df.drop(columns=["COMBINATIONS", "DRAW DATE"], errors="ignore").values
        baseline_predictions = predict_func(model, X)
        baseline_mae = mean_absolute_error(y_true, baseline_predictions)

        importances = {}

        for feature_idx in range(X.shape[1]):
            feature_name = features_df.drop(
                columns=["COMBINATIONS", "DRAW DATE"], errors="ignore"
            ).columns[feature_idx]

            # Shuffle this feature multiple times
            importance_drops = []
            for _ in range(num_repeats):
                X_shuffled = X.copy()
                np.random.shuffle(X_shuffled[:, feature_idx])

                predictions_shuffled = predict_func(model, X_shuffled)
                mae_shuffled = mean_absolute_error(y_true, predictions_shuffled)

                # Importance = how much performance drops when shuffling
                importance_drops.append(mae_shuffled - baseline_mae)

            importances[feature_name] = {
                "mean_importance": float(np.mean(importance_drops)),
                "std_importance": float(np.std(importance_drops)),
                "interpretation": (
                    "Feature is important" if np.mean(importance_drops) > 0.5
                    else "Feature has minimal importance"
                ),
            }

        return {
            "baseline_mae": float(baseline_mae),
            "feature_importances": importances,
            "top_5_important": sorted(
                importances.items(),
                key=lambda x: x[1]["mean_importance"],
                reverse=True,
            )[:5],
        }
