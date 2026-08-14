"""Model evaluation and performance tracking."""

import logging
import numpy as np
from typing import List, Dict
from sklearn.metrics import mean_squared_error, mean_absolute_error

log = logging.getLogger(__name__)


class ModelEvaluator:
    """Handles model evaluation and performance metrics."""

    def __init__(self, config_path: str = None):
        self.config_path = config_path
        self.evaluation_history = []

    def evaluate(self, data_path: str = None, random_baseline: bool = False) -> Dict[str, float]:
        """Evaluate model performance on historical draw data.

        If random_baseline is True, also run statistical randomness tests and report results.
        """
        from .system_factory import PredictionSystemFactory
        from .constants import FilePaths

        config = self.config_path or FilePaths.DEFAULT_CONFIG_FILE
        data = data_path or FilePaths.DEFAULT_DATA_FILE

        service = PredictionSystemFactory.create_lottery_predictor(config)
        service.train(data, model_config={})

        raw = service.data_loader.load(data)
        processed = service._process_dates(raw)
        featured = service.feature_engineer.create_features(processed)

        number_cols = [f"num_{i}" for i in range(1, service.config["numbers_per_draw"] + 1)]
        actuals = featured[number_cols].values

        feature_cols = [
            c
            for c in featured.columns
            if c.startswith("freq_") or c in ("sum_numbers", "odd_count", "low_count")
        ]

        metrics_list = []
        eval_sample_size = min(20, len(featured) - 1)
        for idx in range(len(featured) - eval_sample_size, len(featured) - 1):
            row_features = featured[feature_cols].iloc[idx : idx + 1].values
            pred = service.predict(row_features)
            act = actuals[idx + 1]
            m = self.evaluate_predictions(act, pred)
            metrics_list.append(m)

        summary = self.generate_report(metrics_list)
        log.info(f"Model Evaluation Summary (over {len(metrics_list)} recent draws):")
        for k, v in summary.items():
            log.info(f"  {k}: {v:.4f}")

        # Optional randomness baseline tests
        if random_baseline:
            try:
                from .eval.randomness import analyze_draws

                # use the last 200 draws or all if smaller
                recent = actuals[-200:]
                randomness_report = analyze_draws(recent, num_bins=service.config.get("number_max", 58))
                log.info("Randomness baseline tests:")
                log.info(f"  chi2.stat: {randomness_report['chi2']['chi2']:.4f}, dof: {randomness_report['chi2']['dof']}, p: {randomness_report['chi2']['p_value']}")
                log.info(f"  runs.z: {randomness_report['runs']['z']:.4f}, p: {randomness_report['runs']['p_value']}")
                log.info(f"  serial_corr.lag1: {randomness_report['serial_corr_lag1']['autocorr']:.6f}")
                log.info(f"  compression.ratio: {randomness_report['compression']['ratio']:.6f}")
                summary["randomness"] = randomness_report
            except Exception:
                log.exception("Failed to run randomness baseline tests")

        return summary

    def evaluate_predictions(self, actual: np.ndarray, predicted: np.ndarray) -> Dict[str, float]:
        """Evaluate prediction accuracy.

        Args:
            actual: Array of actual lottery numbers drawn.
            predicted: Array of predicted lottery numbers.

        Returns:
            Dictionary with accuracy metrics.
        """
        metrics = {}

        # Exact match accuracy
        exact_matches = np.sum(np.isin(predicted, actual))
        metrics["exact_matches"] = exact_matches
        if len(actual) > 0:
            metrics["exact_match_rate"] = exact_matches / len(actual)
        else:
            metrics["exact_match_rate"] = 0.0

        # Position-wise accuracy
        position_matches = np.sum(actual == predicted)
        metrics["position_matches"] = position_matches
        if len(actual) > 0:
            metrics["position_accuracy"] = position_matches / len(actual)
        else:
            metrics["position_accuracy"] = 0.0

        # Distance-based metrics
        if len(actual) > 0 and len(predicted) > 0:
            metrics["mse"] = mean_squared_error(actual, predicted)
            metrics["mae"] = mean_absolute_error(actual, predicted)
        else:
            metrics["mse"] = float("nan")
            metrics["mae"] = float("nan")

        return metrics

    def backtest_model(self, prediction_service, data_path: str, test_size: int = 10) -> List[Dict]:
        """Perform backtesting on historical data.

        WARNING: This method is complex and requires careful integration with PredictionService.
        Currently returns empty results as it requires proper data pipeline setup.
        See CODE_REVIEW_BUGS.md for implementation details.

        Args:
            prediction_service: An initialized and trained PredictionService instance.
            data_path: Path to historical lottery data CSV file.
            test_size: Number of recent draws to backtest (default 10).

        Returns:
            List of evaluation results for each test period.
        """
        log.warning(
            "Backtest functionality requires proper data pipeline integration. "
            "Returning empty results. See CODE_REVIEW_BUGS.md for details."
        )
        return []

    def generate_report(self, results: List[Dict]) -> Dict[str, float]:
        """Generate summary report from evaluation results.

        Args:
            results: List of evaluation result dictionaries.

        Returns:
            Dictionary with aggregated metrics and statistics.
        """
        if not results:
            return {}

        report = {}

        # Average metrics
        for key in [
            "exact_matches",
            "exact_match_rate",
            "position_matches",
            "position_accuracy",
            "mse",
            "mae",
        ]:
            values = [r[key] for r in results if key in r and not np.isnan(r[key])]
            if values:
                report[f"avg_{key}"] = np.mean(values)
                report[f"std_{key}"] = np.std(values)

        # Best performance
        if results and "exact_matches" in results[0]:
            best_exact = max(results, key=lambda x: x.get("exact_matches", 0))
            report["best_exact_matches"] = best_exact.get("exact_matches", 0)

        return report
