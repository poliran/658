"""Input validation utilities."""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import List, Union, Optional
import yaml
from .constants import LotteryConstants, LotteryType, ColumnNames
from .exceptions import ValidationError


class DataValidator:
    """Validates input data for lottery prediction."""

    @staticmethod
    def validate_file_path(
        file_path: Union[str, Path], allowed_extensions: List[str] = None
    ) -> Path:
        """Validate that file path exists and is readable."""
        if not file_path:
            raise ValidationError("File path cannot be empty")

        path = Path(file_path)

        if not path.exists():
            raise ValidationError(f"File does not exist: {file_path}")

        if not path.is_file():
            raise ValidationError(f"Path is not a file: {file_path}")

        if allowed_extensions is None:
            allowed_extensions = [".csv", ".xlsx", ".json", ".yaml", ".yml"]

        if not path.suffix.lower() in allowed_extensions:
            raise ValidationError(f"Unsupported file type: {path.suffix}")

        # Check file size (max 100MB)
        if path.stat().st_size > 100 * 1024 * 1024:
            raise ValidationError(
                f"File too large: {path.stat().st_size / 1024 / 1024:.1f}MB (max 100MB)"
            )

        return path

    @staticmethod
    def validate_dataframe(
        df: pd.DataFrame, required_columns: List[str], lottery_type=None
    ) -> None:
        """Validate DataFrame structure and content."""
        if df is None:
            raise ValidationError("DataFrame cannot be None")

        if df.empty:
            raise ValidationError("DataFrame is empty")

        if len(df) < 10:
            raise ValidationError(f"Insufficient data: {len(df)} rows (minimum 10 required)")

        missing_columns = set(required_columns) - set(df.columns)
        if missing_columns:
            raise ValidationError(
                f"Missing required columns: {missing_columns}",
                details={"available_columns": list(df.columns)},
            )

        # Check for null values in critical columns
        null_counts = df[required_columns].isnull().sum()
        if null_counts.any():
            raise ValidationError(
                f"Null values found in required columns: {null_counts[null_counts > 0].to_dict()}"
            )

        # Validate combinations format
        if ColumnNames.COMBINATIONS in df.columns:
            if lottery_type is not None:
                config = LotteryConstants.get_config(lottery_type)
                DataValidator._validate_combinations_format(
                    df[ColumnNames.COMBINATIONS],
                    numbers_per_draw=config["numbers_per_draw"],
                    max_number=config["max_number"],
                )
            else:
                DataValidator._validate_combinations_format(df[ColumnNames.COMBINATIONS])

        # Validate dates
        if ColumnNames.DRAW_DATE in df.columns:
            DataValidator._validate_dates(df[ColumnNames.DRAW_DATE])

    @staticmethod
    def _validate_combinations_format(
        combinations: pd.Series, numbers_per_draw: int = 6, max_number: int = 58
    ) -> None:
        """Validate lottery combination format."""
        invalid_combinations = []

        for idx, combo in combinations.items():
            if not isinstance(combo, str):
                invalid_combinations.append(f"Row {idx}: Not a string")
                continue

            if not combo or combo.strip() == "":
                invalid_combinations.append(f"Row {idx}: Empty combination")
                continue

            parts = combo.split("-")
            if len(parts) != numbers_per_draw:
                invalid_combinations.append(
                    f"Row {idx}: Expected {numbers_per_draw} numbers, got {len(parts)}"
                )
                continue

            try:
                numbers = [int(part.strip()) for part in parts]
                if any(n < 1 or n > max_number for n in numbers):
                    invalid_combinations.append(f"Row {idx}: Numbers outside range 1-{max_number}")
                if len(set(numbers)) != len(numbers):
                    invalid_combinations.append(f"Row {idx}: Duplicate numbers")
            except ValueError:
                invalid_combinations.append(f"Row {idx}: Non-numeric values")

        if invalid_combinations:
            raise ValidationError(
                f"Invalid combinations found: {len(invalid_combinations)} errors",
                details={"errors": invalid_combinations[:10]},  # Limit to first 10
            )

    @staticmethod
    def _validate_dates(dates: pd.Series) -> None:
        """Validate date format and range."""
        parsed_dates = pd.to_datetime(dates, errors="coerce")
        invalid_dates = parsed_dates.isnull().sum()

        if invalid_dates > 0:
            raise ValidationError(f"Invalid date format in {invalid_dates} rows")

        min_date = parsed_dates.min()
        max_date = parsed_dates.max()

        if min_date.year < 2000:
            raise ValidationError(f"Dates too old: earliest date is {min_date}")

        if max_date > pd.Timestamp.now() + pd.Timedelta(days=1):
            raise ValidationError(f"Future dates found: latest date is {max_date}")

    @staticmethod
    def validate_lottery_numbers(
        numbers: List[int], lottery_type: LotteryType = LotteryType.ULTRA_LOTTO_6_58
    ) -> None:
        """Validate lottery number combinations."""
        if not numbers:
            raise ValidationError("Numbers list cannot be empty")

        if not isinstance(numbers, (list, tuple, np.ndarray)):
            raise ValidationError(f"Numbers must be a list, got {type(numbers)}")

        config = LotteryConstants.get_config(lottery_type)
        valid_range = LotteryConstants.get_number_range(lottery_type)

        if len(numbers) != config["numbers_per_draw"]:
            raise ValidationError(
                f"Expected {config['numbers_per_draw']} numbers, got {len(numbers)}"
            )

        # Check for non-integer values
        try:
            numbers = [int(n) for n in numbers]
        except (ValueError, TypeError):
            raise ValidationError("All numbers must be integers")

        if len(set(numbers)) != len(numbers):
            duplicates = [n for n in set(numbers) if numbers.count(n) > 1]
            raise ValidationError(f"Duplicate numbers found: {duplicates}")

        invalid_numbers = [n for n in numbers if n not in valid_range]
        if invalid_numbers:
            raise ValidationError(
                f"Numbers outside valid range {min(valid_range)}-{max(valid_range)}: {invalid_numbers}"
            )

    @staticmethod
    def validate_features(features: np.ndarray, expected_shape: Optional[tuple] = None) -> None:
        """Validate feature array for prediction."""
        if features is None:
            raise ValidationError("Features cannot be None")

        if not isinstance(features, np.ndarray):
            raise ValidationError(f"Features must be numpy array, got {type(features)}")

        if features.size == 0:
            raise ValidationError("Features array is empty")

        if len(features.shape) != 2:
            raise ValidationError(f"Features must be 2D array, got shape {features.shape}")

        if expected_shape and features.shape != expected_shape:
            raise ValidationError(f"Expected features shape {expected_shape}, got {features.shape}")

        if np.isnan(features).any():
            nan_count = np.isnan(features).sum()
            raise ValidationError(f"Features contain {nan_count} NaN values")

        if np.isinf(features).any():
            inf_count = np.isinf(features).sum()
            raise ValidationError(f"Features contain {inf_count} infinite values")

        # Check for reasonable value ranges
        if features.min() < -1000 or features.max() > 1000:
            raise ValidationError(
                f"Features have extreme values: min={features.min():.2f}, max={features.max():.2f}"
            )


