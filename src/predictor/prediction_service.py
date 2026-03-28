"""PredictionService — clean DI-based predictor (replaces ImprovedLotteryPredictor)."""
import os
import numpy as np
import pandas as pd
import joblib
from typing import List, Tuple, Dict
from sklearn.preprocessing import StandardScaler
from xgboost import XGBRegressor

from .interfaces import DataLoader, DataValidator, FeatureEngineer, ModelFactory, PredictionStrategy, LotteryConfig


class PredictionService:
    """Lottery predictor with explicit dependency injection and no hidden state."""

    def __init__(
        self,
        data_loader: DataLoader,
        data_validator: DataValidator,
        feature_engineer: FeatureEngineer,
        model_factory: ModelFactory,
        prediction_strategy: PredictionStrategy,
        config: LotteryConfig,
        optimizer=None,
    ):
        self.data_loader = data_loader
        self.data_validator = data_validator
        self.feature_engineer = feature_engineer
        self.model_factory = model_factory
        self.prediction_strategy = prediction_strategy
        self.config = config
        self.optimizer = optimizer

        self.models: List[Tuple] = []
        self.is_trained = False
        self._training_data: pd.DataFrame = None

    # ------------------------------------------------------------------
    # Training
    # ------------------------------------------------------------------

    def train(self, data_source: str, model_config: Dict) -> None:
        """Load data, engineer features, and fit per-position models."""
        raw = self.data_loader.load(data_source)
        self.data_validator.validate(raw)

        processed = self._process_dates(raw)
        featured = self.feature_engineer.create_features(processed)
        self._training_data = featured

        X, y = self._prepare_training_data(featured)

        self.models = []
        for i in range(self.config.numbers_per_draw):
            model = self.model_factory.create_model("ensemble", model_config)
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X)
            model.fit(X_scaled, y[:, i])
            self.models.append((model, scaler))

        self.is_trained = True

    # ------------------------------------------------------------------
    # Feature preparation (explicit — no hidden state)
    # ------------------------------------------------------------------

    def prepare_features(self, data_source: str) -> np.ndarray:
        """Load data and return feature vector for the latest draw."""
        raw = self.data_loader.load(data_source)
        processed = self._process_dates(raw)
        featured = self.feature_engineer.create_features(processed)
        return self._extract_latest_features(featured)

    # ------------------------------------------------------------------
    # Prediction
    # ------------------------------------------------------------------

    def predict(self, features: np.ndarray) -> np.ndarray:
        """Generate predictions from explicit features."""
        self._assert_trained()
        return self.prediction_strategy.predict(self.models, features)

    def predict_optimized(self, features: np.ndarray) -> np.ndarray:
        """Return jackpot-sharing-optimised prediction."""
        self._assert_trained()
        self._assert_optimizer()
        candidates = [self.predict(features)]
        return self.optimizer.optimize_selection(candidates, self._training_data)

    def predict_anti_popular(self, features: np.ndarray, count: int = 1) -> List[np.ndarray]:
        """Return anti-popular predictions to minimise jackpot sharing."""
        self._assert_trained()
        self._assert_optimizer()
        return self.optimizer.generate_anti_popular_prediction(count)

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _assert_trained(self) -> None:
        if not self.is_trained:
            raise ValueError("PredictionService must be trained before prediction.")

    def _assert_optimizer(self) -> None:
        if self.optimizer is None:
            raise ValueError("No optimizer injected into PredictionService.")

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def save(self, directory: str) -> None:
        """Persist models to directory. XGBoost saved as .json, others via joblib."""
        self._assert_trained()
        os.makedirs(directory, exist_ok=True)
        for i, (model, scaler) in enumerate(self.models):
            if isinstance(model, XGBRegressor):
                model.save_model(os.path.join(directory, f"model_{i}.json"))
            else:
                joblib.dump(model, os.path.join(directory, f"model_{i}.joblib"))
            joblib.dump(scaler, os.path.join(directory, f"scaler_{i}.joblib"))

    def load(self, directory: str) -> None:
        """Restore models saved by save()."""
        self.models = []
        i = 0
        while True:
            json_path = os.path.join(directory, f"model_{i}.json")
            joblib_path = os.path.join(directory, f"model_{i}.joblib")
            scaler_path = os.path.join(directory, f"scaler_{i}.joblib")
            if not os.path.exists(scaler_path):
                break
            if os.path.exists(json_path):
                model = XGBRegressor()
                model.load_model(json_path)
            else:
                model = joblib.load(joblib_path)
            scaler = joblib.load(scaler_path)
            self.models.append((model, scaler))
            i += 1
        self.is_trained = bool(self.models)

    def _process_dates(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        df["DRAW_DATE"] = pd.to_datetime(df["DRAW DATE"])
        return df.sort_values("DRAW_DATE").reset_index(drop=True)

    def _prepare_training_data(self, df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        feature_cols = [
            c for c in df.columns
            if c.startswith("freq_") or c in ("sum_numbers", "odd_count", "low_count")
        ]
        X = df[feature_cols].values
        y = df[[f"num_{i}" for i in range(1, self.config.numbers_per_draw + 1)]].values
        return X[:-1], y[1:]

    def _extract_latest_features(self, df: pd.DataFrame) -> np.ndarray:
        feature_cols = [
            c for c in df.columns
            if c.startswith("freq_") or c in ("sum_numbers", "odd_count", "low_count")
        ]
        return df[feature_cols].values[-1:]
