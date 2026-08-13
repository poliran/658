"""Interfaces and protocols for the prediction system."""
from abc import ABC, abstractmethod
from typing import Dict, List, Tuple, Any
import numpy as np
import pandas as pd

class DataLoader(ABC):
    """Abstract interface for data loading."""
    
    @abstractmethod
    def load(self, source: str) -> pd.DataFrame:
        """Load data from source."""
        pass

class DataValidator(ABC):
    """Abstract interface for data validation."""
    
    @abstractmethod
    def validate(self, data: pd.DataFrame) -> bool:
        """Validate data structure and content."""
        pass

class FeatureEngineer(ABC):
    """Abstract interface for feature engineering."""
    
    @abstractmethod
    def create_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """Create features from raw data."""
        pass

class ModelFactory(ABC):
    """Abstract factory for creating models."""
    
    @abstractmethod
    def create_model(self, model_type: str, config: Dict) -> Any:
        """Create a model instance."""
        pass

class PredictionStrategy(ABC):
    """Abstract strategy for prediction algorithms."""
    
    @abstractmethod
    def predict(self, models: List, features: np.ndarray) -> np.ndarray:
        """Generate predictions using the strategy."""
        pass
