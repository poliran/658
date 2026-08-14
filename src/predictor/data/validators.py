"""Data validation implementations."""

import pandas as pd
from typing import List
from ..interfaces import DataValidator


class LotteryDataValidator(DataValidator):
    """Validator for lottery data structure."""

    def __init__(self, required_columns: List[str]):
        self.required_columns = required_columns

    def validate(self, data: pd.DataFrame) -> bool:
        """Validate lottery data structure."""
        missing_cols = [col for col in self.required_columns if col not in data.columns]

        if missing_cols:
            raise ValueError(f"Missing required columns: {missing_cols}")

        if data.empty:
            raise ValueError("Data is empty")

        return True
