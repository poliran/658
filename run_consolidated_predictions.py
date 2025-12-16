#!/usr/bin/env python3
"""Consolidated prediction runner - all prediction methods in one place."""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.predictor.consolidated_predictor import ConsolidatedPredictor
import json
import numpy as np

def main():
    """Run consolidated prediction analysis."""
    try:
        print("🎯 CONSOLIDATED LOTTERY PREDICTION SYSTEM")
        print("=" * 60)
        
        # Initialize consolidated predictor
        predictor = ConsolidatedPredictor()
        
        # Train system
        print("📊 Training all models and strategies...")
        predictor.train()
        
        # Generate summary report
        print("\n" + predictor.get_summary_report())
        
        # Get detailed results
        print("\n🔍 DETAILED ANALYSIS")
        print("-" * 40)
        
        results = predictor.get_all_predictions()
        
        # Basic predictions
        print("\n📈 BASIC PREDICTIONS:")
        basic = results['basic']
        print(f"   Standard Method: {sorted(basic['standard'])}")
        print(f"   Improved Method: {sorted(basic['improved'])}")
        print(f"   Ensemble Method: {sorted(basic['ensemble'])}")
        
        # Advanced predictions
        print("\n🎯 ADVANCED PREDICTIONS:")
        advanced = results['advanced']
        
        print("   Multiple Sets:")
        for i, pred in enumerate(advanced['multiple_sets'], 1):
            print(f"     Set {i}: {sorted(pred)}")
        
        print("   Anti-Popular Sets:")
        for i, pred in enumerate(advanced['anti_popular'], 1):
            print(f"     Set {i}: {sorted(pred)}")
        
        # Optimized predictions
        print("\n💰 OPTIMIZED PREDICTIONS:")
        optimized = results['optimized']
        print(f"   Jackpot Optimized: {sorted(optimized['jackpot_optimized'])}")
        print(f"   Sharing Optimized: {sorted(optimized['sharing_optimized'])}")
        
        # Risk analysis
        risk = optimized['risk_analysis']
        print(f"\n📊 RISK ANALYSIS:")
        print(f"   Overall Risk Score: {risk['overall_risk']:.1f}")
        print(f"   Average Popularity: {risk['individual_popularity']:.1f}")
        print(f"   Birthday Numbers: {risk['birthday_numbers']}")
        print(f"   Lucky Numbers: {risk['lucky_numbers']}")
        print(f"   Consecutive Pairs: {risk['consecutive_pairs']}")
        
        # Frequency analysis
        analysis = results['analysis']
        print(f"\n🔢 FREQUENCY ANALYSIS:")
        top_numbers = list(analysis['number_frequency'].items())[:10]
        print("   Most Frequent Numbers:")
        for num, freq in top_numbers:
            print(f"     {num}: appears in {freq} predictions")
        
        # Statistics
        stats = analysis['statistics']
        print(f"\n📊 STATISTICS:")
        print(f"   Total Predictions Generated: {stats['total_predictions']}")
        print(f"   Unique Numbers Used: {stats['unique_numbers_used']}")
        print(f"   Average Number: {stats['average_number']:.1f}")
        print(f"   Number Range: {stats['number_range'][0]}-{stats['number_range'][1]}")
        print(f"   Odd/Even Ratio: {stats['odd_even_ratio']:.1%} odd")
        
        # Strategy comparison
        print(f"\n🏆 STRATEGY COMPARISON:")
        comparison = optimized['strategy_comparison']
        print(comparison.to_string(index=False))
        
        # Save simplified results (skip complex JSON serialization)
        output_file = "outputs/consolidated_predictions_summary.txt"
        os.makedirs("outputs", exist_ok=True)
        
        with open(output_file, 'w') as f:
            f.write(predictor.get_summary_report())
            f.write("\n\n" + "="*60 + "\n")
            f.write("DETAILED PREDICTIONS:\n")
            f.write(f"Standard: {sorted(results['basic']['standard'])}\n")
            f.write(f"Improved: {sorted(results['basic']['improved'])}\n")
            f.write(f"Optimized: {sorted(results['optimized']['jackpot_optimized'])}\n")
        
        print(f"\n💾 Summary report saved to: {output_file}")
        
        # Quick prediction for immediate use
        print(f"\n⚡ QUICK PREDICTION:")
        quick = predictor.get_quick_prediction()
        print(f"   {sorted(quick)} (Optimized for minimal sharing)")
        
        print(f"\n✨ Analysis Complete!")
        print(f"🍀 Good luck with your lottery predictions!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
