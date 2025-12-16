"""Data processing module for lottery prediction."""
from typing import Dict, List, Tuple
import pandas as pd
import numpy as np
from datetime import datetime

class DataProcessor:
    """Handles all data preprocessing operations."""
    
    def __init__(self, config: Dict):
        self.config = config
        self.last_features = None
        
    def load_data(self, file_path: str) -> pd.DataFrame:
        """Load and validate lottery data."""
        try:
            df = pd.read_csv(file_path)
            self._validate_data(df)
            return self._preprocess_data(df)
        except Exception as e:
            raise ValueError(f"Data loading failed: {str(e)}")
    
    def _validate_data(self, df: pd.DataFrame) -> None:
        """Validate input data structure."""
        required_columns = self.config['data']['validation']['required_columns']
        if not all(col in df.columns for col in required_columns):
            raise ValueError(f"Missing required columns: {required_columns}")
    
    def _preprocess_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Apply all preprocessing steps."""
        df = self._process_dates(df)
        df = self._extract_numbers(df)
        df = self._create_features(df)
        return df
    
    def _process_dates(self, df: pd.DataFrame) -> pd.DataFrame:
        """Convert date strings to datetime objects."""
        df['DRAW_DATE'] = pd.to_datetime(df['DRAW DATE'])
        df = df.sort_values('DRAW_DATE').reset_index(drop=True)
        return df
    
    def _extract_numbers(self, df: pd.DataFrame) -> pd.DataFrame:
        """Extract individual numbers from combination strings."""
        numbers = df['COMBINATIONS'].str.split('-').apply(lambda x: [int(n) for n in x])
        for i in range(6):
            df[f'num_{i+1}'] = numbers.apply(lambda x: x[i] if len(x) > i else 0)
        return df
    
    def _create_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create engineered features for prediction."""
        # Number frequency features
        for i in range(1, 59):
            df[f'freq_{i}'] = 0
            for j in range(1, 7):
                df[f'freq_{i}'] += (df[f'num_{j}'] == i).astype(int)
        
        # Pattern features
        df['sum_numbers'] = sum(df[f'num_{i}'] for i in range(1, 7))
        df['odd_count'] = sum((df[f'num_{i}'] % 2) for i in range(1, 7))
        df['low_count'] = sum((df[f'num_{i}'] <= 29).astype(int) for i in range(1, 7))
        
        return df
    
    def prepare_training_data(self, df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        """Prepare features and targets for training."""
        feature_cols = [col for col in df.columns if col.startswith('freq_') or 
                       col in ['sum_numbers', 'odd_count', 'low_count']]
        
        X = df[feature_cols].values
        y = df[[f'num_{i}' for i in range(1, 7)]].values
        
        self.last_features = X[-1:] if len(X) > 0 else None
        return X[:-1], y[1:]  # Use previous draws to predict next
    
    def prepare_next_draw_features(self) -> np.ndarray:
        """Prepare features for next draw prediction."""
        if self.last_features is None:
            raise ValueError("No training data processed yet")
        return self.last_features 