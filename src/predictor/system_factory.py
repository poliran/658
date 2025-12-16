"""Factory for building the complete prediction system."""
from .improved_predictor import ImprovedLotteryPredictor
from .config_manager import ConfigManager
from .data.loaders import CSVDataLoader
from .data.validators import LotteryDataValidator
from .features.engineers import LotteryFeatureEngineer
from .models.factory import SklearnModelFactory
from .strategies.prediction import UniqueLotteryPredictionStrategy

class PredictionSystemFactory:
    """Factory for creating configured prediction systems."""
    
    @staticmethod
    def create_lottery_predictor(config_path: str) -> ImprovedLotteryPredictor:
        """Create a fully configured lottery predictor."""
        # Load configuration
        config_manager = ConfigManager(config_path)
        lottery_config = config_manager.get_lottery_config()
        required_columns = config_manager.get_required_columns()
        
        # Create components
        data_loader = CSVDataLoader()
        data_validator = LotteryDataValidator(required_columns)
        feature_engineer = LotteryFeatureEngineer(lottery_config)
        model_factory = SklearnModelFactory()
        prediction_strategy = UniqueLotteryPredictionStrategy(lottery_config)
        
        # Create and return predictor
        return ImprovedLotteryPredictor(
            data_loader=data_loader,
            data_validator=data_validator,
            feature_engineer=feature_engineer,
            model_factory=model_factory,
            prediction_strategy=prediction_strategy,
            config=lottery_config
        )
