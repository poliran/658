"""Improved prediction strategies for better lottery number generation."""
import numpy as np
import pandas as pd
from typing import List, Dict, Tuple
from collections import Counter
from .constants import LotteryConstants, DEFAULT_LOTTERY, ColumnNames

class ImprovedPredictionStrategy:
    """Advanced prediction strategy combining multiple approaches."""
    
    def __init__(self, lottery_type=DEFAULT_LOTTERY):
        self.lottery_type = lottery_type
        self.lottery_config = LotteryConstants.get_config(lottery_type)
        self.number_range = LotteryConstants.get_number_range(lottery_type)
        
    def predict_ensemble(self, models: List, features: np.ndarray, 
                        historical_data: pd.DataFrame, optimize_sharing: bool = False) -> np.ndarray:
        """Generate predictions using ensemble of strategies."""
        
        # Strategy 1: Model-based predictions
        model_predictions = self._model_based_prediction(models, features)
        
        # Strategy 2: Frequency-based predictions
        freq_predictions = self._frequency_based_prediction(historical_data)
        
        # Strategy 3: Pattern-based predictions
        pattern_predictions = self._pattern_based_prediction(historical_data)
        
        # Strategy 4: Hot/Cold number analysis
        hot_cold_predictions = self._hot_cold_analysis(historical_data)
        
        # Combine strategies with weights
        combined = self._combine_strategies({
            'model': (model_predictions, 0.4),
            'frequency': (freq_predictions, 0.25),
            'pattern': (pattern_predictions, 0.2),
            'hot_cold': (hot_cold_predictions, 0.15)
        })
        
        # Apply jackpot sharing optimization if requested
        if optimize_sharing:
            from .jackpot_optimizer import JackpotSharingOptimizer
            optimizer = JackpotSharingOptimizer(self.lottery_type)
            
            # Generate multiple candidates and optimize
            candidates = [combined]
            for _ in range(4):  # Generate 4 additional candidates
                candidate = self._combine_strategies({
                    'model': (model_predictions, 0.4),
                    'frequency': (freq_predictions, 0.25),
                    'pattern': (pattern_predictions, 0.2),
                    'hot_cold': (hot_cold_predictions, 0.15)
                })
                candidates.append(candidate)
            
            combined = optimizer.optimize_selection(candidates, historical_data)
        
        return combined
    
    def _model_based_prediction(self, models: List, features: np.ndarray) -> np.ndarray:
        """Generate predictions using trained models."""
        predictions = []
        used_numbers = set()
        
        for model, scaler in models:
            features_scaled = scaler.transform(features)
            pred_value = model.predict(features_scaled)[0]
            
            # Add some randomness to avoid identical predictions
            noise = np.random.normal(0, 0.5)
            predicted_num = max(
                self.lottery_config["min_number"],
                min(self.lottery_config["max_number"], round(pred_value + noise))
            )
            
            # Find unique number
            if predicted_num in used_numbers:
                for offset in range(1, len(self.number_range)):
                    for candidate in [predicted_num + offset, predicted_num - offset]:
                        if candidate in self.number_range and candidate not in used_numbers:
                            predicted_num = candidate
                            break
                    if predicted_num not in used_numbers:
                        break
            
            predictions.append(predicted_num)
            used_numbers.add(predicted_num)
        
        return np.array(predictions)
    
    def _frequency_based_prediction(self, df: pd.DataFrame) -> np.ndarray:
        """Predict based on historical frequency analysis."""
        # Get recent draws (last 50)
        recent_df = df.tail(50)
        
        # Count frequency of each number
        all_numbers = []
        number_cols = ColumnNames.get_number_columns(self.lottery_config["numbers_per_draw"])
        
        for _, row in recent_df.iterrows():
            for col in number_cols:
                if col in row:
                    all_numbers.append(row[col])
        
        # Calculate frequencies
        freq_counter = Counter(all_numbers)
        
        # Select numbers with balanced frequency (not too hot, not too cold)
        avg_freq = len(all_numbers) / len(self.number_range)
        balanced_numbers = [
            num for num in self.number_range 
            if abs(freq_counter.get(num, 0) - avg_freq) <= avg_freq * 0.3
        ]
        
        # Randomly select from balanced numbers
        if len(balanced_numbers) >= self.lottery_config["numbers_per_draw"]:
            selected = np.random.choice(
                balanced_numbers, 
                self.lottery_config["numbers_per_draw"], 
                replace=False
            )
        else:
            # Fallback to weighted random selection
            numbers = list(self.number_range)
            weights = [freq_counter.get(num, 1) for num in numbers]
            selected = np.random.choice(
                numbers, 
                self.lottery_config["numbers_per_draw"], 
                replace=False,
                p=np.array(weights) / sum(weights)
            )
        
        return np.sort(selected)
    
    def _pattern_based_prediction(self, df: pd.DataFrame) -> np.ndarray:
        """Predict based on number patterns and sequences."""
        recent_df = df.tail(20)
        number_cols = ColumnNames.get_number_columns(self.lottery_config["numbers_per_draw"])
        
        # Analyze consecutive number patterns
        consecutive_pairs = []
        for _, row in recent_df.iterrows():
            numbers = sorted([row[col] for col in number_cols if col in row])
            for i in range(len(numbers) - 1):
                if numbers[i+1] == numbers[i] + 1:
                    consecutive_pairs.append((numbers[i], numbers[i+1]))
        
        # Analyze odd/even patterns
        odd_even_patterns = []
        for _, row in recent_df.iterrows():
            numbers = [row[col] for col in number_cols if col in row]
            odd_count = sum(1 for n in numbers if n % 2 == 1)
            odd_even_patterns.append(odd_count)
        
        avg_odd = np.mean(odd_even_patterns)
        target_odd = max(1, min(5, round(avg_odd)))
        
        # Generate numbers following patterns
        predictions = []
        
        # Add some consecutive numbers if pattern exists
        if consecutive_pairs and np.random.random() < 0.3:
            pair = consecutive_pairs[np.random.randint(len(consecutive_pairs))]
            predictions.extend(pair)
        
        # Fill remaining with balanced odd/even
        while len(predictions) < self.lottery_config["numbers_per_draw"]:
            candidate = np.random.choice(list(self.number_range))
            
            if candidate not in predictions:
                current_odd = sum(1 for n in predictions if n % 2 == 1)
                needed_odd = target_odd - current_odd
                remaining_slots = self.lottery_config["numbers_per_draw"] - len(predictions)
                
                if (candidate % 2 == 1 and needed_odd > 0) or \
                   (candidate % 2 == 0 and needed_odd <= remaining_slots - 1):
                    predictions.append(candidate)
        
        return np.sort(predictions[:self.lottery_config["numbers_per_draw"]])
    
    def _hot_cold_analysis(self, df: pd.DataFrame) -> np.ndarray:
        """Analyze hot and cold numbers for prediction."""
        # Analyze last 100 draws
        recent_df = df.tail(100)
        number_cols = ColumnNames.get_number_columns(self.lottery_config["numbers_per_draw"])
        
        # Count occurrences
        number_counts = Counter()
        for _, row in recent_df.iterrows():
            for col in number_cols:
                if col in row:
                    number_counts[row[col]] += 1
        
        # Identify hot and cold numbers
        avg_count = sum(number_counts.values()) / len(self.number_range)
        
        hot_numbers = [n for n in self.number_range if number_counts.get(n, 0) > avg_count * 1.2]
        cold_numbers = [n for n in self.number_range if number_counts.get(n, 0) < avg_count * 0.8]
        warm_numbers = [n for n in self.number_range if n not in hot_numbers and n not in cold_numbers]
        
        # Balanced selection: mix of hot, warm, and cold
        predictions = []
        
        # Select 2-3 hot numbers
        if hot_numbers:
            hot_count = min(3, len(hot_numbers), self.lottery_config["numbers_per_draw"] // 2)
            predictions.extend(np.random.choice(hot_numbers, hot_count, replace=False))
        
        # Select 2-3 warm numbers
        remaining = self.lottery_config["numbers_per_draw"] - len(predictions)
        if warm_numbers and remaining > 0:
            warm_count = min(remaining, len(warm_numbers), 3)
            predictions.extend(np.random.choice(warm_numbers, warm_count, replace=False))
        
        # Fill remaining with cold numbers (due for appearance)
        remaining = self.lottery_config["numbers_per_draw"] - len(predictions)
        if cold_numbers and remaining > 0:
            cold_count = min(remaining, len(cold_numbers))
            predictions.extend(np.random.choice(cold_numbers, cold_count, replace=False))
        
        # Fill any remaining slots randomly
        while len(predictions) < self.lottery_config["numbers_per_draw"]:
            candidate = np.random.choice(list(self.number_range))
            if candidate not in predictions:
                predictions.append(candidate)
        
        return np.sort(predictions[:self.lottery_config["numbers_per_draw"]])
    
    def _combine_strategies(self, strategies: Dict[str, Tuple[np.ndarray, float]]) -> np.ndarray:
        """Combine multiple prediction strategies with weights."""
        # Create scoring matrix
        scores = np.zeros(len(self.number_range))
        
        for strategy_name, (predictions, weight) in strategies.items():
            for i, num in enumerate(predictions):
                if num in self.number_range:
                    idx = num - self.lottery_config["min_number"]
                    # Higher score for earlier positions (more confident predictions)
                    position_weight = (len(predictions) - i) / len(predictions)
                    scores[idx] += weight * position_weight
        
        # Add randomness to prevent identical results
        noise = np.random.normal(0, 0.1, len(scores))
        scores += noise
        
        # Select top numbers
        top_indices = np.argsort(scores)[-self.lottery_config["numbers_per_draw"]:]
        selected_numbers = [idx + self.lottery_config["min_number"] for idx in top_indices]
        
        return np.sort(selected_numbers)
    
    def generate_multiple_predictions(self, models: List, features: np.ndarray,
                                    historical_data: pd.DataFrame, count: int = 5) -> List[np.ndarray]:
        """Generate multiple diverse prediction sets."""
        predictions = []
        
        for i in range(count):
            # Set different random seed for each prediction
            np.random.seed(42 + i)
            
            pred = self.predict_ensemble(models, features, historical_data)
            predictions.append(pred)
        
        return predictions
