"""Game-theoretic jackpot sharing optimization for lottery predictions."""
import numpy as np
import pandas as pd
from typing import List, Dict, Tuple, Set
from collections import Counter
from itertools import combinations
from .constants import LotteryConstants, DEFAULT_LOTTERY

class JackpotSharingOptimizer:
    """Optimizes lottery number selection to minimize jackpot sharing using game theory."""
    
    def __init__(self, lottery_type=DEFAULT_LOTTERY):
        self.lottery_type = lottery_type
        self.lottery_config = LotteryConstants.get_config(lottery_type)
        self.number_range = LotteryConstants.get_number_range(lottery_type)
        
        # Common human biases in number selection
        self.bias_patterns = {
            'birthdays': list(range(1, 32)),  # Birthday numbers (1-31)
            'lucky_numbers': [7, 11, 13, 21, 23],  # Commonly considered lucky
            'patterns': self._generate_visual_patterns(),  # Visual patterns on tickets
            'sequences': self._generate_sequences(),  # Consecutive sequences
            'multiples': self._generate_multiples(),  # Multiples of 5, 10
        }
    
    def optimize_selection(self, base_predictions: List[np.ndarray], 
                          historical_data: pd.DataFrame = None) -> np.ndarray:
        """Optimize number selection to minimize expected jackpot sharing."""
        
        # Calculate popularity scores for all numbers
        popularity_scores = self._calculate_popularity_scores(historical_data)
        
        # Evaluate each prediction set
        best_prediction = None
        lowest_sharing_risk = float('inf')
        
        for prediction in base_predictions:
            sharing_risk = self._calculate_sharing_risk(prediction, popularity_scores)
            
            if sharing_risk < lowest_sharing_risk:
                lowest_sharing_risk = sharing_risk
                best_prediction = prediction
        
        # Further optimize the best prediction
        optimized = self._fine_tune_selection(best_prediction, popularity_scores)
        
        return optimized
    
    def _calculate_popularity_scores(self, historical_data: pd.DataFrame = None) -> Dict[int, float]:
        """Calculate popularity scores for each number based on human biases."""
        scores = {}
        
        for num in self.number_range:
            score = 1.0  # Base popularity
            
            # Birthday bias (very high popularity for 1-31)
            if num in self.bias_patterns['birthdays']:
                score *= 3.5
            
            # Lucky number bias
            if num in self.bias_patterns['lucky_numbers']:
                score *= 2.8
            
            # Pattern bias (visual patterns on lottery tickets)
            if num in self.bias_patterns['patterns']:
                score *= 2.2
            
            # Multiple bias (people like round numbers)
            if num in self.bias_patterns['multiples']:
                score *= 1.8
            
            # Sequence bias
            if num in self.bias_patterns['sequences']:
                score *= 1.5
            
            # Edge number bias (people avoid very high/low numbers)
            if num <= 5 or num >= 55:
                score *= 0.7
            
            # Middle range preference
            if 20 <= num <= 40:
                score *= 1.3
            
            scores[num] = score
        
        return scores
    
    def _calculate_sharing_risk(self, prediction: np.ndarray, 
                               popularity_scores: Dict[int, float]) -> float:
        """Calculate expected jackpot sharing risk for a prediction set."""
        
        # Individual number popularity
        individual_risk = sum(popularity_scores[num] for num in prediction)
        
        # Combination pattern penalties
        pattern_risk = 0.0
        
        # Check for consecutive numbers (very popular pattern)
        consecutive_count = self._count_consecutive_numbers(prediction)
        pattern_risk += consecutive_count * 2.0
        
        # Check for arithmetic sequences
        if self._is_arithmetic_sequence(prediction):
            pattern_risk += 3.0
        
        # Check for all odd/even (popular patterns)
        odd_count = sum(1 for n in prediction if n % 2 == 1)
        if odd_count == 0 or odd_count == len(prediction):
            pattern_risk += 2.5
        
        # Check for birthday-heavy combinations
        birthday_count = sum(1 for n in prediction if n <= 31)
        if birthday_count >= 4:
            pattern_risk += birthday_count * 1.5
        
        # Check for multiples pattern
        multiples_count = sum(1 for n in prediction if n % 5 == 0 or n % 10 == 0)
        if multiples_count >= 3:
            pattern_risk += multiples_count * 1.2
        
        return individual_risk + pattern_risk
    
    def _fine_tune_selection(self, prediction: np.ndarray, 
                            popularity_scores: Dict[int, float]) -> np.ndarray:
        """Fine-tune selection by replacing high-risk numbers with low-risk alternatives."""
        
        optimized = prediction.copy()
        sorted_by_popularity = sorted(prediction, key=lambda x: popularity_scores[x], reverse=True)
        
        # Replace the most popular numbers if better alternatives exist
        for i, high_risk_num in enumerate(sorted_by_popularity[:2]):  # Top 2 most popular
            
            # Find low-popularity alternatives
            alternatives = [
                num for num in self.number_range 
                if num not in optimized and popularity_scores[num] < popularity_scores[high_risk_num] * 0.7
            ]
            
            if alternatives:
                # Choose the least popular alternative
                best_alternative = min(alternatives, key=lambda x: popularity_scores[x])
                
                # Check if replacement improves overall risk
                current_risk = self._calculate_sharing_risk(optimized, popularity_scores)
                
                test_prediction = optimized.copy()
                test_prediction[np.where(test_prediction == high_risk_num)[0][0]] = best_alternative
                new_risk = self._calculate_sharing_risk(test_prediction, popularity_scores)
                
                if new_risk < current_risk:
                    optimized = test_prediction
        
        return np.sort(optimized)
    
    def _generate_visual_patterns(self) -> List[int]:
        """Generate numbers that form visual patterns on lottery tickets."""
        patterns = []
        
        # Diagonal patterns (assuming 6x10 grid layout)
        for start in range(1, 50, 7):  # Diagonal lines
            patterns.extend(range(start, min(start + 30, 59), 7))
        
        # Vertical columns
        for col in range(1, 11):
            patterns.extend(range(col, 59, 10))
        
        return list(set(patterns))
    
    def _generate_sequences(self) -> List[int]:
        """Generate anchor numbers of commonly chosen sequential runs (e.g. 1-2-3)."""
        # Only the starting anchors of the most popular sequential picks
        return list(range(1, 10))
    
    def _generate_multiples(self) -> List[int]:
        """Generate multiples that people commonly choose."""
        multiples = []
        
        # Multiples of 5
        multiples.extend(range(5, 59, 5))
        
        # Multiples of 10
        multiples.extend(range(10, 59, 10))
        
        return list(set(multiples))
    
    def _count_consecutive_numbers(self, numbers: np.ndarray) -> int:
        """Count consecutive number pairs in the selection."""
        sorted_nums = np.sort(numbers)
        consecutive_count = 0
        
        for i in range(len(sorted_nums) - 1):
            if sorted_nums[i + 1] == sorted_nums[i] + 1:
                consecutive_count += 1
        
        return consecutive_count
    
    def _is_arithmetic_sequence(self, numbers: np.ndarray) -> bool:
        """Check if numbers form an arithmetic sequence."""
        if len(numbers) < 3:
            return False
        
        sorted_nums = np.sort(numbers)
        diff = sorted_nums[1] - sorted_nums[0]
        
        for i in range(2, len(sorted_nums)):
            if sorted_nums[i] - sorted_nums[i-1] != diff:
                return False
        
        return True
    
    def analyze_sharing_risk(self, prediction: np.ndarray) -> Dict[str, float]:
        """Analyze and report sharing risk factors for a prediction."""
        popularity_scores = self._calculate_popularity_scores()
        
        analysis = {
            'overall_risk': self._calculate_sharing_risk(prediction, popularity_scores),
            'individual_popularity': sum(popularity_scores[num] for num in prediction) / len(prediction),
            'birthday_numbers': sum(1 for n in prediction if n <= 31),
            'lucky_numbers': sum(1 for n in prediction if n in self.bias_patterns['lucky_numbers']),
            'consecutive_pairs': self._count_consecutive_numbers(prediction),
            'multiples_count': sum(1 for n in prediction if n % 5 == 0 or n % 10 == 0),
            'odd_even_balance': sum(1 for n in prediction if n % 2 == 1),
            'is_arithmetic_sequence': self._is_arithmetic_sequence(prediction),
        }
        
        return analysis
    
    def generate_anti_popular_prediction(self, count: int = 1) -> List[np.ndarray]:
        """Generate predictions specifically designed to minimize sharing."""
        popularity_scores = self._calculate_popularity_scores()
        
        # Sort numbers by popularity (ascending - least popular first)
        sorted_numbers = sorted(self.number_range, key=lambda x: popularity_scores[x])
        
        predictions = []
        
        for i in range(count):
            # Start with least popular numbers
            base_selection = sorted_numbers[:self.lottery_config["numbers_per_draw"] + 5]
            selected = np.random.choice(
                base_selection, 
                self.lottery_config["numbers_per_draw"], 
                replace=False
            )
            
            # Ensure no obvious patterns
            while (self._count_consecutive_numbers(selected) > 1 or 
                   self._is_arithmetic_sequence(selected)):
                selected = np.random.choice(
                    base_selection, 
                    self.lottery_config["numbers_per_draw"], 
                    replace=False
                )
            
            predictions.append(np.sort(selected))
        
        return predictions
    
    def compare_strategies(self, predictions: List[np.ndarray]) -> pd.DataFrame:
        """Compare sharing risk across different prediction strategies."""
        results = []
        
        for i, pred in enumerate(predictions):
            analysis = self.analyze_sharing_risk(pred)
            results.append({
                'strategy': f'Strategy_{i+1}',
                'numbers': sorted(pred),
                'sharing_risk': analysis['overall_risk'],
                'avg_popularity': analysis['individual_popularity'],
                'birthday_count': analysis['birthday_numbers'],
                'consecutive_pairs': analysis['consecutive_pairs'],
                'risk_level': 'Low' if analysis['overall_risk'] < 15 else 'Medium' if analysis['overall_risk'] < 25 else 'High'
            })
        
        return pd.DataFrame(results).sort_values('sharing_risk')
