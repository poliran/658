"""Consolidated prediction system — now backed by PredictionService via factory."""
import numpy as np
from typing import Dict, Any, List
from .system_factory import PredictionSystemFactory
from .constants import DEFAULT_LOTTERY, FilePaths


class ConsolidatedPredictor:
    """Unified interface for all prediction methods. Delegates to PredictionService."""

    def __init__(self, config_path: str = None, lottery_type=DEFAULT_LOTTERY):
        self.config_path = config_path or FilePaths.DEFAULT_CONFIG_FILE
        self.lottery_type = lottery_type
        self._service = PredictionSystemFactory.create_lottery_predictor(
            self.config_path, lottery_type
        )
        self._model_config = {}
        self._features = None
        self.is_trained = False

    def train(self, data_path: str = None) -> None:
        data_path = data_path or FilePaths.DEFAULT_DATA_FILE
        self._service.train(data_path, self._model_config)
        self._features = self._service.prepare_features(data_path)
        self.is_trained = True

    def get_all_predictions(self) -> Dict[str, Any]:
        self._ensure_trained()
        basic = self._get_basic_predictions()
        advanced = self._get_advanced_predictions()
        optimized = self._get_optimized_predictions()
        analysis = self._get_prediction_analysis(basic, advanced)
        return {
            "basic": basic,
            "advanced": advanced,
            "optimized": optimized,
            "analysis": analysis,
            "recommendations": self._get_recommendations(analysis, optimized),
        }

    def get_quick_prediction(self) -> np.ndarray:
        if not self.is_trained:
            self.train()
        return self._service.predict_optimized(self._features)

    def get_summary_report(self) -> str:
        if not self.is_trained:
            self.train()
        results = self.get_all_predictions()
        rec = results["recommendations"]
        lines = [
            "🎯 CONSOLIDATED LOTTERY PREDICTION REPORT",
            "=" * 50,
            f"\n🎲 PRIMARY RECOMMENDATION: {rec['primary_recommendation']}",
            f"   Strategy: {rec['strategy_used']}",
            f"   Confidence: {rec['confidence_score']:.1%}",
            f"   Risk Level: {rec['sharing_risk_level']}",
            "\n🎯 ALTERNATIVES:",
        ]
        for i, alt in enumerate(rec["alternative_recommendations"], 1):
            lines.append(f"   Option {i}: {alt}")
        lines.append("\n💡 KEY INSIGHTS:")
        for insight in rec["key_insights"]:
            lines.append(f"   • {insight}")
        high_conf = results["analysis"]["confidence_levels"]["high_confidence"]
        if high_conf:
            lines.append(f"\n🔥 HIGH CONFIDENCE NUMBERS: {sorted(high_conf)}")
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _ensure_trained(self):
        if not self.is_trained:
            raise ValueError("Call train() first.")

    def _get_basic_predictions(self) -> Dict[str, np.ndarray]:
        return {
            "standard": self._service.predict(self._features),
            "optimized": self._service.predict_optimized(self._features),
        }

    def _get_advanced_predictions(self) -> Dict[str, List[np.ndarray]]:
        anti_popular = self._service.predict_anti_popular(self._features, count=3)
        multiple = [self._service.predict(self._features) for _ in range(5)]
        return {"anti_popular": anti_popular, "multiple_sets": multiple}

    def _get_optimized_predictions(self) -> Dict[str, Any]:
        optimized = self._service.predict_optimized(self._features)
        risk = self._service.optimizer.analyze_sharing_risk(optimized)
        candidates = [self._service.predict(self._features) for _ in range(5)]
        return {
            "jackpot_optimized": optimized,
            "risk_analysis": risk,
            "strategy_comparison": self._service.optimizer.compare_strategies(candidates),
        }

    def _get_prediction_analysis(self, basic, advanced) -> Dict[str, Any]:
        all_preds = list(basic.values()) + [
            p for lst in advanced.values() for p in lst
        ]
        freq: Dict[int, int] = {}
        for pred in all_preds:
            for n in pred:
                freq[n] = freq.get(n, 0) + 1
        total = len(all_preds)
        confidence = {
            "high_confidence": [n for n, f in freq.items() if f >= total * 0.4],
            "medium_confidence": [n for n, f in freq.items() if total * 0.2 <= f < total * 0.4],
            "low_confidence": [n for n, f in freq.items() if f < total * 0.2],
        }
        all_nums = [n for p in all_preds for n in p]
        return {
            "number_frequency": dict(sorted(freq.items(), key=lambda x: x[1], reverse=True)),
            "confidence_levels": confidence,
            "statistics": {
                "total_predictions": total,
                "unique_numbers_used": len(freq),
                "most_frequent": max(freq.items(), key=lambda x: x[1]),
                "average_number": float(np.mean(all_nums)),
                "odd_even_ratio": sum(1 for n in all_nums if n % 2 == 1) / len(all_nums),
            },
        }

    def _get_recommendations(self, analysis, optimized) -> Dict[str, Any]:
        best = optimized["jackpot_optimized"]
        risk = optimized["risk_analysis"]
        high_conf = analysis["confidence_levels"]["high_confidence"]
        n = self._service.config.numbers_per_draw

        recommendation = list(best)
        for num in high_conf:
            if num not in recommendation and len(recommendation) < n:
                recommendation.append(num)

        return {
            "primary_recommendation": sorted(recommendation[:n]),
            "alternative_recommendations": [sorted(best)],
            "confidence_score": len(high_conf) / n if high_conf else 0.5,
            "sharing_risk_level": (
                "Low" if risk["overall_risk"] < 15
                else "Medium" if risk["overall_risk"] < 25
                else "High"
            ),
            "strategy_used": "Confidence + Risk Optimization" if high_conf else "Pure Risk Optimization",
            "key_insights": [
                f"Most frequent number: {analysis['statistics']['most_frequent'][0]}",
                f"Average number: {analysis['statistics']['average_number']:.1f}",
                f"Sharing risk: {risk['overall_risk']:.1f}",
                f"Birthday numbers in recommendation: {sum(1 for n in recommendation if n <= 31)}",
            ],
        }
