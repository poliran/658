"""Tests for lottery predictor functionality."""

import unittest
import numpy as np
import pandas as pd
import tempfile
import os
from src.predictor import PredictionService, ModelTrainer
from src.predictor.system_factory import PredictionSystemFactory
from src.predictor.constants import ColumnNames


class TestDataProcessor(unittest.TestCase):
    """Test data validation via LotteryDataValidator."""

    def setUp(self):
        from src.predictor.data.validators import LotteryDataValidator

        required = [ColumnNames.LOTTO_GAME, ColumnNames.COMBINATIONS, ColumnNames.DRAW_DATE]
        self.validator = LotteryDataValidator(required)

    def test_validate_data_success(self):
        data = [
            {
                ColumnNames.LOTTO_GAME: "Ultra Lotto 6/58",
                ColumnNames.COMBINATIONS: f"{i+1:02d}-{i+2:02d}-{i+3:02d}-{i+4:02d}-{i+5:02d}-{i+6:02d}",
                ColumnNames.DRAW_DATE: f"1/{i+1}/2024",
            }
            for i in range(12)
        ]
        df = pd.DataFrame(data)
        self.assertTrue(self.validator.validate(df))

    def test_validate_data_failure(self):
        df = pd.DataFrame({"invalid": [1, 2, 3]})
        with self.assertRaises(Exception):
            self.validator.validate(df)


class TestModelTrainer(unittest.TestCase):
    """Test model training functionality."""

    def setUp(self):
        self.config = {
            "models": {
                "xgboost": {"n_estimators": 10, "learning_rate": 0.1, "max_depth": 3},
                "random_forest": {"n_estimators": 10, "max_depth": 3},
                "gradient_boosting": {"n_estimators": 10, "learning_rate": 0.1, "max_depth": 3},
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


class TestPredictionService(unittest.TestCase):
    """Test PredictionService via PredictionSystemFactory."""

    def setUp(self):
        self.config_data = f"""
lottery:
  min_number: 1
  max_number: 58
  numbers_per_draw: 6

data:
  validation:
    required_columns:
      - {ColumnNames.LOTTO_GAME}
      - {ColumnNames.COMBINATIONS}
      - {ColumnNames.DRAW_DATE}

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
        self.config_file = tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False)
        self.config_file.write(self.config_data)
        self.config_file.close()

        data_rows = []
        for i in range(55):
            nums = [(i + j) % 58 + 1 for j in range(6)]
            combo = "-".join([f"{n:02d}" for n in nums])
            month = (i % 12) + 1
            day = (i % 28) + 1
            data_rows.append(f"Ultra Lotto 6/58,{combo},{month}/{day}/2024,50000000,0")

        self.data = (
            f"{ColumnNames.LOTTO_GAME},{ColumnNames.COMBINATIONS},"
            f"{ColumnNames.DRAW_DATE},{ColumnNames.JACKPOT},{ColumnNames.WINNERS}\n"
            + "\n".join(data_rows)
        )
        self.data_file = tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False)
        self.data_file.write(self.data)
        self.data_file.close()

    def tearDown(self):
        os.unlink(self.config_file.name)
        os.unlink(self.data_file.name)

    def test_service_initialization(self):
        """PredictionSystemFactory produces a PredictionService."""
        service = PredictionSystemFactory.create_lottery_predictor(self.config_file.name)
        self.assertIsInstance(service, PredictionService)

    def test_prediction_output_format(self):
        """predict() returns correct count of unique numbers in valid range."""
        service = PredictionSystemFactory.create_lottery_predictor(self.config_file.name)
        service.train(self.data_file.name, model_config={})

        features = service.prepare_features(self.data_file.name)
        predictions = service.predict(features)

        self.assertEqual(len(predictions), service.config["numbers_per_draw"])
        self.assertTrue(
            all(
                service.config["min_number"] <= p <= service.config["max_number"]
                for p in predictions
            )
        )
        self.assertEqual(len(set(predictions)), service.config["numbers_per_draw"])

    def test_predict_requires_training(self):
        """predict() raises before train() is called."""
        service = PredictionSystemFactory.create_lottery_predictor(self.config_file.name)
        features = np.zeros((1, 10))
        with self.assertRaises(ValueError):
            service.predict(features)


if __name__ == "__main__":
    unittest.main()
