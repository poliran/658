"""Optimized data processing with performance improvements."""
import pandas as pd
import numpy as np
from typing import Dict, Tuple
from functools import lru_cache

class OptimizedDataProcessor:
    """High-performance data processor with vectorized operations."""
    
    def __init__(self, config: Dict):
        self.config = config
        self.last_features = None
        self._feature_cache = {}
    
    def load_data(self, file_path: str) -> pd.DataFrame:
        """Load and validate lottery data with optimizations."""
        # Use efficient dtypes and parse dates during load
        dtype_dict = {
            'LOTTO GAME': 'category',
            'COMBINATIONS': 'string',
            'JACKPOT (PHP)': 'string',
            'WINNERS': 'int16'
        }
        
        df = pd.read_csv(
            file_path, 
            dtype=dtype_dict,
            parse_dates=['DRAW DATE'],
            date_parser=pd.to_datetime
        )
        
        self._validate_data(df)
        return self._preprocess_data_vectorized(df)
    
    def _validate_data(self, df: pd.DataFrame) -> None:
        """Fast validation using set operations."""
        required_cols = set(self.config['data']['validation']['required_columns'])
        actual_cols = set(df.columns)
        
        if not required_cols.issubset(actual_cols):
            missing = required_cols - actual_cols
            raise ValueError(f"Missing columns: {missing}")
    
    def _preprocess_data_vectorized(self, df: pd.DataFrame) -> pd.DataFrame:
        """Vectorized preprocessing pipeline."""
        df = df.copy()
        
        # Process dates (already parsed during load)
        df['DRAW_DATE'] = df['DRAW DATE']
        df = df.sort_values('DRAW_DATE').reset_index(drop=True)
        
        # Vectorized number extraction
        df = self._extract_numbers_vectorized(df)
        
        # Vectorized feature creation
        df = self._create_features_vectorized(df)
        
        return df
    
    def _extract_numbers_vectorized(self, df: pd.DataFrame) -> pd.DataFrame:
        """Extract numbers using vectorized operations."""
        # Single split operation for all rows
        numbers_split = df['COMBINATIONS'].str.split('-', expand=True).astype('int8')
        
        # Assign columns in one operation
        for i in range(6):
            df[f'num_{i+1}'] = numbers_split.iloc[:, i]
        
        return df
    
    def _create_features_vectorized(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create features using efficient vectorized operations."""
        # Get number columns as numpy array for speed
        num_cols = [f'num_{i}' for i in range(1, 7)]
        numbers_array = df[num_cols].values  # Shape: (n_rows, 6)
        
        # Vectorized frequency calculation using broadcasting
        # Create frequency matrix in one operation
        freq_matrix = self._calculate_frequencies_vectorized(numbers_array)
        
        # Add frequency columns efficiently
        for i, freq_col in enumerate(range(1, 59)):
            df[f'freq_{freq_col}'] = freq_matrix[:, i]
        
        # Vectorized pattern features
        df['sum_numbers'] = numbers_array.sum(axis=1)
        df['odd_count'] = (numbers_array % 2).sum(axis=1)
        df['low_count'] = (numbers_array <= 29).sum(axis=1)
        
        # Additional efficient features
        df['number_range'] = numbers_array.max(axis=1) - numbers_array.min(axis=1)
        df['number_std'] = numbers_array.std(axis=1)
        
        return df
    
    @lru_cache(maxsize=1)
    def _calculate_frequencies_vectorized(self, numbers_tuple) -> np.ndarray:
        """Calculate frequencies using vectorized operations with caching."""
        # Convert tuple back to array (needed for caching)
        numbers_array = np.array(numbers_tuple).reshape(-1, 6)
        
        # Create frequency matrix using broadcasting
        # Shape: (n_rows, 58) - each column represents frequency of number 1-58
        freq_matrix = np.zeros((numbers_array.shape[0], 58), dtype='int8')
        
        # Vectorized frequency calculation
        for i in range(1, 59):
            freq_matrix[:, i-1] = (numbers_array == i).sum(axis=1)
        
        return freq_matrix
    
    def prepare_training_data(self, df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        """Prepare training data with memory optimization."""
        # Use efficient column selection
        feature_cols = [col for col in df.columns 
                       if col.startswith('freq_') or 
                       col in ['sum_numbers', 'odd_count', 'low_count', 
                              'number_range', 'number_std']]
        
        # Use memory-efficient data types
        X = df[feature_cols].values.astype('float32')
        y = df[[f'num_{i}' for i in range(1, 7)]].values.astype('int8')
        
        self.last_features = X[-1:] if len(X) > 0 else None
        return X[:-1], y[1:]
    
    def prepare_next_draw_features(self) -> np.ndarray:
        """Get cached features for prediction."""
        if self.last_features is None:
            raise ValueError("No training data processed yet")
        return self.last_features
