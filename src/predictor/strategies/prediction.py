"""Prediction strategy implementations."""
import numpy as np
from typing import List, Set
from ..interfaces import PredictionStrategy, LotteryConfig

class UniqueLotteryPredictionStrategy(PredictionStrategy):
    """Strategy for generating unique lottery predictions."""
    
    def __init__(self, config: LotteryConfig):
        self.config = config
    
    def predict(self, models: List, features: np.ndarray) -> np.ndarray:
        """Generate unique predictions using ensemble models."""
        predictions = []
        used_numbers = set()
        
        for model, scaler in models:
            pred = self._generate_unique_prediction(
                model, scaler, features, used_numbers
            )
            predictions.append(pred)
            used_numbers.add(pred)
        
        return np.sort(predictions)
    
    def _generate_unique_prediction(self, model, scaler, features: np.ndarray, 
                                  used_numbers: Set[int]) -> int:
        """Generate a unique prediction avoiding used numbers."""
        features_scaled = scaler.transform(features)
        prediction = model.predict(features_scaled)[0]
        
        # Clamp to valid range
        predicted_num = max(
            self.config.min_number, 
            min(self.config.max_number, round(prediction))
        )
        
        # Find unused number
        if predicted_num in used_numbers:
            for offset in range(1, self.config.max_number):
                for candidate in [predicted_num + offset, predicted_num - offset]:
                    if (self.config.min_number <= candidate <= self.config.max_number 
                        and candidate not in used_numbers):
                        return candidate
        
        return predicted_num

class TopKPredictionStrategy(PredictionStrategy):
    """Strategy for selecting top-K most likely numbers."""
    
    def __init__(self, config: LotteryConfig):
        self.config = config
    
    def predict(self, models: List, features: np.ndarray) -> np.ndarray:
        """Generate predictions by selecting top-K numbers."""
        # Aggregate predictions from all models
        all_predictions = []
        
        for model, scaler in models:
            features_scaled = scaler.transform(features)
            pred = model.predict(features_scaled)[0]
            all_predictions.append(pred)
        
        # Select top numbers based on aggregated scores
        scores = np.mean(all_predictions, axis=0) if len(all_predictions) > 1 else all_predictions[0]
        top_indices = np.argsort(scores)[-self.config.numbers_per_draw:]
        
        return np.sort(top_indices + self.config.min_number)
