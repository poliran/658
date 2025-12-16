"""Optimized model evaluator with caching and batch processing."""
import numpy as np
import pandas as pd
from typing import List, Dict, Tuple
from functools import lru_cache
from sklearn.metrics import mean_squared_error, mean_absolute_error
import joblib

class OptimizedModelEvaluator:
    """High-performance evaluator with caching and batch processing."""
    
    def __init__(self):
        self.evaluation_history = []
        self._prediction_cache = {}
        self._data_cache = {}
    
    @lru_cache(maxsize=100)
    def evaluate_predictions_cached(self, actual_tuple: tuple, 
                                   predicted_tuple: tuple) -> Dict[str, float]:
        """Cached evaluation for repeated comparisons."""
        actual = np.array(actual_tuple)
        predicted = np.array(predicted_tuple)
        
        return self._calculate_metrics(actual, predicted)
    
    def _calculate_metrics(self, actual: np.ndarray, 
                          predicted: np.ndarray) -> Dict[str, float]:
        """Vectorized metric calculations."""
        metrics = {}
        
        # Vectorized exact match calculation
        exact_matches = np.isin(predicted, actual).sum()
        metrics['exact_matches'] = int(exact_matches)
        metrics['exact_match_rate'] = float(exact_matches / len(actual))
        
        # Vectorized position accuracy
        position_matches = (actual == predicted).sum()
        metrics['position_matches'] = int(position_matches)
        metrics['position_accuracy'] = float(position_matches / len(actual))
        
        # Efficient distance metrics
        metrics['mse'] = float(mean_squared_error(actual, predicted))
        metrics['mae'] = float(mean_absolute_error(actual, predicted))
        
        return metrics
    
    def backtest_optimized(self, predictor, data_path: str, 
                          test_size: int = 10) -> List[Dict]:
        """Optimized backtesting with incremental training."""
        # Load and cache data
        cache_key = f"{data_path}_{test_size}"
        
        if cache_key in self._data_cache:
            df = self._data_cache[cache_key]
        else:
            df = pd.read_csv(data_path)
            df = predictor.data_processor._preprocess_data_vectorized(df)
            self._data_cache[cache_key] = df
        
        results = []
        base_size = len(df) - test_size
        
        # Pre-compute base training data
        base_data = df.iloc[:base_size]
        base_X, base_y = predictor.data_processor.prepare_training_data(base_data)
        
        # Incremental evaluation
        for i in range(test_size):
            current_idx = base_size + i
            
            # Incremental data (just add one row)
            if i == 0:
                train_X, train_y = base_X, base_y
            else:
                # Add one more row to training data
                additional_data = df.iloc[:current_idx]
                train_X, train_y = predictor.data_processor.prepare_training_data(additional_data)
            
            actual_draw = df.iloc[current_idx]
            
            # Use cached models if available
            model_key = f"{current_idx}_{train_X.shape[0]}"
            
            if model_key in self._prediction_cache:
                predictions = self._prediction_cache[model_key]
            else:
                # Train models (can be parallelized)
                models = predictor.model_trainer.train_parallel(train_X, train_y)
                
                # Generate predictions
                features = predictor.data_processor.prepare_next_draw_features()
                predictions = self._generate_predictions_batch(models, features)
                
                self._prediction_cache[model_key] = predictions
            
            # Evaluate
            actual = tuple(actual_draw[f'num_{j}'] for j in range(1, 7))
            predicted = tuple(sorted(predictions))
            
            metrics = self.evaluate_predictions_cached(actual, predicted)
            metrics['draw_date'] = actual_draw['DRAW_DATE']
            results.append(metrics)
        
        return results
    
    def _generate_predictions_batch(self, models: List[Tuple], 
                                   features: np.ndarray) -> List[int]:
        """Generate predictions in batch for efficiency."""
        predictions = []
        used_numbers = set()
        
        # Batch prediction for all models
        scaled_features = []
        for model, scaler in models:
            scaled_features.append(scaler.transform(features))
        
        # Generate predictions
        for i, (model, scaler) in enumerate(models):
            pred_value = model.predict(scaled_features[i])[0]
            predicted_num = max(1, min(58, round(pred_value)))
            
            # Find unique number efficiently
            if predicted_num in used_numbers:
                for offset in range(1, 59):
                    for candidate in [predicted_num + offset, predicted_num - offset]:
                        if 1 <= candidate <= 58 and candidate not in used_numbers:
                            predicted_num = candidate
                            break
                    if predicted_num not in used_numbers:
                        break
            
            predictions.append(predicted_num)
            used_numbers.add(predicted_num)
        
        return predictions
    
    def generate_report_vectorized(self, results: List[Dict]) -> Dict[str, float]:
        """Generate report using vectorized operations."""
        if not results:
            return {}
        
        # Convert to arrays for vectorized operations
        metrics_arrays = {}
        for key in ['exact_matches', 'exact_match_rate', 'position_matches', 
                   'position_accuracy', 'mse', 'mae']:
            values = [r[key] for r in results if key in r]
            if values:
                arr = np.array(values)
                metrics_arrays[f'avg_{key}'] = float(arr.mean())
                metrics_arrays[f'std_{key}'] = float(arr.std())
                metrics_arrays[f'min_{key}'] = float(arr.min())
                metrics_arrays[f'max_{key}'] = float(arr.max())
        
        # Best performance
        exact_matches = [r.get('exact_matches', 0) for r in results]
        if exact_matches:
            metrics_arrays['best_exact_matches'] = max(exact_matches)
        
        return metrics_arrays
    
    def clear_cache(self) -> None:
        """Clear evaluation caches to free memory."""
        self._prediction_cache.clear()
        self._data_cache.clear()
        self.evaluate_predictions_cached.cache_clear()
