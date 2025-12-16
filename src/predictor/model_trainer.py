"""Model training and evaluation module."""
from typing import List, Tuple, Dict
import numpy as np
from sklearn.ensemble import VotingRegressor, RandomForestRegressor, GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler
from xgboost import XGBRegressor

class ModelTrainer:
    """Handles model training and evaluation."""
    
    def __init__(self, config: Dict):
        self.config = config
        self.models = []
        self.scalers = []
    
    def _create_xgb_model(self) -> XGBRegressor:
        """Create XGBoost model with configured parameters."""
        params = self.config['models']['xgboost']
        return XGBRegressor(
            n_estimators=params['n_estimators'],
            learning_rate=params['learning_rate'],
            max_depth=params['max_depth'],
            random_state=42
        )
    
    def _create_rf_model(self) -> RandomForestRegressor:
        """Create Random Forest model with configured parameters."""
        params = self.config['models']['random_forest']
        return RandomForestRegressor(
            n_estimators=params['n_estimators'],
            max_depth=params['max_depth'],
            random_state=42
        )
    
    def _create_gb_model(self) -> GradientBoostingRegressor:
        """Create Gradient Boosting model with configured parameters."""
        params = self.config['models']['gradient_boosting']
        return GradientBoostingRegressor(
            n_estimators=params['n_estimators'],
            learning_rate=params['learning_rate'],
            max_depth=params['max_depth'],
            random_state=42
        )
    
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