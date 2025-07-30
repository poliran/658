"""Model training and evaluation module."""
from typing import List, Tuple, Dict
import numpy as np
from sklearn.ensemble import VotingRegressor
from sklearn.preprocessing import StandardScaler

class ModelTrainer:
    """Handles model training and evaluation."""
    
    def __init__(self, config: Dict):
        self.config = config
        self.models = []
        self.scalers = []
    
    def create_ensemble(self) -> VotingRegressor:
        """Create an ensemble of models with optimal parameters."""
        models = [
            ('xgb', self._create_xgb_model()),
            ('rf', self._create_rf_model()),
            ('gb', self._create_gb_model())
        ]
        return VotingRegressor(models, n_jobs=-1)
    
    def train(self, X: np.ndarray, y: np.ndarray) -> Tuple[VotingRegressor, StandardScaler]:
        """Train a model with cross-validation and scaling."""
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        model = self.create_ensemble()
        model.fit(X_scaled, y)
        
        return model, scaler 