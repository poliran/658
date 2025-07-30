"""Main lottery prediction module."""
from typing import List, Optional
import numpy as np
import yaml
from .data_processor import DataProcessor
from .model_trainer import ModelTrainer

class LotteryPredictor:
    """Main class for lottery number prediction."""
    
    def __init__(self, config_path: str):
        self.config = self._load_config(config_path)
        self.data_processor = DataProcessor(self.config)
        self.model_trainer = ModelTrainer(self.config)
        self.models: List = []
        
    @staticmethod
    def _load_config(config_path: str) -> dict:
        """Load configuration from YAML file."""
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    
    def train(self, data_path: str) -> None:
        """Train the prediction models."""
        df = self.data_processor.load_data(data_path)
        X, y = self.data_processor.prepare_training_data(df)
        
        self.models = []
        for i in range(6):
            model, scaler = self.model_trainer.train(X, y[:, i])
            self.models.append((model, scaler))
    
    def predict(self, features: np.ndarray) -> np.ndarray:
        """Generate predictions for next draw."""
        predictions = []
        used_numbers = set()
        
        for model, scaler in self.models:
            pred = self._generate_unique_prediction(
                model, scaler, features, used_numbers
            )
            predictions.append(pred)
            used_numbers.add(pred)
            
        return np.sort(predictions) 