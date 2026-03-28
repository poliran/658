"""Model factory implementations."""
from typing import Dict, Any
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor, VotingRegressor
from xgboost import XGBRegressor
from ..interfaces import ModelFactory

class SklearnModelFactory(ModelFactory):
    """Factory for scikit-learn based models."""
    
    def create_model(self, model_type: str, config: Dict) -> Any:
        """Create a model instance based on type and config."""
        if model_type == 'xgboost':
            return self._create_xgb_model(config)
        elif model_type == 'random_forest':
            return self._create_rf_model(config)
        elif model_type == 'gradient_boosting':
            return self._create_gb_model(config)
        elif model_type == 'ensemble':
            return self._create_ensemble(config)
        else:
            raise ValueError(f"Unknown model type: {model_type}")
    
    def _create_xgb_model(self, config: Dict) -> XGBRegressor:
        """Create XGBoost model."""
        return XGBRegressor(
            n_estimators=config.get('n_estimators', 100),
            learning_rate=config.get('learning_rate', 0.1),
            max_depth=config.get('max_depth', 6),
            tree_method='hist',
            random_state=42
        )
    
    def _create_rf_model(self, config: Dict) -> RandomForestRegressor:
        """Create Random Forest model."""
        return RandomForestRegressor(
            n_estimators=config.get('n_estimators', 100),
            max_depth=config.get('max_depth', 10),
            random_state=42
        )
    
    def _create_gb_model(self, config: Dict) -> GradientBoostingRegressor:
        """Create Gradient Boosting model."""
        return GradientBoostingRegressor(
            n_estimators=config.get('n_estimators', 100),
            learning_rate=config.get('learning_rate', 0.1),
            max_depth=config.get('max_depth', 6),
            random_state=42
        )
    
    def _create_ensemble(self, config: Dict) -> VotingRegressor:
        """Create ensemble model."""
        models = [
            ('xgb', self._create_xgb_model(config.get('xgboost', {}))),
            ('rf', self._create_rf_model(config.get('random_forest', {}))),
            ('gb', self._create_gb_model(config.get('gradient_boosting', {})))
        ]
        return VotingRegressor(models, n_jobs=-1)