class ConfigValidator:
    """Validates configuration parameters."""

    @staticmethod
    def validate_config_file(config_path: str) -> dict:
        """Validate and load configuration file."""
        path = DataValidator.validate_file_path(config_path)

        try:
            with open(path, "r") as f:
                config = yaml.safe_load(f)

            if not isinstance(config, dict):
                raise ValidationError("Configuration must be a dictionary")

            ConfigValidator.validate_model_config(config)
            return config

        except yaml.YAMLError as e:
            raise ValidationError(f"Invalid YAML format: {str(e)}")
        except Exception as e:
            raise ValidationError(f"Configuration loading failed: {str(e)}")

    @staticmethod
    def validate_model_config(config: dict) -> None:
        """Validate model configuration."""
        if not config:
            raise ValidationError("Configuration cannot be empty")

        required_sections = ["models"]
        missing_sections = [s for s in required_sections if s not in config]
        if missing_sections:
            raise ValidationError(f"Missing configuration sections: {missing_sections}")

        # Validate model parameters
        models_config = config["models"]
        if not isinstance(models_config, dict):
            raise ValidationError("Models configuration must be a dictionary")

        required_models = ["xgboost", "random_forest", "gradient_boosting"]

        for model in required_models:
            if model not in models_config:
                raise ValidationError(f"Missing model configuration: {model}")

            model_params = models_config[model]
            if not isinstance(model_params, dict):
                raise ValidationError(f"Model parameters must be dict for {model}")

            ConfigValidator._validate_model_params(model, model_params)

    @staticmethod
    def _validate_model_params(model_name: str, params: dict) -> None:
        """Validate individual model parameters."""
        if "n_estimators" in params:
            n_est = params["n_estimators"]
            if not isinstance(n_est, int) or n_est < 1 or n_est > 1000:
                raise ValidationError(f"{model_name}: n_estimators must be 1-1000, got {n_est}")

        if "learning_rate" in params:
            lr = params["learning_rate"]
            if not isinstance(lr, (int, float)) or lr <= 0 or lr > 1:
                raise ValidationError(f"{model_name}: learning_rate must be 0-1, got {lr}")

        if "max_depth" in params:
            depth = params["max_depth"]
            if depth is not None and (not isinstance(depth, int) or depth < 1 or depth > 20):
                raise ValidationError(f"{model_name}: max_depth must be 1-20 or None, got {depth}")

    @staticmethod
    def validate_lottery_config(lottery_type: LotteryType) -> None:
        """Validate lottery type configuration."""
        if not isinstance(lottery_type, LotteryType):
            raise ValidationError(f"Invalid lottery type: {lottery_type}")

        try:
            config = LotteryConstants.get_config(lottery_type)
        except KeyError:
            raise ValidationError(f"Unsupported lottery type: {lottery_type}")

        required_keys = ["min_number", "max_number", "numbers_per_draw", "name"]
        missing_keys = [k for k in required_keys if k not in config]
        if missing_keys:
            raise ValidationError(f"Missing lottery config keys: {missing_keys}")

        if config["min_number"] >= config["max_number"]:
            raise ValidationError("min_number must be less than max_number")

        if config["numbers_per_draw"] <= 0 or config["numbers_per_draw"] > 10:
            raise ValidationError("numbers_per_draw must be 1-10")


