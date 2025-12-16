"""Configuration management for the prediction system."""
import yaml
from typing import Dict, Any
from .interfaces import LotteryConfig

class ConfigManager:
    """Centralized configuration management."""
    
    def __init__(self, config_path: str):
        self.config_path = config_path
        self._config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        with open(self.config_path, 'r') as f:
            return yaml.safe_load(f)
    
    def get_lottery_config(self) -> LotteryConfig:
        """Get lottery-specific configuration."""
        lottery_config = self._config.get('lottery', {})
        return LotteryConfig(
            min_number=lottery_config.get('min_number', 1),
            max_number=lottery_config.get('max_number', 58),
            numbers_per_draw=lottery_config.get('numbers_per_draw', 6)
        )
    
    def get_data_config(self) -> Dict[str, Any]:
        """Get data processing configuration."""
        return self._config.get('data', {})
    
    def get_model_config(self) -> Dict[str, Any]:
        """Get model configuration."""
        return self._config.get('models', {})
    
    def get_prediction_config(self) -> Dict[str, Any]:
        """Get prediction configuration."""
        return self._config.get('prediction', {})
    
    def get_required_columns(self) -> list:
        """Get required data columns."""
        return self.get_data_config().get('validation', {}).get('required_columns', [])
