#!/usr/bin/env python3
"""Enhanced lottery prediction script with multiple strategies."""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.predictor import LotteryPredictor
from src.predictor.constants import FilePaths
import numpy as np

def main():
    """Run improved lottery predictions."""
    try:
        print("🎯 Enhanced Lottery Prediction System")
        print("=" * 50)
        
        # Initialize predictor
        predictor = LotteryPredictor(FilePaths.DEFAULT_CONFIG_FILE)
        
        # Train models
        print("📊 Training models...")
        predictor.train(FilePaths.DEFAULT_DATA_FILE)
        
        # Prepare features for next draw
        features = predictor.data_processor.prepare_next_draw_features()
        
        print("\n🔮 IMPROVED PREDICTIONS")
        print("-" * 30)
        
        # Single improved prediction
        improved_prediction = predictor.predict(features, use_improved_strategy=True)
        print(f"🎲 Best Prediction: {sorted(improved_prediction)}")
        
        # Multiple diverse predictions
        print("\n🎯 MULTIPLE PREDICTIONS")
        print("-" * 30)
        
        multiple_predictions = predictor.predict_multiple(features, count=5)
        for i, pred in enumerate(multiple_predictions, 1):
            print(f"Set {i}: {sorted(pred)}")
        
        # Original method for comparison
        print("\n📈 COMPARISON")
        print("-" * 30)
        
        original_prediction = predictor.predict(features, use_improved_strategy=False)
        print(f"Original Method: {sorted(original_prediction)}")
        print(f"Improved Method: {sorted(improved_prediction)}")
        
        # Analysis
        print("\n📊 PREDICTION ANALYSIS")
        print("-" * 30)
        
        all_predictions = [improved_prediction] + multiple_predictions
        
        # Number frequency across predictions
        number_freq = {}
        for pred in all_predictions:
            for num in pred:
                number_freq[num] = number_freq.get(num, 0) + 1
        
        # Most confident numbers (appearing in multiple predictions)
        confident_numbers = [num for num, freq in number_freq.items() if freq > 1]
        if confident_numbers:
            print(f"🔥 High Confidence Numbers: {sorted(confident_numbers)}")
        
        # Range analysis
        all_nums = [num for pred in all_predictions for num in pred]
        print(f"📈 Number Range: {min(all_nums)} - {max(all_nums)}")
        print(f"📊 Average Number: {np.mean(all_nums):.1f}")
        
        # Odd/Even distribution
        odd_count = sum(1 for num in improved_prediction if num % 2 == 1)
        even_count = len(improved_prediction) - odd_count
        print(f"⚖️  Odd/Even Split: {odd_count} odd, {even_count} even")
        
        print("\n✨ Prediction Complete!")
        print("Good luck! 🍀")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
