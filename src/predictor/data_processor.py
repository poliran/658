"""Data processing module for lottery prediction."""
from typing import Dict, List, Tuple
import pandas as pd
import numpy as np
from datetime import datetime
from .constants import LotteryConstants, DEFAULT_LOTTERY, ColumnNames
from .exceptions import DataProcessingError, ValidationError
from .validators import DataValidator

class DataProcessor:
    """Handles all data preprocessing operations."""
    
    def __init__(self, config: Dict, lottery_type=DEFAULT_LOTTERY):
        self.config = config
        self.lottery_type = lottery_type
        self.lottery_config = LotteryConstants.get_config(lottery_type)
        self.last_features = None
        
    def load_data(self, file_path: str) -> pd.DataFrame:
        """Load and validate lottery data."""
        try:
            # Comprehensive file validation
            validated_path = DataValidator.validate_file_path(file_path)
            
            # Load data with validation
            df = pd.read_csv(validated_path)
            
            # Validate data structure and content
            required_columns = self.config['data']['validation']['required_columns']
            DataValidator.validate_dataframe(df, required_columns)
            
            return self._preprocess_data(df)
        except Exception as e:
            raise DataProcessingError(f"Data loading failed: {str(e)}")
    
    def _validate_data(self, df: pd.DataFrame) -> None:
        """Validate input data structure."""
        required_columns = self.config['data']['validation']['required_columns']
        DataValidator.validate_dataframe(df, required_columns)
    
    def _preprocess_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Apply all preprocessing steps."""
        df = self._process_dates(df)
        df = self._extract_numbers(df)
        df = self._create_features(df)
        return df
    
    def _process_dates(self, df: pd.DataFrame) -> pd.DataFrame:
        """Convert date strings to datetime objects."""
        df[ColumnNames.DRAW_DATE_PROCESSED] = pd.to_datetime(df[ColumnNames.DRAW_DATE])
        df = df.sort_values(ColumnNames.DRAW_DATE_PROCESSED).reset_index(drop=True)
        return df
    
    def _extract_numbers(self, df: pd.DataFrame) -> pd.DataFrame:
        """Extract individual numbers from combination strings."""
        numbers = df[ColumnNames.COMBINATIONS].str.split('-').apply(lambda x: [int(n) for n in x])
        
        number_columns = ColumnNames.get_number_columns(self.lottery_config["numbers_per_draw"])
        for i, col in enumerate(number_columns):
            df[col] = numbers.apply(lambda x: x[i] if len(x) > i else 0)
        
        return df
    
    def _create_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create engineered features for prediction."""
        number_range = LotteryConstants.get_number_range(self.lottery_type)
        number_columns = ColumnNames.get_number_columns(self.lottery_config["numbers_per_draw"])
        
        # Number frequency features
        for num in number_range:
            df[f'freq_{num}'] = sum((df[col] == num).astype(int) for col in number_columns)
        
        # Pattern features
        df['sum_numbers'] = df[number_columns].sum(axis=1)
        df['odd_count'] = (df[number_columns] % 2).sum(axis=1)
        df['low_count'] = (df[number_columns] <= self.lottery_config["max_number"] // 2).sum(axis=1)
        
        return df
    
    def prepare_training_data(self, df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        """Prepare features and targets for training."""
        if df is None or df.empty:
            raise ValidationError("DataFrame cannot be None or empty")
        
        freq_columns = ColumnNames.get_frequency_columns(self.lottery_config["max_number"])
        feature_cols = [col for col in df.columns if col in freq_columns or 
                       col in ['sum_numbers', 'odd_count', 'low_count']]
        
        if not feature_cols:
            raise ValidationError("No valid feature columns found")
        
        X = df[feature_cols].values
        number_columns = ColumnNames.get_number_columns(self.lottery_config["numbers_per_draw"])
        
        # Validate number columns exist
        missing_cols = [col for col in number_columns if col not in df.columns]
        if missing_cols:
            raise ValidationError(f"Missing number columns: {missing_cols}")
        
        y = df[number_columns].values
        
        # Validate training data
        from .validators import ModelValidator
        ModelValidator.validate_training_data(X[:-1], y[1:])
        
        self.last_features = X[-1:] if len(X) > 0 else None
        return X[:-1], y[1:]  # Use previous draws to predict next
    
    def prepare_next_draw_features(self) -> np.ndarray:
        """Prepare features for next draw prediction."""
        if self.last_features is None:
            raise ValidationError("No training data processed yet")
        
        # Validate features before returning
        DataValidator.validate_features(self.last_features)
        return self.last_features 