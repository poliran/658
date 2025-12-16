"""Feature engineering implementations."""
import pandas as pd
import numpy as np
from typing import Dict
from ..interfaces import FeatureEngineer, LotteryConfig

class LotteryFeatureEngineer(FeatureEngineer):
    """Feature engineer for lottery data."""
    
    def __init__(self, config: LotteryConfig):
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
        numbers = df['COMBINATIONS'].str.split('-').apply(
            lambda x: [int(n) for n in x]
        )
        
        for i in range(self.config.numbers_per_draw):
            df[f'num_{i+1}'] = numbers.apply(
                lambda x: x[i] if len(x) > i else 0
            )
        
        return df
    
    def _create_frequency_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create number frequency features."""
        for num in self.config.number_range:
            df[f'freq_{num}'] = sum(
                (df[f'num_{i}'] == num).astype(int) 
                for i in range(1, self.config.numbers_per_draw + 1)
            )
        
        return df
    
    def _create_pattern_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create pattern-based features."""
        num_cols = [f'num_{i}' for i in range(1, self.config.numbers_per_draw + 1)]
        
        df['sum_numbers'] = df[num_cols].sum(axis=1)
        df['odd_count'] = (df[num_cols] % 2).sum(axis=1)
        df['low_count'] = (df[num_cols] <= self.config.max_number // 2).sum(axis=1)
        
        return df
