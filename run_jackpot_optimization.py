#!/usr/bin/env python3
"""Jackpot sharing optimization demonstration script."""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.predictor import LotteryPredictor
from src.predictor.jackpot_optimizer import JackpotSharingOptimizer
from src.predictor.constants import FilePaths
import pandas as pd

def main():
    """Demonstrate jackpot sharing optimization strategies."""
    try:
        print("🎯 Jackpot Sharing Optimization System")
        print("=" * 50)
        
        # Initialize predictor and optimizer
        predictor = LotteryPredictor(FilePaths.DEFAULT_CONFIG_FILE)
        optimizer = JackpotSharingOptimizer()
        
        # Train models
        print("📊 Training models...")
        predictor.train(FilePaths.DEFAULT_DATA_FILE)
        
        # Prepare features
        features = predictor.data_processor.prepare_next_draw_features()
        
        print("\n🎲 PREDICTION COMPARISON")
        print("-" * 40)
        
        # Standard prediction
        standard_pred = predictor.predict(features, optimize_sharing=False)
        print(f"Standard Prediction: {sorted(standard_pred)}")
        
        # Optimized prediction
        optimized_pred = predictor.predict(features, optimize_sharing=True)
        print(f"Optimized Prediction: {sorted(optimized_pred)}")
        
        # Anti-popular predictions
        anti_popular = predictor.predict_anti_popular(features, count=3)
        print(f"\nAnti-Popular Predictions:")
        for i, pred in enumerate(anti_popular, 1):
            print(f"  Set {i}: {sorted(pred)}")
        
        print("\n📊 SHARING RISK ANALYSIS")
        print("-" * 40)
        
        # Analyze all predictions
        all_predictions = [standard_pred, optimized_pred] + anti_popular
        
        for i, pred in enumerate(all_predictions):
            strategy_name = ["Standard", "Optimized", "Anti-Popular 1", "Anti-Popular 2", "Anti-Popular 3"][i]
            analysis = optimizer.analyze_sharing_risk(pred)
            
            print(f"\n{strategy_name}:")
            print(f"  Numbers: {sorted(pred)}")
            print(f"  Overall Risk: {analysis['overall_risk']:.1f}")
            print(f"  Avg Popularity: {analysis['individual_popularity']:.1f}")
            print(f"  Birthday Numbers: {analysis['birthday_numbers']}")
            print(f"  Consecutive Pairs: {analysis['consecutive_pairs']}")
            print(f"  Lucky Numbers: {analysis['lucky_numbers']}")
            print(f"  Multiples: {analysis['multiples_count']}")
            
            # Risk level
            risk_level = "Low" if analysis['overall_risk'] < 15 else "Medium" if analysis['overall_risk'] < 25 else "High"
            print(f"  Risk Level: {risk_level}")
        
        print("\n📈 STRATEGY COMPARISON")
        print("-" * 40)
        
        # Compare strategies
        comparison_df = optimizer.compare_strategies(all_predictions)
        
        print(comparison_df.to_string(index=False))
        
        print("\n🧠 GAME THEORY INSIGHTS")
        print("-" * 40)
        
        best_strategy = comparison_df.iloc[0]
        worst_strategy = comparison_df.iloc[-1]
        
        print(f"🏆 Best Strategy: {best_strategy['strategy']}")
        print(f"   Numbers: {best_strategy['numbers']}")
        print(f"   Sharing Risk: {best_strategy['sharing_risk']:.1f}")
        print(f"   Risk Level: {best_strategy['risk_level']}")
        
        print(f"\n⚠️  Worst Strategy: {worst_strategy['strategy']}")
        print(f"   Numbers: {worst_strategy['numbers']}")
        print(f"   Sharing Risk: {worst_strategy['sharing_risk']:.1f}")
        print(f"   Risk Level: {worst_strategy['risk_level']}")
        
        risk_reduction = worst_strategy['sharing_risk'] - best_strategy['sharing_risk']
        print(f"\n💰 Potential Risk Reduction: {risk_reduction:.1f} points")
        print(f"   ({risk_reduction/worst_strategy['sharing_risk']*100:.1f}% improvement)")
        
        print("\n🎯 RECOMMENDATIONS")
        print("-" * 40)
        
        recommendations = []
        
        if best_strategy['birthday_count'] <= 2:
            recommendations.append("✅ Avoid birthday-heavy combinations (1-31)")
        
        if best_strategy['consecutive_pairs'] == 0:
            recommendations.append("✅ Avoid consecutive number sequences")
        
        recommendations.extend([
            "✅ Choose numbers > 31 when possible",
            "✅ Avoid multiples of 5 and 10",
            "✅ Mix high and low numbers",
            "✅ Avoid obvious visual patterns"
        ])
        
        for rec in recommendations:
            print(f"  {rec}")
        
        print(f"\n🎲 RECOMMENDED NUMBERS: {sorted(best_strategy['numbers'])}")
        print("\n💡 Remember: Lower sharing risk = Higher expected payout if you win!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
