"""Model evaluation and performance tracking."""
import numpy as np
from typing import List, Dict, Tuple
from sklearn.metrics import mean_squared_error, mean_absolute_error

class ModelEvaluator:
    """Handles model evaluation and performance metrics."""
    
    def __init__(self):
        self.evaluation_history = []
    
    def evaluate_predictions(self, actual: np.ndarray, predicted: np.ndarray) -> Dict[str, float]:
        """Evaluate prediction accuracy."""
        metrics = {}
        
        # Exact match accuracy
        exact_matches = np.sum(np.isin(predicted, actual))
        metrics['exact_matches'] = exact_matches
        metrics['exact_match_rate'] = exact_matches / len(actual)
        
        # Position-wise accuracy
        position_matches = np.sum(actual == predicted)
        metrics['position_matches'] = position_matches
        metrics['position_accuracy'] = position_matches / len(actual)
        
        # Distance-based metrics
        metrics['mse'] = mean_squared_error(actual, predicted)
        metrics['mae'] = mean_absolute_error(actual, predicted)
        
        return metrics
    
    def backtest_model(self, predictor, data_path: str, test_size: int = 10) -> List[Dict]:
        """Perform backtesting on historical data."""
        import pandas as pd
        
        df = pd.read_csv(data_path)
        df = predictor.data_processor._preprocess_data(df)
        
        results = []
        
        for i in range(len(df) - test_size, len(df)):
            # Train on data up to point i
            train_data = df.iloc[:i]
            actual_draw = df.iloc[i]
            
            # Prepare training data
            X, y = predictor.data_processor.prepare_training_data(train_data)
            
            # Train models
            models = []
            for j in range(6):
                model, scaler = predictor.model_trainer.train(X, y[:, j])
                models.append((model, scaler))
            
            # Make prediction
            features = predictor.data_processor.prepare_next_draw_features()
            predictions = []
            used_numbers = set()
            
            for model, scaler in models:
                pred = predictor._generate_unique_prediction(
                    model, scaler, features, used_numbers
                )
                predictions.append(pred)
                used_numbers.add(pred)
            
            # Evaluate
            actual = np.array([actual_draw[f'num_{j}'] for j in range(1, 7)])
            predicted = np.array(sorted(predictions))
            
            metrics = self.evaluate_predictions(actual, predicted)
            metrics['draw_date'] = actual_draw['DRAW_DATE']
            results.append(metrics)
        
        return results
    
    def generate_report(self, results: List[Dict]) -> Dict[str, float]:
        """Generate summary report from evaluation results."""
        if not results:
            return {}
        
        report = {}
        
        # Average metrics
        for key in ['exact_matches', 'exact_match_rate', 'position_matches', 
                   'position_accuracy', 'mse', 'mae']:
            values = [r[key] for r in results if key in r]
            if values:
                report[f'avg_{key}'] = np.mean(values)
                report[f'std_{key}'] = np.std(values)
        
        # Best performance
        best_exact = max(results, key=lambda x: x.get('exact_matches', 0))
        report['best_exact_matches'] = best_exact.get('exact_matches', 0)
        
        return report
