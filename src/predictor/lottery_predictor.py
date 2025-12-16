"""Main lottery prediction module."""
from typing import List, Optional
import numpy as np
import yaml
from .data_processor import DataProcessor
from .model_trainer import ModelTrainer
from .constants import LotteryConstants, DEFAULT_LOTTERY, FilePaths
from .exceptions import PredictionError, ConfigurationError
from .validators import DataValidator

class LotteryPredictor:
    """Main class for lottery number prediction."""
    
    def __init__(self, config_path: str, lottery_type=DEFAULT_LOTTERY):
        self.config = self._load_config(config_path)
        self.lottery_type = lottery_type
        self.lottery_config = LotteryConstants.get_config(lottery_type)
        self.data_processor = DataProcessor(self.config, lottery_type)
        self.model_trainer = ModelTrainer(self.config)
        self.models: List = []
        
    @staticmethod
    def _load_config(config_path: str) -> dict:
        """Load configuration from YAML file."""
        try:
            from .validators import ConfigValidator
            return ConfigValidator.validate_config_file(config_path)
        except Exception as e:
            raise ConfigurationError(f"Failed to load config: {str(e)}")
    
    def train(self, data_path: str) -> None:
        """Train the prediction models."""
        try:
            # Validate inputs
            if not data_path or not isinstance(data_path, str):
                raise ValidationError("Data path must be a non-empty string")
            
            df = self.data_processor.load_data(data_path)
            X, y = self.data_processor.prepare_training_data(df)
            
            # Validate we have enough data
            if len(X) < 50:
                raise ValidationError(f"Insufficient training data: {len(X)} samples (minimum 50)")
            
            self.models = []
            for i in range(self.lottery_config["numbers_per_draw"]):
                model, scaler = self.model_trainer.train(X, y[:, i])
                self.models.append((model, scaler))
                
        except Exception as e:
            raise PredictionError(f"Training failed: {str(e)}")
    
    def _generate_unique_prediction(self, model, scaler, features: np.ndarray, 
                                  used_numbers: set) -> int:
        """Generate a unique prediction avoiding already used numbers."""
        try:
            features_scaled = scaler.transform(features)
            prediction = model.predict(features_scaled)[0]
            
            # Round to nearest integer and ensure it's in valid range
            predicted_num = max(
                self.lottery_config["min_number"], 
                min(self.lottery_config["max_number"], round(prediction))
            )
            
            # If number already used, find closest unused number
            if predicted_num in used_numbers:
                number_range = LotteryConstants.get_number_range(self.lottery_type)
                for offset in range(1, len(number_range)):
                    for candidate in [predicted_num + offset, predicted_num - offset]:
                        if candidate in number_range and candidate not in used_numbers:
                            return candidate
            
            return predicted_num
        except Exception as e:
            raise PredictionError(f"Unique prediction generation failed: {str(e)}")
    
    def predict(self, features: np.ndarray, use_improved_strategy: bool = True) -> np.ndarray:
        """Generate predictions for next draw."""
        if not self.models:
            raise PredictionError("Models not trained yet")
        
        # Validate input features
        DataValidator.validate_features(features)
        
        try:
            if use_improved_strategy:
                from .improved_prediction_strategy import ImprovedPredictionStrategy
                
                strategy = ImprovedPredictionStrategy(self.lottery_type)
                result = strategy.predict_ensemble(
                    self.models, 
                    features, 
                    self.data_processor.data
                )
            else:
                # Fallback to original method
                predictions = []
                used_numbers = set()
                
                for model, scaler in self.models:
                    pred = self._generate_unique_prediction(
                        model, scaler, features, used_numbers
                    )
                    predictions.append(pred)
                    used_numbers.add(pred)
                
                result = np.sort(predictions)
            
            # Validate output predictions
            from .validators import ModelValidator
            ModelValidator.validate_predictions(result, self.lottery_type)
            
            return result
        except Exception as e:
            raise PredictionError(f"Prediction failed: {str(e)}")
    
    def predict_multiple(self, features: np.ndarray, count: int = 5) -> List[np.ndarray]:
        """Generate multiple diverse prediction sets."""
        from .improved_prediction_strategy import ImprovedPredictionStrategy
        
        strategy = ImprovedPredictionStrategy(self.lottery_type)
        return strategy.generate_multiple_predictions(
            self.models, 
            features, 
            self.data_processor.data,
            count
        ) 