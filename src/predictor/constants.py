"""Configuration constants for lottery prediction system."""

from enum import Enum
from typing import Dict, Any


class LotteryType(Enum):
    """Supported lottery types."""

    ULTRA_LOTTO_6_58 = "ultra_lotto_6_58"
    POWERBALL = "powerball"
    EUROMILLIONS = "euromillions"


class RiskLevel(Enum):
    """Jackpot sharing risk levels."""

    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"

    @classmethod
    def from_score(cls, score: float) -> "RiskLevel":
        """Determine risk level from numeric score.

        Args:
            score: Numeric risk score (typically 0-50+).

        Returns:
            RiskLevel enum member.
        """
        if score < 15:
            return cls.LOW
        elif score < 25:
            return cls.MEDIUM
        else:
            return cls.HIGH


class LotteryConstants:
    """Constants for different lottery types."""

    CONFIGS: Dict[LotteryType, Dict[str, Any]] = {
        LotteryType.ULTRA_LOTTO_6_58: {
            "min_number": 1,
            "max_number": 58,
            "numbers_per_draw": 6,
            "name": "Ultra Lotto 6/58",
        },
        LotteryType.POWERBALL: {
            "min_number": 1,
            "max_number": 69,
            "numbers_per_draw": 5,
            "name": "Powerball",
        },
        LotteryType.EUROMILLIONS: {
            "min_number": 1,
            "max_number": 50,
            "numbers_per_draw": 5,
            "name": "EuroMillions",
        },
    }

    @classmethod
    def get_config(cls, lottery_type: LotteryType) -> Dict[str, Any]:
        """Get configuration for specific lottery type.

        Args:
            lottery_type: A LotteryType enum member.

        Returns:
            Dictionary with lottery configuration.

        Raises:
            ValueError: If lottery_type is not a valid LotteryType member.
        """
        if not isinstance(lottery_type, LotteryType):
            raise ValueError(
                f"lottery_type must be a LotteryType enum member, got {type(lottery_type).__name__}: {lottery_type}"
            )

        if lottery_type not in cls.CONFIGS:
            raise ValueError(
                f"Unsupported lottery type: {lottery_type}. Supported: {list(cls.CONFIGS.keys())}"
            )

        return cls.CONFIGS[lottery_type]

    @classmethod
    def get_number_range(cls, lottery_type: LotteryType) -> range:
        """Get valid number range for lottery type."""
        config = cls.get_config(lottery_type)
        return range(config["min_number"], config["max_number"] + 1)


# Default lottery type for backward compatibility
DEFAULT_LOTTERY = LotteryType.ULTRA_LOTTO_6_58


# File paths
class FilePaths:
    """Standard file paths."""

    DATA_DIR = "data"
    CONFIG_DIR = "config"
    MODELS_DIR = "models"
    OUTPUTS_DIR = "outputs"

    DEFAULT_DATA_FILE = f"{DATA_DIR}/lottery_history.csv"
    DEFAULT_CONFIG_FILE = f"{CONFIG_DIR}/model_config.yaml"


# Column names
class ColumnNames:
    """Standard column names for data processing."""

    LOTTO_GAME = "LOTTO GAME"
    COMBINATIONS = "COMBINATIONS"
    DRAW_DATE = "DRAW DATE"
    JACKPOT = "JACKPOT (PHP)"
    WINNERS = "WINNERS"

    # Processed columns
    DRAW_DATE_PROCESSED = "DRAW_DATE"

    @classmethod
    def get_number_columns(cls, count: int = 6) -> list:
        """Get list of number column names."""
        return [f"num_{i}" for i in range(1, count + 1)]

    @classmethod
    def get_frequency_columns(cls, max_number: int = 58) -> list:
        """Get list of frequency column names."""
        return [f"freq_{i}" for i in range(1, max_number + 1)]


# Model parameters
class ModelDefaults:
    """Default model parameters."""

    RANDOM_STATE = 42
    N_JOBS = -1

    XGBOOST = {
        "n_estimators": 100,
        "learning_rate": 0.1,
        "max_depth": 6,
        "random_state": RANDOM_STATE,
    }

    RANDOM_FOREST = {
        "n_estimators": 100,
        "max_depth": 10,
        "random_state": RANDOM_STATE,
        "n_jobs": N_JOBS,
    }

    GRADIENT_BOOSTING = {
        "n_estimators": 100,
        "learning_rate": 0.1,
        "max_depth": 6,
        "random_state": RANDOM_STATE,
    }