class ModelValidator:
    """Validates model inputs and outputs."""

    @staticmethod
    def validate_training_data(X: np.ndarray, y: np.ndarray) -> None:
        """Validate training data arrays."""
        if X is None or y is None:
            raise ValidationError("Training data cannot be None")

        if not isinstance(X, np.ndarray) or not isinstance(y, np.ndarray):
            raise ValidationError("Training data must be numpy arrays")

        if X.size == 0 or y.size == 0:
            raise ValidationError("Training data cannot be empty")

        if len(X) != len(y):
            raise ValidationError(f"X and y must have same length: {len(X)} vs {len(y)}")

        if len(X) < 50:
            raise ValidationError(f"Insufficient training data: {len(X)} samples (minimum 50)")

        DataValidator.validate_features(X)

        # Validate targets
        if len(y.shape) != 2:
            raise ValidationError(f"Target array must be 2D, got shape {y.shape}")

        if y.shape[1] not in [5, 6, 7]:  # Common lottery sizes
            raise ValidationError(f"Unexpected number of target columns: {y.shape[1]}")

    @staticmethod
    def validate_predictions(predictions: np.ndarray, lottery_type: LotteryType) -> None:
        """Validate prediction outputs."""
        if predictions is None:
            raise ValidationError("Predictions cannot be None")

        if not isinstance(predictions, np.ndarray):
            raise ValidationError(f"Predictions must be numpy array, got {type(predictions)}")

        config = LotteryConstants.get_config(lottery_type)
        expected_length = config["numbers_per_draw"]

        if len(predictions) != expected_length:
            raise ValidationError(f"Expected {expected_length} predictions, got {len(predictions)}")

        # Convert to list for validation
        pred_list = predictions.tolist()
        DataValidator.validate_lottery_numbers(pred_list, lottery_type)


def validate_prediction_input(
    data_path: str, lottery_type: LotteryType = LotteryType.ULTRA_LOTTO_6_58
) -> None:
    """Comprehensive validation for prediction input."""
    # Validate file path
    DataValidator.validate_file_path(data_path)

    # Validate lottery configuration
    ConfigValidator.validate_lottery_config(lottery_type)

    # Load and validate data structure
    try:
        df = pd.read_csv(data_path)
        required_columns = [ColumnNames.LOTTO_GAME, ColumnNames.COMBINATIONS, ColumnNames.DRAW_DATE]
        DataValidator.validate_dataframe(df, required_columns)
    except Exception as e:
        raise ValidationError(f"Data validation failed: {str(e)}")


def validate_system_requirements() -> None:
    """Validate system requirements and dependencies."""
    import sys

    # Check Python version
    if sys.version_info < (3, 8):
        raise ValidationError(f"Python 3.8+ required, got {sys.version_info}")

    # Check required packages
    required_packages = ["numpy", "pandas", "sklearn", "xgboost", "yaml"]
    missing_packages = []

    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)

    if missing_packages:
        raise ValidationError(f"Missing required packages: {missing_packages}")
