"""Optimized data processing with performance improvements."""
import pandas as pd
import numpy as np
from typing import Dict, Tuple
from functools import lru_cache
from .constants import LotteryConstants, DEFAULT_LOTTERY, ColumnNames
from .exceptions import DataProcessingError
from .validators import DataValidator

class OptimizedDataProcessor:
    """High-performance data processor with vectorized operations."""
    
    def __init__(self, config: Dict, lottery_type=DEFAULT_LOTTERY):
        self.config = config
        self.lottery_type = lottery_type
        self.lottery_config = LotteryConstants.get_config(lottery_type)
        self.last_features = None
        self._feature_cache = {}
    
    def load_data(self, file_path: str) -> pd.DataFrame:
        """Load and validate lottery data with optimizations."""
        # Use efficient dtypes and parse dates during load
        dtype_dict = {
            ColumnNames.LOTTO_GAME: 'category',
            ColumnNames.COMBINATIONS: 'string',
            ColumnNames.JACKPOT: 'string',
            ColumnNames.WINNERS: 'int16'
        }
        
        try:
            DataValidator.validate_file_path(file_path)
            
            df = pd.read_csv(
                file_path, 
                dtype=dtype_dict,
                parse_dates=[ColumnNames.DRAW_DATE],
                date_parser=pd.to_datetime
            )
            
            self._validate_data(df)
            return self._preprocess_data_vectorized(df)
        except Exception as e:
            raise DataProcessingError(f"Optimized data loading failed: {str(e)}")
    
    def _validate_data(self, df: pd.DataFrame) -> None:
        """Fast validation using set operations."""
        required_cols = set(self.config['data']['validation']['required_columns'])
        actual_cols = set(df.columns)
        
        if not required_cols.issubset(actual_cols):
            missing = required_cols - actual_cols
            raise DataProcessingError(f"Missing columns: {missing}")
    
    def _preprocess_data_vectorized(self, df: pd.DataFrame) -> pd.DataFrame:
        """Vectorized preprocessing pipeline."""
        df = df.copy()
        
        # Process dates (already parsed during load)
        df[ColumnNames.DRAW_DATE_PROCESSED] = df[ColumnNames.DRAW_DATE]
        df = df.sort_values(ColumnNames.DRAW_DATE_PROCESSED).reset_index(drop=True)
        
        # Vectorized number extraction
        df = self._extract_numbers_vectorized(df)
        
        # Vectorized feature creation
        df = self._create_features_vectorized(df)
        
        return df
    
    def _extract_numbers_vectorized(self, df: pd.DataFrame) -> pd.DataFrame:
        """Extract numbers using vectorized operations."""
        # Single split operation for all rows
        numbers_split = df[ColumnNames.COMBINATIONS].str.split('-', expand=True).astype('int8')
        
        # Assign columns in one operation
        number_columns = ColumnNames.get_number_columns(self.lottery_config["numbers_per_draw"])
        for i, col in enumerate(number_columns):
            df[col] = numbers_split.iloc[:, i]
        
        return df
    
    def _create_features_vectorized(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create features using efficient vectorized operations."""
        # Get number columns as numpy array for speed
        number_columns = ColumnNames.get_number_columns(self.lottery_config["numbers_per_draw"])
        numbers_array = df[number_columns].values
        
        # Vectorized frequency calculation using broadcasting
        freq_matrix = self._calculate_frequencies_vectorized(numbers_array)
        
        # Add frequency columns efficiently
        number_range = LotteryConstants.get_number_range(self.lottery_type)
        for i, num in enumerate(number_range):
            df[f'freq_{num}'] = freq_matrix[:, i]
        
        # Vectorized pattern features
        df['sum_numbers'] = numbers_array.sum(axis=1)
        df['odd_count'] = (numbers_array % 2).sum(axis=1)
        df['low_count'] = (numbers_array <= self.lottery_config["max_number"] // 2).sum(axis=1)
        
        # Additional efficient features
        df['number_range'] = numbers_array.max(axis=1) - numbers_array.min(axis=1)
        df['number_std'] = numbers_array.std(axis=1)
        
        return df
    
    def _calculate_frequencies_vectorized(self, numbers_array) -> np.ndarray:
        """Calculate frequencies using vectorized operations."""
        number_range = LotteryConstants.get_number_range(self.lottery_type)
        freq_matrix = np.zeros((numbers_array.shape[0], len(number_range)), dtype='int8')
        
        # Vectorized frequency calculation
        for i, num in enumerate(number_range):
            freq_matrix[:, i] = (numbers_array == num).sum(axis=1)
        
        return freq_matrix
    
    def prepare_training_data(self, df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        """Prepare training data with memory optimization."""
        # Use efficient column selection
        freq_columns = ColumnNames.get_frequency_columns(self.lottery_config["max_number"])
        feature_cols = [col for col in df.columns 
                       if col in freq_columns or 
                       col in ['sum_numbers', 'odd_count', 'low_count', 
                              'number_range', 'number_std']]
        
        # Use memory-efficient data types
        X = df[feature_cols].values.astype('float32')
        number_columns = ColumnNames.get_number_columns(self.lottery_config["numbers_per_draw"])
        y = df[number_columns].values.astype('int8')
        
        self.last_features = X[-1:] if len(X) > 0 else None
        return X[:-1], y[1:]
    
    def prepare_next_draw_features(self) -> np.ndarray:
        """Get cached features for prediction."""
        if self.last_features is None:
            raise DataProcessingError("No training data processed yet")
        return self.last_features
