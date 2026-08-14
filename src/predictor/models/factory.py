"""Model factory implementations."""

import logging
from typing import Dict, Any
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor, VotingRegressor
from xgboost import XGBRegressor
from ..interfaces import ModelFactory

log = logging.getLogger(__name__)


class SklearnModelFactory(ModelFactory):
    """Factory for scikit-learn based models."""

    def create_model(self, model_type: str, config: Dict) -> Any:
        """Create a model instance based on type and config.

        Args:
            model_type: Model type (xgboost, random_forest, gradient_boosting, or
                ensemble).
            config: Configuration dict with model parameters.

        Returns:
            Initialized model instance.

        Raises:
            ValueError: If model_type is unknown or config is invalid.
        """
        if not isinstance(config, dict):
            log.warning(f"Config must be dict, got {type(config)}. Using empty dict.")
            config = {}

        if model_type == "xgboost":
            return self._create_xgb_model(config)
        elif model_type == "random_forest":
            return self._create_rf_model(config)
        elif model_type == "gradient_boosting":
            return self._create_gb_model(config)
        elif model_type == "ensemble":
            return self._create_ensemble(config)
        else:
            raise ValueError(
                f"Unknown model type: {model_type}. Supported: "
                f"xgboost, random_forest, gradient_boosting, ensemble"
            )

    def _create_xgb_model(self, config: Dict) -> XGBRegressor:
        """Create XGBoost model with configured parameters."""
        params = config.get("xgboost", {})
        return XGBRegressor(
            n_estimators=params.get("n_estimators", 100),
            learning_rate=params.get("learning_rate", 0.1),
            max_depth=params.get("max_depth", 6),
            tree_method="hist",
            random_state=42,
        )

    def _create_rf_model(self, config: Dict) -> RandomForestRegressor:
        """Create Random Forest model with configured parameters."""
        params = config.get("random_forest", {})
        return RandomForestRegressor(
            n_estimators=params.get("n_estimators", 100),
            max_depth=params.get("max_depth", 10),
            random_state=42,
            n_jobs=-1,
        )

    def _create_gb_model(self, config: Dict) -> GradientBoostingRegressor:
        """Create Gradient Boosting model with configured parameters."""
        params = config.get("gradient_boosting", {})
        return GradientBoostingRegressor(
            n_estimators=params.get("n_estimators", 100),
            learning_rate=params.get("learning_rate", 0.1),
            max_depth=params.get("max_depth", 6),
            random_state=42,
        )

    def _create_ensemble(self, config: Dict) -> VotingRegressor:
        """Create ensemble model combining multiple estimators."""
        models = [
            ("xgb", self._create_xgb_model(config)),
            ("rf", self._create_rf_model(config)),
            ("gb", self._create_gb_model(config)),
        ]
        return VotingRegressor(models, n_jobs=-1)
