"""PredictionOrchestrator — coordinates PredictionService calls, returns raw prediction sets."""

import numpy as np
from typing import Dict, Any
from .prediction_service import PredictionService
from .constants import FilePaths


class PredictionOrchestrator:
    """Thin coordinator: trains the service and collects raw prediction sets."""

    def __init__(self, service: PredictionService, model_config: Dict = None):
        self.service = service
        self.model_config = model_config or {}
        self.features: np.ndarray = None
        self.is_trained = False

    def train(self, data_path: str = None) -> None:
        data_path = data_path or FilePaths.DEFAULT_DATA_FILE
        self.service.train(data_path, self.model_config)
        self.features = self.service.prepare_features(data_path)
        self.is_trained = True

    def get_predictions(self) -> Dict[str, Any]:
        """Return all raw prediction sets."""
        self._ensure_trained()
        return {
            "standard": self.service.predict(self.features),
            "optimized": self.service.predict_optimized(self.features),
            "anti_popular": self.service.predict_anti_popular(self.features, count=3),
            "multiple_sets": [self.service.predict(self.features) for _ in range(5)],
            "risk_analysis": self.service.optimizer.analyze_sharing_risk(
                self.service.predict_optimized(self.features)
            ),
        }

    def _ensure_trained(self) -> None:
        if not self.is_trained:
            raise ValueError("Call train() first.")
