"""PredictionAnalyzer — pure analysis functions over prediction sets."""

import numpy as np
from typing import Dict, List, Any


class PredictionAnalyzer:
    """Stateless analysis of prediction sets. No I/O, no side effects."""

    def analyze(self, predictions: Dict[str, Any], numbers_per_draw: int) -> Dict[str, Any]:
        """Compute frequency and confidence stats over all prediction sets."""
        all_preds: List[np.ndarray] = self._flatten(predictions)
        freq = self._frequency(all_preds)
        total = len(all_preds)
        all_nums = [n for p in all_preds for n in p]

        return {
            "number_frequency": dict(sorted(freq.items(), key=lambda x: x[1], reverse=True)),
            "confidence_levels": {
                "high_confidence": [n for n, f in freq.items() if f >= total * 0.4],
                "medium_confidence": [n for n, f in freq.items() if total * 0.2 <= f < total * 0.4],
                "low_confidence": [n for n, f in freq.items() if f < total * 0.2],
            },
            "statistics": {
                "total_predictions": total,
                "unique_numbers_used": len(freq),
                "most_frequent": max(freq.items(), key=lambda x: x[1]),
                "average_number": float(np.mean(all_nums)),
                "odd_even_ratio": sum(1 for n in all_nums if n % 2 == 1) / len(all_nums),
            },
        }

    # ------------------------------------------------------------------

    def _flatten(self, predictions: Dict[str, Any]) -> List[np.ndarray]:
        result = []
        for v in predictions.values():
            if isinstance(v, np.ndarray):
                result.append(v)
            elif isinstance(v, list):
                for item in v:
                    if isinstance(item, np.ndarray):
                        result.append(item)
        return result

    def _frequency(self, preds: List[np.ndarray]) -> Dict[int, int]:
        freq: Dict[int, int] = {}
        for pred in preds:
            for n in pred:
                freq[int(n)] = freq.get(int(n), 0) + 1
        return freq
