"""Optimized model trainer with parallel processing."""
import numpy as np
from typing import Dict, List, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from sklearn.ensemble import VotingRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import cross_val_score
import joblib
from .constants import ModelDefaults, DEFAULT_LOTTERY, LotteryConstants
from .exceptions import ModelTrainingError

class OptimizedModelTrainer:
    """High-performance model trainer with parallelization."""
    
    def __init__(self, config: Dict, lottery_type=DEFAULT_LOTTERY):
        self.config = config
        self.lottery_type = lottery_type
        self.lottery_config = LotteryConstants.get_config(lottery_type)
        self.model_cache = {}
    
    def train_parallel(self, X: np.ndarray, y: np.ndarray) -> List[Tuple]:
        """Train multiple models in parallel."""
        models = []
        
        try:
            # Use ThreadPoolExecutor for parallel training
            with ThreadPoolExecutor(max_workers=self.lottery_config["numbers_per_draw"]) as executor:
                futures = []
                
                for i in range(self.lottery_config["numbers_per_draw"]):
                    future = executor.submit(self._train_single_model, X, y[:, i], i)
                    futures.append(future)
                
                # Collect results as they complete
                for future in as_completed(futures):
                    model, scaler, position = future.result()
                    models.append((model, scaler, position))
            
            # Sort by position to maintain order
            models.sort(key=lambda x: x[2])
            return [(model, scaler) for model, scaler, pos in models]
        except Exception as e:
            raise ModelTrainingError(f"Parallel training failed: {str(e)}")
    
    def _train_single_model(self, X: np.ndarray, y: np.ndarray, 
                           position: int) -> Tuple:
        """Train a single model for one position."""
        try:
            # Use cached scaler if available
            cache_key = f"scaler_{X.shape[1]}_{position}"
            
            if cache_key in self.model_cache:
                scaler = self.model_cache[cache_key]
            else:
                scaler = StandardScaler()
                self.model_cache[cache_key] = scaler
            
            X_scaled = scaler.fit_transform(X)
            
            # Create optimized ensemble
            model = self._create_optimized_ensemble()
            model.fit(X_scaled, y)
            
            return model, scaler, position
        except Exception as e:
            raise ModelTrainingError(f"Single model training failed for position {position}: {str(e)}")
    
    def _create_optimized_ensemble(self) -> VotingRegressor:
        """Create ensemble with optimized parameters."""
        from xgboost import XGBRegressor
        from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
        
        # Use optimized parameters for speed
        xgb_params = self.config.get('models', {}).get('xgboost', ModelDefaults.XGBOOST)
        rf_params = self.config.get('models', {}).get('random_forest', ModelDefaults.RANDOM_FOREST)
        gb_params = self.config.get('models', {}).get('gradient_boosting', ModelDefaults.GRADIENT_BOOSTING)
        
        models = [
            ('xgb', XGBRegressor(
                n_estimators=min(xgb_params.get('n_estimators', 50), 50),  # Reduced for speed
                learning_rate=xgb_params.get('learning_rate', 0.1),
                max_depth=min(xgb_params.get('max_depth', 4), 4),  # Reduced depth
                n_jobs=1,  # Single thread per model
                random_state=ModelDefaults.RANDOM_STATE
            )),
            ('rf', RandomForestRegressor(
                n_estimators=min(rf_params.get('n_estimators', 50), 50),  # Reduced for speed
                max_depth=min(rf_params.get('max_depth', 8), 8),  # Reduced depth
                n_jobs=1,  # Single thread per model
                random_state=ModelDefaults.RANDOM_STATE
            )),
            ('gb', GradientBoostingRegressor(
                n_estimators=min(gb_params.get('n_estimators', 50), 50),  # Reduced for speed
                learning_rate=gb_params.get('learning_rate', 0.1),
                max_depth=min(gb_params.get('max_depth', 4), 4),  # Reduced depth
                random_state=ModelDefaults.RANDOM_STATE
            ))
        ]
        
        return VotingRegressor(models, n_jobs=1)  # Parallel at position level
    
    def train_with_validation(self, X: np.ndarray, y: np.ndarray) -> List[Tuple]:
        """Train with cross-validation for performance monitoring."""
        models = []
        
        try:
            for i in range(self.lottery_config["numbers_per_draw"]):
                model, scaler = self._train_single_model(X, y[:, i], i)[:2]
                
                # Quick validation
                X_scaled = scaler.transform(X)
                cv_scores = cross_val_score(model, X_scaled, y[:, i], cv=3, n_jobs=ModelDefaults.N_JOBS)
                
                print(f"Position {i+1} CV Score: {cv_scores.mean():.4f} (+/- {cv_scores.std() * 2:.4f})")
                models.append((model, scaler))
            
            return models
        except Exception as e:
            raise ModelTrainingError(f"Validation training failed: {str(e)}")
    
    def save_models(self, models: List[Tuple], filepath: str) -> None:
        """Save trained models efficiently."""
        try:
            joblib.dump(models, filepath, compress=3)
        except Exception as e:
            raise ModelTrainingError(f"Model saving failed: {str(e)}")
    
    def load_models(self, filepath: str) -> List[Tuple]:
        """Load trained models efficiently."""
        try:
            return joblib.load(filepath)
        except Exception as e:
            raise ModelTrainingError(f"Model loading failed: {str(e)}")
