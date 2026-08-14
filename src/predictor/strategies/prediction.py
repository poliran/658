"""Prediction strategy implementations."""

import numpy as np
from typing import List, Set, Dict, Any
from ..interfaces import PredictionStrategy


class UniqueLotteryPredictionStrategy(PredictionStrategy):
    """Strategy for generating unique lottery predictions."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize strategy with lottery configuration.

        Args:
            config: Dictionary with keys: min_number, max_number, numbers_per_draw
        """
        self.config = config

    def predict(self, models: List, features: np.ndarray) -> np.ndarray:
        """Generate unique predictions using ensemble models."""
        predictions = []
        used_numbers = set()

        for model, scaler in models:
            pred = self._generate_unique_prediction(model, scaler, features, used_numbers)
            predictions.append(pred)
            used_numbers.add(pred)

        return np.sort(predictions)

    def _generate_unique_prediction(
        self, model, scaler, features: np.ndarray, used_numbers: Set[int]
    ) -> int:
        """Generate a unique prediction avoiding used numbers."""
        features_scaled = scaler.transform(features)
        prediction = model.predict(features_scaled)[0]

        # Clamp to valid range
        predicted_num = max(
            self.config["min_number"], min(self.config["max_number"], round(prediction))
        )

        # Find unused number
        if predicted_num in used_numbers:
            for offset in range(1, self.config["max_number"]):
                for candidate in [predicted_num + offset, predicted_num - offset]:
                    if (
                        self.config["min_number"] <= candidate <= self.config["max_number"]
                        and candidate not in used_numbers
                    ):
                        return candidate

        return predicted_num


class TopKPredictionStrategy(PredictionStrategy):
    """Strategy for selecting top-K most likely numbers."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize strategy with lottery configuration.

        Args:
            config: Dictionary with keys: min_number, max_number, numbers_per_draw
        """
        self.config = config

    def predict(self, models: List, features: np.ndarray) -> np.ndarray:
        """Generate predictions by selecting top-K numbers.

        For each model, get a single prediction value, then select the K highest values.

        Args:
            models: List of (model, scaler) tuples trained per position
            features: Feature array (1, n_features)

        Returns:
            Sorted array of K unique lottery numbers
        """
        # Aggregate predictions from all models
        predictions = []

        for model, scaler in models:
            features_scaled = scaler.transform(features)
            pred = model.predict(features_scaled)[0]
            predictions.append(pred)

        # Predictions is now a list of scalars, one per model
        # Find the K highest scoring predictions
        predictions = np.array(predictions)

        # Get indices of top K predictions
        if len(predictions) > self.config["numbers_per_draw"]:
            top_indices = np.argsort(predictions)[-self.config["numbers_per_draw"] :]
        else:
            top_indices = np.arange(len(predictions))

        # Convert indices to lottery numbers (scaled to valid range)
        top_values = predictions[top_indices]
        selected_numbers = np.clip(
            np.round(top_values).astype(int), self.config["min_number"], self.config["max_number"]
        )

        # Remove duplicates if any
        selected_numbers = np.unique(selected_numbers)

        # If we lost numbers due to duplicates, fill with nearby numbers
        while len(selected_numbers) < self.config["numbers_per_draw"]:
            for candidate in range(self.config["min_number"], self.config["max_number"] + 1):
                if candidate not in selected_numbers:
                    selected_numbers = np.append(selected_numbers, candidate)
                    break

        return np.sort(selected_numbers[: self.config["numbers_per_draw"]])
