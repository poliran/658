"""Consolidated prediction system combining all prediction methods."""
import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional
from .lottery_predictor import LotteryPredictor
from .improved_prediction_strategy import ImprovedPredictionStrategy
from .jackpot_optimizer import JackpotSharingOptimizer
from .constants import LotteryConstants, DEFAULT_LOTTERY, FilePaths

class ConsolidatedPredictor:
    """Unified interface for all prediction methods and strategies."""
    
    def __init__(self, config_path: str = None, lottery_type=DEFAULT_LOTTERY):
        self.config_path = config_path or FilePaths.DEFAULT_CONFIG_FILE
        self.lottery_type = lottery_type
        self.lottery_config = LotteryConstants.get_config(lottery_type)
        
        # Initialize core components
        self.predictor = LotteryPredictor(self.config_path, lottery_type)
        self.strategy = ImprovedPredictionStrategy(lottery_type)
        self.optimizer = JackpotSharingOptimizer(lottery_type)
        
        self.is_trained = False
        self.features = None
    
    def train(self, data_path: str = None) -> None:
        """Train all models and prepare for predictions."""
        data_path = data_path or FilePaths.DEFAULT_DATA_FILE
        self.predictor.train(data_path)
        self.features = self.predictor.data_processor.prepare_next_draw_features()
        self.is_trained = True
    
    def get_all_predictions(self) -> Dict[str, Any]:
        """Generate all types of predictions in one call."""
        if not self.is_trained:
            raise ValueError("System not trained. Call train() first.")
        
        results = {
            'basic': self._get_basic_predictions(),
            'advanced': self._get_advanced_predictions(),
            'optimized': self._get_optimized_predictions(),
            'analysis': self._get_prediction_analysis(),
            'recommendations': self._get_recommendations()
        }
        
        return results
    
    def _get_basic_predictions(self) -> Dict[str, np.ndarray]:
        """Get basic prediction methods."""
        return {
            'standard': self.predictor.predict(self.features, use_improved_strategy=False),
            'improved': self.predictor.predict(self.features, use_improved_strategy=True),
            'ensemble': self.strategy.predict_ensemble(
                self.predictor.models, 
                self.features, 
                self.predictor.data_processor.data
            )
        }
    
    def _get_advanced_predictions(self) -> Dict[str, List[np.ndarray]]:
        """Get advanced prediction strategies."""
        return {
            'multiple_sets': self.predictor.predict_multiple(self.features, count=5),
            'anti_popular': self.predictor.predict_anti_popular(self.features, count=3),
            'strategy_variants': self.strategy.generate_multiple_predictions(
                self.predictor.models,
                self.features,
                self.predictor.data_processor.data,
                count=3
            )
        }
    
    def _get_optimized_predictions(self) -> Dict[str, Any]:
        """Get game-theory optimized predictions."""
        # Generate candidates for optimization
        candidates = []
        candidates.append(self.predictor.predict(self.features, use_improved_strategy=True))
        candidates.extend(self.predictor.predict_multiple(self.features, count=4))
        
        optimized = self.optimizer.optimize_selection(
            candidates, 
            self.predictor.data_processor.data
        )
        
        return {
            'jackpot_optimized': optimized,
            'sharing_optimized': self.predictor.predict(self.features, optimize_sharing=True),
            'risk_analysis': self.optimizer.analyze_sharing_risk(optimized),
            'strategy_comparison': self.optimizer.compare_strategies(candidates)
        }
    
    def _get_prediction_analysis(self) -> Dict[str, Any]:
        """Analyze all predictions for insights."""
        basic = self._get_basic_predictions()
        advanced = self._get_advanced_predictions()
        
        all_predictions = []
        all_predictions.extend(basic.values())
        all_predictions.extend([pred for pred_list in advanced.values() for pred in pred_list])
        
        # Number frequency analysis
        number_freq = {}
        for pred in all_predictions:
            for num in pred:
                number_freq[num] = number_freq.get(num, 0) + 1
        
        # Confidence analysis
        total_predictions = len(all_predictions)
        confidence_levels = {
            'high_confidence': [num for num, freq in number_freq.items() if freq >= total_predictions * 0.4],
            'medium_confidence': [num for num, freq in number_freq.items() if total_predictions * 0.2 <= freq < total_predictions * 0.4],
            'low_confidence': [num for num, freq in number_freq.items() if freq < total_predictions * 0.2]
        }
        
        # Statistical analysis
        all_nums = [num for pred in all_predictions for num in pred]
        
        return {
            'number_frequency': dict(sorted(number_freq.items(), key=lambda x: x[1], reverse=True)),
            'confidence_levels': confidence_levels,
            'statistics': {
                'total_predictions': total_predictions,
                'unique_numbers_used': len(number_freq),
                'most_frequent': max(number_freq.items(), key=lambda x: x[1]),
                'least_frequent': min(number_freq.items(), key=lambda x: x[1]),
                'average_number': np.mean(all_nums),
                'number_range': (min(all_nums), max(all_nums)),
                'odd_even_ratio': sum(1 for n in all_nums if n % 2 == 1) / len(all_nums)
            }
        }
    
    def _get_recommendations(self) -> Dict[str, Any]:
        """Generate consolidated recommendations."""
        analysis = self._get_prediction_analysis()
        optimized = self._get_optimized_predictions()
        
        # Best overall prediction (lowest sharing risk)
        best_prediction = optimized['jackpot_optimized']
        risk_analysis = optimized['risk_analysis']
        
        # High confidence numbers
        high_confidence = analysis['confidence_levels']['high_confidence']
        
        # Generate final recommendation
        if high_confidence:
            # Combine high confidence with low risk
            recommendation = []
            for num in best_prediction:
                if num in high_confidence or len(recommendation) < 3:
                    recommendation.append(num)
            
            # Fill remaining slots with high confidence numbers
            for num in high_confidence:
                if num not in recommendation and len(recommendation) < self.lottery_config["numbers_per_draw"]:
                    recommendation.append(num)
            
            # Fill any remaining slots from best prediction
            for num in best_prediction:
                if num not in recommendation and len(recommendation) < self.lottery_config["numbers_per_draw"]:
                    recommendation.append(num)
        else:
            recommendation = best_prediction
        
        return {
            'primary_recommendation': sorted(recommendation[:self.lottery_config["numbers_per_draw"]]),
            'alternative_recommendations': [
                sorted(optimized['sharing_optimized']),
                sorted(analysis['confidence_levels']['high_confidence'][:self.lottery_config["numbers_per_draw"]] if high_confidence else best_prediction)
            ],
            'confidence_score': len(high_confidence) / self.lottery_config["numbers_per_draw"] if high_confidence else 0.5,
            'sharing_risk_level': 'Low' if risk_analysis['overall_risk'] < 15 else 'Medium' if risk_analysis['overall_risk'] < 25 else 'High',
            'strategy_used': 'Confidence + Risk Optimization' if high_confidence else 'Pure Risk Optimization',
            'key_insights': [
                f"Most frequent number across predictions: {analysis['statistics']['most_frequent'][0]}",
                f"Average number: {analysis['statistics']['average_number']:.1f}",
                f"Sharing risk level: {risk_analysis['overall_risk']:.1f}",
                f"Birthday numbers in recommendation: {sum(1 for n in recommendation if n <= 31)}"
            ]
        }
    
    def get_quick_prediction(self) -> np.ndarray:
        """Get single best prediction quickly."""
        if not self.is_trained:
            self.train()
        
        return self.predictor.predict(self.features, optimize_sharing=True)
    
    def get_summary_report(self) -> str:
        """Generate human-readable summary report."""
        if not self.is_trained:
            self.train()
        
        results = self.get_all_predictions()
        
        report = []
        report.append("🎯 CONSOLIDATED LOTTERY PREDICTION REPORT")
        report.append("=" * 50)
        
        # Primary recommendation
        rec = results['recommendations']
        report.append(f"\n🎲 PRIMARY RECOMMENDATION: {rec['primary_recommendation']}")
        report.append(f"   Strategy: {rec['strategy_used']}")
        report.append(f"   Confidence: {rec['confidence_score']:.1%}")
        report.append(f"   Risk Level: {rec['sharing_risk_level']}")
        
        # Alternative recommendations
        report.append(f"\n🎯 ALTERNATIVES:")
        for i, alt in enumerate(rec['alternative_recommendations'], 1):
            report.append(f"   Option {i}: {alt}")
        
        # Key insights
        report.append(f"\n💡 KEY INSIGHTS:")
        for insight in rec['key_insights']:
            report.append(f"   • {insight}")
        
        # High confidence numbers
        high_conf = results['analysis']['confidence_levels']['high_confidence']
        if high_conf:
            report.append(f"\n🔥 HIGH CONFIDENCE NUMBERS: {sorted(high_conf)}")
        
        # Strategy comparison
        comparison = results['optimized']['strategy_comparison']
        best_strategy = comparison.iloc[0]
        report.append(f"\n📊 BEST STRATEGY: {best_strategy['risk_level']} risk")
        report.append(f"   Numbers: {best_strategy['numbers']}")
        report.append(f"   Sharing Risk: {best_strategy['sharing_risk']:.1f}")
        
        return "\n".join(report)
