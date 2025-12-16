"""Improved lottery predictor with proper architecture."""
import numpy as np
import pandas as pd
from typing import List, Tuple, Dict
from sklearn.preprocessing import StandardScaler

from .interfaces import (
    DataLoader, DataValidator, FeatureEngineer, 
    ModelFactory, PredictionStrategy, LotteryConfig
)

class ImprovedLotteryPredictor:
    """Improved lottery predictor with proper separation of concerns."""
    
    def __init__(self, 
                 data_loader: DataLoader,
                 data_validator: DataValidator,
                 feature_engineer: FeatureEngineer,
                 model_factory: ModelFactory,
                 prediction_strategy: PredictionStrategy,
                 config: LotteryConfig):
        
        self.data_loader = data_loader
        self.data_validator = data_validator
        self.feature_engineer = feature_engineer
        self.model_factory = model_factory
        self.prediction_strategy = prediction_strategy
        self.config = config
        
        self.models: List[Tuple] = []
        self.is_trained = False
    
    def train(self, data_source: str, model_config: Dict) -> None:
        """Train the prediction models."""
        # Load and validate data
        raw_data = self.data_loader.load(data_source)
        self.data_validator.validate(raw_data)
        
        # Process dates and create features
        processed_data = self._process_dates(raw_data)
        featured_data = self.feature_engineer.create_features(processed_data)
        
        # Prepare training data
        X, y = self._prepare_training_data(featured_data)
        
        # Train models for each position
        self.models = []
        for i in range(self.config.numbers_per_draw):
            model = self.model_factory.create_model('ensemble', model_config)
            scaler = StandardScaler()
            
            X_scaled = scaler.fit_transform(X)
            model.fit(X_scaled, y[:, i])
            
            self.models.append((model, scaler))
        
        self.is_trained = True
    
    def predict(self, data_source: str = None) -> np.ndarray:
        """Generate predictions for next draw."""
        if not self.is_trained:
            raise ValueError("Model must be trained before prediction")
        
        # Use last training features or load new data
        if data_source:
            raw_data = self.data_loader.load(data_source)
            processed_data = self._process_dates(raw_data)
            featured_data = self.feature_engineer.create_features(processed_data)
            features = self._get_latest_features(featured_data)
        else:
            features = self._get_latest_features()
        
        return self.prediction_strategy.predict(self.models, features)
    
    def _process_dates(self, df: pd.DataFrame) -> pd.DataFrame:
        """Process date columns."""
        df = df.copy()
        df['DRAW_DATE'] = pd.to_datetime(df['DRAW DATE'])
        return df.sort_values('DRAW_DATE').reset_index(drop=True)
    
    def _prepare_training_data(self, df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        """Prepare features and targets for training."""
        feature_cols = [col for col in df.columns 
                       if col.startswith('freq_') or 
                       col in ['sum_numbers', 'odd_count', 'low_count']]
        
        X = df[feature_cols].values
        y = df[[f'num_{i}' for i in range(1, self.config.numbers_per_draw + 1)]].values
        
        self.last_features = X[-1:] if len(X) > 0 else None
        return X[:-1], y[1:]  # Use previous draws to predict next
    
    def _get_latest_features(self, df: pd.DataFrame = None) -> np.ndarray:
        """Get features for latest draw."""
        if df is not None:
            feature_cols = [col for col in df.columns 
                           if col.startswith('freq_') or 
                           col in ['sum_numbers', 'odd_count', 'low_count']]
            return df[feature_cols].values[-1:]
        
        if self.last_features is None:
            raise ValueError("No training data available for prediction")
        
        return self.last_features
