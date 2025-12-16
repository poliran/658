"""Tests for comprehensive input validation."""
import unittest
import numpy as np
import pandas as pd
import tempfile
import os
from pathlib import Path

from src.predictor.validators import (
    DataValidator, ConfigValidator, ModelValidator, 
    validate_prediction_input, validate_system_requirements
)
from src.predictor.constants import LotteryType, ColumnNames
from src.predictor.exceptions import ValidationError

class TestDataValidator(unittest.TestCase):
    """Test data validation functionality."""
    
    def test_validate_file_path_success(self):
        """Test successful file path validation."""
        with tempfile.NamedTemporaryFile(suffix='.csv') as f:
            f.write(b"test,data\n1,2\n")
            f.flush()
            result = DataValidator.validate_file_path(f.name)
            self.assertIsInstance(result, Path)
    
    def test_validate_file_path_nonexistent(self):
        """Test validation of non-existent file."""
        with self.assertRaises(ValidationError):
            DataValidator.validate_file_path("nonexistent_file.csv")
    
    def test_validate_file_path_unsupported_type(self):
        """Test validation of unsupported file type."""
        with tempfile.NamedTemporaryFile(suffix='.txt') as f:
            with self.assertRaises(ValidationError):
                DataValidator.validate_file_path(f.name)
    
    def test_validate_dataframe_empty(self):
        """Test validation of empty DataFrame."""
        df = pd.DataFrame()
        with self.assertRaises(ValidationError):
            DataValidator.validate_dataframe(df, ['col1'])
    
    def test_validate_dataframe_missing_columns(self):
        """Test validation with missing columns."""
        df = pd.DataFrame({'col1': [1, 2, 3]})
        with self.assertRaises(ValidationError):
            DataValidator.validate_dataframe(df, ['col1', 'col2'])
    
    def test_validate_dataframe_insufficient_data(self):
        """Test validation with insufficient data."""
        df = pd.DataFrame({
            ColumnNames.LOTTO_GAME: ['test'] * 5,
            ColumnNames.COMBINATIONS: ['1-2-3-4-5-6'] * 5,
            ColumnNames.DRAW_DATE: ['1/1/2024'] * 5
        })
        with self.assertRaises(ValidationError):
            DataValidator.validate_dataframe(df, [ColumnNames.LOTTO_GAME])
    
    def test_validate_lottery_numbers_success(self):
        """Test successful lottery number validation."""
        numbers = [1, 15, 23, 34, 45, 58]
        DataValidator.validate_lottery_numbers(numbers, LotteryType.ULTRA_LOTTO_6_58)
    
    def test_validate_lottery_numbers_duplicates(self):
        """Test validation with duplicate numbers."""
        numbers = [1, 15, 23, 23, 45, 58]
        with self.assertRaises(ValidationError):
            DataValidator.validate_lottery_numbers(numbers, LotteryType.ULTRA_LOTTO_6_58)
    
    def test_validate_lottery_numbers_out_of_range(self):
        """Test validation with out-of-range numbers."""
        numbers = [0, 15, 23, 34, 45, 59]
        with self.assertRaises(ValidationError):
            DataValidator.validate_lottery_numbers(numbers, LotteryType.ULTRA_LOTTO_6_58)
    
    def test_validate_features_success(self):
        """Test successful feature validation."""
        features = np.array([[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]])
        DataValidator.validate_features(features)
    
    def test_validate_features_nan(self):
        """Test validation with NaN values."""
        features = np.array([[1.0, np.nan, 3.0], [4.0, 5.0, 6.0]])
        with self.assertRaises(ValidationError):
            DataValidator.validate_features(features)
    
    def test_validate_features_infinite(self):
        """Test validation with infinite values."""
        features = np.array([[1.0, np.inf, 3.0], [4.0, 5.0, 6.0]])
        with self.assertRaises(ValidationError):
            DataValidator.validate_features(features)

