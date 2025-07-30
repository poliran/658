"""Data processing module for lottery prediction."""
from typing import Dict, List, Tuple
import pandas as pd
import numpy as np

class DataProcessor:
    """Handles all data preprocessing operations."""
    
    def __init__(self, config: Dict):
        self.config = config
        
    def load_data(self, file_path: str) -> pd.DataFrame:
        """Load and validate lottery data."""
        try:
            df = pd.read_csv(file_path, dtype=str)
            self._validate_data(df)
            return self._preprocess_data(df)
        except Exception as e:
            raise ValueError(f"Data loading failed: {str(e)}")
    
    def _validate_data(self, df: pd.DataFrame) -> None:
        """Validate input data structure."""
        required_columns = ["LOTTO_GAME", "COMBINATIONS", "DRAW_DATE"]
        if not all(col in df.columns for col in required_columns):
            raise ValueError(f"Missing required columns: {required_columns}")
    
    def _preprocess_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Apply all preprocessing steps."""
        df = self._process_dates(df)
        df = self._extract_numbers(df)
        df = self._create_features(df)
        return df 