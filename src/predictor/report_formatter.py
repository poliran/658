"""ReportFormatter — formats orchestrator + analyzer output into human-readable reports."""
from typing import Dict, Any
from .prediction_orchestrator import PredictionOrchestrator
from .prediction_analyzer import PredictionAnalyzer


class ReportFormatter:
    """Formats prediction results into human-readable output."""

    def __init__(self, orchestrator: PredictionOrchestrator, analyzer: PredictionAnalyzer):
        self.orchestrator = orchestrator
        self.analyzer = analyzer

    def summary(self) -> str:
        """Generate a full summary report."""
        predictions = self.orchestrator.get_predictions()
        n = self.orchestrator.service.config.numbers_per_draw
        analysis = self.analyzer.analyze(predictions, n)

        optimized = predictions["optimized"]
        risk = predictions["risk_analysis"]
        high_conf = analysis["confidence_levels"]["high_confidence"]

        recommendation = list(optimized)
        for num in high_conf:
            if num not in recommendation and len(recommendation) < n:
                recommendation.append(num)
        recommendation = sorted(recommendation[:n])

        risk_label = (
            "Low" if risk["overall_risk"] < 15
            else "Medium" if risk["overall_risk"] < 25
            else "High"
        )
        strategy = "Confidence + Risk Optimization" if high_conf else "Pure Risk Optimization"
        confidence_score = len(high_conf) / n if high_conf else 0.5

        lines = [
            "🎯 CONSOLIDATED LOTTERY PREDICTION REPORT",
            "=" * 50,
            f"\n🎲 PRIMARY RECOMMENDATION: {recommendation}",
            f"   Strategy: {strategy}",
            f"   Confidence: {confidence_score:.1%}",
            f"   Risk Level: {risk_label}",
            "\n🎯 ALTERNATIVES:",
            f"   Option 1: {sorted(optimized)}",
        ]
        if high_conf:
            lines.append(f"\n🔥 HIGH CONFIDENCE NUMBERS: {sorted(high_conf)}")
        lines += [
            "\n💡 KEY INSIGHTS:",
            f"   • Most frequent number: {analysis['statistics']['most_frequent'][0]}",
            f"   • Average number: {analysis['statistics']['average_number']:.1f}",
            f"   • Sharing risk: {risk['overall_risk']:.1f}",
            f"   • Birthday numbers in recommendation: {sum(1 for n in recommendation if n <= 31)}",
        ]
        return "\n".join(lines)