class TestConfigValidator(unittest.TestCase):
    """Test configuration validation."""
    
    def setUp(self):
        self.valid_config = {
            'models': {
                'xgboost': {'n_estimators': 100, 'learning_rate': 0.1, 'max_depth': 6},
                'random_forest': {'n_estimators': 100, 'max_depth': 10},
                'gradient_boosting': {'n_estimators': 100, 'learning_rate': 0.1, 'max_depth': 6}
            }
        }
    
    def test_validate_model_config_success(self):
        """Test successful model config validation."""
        ConfigValidator.validate_model_config(self.valid_config)
    
    def test_validate_model_config_missing_section(self):
        """Test validation with missing models section."""
        config = {'data': {}}
        with self.assertRaises(ValidationError):
            ConfigValidator.validate_model_config(config)
    
    def test_validate_model_config_invalid_params(self):
        """Test validation with invalid model parameters."""
        config = {
            'models': {
                'xgboost': {'n_estimators': -1},  # Invalid
                'random_forest': {'n_estimators': 100},
                'gradient_boosting': {'n_estimators': 100}
            }
        }
        with self.assertRaises(ValidationError):
            ConfigValidator.validate_model_config(config)
    
    def test_validate_lottery_config_success(self):
        """Test successful lottery config validation."""
        ConfigValidator.validate_lottery_config(LotteryType.ULTRA_LOTTO_6_58)
    
    def test_validate_config_file_success(self):
        """Test successful config file validation."""
        config_content = """
models:
  xgboost:
    n_estimators: 100
    learning_rate: 0.1
    max_depth: 6
  random_forest:
    n_estimators: 100
    max_depth: 10
  gradient_boosting:
    n_estimators: 100
    learning_rate: 0.1
    max_depth: 6
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(config_content)
            f.flush()
            
            try:
                config = ConfigValidator.validate_config_file(f.name)
                self.assertIsInstance(config, dict)
                self.assertIn('models', config)
            finally:
                os.unlink(f.name)

class TestModelValidator(unittest.TestCase):
    """Test model validation."""
    
    def test_validate_training_data_success(self):
        """Test successful training data validation."""
        X = np.random.rand(100, 10)
        y = np.random.randint(1, 59, (100, 6))
        ModelValidator.validate_training_data(X, y)
    
    def test_validate_training_data_insufficient(self):
        """Test validation with insufficient training data."""
        X = np.random.rand(30, 10)  # Too few samples
        y = np.random.randint(1, 59, (30, 6))
        with self.assertRaises(ValidationError):
            ModelValidator.validate_training_data(X, y)
    
    def test_validate_training_data_mismatched_length(self):
        """Test validation with mismatched X and y lengths."""
        X = np.random.rand(100, 10)
        y = np.random.randint(1, 59, (90, 6))  # Different length
        with self.assertRaises(ValidationError):
            ModelValidator.validate_training_data(X, y)
    
    def test_validate_predictions_success(self):
        """Test successful prediction validation."""
        predictions = np.array([1, 15, 23, 34, 45, 58])
        ModelValidator.validate_predictions(predictions, LotteryType.ULTRA_LOTTO_6_58)
    
    def test_validate_predictions_wrong_length(self):
        """Test validation with wrong prediction length."""
        predictions = np.array([1, 15, 23, 34, 45])  # Only 5 numbers
        with self.assertRaises(ValidationError):
            ModelValidator.validate_predictions(predictions, LotteryType.ULTRA_LOTTO_6_58)

class TestSystemValidation(unittest.TestCase):
    """Test system-level validation."""
    
    def test_validate_system_requirements(self):
        """Test system requirements validation."""
        # Should not raise an exception in normal environment
        validate_system_requirements()
    
    def test_validate_prediction_input_success(self):
        """Test successful prediction input validation."""
        # Create temporary valid data file
        data_content = f"""{ColumnNames.LOTTO_GAME},{ColumnNames.COMBINATIONS},{ColumnNames.DRAW_DATE}
Ultra Lotto 6/58,01-02-03-04-05-06,1/1/2024
Ultra Lotto 6/58,07-08-09-10-11-12,1/2/2024
Ultra Lotto 6/58,13-14-15-16-17-18,1/3/2024
Ultra Lotto 6/58,19-20-21-22-23-24,1/4/2024
Ultra Lotto 6/58,25-26-27-28-29-30,1/5/2024
Ultra Lotto 6/58,31-32-33-34-35-36,1/6/2024
Ultra Lotto 6/58,37-38-39-40-41-42,1/7/2024
Ultra Lotto 6/58,43-44-45-46-47-48,1/8/2024
Ultra Lotto 6/58,49-50-51-52-53-54,1/9/2024
Ultra Lotto 6/58,55-56-57-58-01-02,1/10/2024
Ultra Lotto 6/58,03-04-05-06-07-08,1/11/2024"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(data_content)
            f.flush()
            
            try:
                validate_prediction_input(f.name, LotteryType.ULTRA_LOTTO_6_58)
            finally:
                os.unlink(f.name)

if __name__ == '__main__':
    unittest.main()
