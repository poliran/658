#!/usr/bin/env python3
"""Simple consolidated prediction interface."""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.predictor.consolidated_predictor import ConsolidatedPredictor

def main():
    """Generate consolidated lottery predictions quickly."""
    try:
        print("🎯 Lottery Prediction System")
        print("=" * 40)
        
        # Initialize and train
        predictor = ConsolidatedPredictor()
        print("📊 Training models...")
        predictor.train()
        
        # Get primary recommendation
        results = predictor.get_all_predictions()
        recommendation = results['recommendations']['primary_recommendation']
        
        print(f"\n🎲 RECOMMENDED NUMBERS: {recommendation}")
        
        # Show alternatives
        alternatives = results['recommendations']['alternative_recommendations']
        print(f"\n🎯 ALTERNATIVES:")
        for i, alt in enumerate(alternatives, 1):
            print(f"   Option {i}: {alt}")
        
        # Show confidence info
        confidence = results['recommendations']['confidence_score']
        risk_level = results['recommendations']['sharing_risk_level']
        print(f"\n📊 Confidence: {confidence:.1%} | Risk Level: {risk_level}")
        
        # High confidence numbers
        high_conf = results['analysis']['confidence_levels']['high_confidence']
        if high_conf:
            print(f"🔥 High Confidence: {sorted(high_conf)}")
        
        # Quick anti-popular option
        anti_popular = results['advanced']['anti_popular'][0]
        print(f"💰 Anti-Popular: {sorted(anti_popular)} (Minimal sharing)")
        
        print(f"\n✨ Good luck! 🍀")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
