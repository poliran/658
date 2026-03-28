"""Factory for building the complete prediction system."""
from .prediction_service import PredictionService
from .config_manager import ConfigManager
from .data.loaders import CSVDataLoader
from .data.validators import LotteryDataValidator
from .features.engineers import LotteryFeatureEngineer
from .models.factory import SklearnModelFactory
from .strategies.prediction import UniqueLotteryPredictionStrategy
from .jackpot_optimizer import JackpotSharingOptimizer
from .constants import DEFAULT_LOTTERY


class PredictionSystemFactory:
    """Factory for creating fully configured PredictionService instances."""

    @staticmethod
    def create_lottery_predictor(config_path: str, lottery_type=DEFAULT_LOTTERY) -> PredictionService:
        """Create a fully wired PredictionService."""
        config_manager = ConfigManager(config_path)
        lottery_config = config_manager.get_lottery_config()
        required_columns = config_manager.get_required_columns()

        return PredictionService(
            data_loader=CSVDataLoader(),
            data_validator=LotteryDataValidator(required_columns),
            feature_engineer=LotteryFeatureEngineer(lottery_config),
            model_factory=SklearnModelFactory(),
            prediction_strategy=UniqueLotteryPredictionStrategy(lottery_config),
            config=lottery_config,
            optimizer=JackpotSharingOptimizer(lottery_type),
        )
