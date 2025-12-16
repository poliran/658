"""Performance benchmarking for optimized vs original implementations."""
import time
import sys
import os
import pandas as pd
import numpy as np
from memory_profiler import profile
import psutil

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.predictor.data_processor import DataProcessor
from src.predictor.optimized_data_processor import OptimizedDataProcessor
from src.predictor.model_trainer import ModelTrainer
from src.predictor.optimized_model_trainer import OptimizedModelTrainer

class PerformanceBenchmark:
    """Benchmark performance improvements."""
    
    def __init__(self, data_path: str, config: dict):
        self.data_path = data_path
        self.config = config
        self.results = {}
    
    def benchmark_data_processing(self):
        """Benchmark data processing performance."""
        print("Benchmarking Data Processing...")
        
        # Original implementation
        start_time = time.time()
        start_memory = psutil.Process().memory_info().rss / 1024 / 1024
        
        original_processor = DataProcessor(self.config)
        original_df = original_processor.load_data(self.data_path)
        
        original_time = time.time() - start_time
        original_memory = psutil.Process().memory_info().rss / 1024 / 1024 - start_memory
        
        # Optimized implementation
        start_time = time.time()
        start_memory = psutil.Process().memory_info().rss / 1024 / 1024
        
        optimized_processor = OptimizedDataProcessor(self.config)
        optimized_df = optimized_processor.load_data(self.data_path)
        
        optimized_time = time.time() - start_time
        optimized_memory = psutil.Process().memory_info().rss / 1024 / 1024 - start_memory
        
        # Results
        self.results['data_processing'] = {
            'original_time': original_time,
            'optimized_time': optimized_time,
            'speedup': original_time / optimized_time,
            'original_memory_mb': original_memory,
            'optimized_memory_mb': optimized_memory,
            'memory_reduction': (original_memory - optimized_memory) / original_memory * 100
        }
        
        print(f"Data Processing Speedup: {self.results['data_processing']['speedup']:.2f}x")
        print(f"Memory Reduction: {self.results['data_processing']['memory_reduction']:.1f}%")
        
        return original_df, optimized_df
    
    def benchmark_model_training(self, df):
        """Benchmark model training performance."""
        print("Benchmarking Model Training...")
        
        # Prepare data
        processor = OptimizedDataProcessor(self.config)
        X, y = processor.prepare_training_data(df)
        
        # Original implementation
        start_time = time.time()
        
        original_trainer = ModelTrainer(self.config)
        original_models = []
        for i in range(6):
            model, scaler = original_trainer.train(X, y[:, i])
            original_models.append((model, scaler))
        
        original_time = time.time() - start_time
        
        # Optimized implementation
        start_time = time.time()
        
        optimized_trainer = OptimizedModelTrainer(self.config)
        optimized_models = optimized_trainer.train_parallel(X, y)
        
        optimized_time = time.time() - start_time
        
        # Results
        self.results['model_training'] = {
            'original_time': original_time,
            'optimized_time': optimized_time,
            'speedup': original_time / optimized_time
        }
        
        print(f"Model Training Speedup: {self.results['model_training']['speedup']:.2f}x")
        
        return original_models, optimized_models
    
    def benchmark_feature_creation(self, df):
        """Benchmark feature creation specifically."""
        print("Benchmarking Feature Creation...")
        
        # Extract just the number columns for testing
        num_cols = [f'num_{i}' for i in range(1, 7)]
        numbers_df = df[num_cols].copy()
        
        # Original approach (nested loops)
        start_time = time.time()
        
        original_features = pd.DataFrame(index=numbers_df.index)
        for i in range(1, 59):
            original_features[f'freq_{i}'] = 0
            for j in range(1, 7):
                original_features[f'freq_{i}'] += (numbers_df[f'num_{j}'] == i).astype(int)
        
        original_time = time.time() - start_time
        
        # Optimized approach (vectorized)
        start_time = time.time()
        
        numbers_array = numbers_df.values
        optimized_features = pd.DataFrame(index=numbers_df.index)
        
        # Vectorized frequency calculation
        for i in range(1, 59):
            optimized_features[f'freq_{i}'] = (numbers_array == i).sum(axis=1)
        
        optimized_time = time.time() - start_time
        
        # Results
        self.results['feature_creation'] = {
            'original_time': original_time,
            'optimized_time': optimized_time,
            'speedup': original_time / optimized_time
        }
        
        print(f"Feature Creation Speedup: {self.results['feature_creation']['speedup']:.2f}x")
    
    def run_full_benchmark(self):
        """Run complete performance benchmark."""
        print("Starting Performance Benchmark...")
        print("=" * 50)
        
        # Benchmark data processing
        original_df, optimized_df = self.benchmark_data_processing()
        
        # Benchmark feature creation
        self.benchmark_feature_creation(optimized_df)
        
        # Benchmark model training
        self.benchmark_model_training(optimized_df)
        
        # Summary
        print("\n" + "=" * 50)
        print("PERFORMANCE SUMMARY")
        print("=" * 50)
        
        for component, metrics in self.results.items():
            print(f"\n{component.upper()}:")
            print(f"  Speedup: {metrics['speedup']:.2f}x")
            if 'memory_reduction' in metrics:
                print(f"  Memory Reduction: {metrics['memory_reduction']:.1f}%")
        
        return self.results

def main():
    """Run performance benchmarks."""
    config = {
        'data': {
            'validation': {
                'required_columns': ['LOTTO GAME', 'COMBINATIONS', 'DRAW DATE']
            }
        },
        'models': {
            'xgboost': {'n_estimators': 50, 'learning_rate': 0.1, 'max_depth': 4},
            'random_forest': {'n_estimators': 50, 'max_depth': 8},
            'gradient_boosting': {'n_estimators': 50, 'learning_rate': 0.1, 'max_depth': 4}
        }
    }
    
    benchmark = PerformanceBenchmark('data/lottery_history.csv', config)
    results = benchmark.run_full_benchmark()
    
    # Save results
    import json
    with open('benchmark_results.json', 'w') as f:
        json.dump(results, f, indent=2)

if __name__ == "__main__":
    main()
