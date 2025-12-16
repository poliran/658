"""Tests for lottery predictor functionality."""
import unittest
import numpy as np
import pandas as pd
import tempfile
import os
from src.predictor import LotteryPredictor, DataProcessor, ModelTrainer

class TestDataProcessor(unittest.TestCase):
    """Test data processing functionality."""
    
    def setUp(self):
        self.config = {
            'data': {
                'validation': {
                    'required_columns': ['LOTTO GAME', 'COMBINATIONS', 'DRAW DATE']
                }
            }
        }
        self.processor = DataProcessor(self.config)
    
    def test_validate_data_success(self):
        """Test successful data validation."""
        df = pd.DataFrame({
            'LOTTO GAME': ['Ultra Lotto 6/58'],
            'COMBINATIONS': ['01-02-03-04-05-06'],
            'DRAW DATE': ['1/1/2024']
        })
        self.processor._validate_data(df)  # Should not raise
    
    def test_validate_data_failure(self):
        """Test data validation failure."""
        df = pd.DataFrame({'invalid': [1, 2, 3]})
        with self.assertRaises(ValueError):
            self.processor._validate_data(df)

class TestModelTrainer(unittest.TestCase):
    """Test model training functionality."""
    
    def setUp(self):
        self.config = {
            'models': {
                'xgboost': {'n_estimators': 10, 'learning_rate': 0.1, 'max_depth': 3},
                'random_forest': {'n_estimators': 10, 'max_depth': 3},
                'gradient_boosting': {'n_estimators': 10, 'learning_rate': 0.1, 'max_depth': 3}
            }
        }
        self.trainer = ModelTrainer(self.config)
    
    def test_model_creation(self):
        """Test model creation methods."""
        xgb_model = self.trainer._create_xgb_model()
        rf_model = self.trainer._create_rf_model()
        gb_model = self.trainer._create_gb_model()
        
        self.assertIsNotNone(xgb_model)
        self.assertIsNotNone(rf_model)
        self.assertIsNotNone(gb_model)
    
    def test_ensemble_creation(self):
        """Test ensemble model creation."""
        ensemble = self.trainer.create_ensemble()
        self.assertEqual(len(ensemble.estimators), 3)

class TestLotteryPredictor(unittest.TestCase):
    """Test main predictor functionality."""
    
    def setUp(self):
        # Create temporary config file
        self.config_data = """
data:
  validation:
    required_columns:
      - LOTTO GAME
      - COMBINATIONS
      - DRAW DATE

models:
  xgboost:
    n_estimators: 10
    learning_rate: 0.1
    max_depth: 3
  random_forest:
    n_estimators: 10
    max_depth: 3
  gradient_boosting:
    n_estimators: 10
    learning_rate: 0.1
    max_depth: 3
"""
        self.config_file = tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False)
        self.config_file.write(self.config_data)
        self.config_file.close()
        
        # Create temporary data file
        self.data = """LOTTO GAME,COMBINATIONS,DRAW DATE,JACKPOT (PHP),WINNERS
Ultra Lotto 6/58,01-02-03-04-05-06,1/1/2024,50000000,0
Ultra Lotto 6/58,07-08-09-10-11-12,1/2/2024,50000000,0
Ultra Lotto 6/58,13-14-15-16-17-18,1/3/2024,50000000,0"""
        
        self.data_file = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
        self.data_file.write(self.data)
        self.data_file.close()
    
    def tearDown(self):
        os.unlink(self.config_file.name)
        os.unlink(self.data_file.name)
    
    def test_predictor_initialization(self):
        """Test predictor initialization."""
        predictor = LotteryPredictor(self.config_file.name)
        self.assertIsNotNone(predictor.config)
        self.assertIsNotNone(predictor.data_processor)
        self.assertIsNotNone(predictor.model_trainer)
    
    def test_prediction_output_format(self):
        """Test prediction output format."""
        predictor = LotteryPredictor(self.config_file.name)
        predictor.train(self.data_file.name)
        
        features = predictor.data_processor.prepare_next_draw_features()
        predictions = predictor.predict(features)
        
        self.assertEqual(len(predictions), 6)
        self.assertTrue(all(1 <= p <= 58 for p in predictions))
        self.assertEqual(len(set(predictions)), 6)  # All unique

if __name__ == '__main__':
    unittest.main()
