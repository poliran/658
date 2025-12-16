"""Custom exceptions for lottery prediction system."""
import logging
from typing import Optional, Any

logger = logging.getLogger(__name__)

class LotteryPredictionError(Exception):
    """Base exception for lottery prediction system."""
    
    def __init__(self, message: str, details: Optional[dict] = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)
        
        # Log the error
        logger.error(f"{self.__class__.__name__}: {message}", extra=self.details)

class DataProcessingError(LotteryPredictionError):
    """Raised when data processing fails."""
    pass

class ModelTrainingError(LotteryPredictionError):
    """Raised when model training fails."""
    pass

class PredictionError(LotteryPredictionError):
    """Raised when prediction generation fails."""
    pass

class ValidationError(LotteryPredictionError):
    """Raised when data validation fails."""
    pass

class ConfigurationError(LotteryPredictionError):
    """Raised when configuration is invalid."""
    pass

def safe_execute(func, *args, error_class=LotteryPredictionError, **kwargs):
    """Safely execute a function with proper error handling."""
    try:
        return func(*args, **kwargs)
    except Exception as e:
        raise error_class(
            f"Failed to execute {func.__name__}: {str(e)}",
            details={"function": func.__name__, "args": args, "kwargs": kwargs}
        ) from e

def validate_input(value: Any, validator_func, error_message: str):
    """Validate input using a validator function."""
    if not validator_func(value):
        raise ValidationError(
            error_message,
            details={"value": str(value), "validator": validator_func.__name__}
        )
