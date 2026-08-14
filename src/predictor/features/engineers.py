"""Feature engineering implementations."""

import pandas as pd
from typing import Dict, Any
from ..interfaces import FeatureEngineer


class LotteryFeatureEngineer(FeatureEngineer):
    """Feature engineer for lottery data."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize feature engineer with lottery configuration.

        Args:
            config: Dictionary with keys: min_number, max_number, numbers_per_draw
        """
        self.config = config

    def create_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """Create lottery-specific features."""
        df = data.copy()

        # Extract individual numbers
        df = self._extract_numbers(df)

        # Create frequency features
        df = self._create_frequency_features(df)

        # Create pattern features
        df = self._create_pattern_features(df)

        return df

    def _extract_numbers(self, df: pd.DataFrame) -> pd.DataFrame:
        """Extract individual numbers from combinations."""
        numbers = df["COMBINATIONS"].str.split("-").apply(lambda x: [int(n) for n in x])
        assignments = {
            f"num_{i+1}": numbers.apply(lambda x: x[i] if len(x) > i else 0)
            for i in range(self.config["numbers_per_draw"])
        }
        return df.assign(**assignments)

    def _create_frequency_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create number frequency features."""
        number_range = range(self.config["min_number"], self.config["max_number"] + 1)
        assignments = {
            f"freq_{num}": sum(
                (df[f"num_{i}"] == num).astype(int)
                for i in range(1, self.config["numbers_per_draw"] + 1)
            )
            for num in number_range
        }
        return df.assign(**assignments)

    def _create_pattern_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create pattern-based features."""
        num_cols = [f"num_{i}" for i in range(1, self.config["numbers_per_draw"] + 1)]
        return df.assign(
            sum_numbers=df[num_cols].sum(axis=1),
            odd_count=(df[num_cols] % 2).sum(axis=1),
            low_count=(df[num_cols] <= self.config["max_number"] // 2).sum(axis=1),
        )
