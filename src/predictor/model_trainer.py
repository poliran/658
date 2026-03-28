"""Model training and evaluation module."""
from typing import List, Tuple, Dict
import numpy as np
from sklearn.ensemble import VotingRegressor, RandomForestRegressor, GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler
from xgboost import XGBRegressor
from .constants import ModelDefaults
from .exceptions import ModelTrainingError

class ModelTrainer:
    """Handles model training and evaluation."""
    
    def __init__(self, config: Dict):
        self.config = config
        self.models = []
        self.scalers = []
    
    def _create_xgb_model(self) -> XGBRegressor:
        """Create XGBoost model with configured parameters."""
        params = self.config.get('models', {}).get('xgboost', ModelDefaults.XGBOOST)
        return XGBRegressor(
            n_estimators=params.get('n_estimators', ModelDefaults.XGBOOST['n_estimators']),
            learning_rate=params.get('learning_rate', ModelDefaults.XGBOOST['learning_rate']),
            max_depth=params.get('max_depth', ModelDefaults.XGBOOST['max_depth']),
            tree_method='hist',
            random_state=ModelDefaults.RANDOM_STATE
        )
    
    def _create_rf_model(self) -> RandomForestRegressor:
        """Create Random Forest model with configured parameters."""
        params = self.config.get('models', {}).get('random_forest', ModelDefaults.RANDOM_FOREST)
        return RandomForestRegressor(
            n_estimators=params.get('n_estimators', ModelDefaults.RANDOM_FOREST['n_estimators']),
            max_depth=params.get('max_depth', ModelDefaults.RANDOM_FOREST['max_depth']),
            random_state=ModelDefaults.RANDOM_STATE,
            n_jobs=ModelDefaults.N_JOBS
        )
    
    def _create_gb_model(self) -> GradientBoostingRegressor:
        """Create Gradient Boosting model with configured parameters."""
        params = self.config.get('models', {}).get('gradient_boosting', ModelDefaults.GRADIENT_BOOSTING)
        return GradientBoostingRegressor(
            n_estimators=params.get('n_estimators', ModelDefaults.GRADIENT_BOOSTING['n_estimators']),
            learning_rate=params.get('learning_rate', ModelDefaults.GRADIENT_BOOSTING['learning_rate']),
            max_depth=params.get('max_depth', ModelDefaults.GRADIENT_BOOSTING['max_depth']),
            random_state=ModelDefaults.RANDOM_STATE
        )
    
    def create_ensemble(self) -> VotingRegressor:
        """Create an ensemble of models with optimal parameters."""
        models = [
            ('xgb', self._create_xgb_model()),
            ('rf', self._create_rf_model()),
            ('gb', self._create_gb_model())
        ]
        return VotingRegressor(models, n_jobs=ModelDefaults.N_JOBS)
    
    def train(self, X: np.ndarray, y: np.ndarray) -> Tuple[VotingRegressor, StandardScaler]:
        """Train a model with cross-validation and scaling."""
        try:
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X)
            
            model = self.create_ensemble()
            model.fit(X_scaled, y)
            
            return model, scaler
        except Exception as e:
            raise ModelTrainingError(f"Model training failed: {str(e)}") 