"""Optimized model trainer with parallel processing."""
import numpy as np
from typing import Dict, List, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from sklearn.ensemble import VotingRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import cross_val_score
import joblib

class OptimizedModelTrainer:
    """High-performance model trainer with parallelization."""
    
    def __init__(self, config: Dict):
        self.config = config
        self.model_cache = {}
    
    def train_parallel(self, X: np.ndarray, y: np.ndarray) -> List[Tuple]:
        """Train multiple models in parallel."""
        models = []
        
        # Use ThreadPoolExecutor for parallel training
        with ThreadPoolExecutor(max_workers=6) as executor:
            futures = []
            
            for i in range(6):  # 6 lottery positions
                future = executor.submit(self._train_single_model, X, y[:, i], i)
                futures.append(future)
            
            # Collect results as they complete
            for future in as_completed(futures):
                model, scaler, position = future.result()
                models.append((model, scaler, position))
        
        # Sort by position to maintain order
        models.sort(key=lambda x: x[2])
        return [(model, scaler) for model, scaler, pos in models]
    
    def _train_single_model(self, X: np.ndarray, y: np.ndarray, 
                           position: int) -> Tuple:
        """Train a single model for one position."""
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
    
    def _create_optimized_ensemble(self) -> VotingRegressor:
        """Create ensemble with optimized parameters."""
        from xgboost import XGBRegressor
        from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
        
        # Use optimized parameters for speed
        models = [
            ('xgb', XGBRegressor(
                n_estimators=50,  # Reduced for speed
                learning_rate=0.1,
                max_depth=4,      # Reduced depth
                n_jobs=1,         # Single thread per model
                random_state=42
            )),
            ('rf', RandomForestRegressor(
                n_estimators=50,  # Reduced for speed
                max_depth=8,      # Reduced depth
                n_jobs=1,         # Single thread per model
                random_state=42
            )),
            ('gb', GradientBoostingRegressor(
                n_estimators=50,  # Reduced for speed
                learning_rate=0.1,
                max_depth=4,      # Reduced depth
                random_state=42
            ))
        ]
        
        return VotingRegressor(models, n_jobs=1)  # Parallel at position level
    
    def train_with_validation(self, X: np.ndarray, y: np.ndarray) -> List[Tuple]:
        """Train with cross-validation for performance monitoring."""
        models = []
        
        for i in range(6):
            model, scaler = self._train_single_model(X, y[:, i], i)[:2]
            
            # Quick validation
            X_scaled = scaler.transform(X)
            cv_scores = cross_val_score(model, X_scaled, y[:, i], cv=3, n_jobs=-1)
            
            print(f"Position {i+1} CV Score: {cv_scores.mean():.4f} (+/- {cv_scores.std() * 2:.4f})")
            models.append((model, scaler))
        
        return models
    
    def save_models(self, models: List[Tuple], filepath: str) -> None:
        """Save trained models efficiently."""
        joblib.dump(models, filepath, compress=3)
    
    def load_models(self, filepath: str) -> List[Tuple]:
        """Load trained models efficiently."""
        return joblib.load(filepath)
