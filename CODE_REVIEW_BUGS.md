# Code Review: Bugs & Issues Found

## Critical Bugs

### 1. **`config_manager.py` - Dead reference to removed class**
**File:** `config_manager.py`  
**Line:** Import statement  
**Severity:** 🔴 CRITICAL - Will crash on import

```python
from .interfaces import LotteryConfig  # ❌ This class was removed
```

**Problem:** After removing `LotteryConfig` from `interfaces.py`, this import will fail.

**Current Usage:**
```python
def get_lottery_config(self) -> LotteryConfig:
    return LotteryConfig(...)  # ❌ Crashes
```

**Fix:** Import the dict-based config instead and return a dict, or import from `constants.py`:
```python
# Option 1: Return dict (recommended)
def get_lottery_config(self) -> Dict[str, Any]:
    return self._config.get('lottery', {})

# Option 2: Keep LotteryConfig in interfaces.py (not ideal)
```

---

### 2. **`prediction_service.py` - Dead import of removed class**
**File:** `prediction_service.py`  
**Line:** 10  
**Severity:** 🔴 CRITICAL - Will crash on import

```python
from .interfaces import DataLoader, DataValidator, FeatureEngineer, ModelFactory, PredictionStrategy, LotteryConfig
#                                                                                                          ^^^^^^^^^^^
#                                                                                      This doesn't exist anymore!

class PredictionService:
    def __init__(
        self,
        ...
        config: LotteryConfig,  # ❌ Invalid type annotation
        ...
    ):
```

**Fix:** Import dict and annotate correctly:
```python
from typing import Dict, Any

class PredictionService:
    def __init__(
        self,
        ...
        config: Dict[str, Any],  # ✅ Use dict
        ...
    ):
```

---

### 3. **`prediction_service.py` - Type mismatch in config usage**
**File:** `prediction_service.py`  
**Lines:** 58-59, 96  
**Severity:** 🟠 HIGH - Runtime AttributeError

```python
def train(self, data_source: str, model_config: Dict) -> None:
    ...
    for i in range(self.config.numbers_per_draw):  # ❌ config is a dict, not object
```

**Problem:** `self.config` is now a dict after removing `LotteryConfig`, but code accesses it as an object with attributes.

**Expected Error:**
```
TypeError: 'dict' object has no attribute 'numbers_per_draw'
```

**Fix:** Access dict keys instead:
```python
for i in range(self.config['numbers_per_draw']):  # ✅
```

**Affected locations:**
- Line 58: `self.config.numbers_per_draw`
- Line 96: `self.config.numbers_per_draw`
- `consolidated_predictor.py` line 122: `self._service.config.numbers_per_draw`

---

### 4. **`features/engineers.py` - Invalid LotteryConfig usage**
**File:** `features/engineers.py`  
**Lines:** 30-31, 44  
**Severity:** 🟠 HIGH - Runtime crash

```python
def __init__(self, config: LotteryConfig):  # ❌ Type doesn't exist
    self.config = config

def _create_frequency_features(self, df: pd.DataFrame) -> pd.DataFrame:
    assignments = {
        f'freq_{num}': sum(...)
        for num in self.config.number_range  # ❌ Accessing .number_range
    }
```

**Problem:** `LotteryConfig` class removed, but code still tries to use it and access `.number_range` attribute.

**Fix:** Use `LotteryConstants` instead:
```python
from ..constants import LotteryConstants

def __init__(self, config: Dict[str, Any]):
    self.config = config

def _create_frequency_features(self, df: pd.DataFrame) -> pd.DataFrame:
    number_range = range(1, self.config['max_number'] + 1)
    assignments = {
        f'freq_{num}': sum(...)
        for num in number_range
    }
```

---

### 5. **`strategies/prediction.py` - Invalid LotteryConfig type annotation**
**File:** `strategies/prediction.py`  
**Lines:** 10, 15  
**Severity:** 🟠 HIGH - Crashes

```python
def __init__(self, config: LotteryConfig):  # ❌ Doesn't exist
    self.config = config

def predict(self, models: List, features: np.ndarray) -> np.ndarray:
    ...
    max(
        self.config.min_number,  # ❌ Dict access as object
        ...
    )
```

**Fix:** Use dict access:
```python
from typing import Dict, Any

def __init__(self, config: Dict[str, Any]):
    self.config = config

def _generate_unique_prediction(...):
    predicted_num = max(
        self.config['min_number'],  # ✅
        min(self.config['max_number'], round(prediction))
    )
```

---

## High-Priority Logic Bugs

### 6. **`jackpot_optimizer.py` - Randomness without seed in production code**
**File:** `jackpot_optimizer.py`  
**Line:** ~280 (`generate_anti_popular_prediction`)  
**Severity:** 🟠 HIGH - Non-deterministic results

```python
def generate_anti_popular_prediction(self, count: int = 1, seed: Optional[int] = None) -> List[np.ndarray]:
    if seed is not None:
        np.random.seed(seed)  # ❌ Modifies global numpy random state!
    
    for i in range(count):
        selected = np.random.choice(...)  # Non-deterministic if seed=None
```

**Problem:** 
1. Setting global seed is a side effect
2. Without seed, predictions are different each call
3. Breaks reproducibility and testing

**Fix:** Use a local `Generator` instead:
```python
def generate_anti_popular_prediction(self, count: int = 1, seed: Optional[int] = None) -> List[np.ndarray]:
    rng = np.random.default_rng(seed)  # ✅ Local, not global
    
    for i in range(count):
        selected = rng.choice(...)
```

---

### 7. **`prediction_service.py` - Hardcoded column names vs. config**
**File:** `prediction_service.py`  
**Lines:** 79-80, 95  
**Severity:** 🟠 HIGH - Brittle to data changes

```python
def _process_dates(self, df: pd.DataFrame) -> pd.DataFrame:
    df["DRAW_DATE"] = pd.to_datetime(df["DRAW DATE"])  # ❌ Hardcoded strings
    return df.sort_values("DRAW_DATE").reset_index(drop=True)

def _prepare_training_data(self, df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
    feature_cols = [
        c for c in df.columns
        if c.startswith("freq_") or c in ("sum_numbers", "odd_count", "low_count")
    ]
    X = df[feature_cols].values
    y = df[[f"num_{i}" for i in range(1, self.config.numbers_per_draw + 1)]].values  # ❌ Magic formula
```

**Problem:** Column names hardcoded; if data format changes, code breaks silently or crashes.

**Fix:** Use `ColumnNames` constants:
```python
from .constants import ColumnNames

def _process_dates(self, df: pd.DataFrame) -> pd.DataFrame:
    df[ColumnNames.DRAW_DATE_PROCESSED] = pd.to_datetime(df[ColumnNames.DRAW_DATE])  # ✅
    return df.sort_values(ColumnNames.DRAW_DATE_PROCESSED).reset_index(drop=True)
```

---

### 8. **`evaluator.py` - Undefined reference to predictor attributes**
**File:** `evaluator.py`  
**Lines:** 31-35  
**Severity:** 🟠 HIGH - AttributeError at runtime

```python
def backtest_model(self, predictor, data_path: str, test_size: int = 10) -> List[Dict]:
    ...
    X, y = predictor.data_processor.prepare_training_data(train_data)  # ❌ predictor has no data_processor
    
    models = []
    for j in range(6):
        model, scaler = predictor.model_trainer.train(X, y[:, j])  # ❌ No model_trainer attribute
```

**Problem:** The `backtest_model()` method assumes attributes (`data_processor`, `model_trainer`) that don't exist on `PredictionService`.

**Fix:** Either:
1. Remove this method (it's not used anywhere)
2. Refactor to use correct PredictionService API
3. Add type hints and implement properly

---

### 9. **`consolidated_predictor.py` - Type error in risk level retrieval**
**File:** `consolidated_predictor.py`  
**Line:** 134  
**Severity:** 🟠 HIGH - KeyError/AttributeError

```python
def _get_recommendations(self, analysis, optimized) -> Dict[str, Any]:
    ...
    risk = optimized["risk_analysis"]
    ...
    "sharing_risk_level": risk.get("risk_level", RiskLevel.MEDIUM.value),
```

**Problem:** After the jackpot_optimizer update, `risk_level` is added to the dict. But if this code runs with old optimizer code, it crashes. Also `.value` returns string, but `from_score()` is used elsewhere.

**Fix:** Be consistent:
```python
risk_score = risk.get('overall_risk', 20)
risk_level = RiskLevel.from_score(risk_score)
"sharing_risk_level": risk_level.value,  # ✅ Consistent
```

---

### 10. **`models/factory.py` - Missing validation of config parameter**
**File:** `models/factory.py`  
**Lines:** 8-18  
**Severity:** 🟡 MEDIUM - Silent failure with empty config

```python
def create_model(self, model_type: str, config: Dict) -> Any:
    if model_type == 'xgboost':
        return self._create_xgb_model(config)  # ❌ No validation that config exists
    ...

def _create_xgb_model(self, config: Dict) -> XGBRegressor:
    return XGBRegressor(
        n_estimators=config.get('n_estimators', 100),  # Falls back to defaults
        ...
    )
```

**Problem:** If `config` is `{}` or `None`, all parameters use defaults silently. Should warn or raise.

**Fix:** Validate upfront:
```python
def create_model(self, model_type: str, config: Dict) -> Any:
    if not isinstance(config, dict):
        raise ValueError(f"Config must be dict, got {type(config)}")
    
    if model_type == 'xgboost':
        return self._create_xgb_model(config)
    ...
```

---

### 11. **`strategies/prediction.py` - Logic error in TopKPredictionStrategy**
**File:** `strategies/prediction.py`  
**Lines:** 53-58  
**Severity:** 🟡 MEDIUM - Wrong predictions

```python
class TopKPredictionStrategy(PredictionStrategy):
    def predict(self, models: List, features: np.ndarray) -> np.ndarray:
        all_predictions = []
        for model, scaler in models:
            features_scaled = scaler.transform(features)
            pred = model.predict(features_scaled)[0]
            all_predictions.append(pred)
        
        # Select top numbers based on aggregated scores
        scores = np.mean(all_predictions, axis=0) if len(all_predictions) > 1 else all_predictions[0]
        top_indices = np.argsort(scores)[-self.config['numbers_per_draw']:]
        
        return np.sort(top_indices + self.config['min_number'])  # ❌ Wrong math
```

**Problem:** 
- `all_predictions` is a list of scalars (one per model), not 2D
- `np.argsort(scores)` on a 1D scalar array returns index array
- Adding `min_number` to indices is wrong

**Fix:** Clarify the intent:
```python
# If selecting top-K numbers across all predictions:
all_predictions = np.concatenate(all_predictions)  # Flatten
top_indices = np.argsort(all_predictions)[-self.config['numbers_per_draw']:]
selected_numbers = top_indices + self.config['min_number']
```

---

## Medium-Priority Issues

### 12. **`validators.py` - Missing ValidationError initialization parameter**
**File:** `validators.py`  
**Lines:** Various  
**Severity:** 🟡 MEDIUM - Inconsistent error handling

```python
class ValidationError(Exception):
    def __init__(self, message: str, details: Optional[dict] = None):
        ...
```

The class accepts `details` parameter, but most raises only pass message:
```python
raise ValidationError("Message only")  # ✅ Works
raise ValidationError("Message", {"key": "value"})  # ✅ Works
```

All good here, but could standardize usage.

---

### 13. **`data_processor.py` - Validation order issue**
**File:** `data_processor.py`  
**Lines:** ~25-35  
**Severity:** 🟡 MEDIUM - Silent data loss

```python
def load_data(self, file_path: str) -> pd.DataFrame:
    validated_path = DataValidator.validate_file_path(file_path, ...)
    df = pd.read_csv(validated_path)  # ❌ If this fails, no fallback
    DataValidator.validate_dataframe(df, ...)
    self.data = self._preprocess_data(df)
    return self.data
```

**Problem:** If `_preprocess_data()` modifies the dataframe and it fails partway, `self.data` is corrupt.

**Fix:** Only update `self.data` after full success:
```python
def load_data(self, file_path: str) -> pd.DataFrame:
    validated_path = DataValidator.validate_file_path(file_path, ...)
    df = pd.read_csv(validated_path)
    DataValidator.validate_dataframe(df, ...)
    processed = self._preprocess_data(df)  # ✅ Separate variable
    self.data = processed  # Only update on success
    return self.data
```

---

### 14. **`jackpot_optimizer.py` - Biased cached scores**
**File:** `jackpot_optimizer.py`  
**Lines:** 43-46  
**Severity:** 🟡 MEDIUM - Correctness issue

```python
def _get_popularity_scores(self, historical_data: pd.DataFrame = None) -> Dict[int, float]:
    if self._popularity_scores_cache is None:
        self._popularity_scores_cache = self._calculate_popularity_scores(historical_data)
    return self._popularity_scores_cache
```

**Problem:** Cache is never invalidated. If historical data changes, scores stay the same. Also, `historical_data` parameter is ignored after first call.

**Fix:** Either:
1. Always use historical data if provided
2. Document that cache is permanent
3. Add a `clear_cache()` method

```python
def _get_popularity_scores(self, historical_data: pd.DataFrame = None) -> Dict[int, float]:
    if historical_data is not None or self._popularity_scores_cache is None:
        self._popularity_scores_cache = self._calculate_popularity_scores(historical_data)
    return self._popularity_scores_cache
```

---

## Low-Priority Issues

### 15. **`constants.py` - No validation of enum member**
**File:** `constants.py`  
**Lines:** 38-45  
**Severity:** 🟡 LOW - Defensive programming

```python
@classmethod
def get_config(cls, lottery_type: LotteryType) -> Dict[str, Any]:
    """Get configuration for specific lottery type."""
    return cls.CONFIGS[lottery_type]  # ❌ Will KeyError if invalid enum
```

**Fix:** Add error handling:
```python
@classmethod
def get_config(cls, lottery_type: LotteryType) -> Dict[str, Any]:
    if lottery_type not in cls.CONFIGS:
        raise ValueError(f"Unsupported lottery type: {lottery_type}")
    return cls.CONFIGS[lottery_type]
```

---

### 16. **`prediction_service.py` - Magic number 6 in loops**
**File:** `prediction_service.py`  
**Lines:** 58  
**Severity:** 🟡 LOW - Code clarity

```python
for i in range(self.config['numbers_per_draw']):  # ✅ Good
    model = self.model_factory.create_model("ensemble", model_config)
```

This is already fixed in most places, but ensure consistency.

---

## Summary Table

| Issue | File | Severity | Type | Fix Time |
|-------|------|----------|------|----------|
| 1. Dead LotteryConfig import | config_manager.py | 🔴 CRITICAL | Import Error | 5 min |
| 2. Dead LotteryConfig import | prediction_service.py | 🔴 CRITICAL | Import Error | 5 min |
| 3. Dict vs object access | prediction_service.py | 🟠 HIGH | AttributeError | 10 min |
| 4. Invalid LotteryConfig | features/engineers.py | 🟠 HIGH | Type Error | 10 min |
| 5. Invalid LotteryConfig | strategies/prediction.py | 🟠 HIGH | Type Error | 10 min |
| 6. Global random seed | jackpot_optimizer.py | 🟠 HIGH | Behavior | 5 min |
| 7. Hardcoded columns | prediction_service.py | 🟠 HIGH | Logic | 10 min |
| 8. Undefined attributes | evaluator.py | 🟠 HIGH | Logic | 15 min |
| 9. Risk level type mismatch | consolidated_predictor.py | 🟠 HIGH | Type | 5 min |
| 10. Missing config validation | models/factory.py | 🟡 MEDIUM | Logic | 5 min |
| 11. Wrong array math | strategies/prediction.py | 🟡 MEDIUM | Logic | 10 min |
| 12. Data loss risk | data_processor.py | 🟡 MEDIUM | Logic | 5 min |
| 13. Cache invalidation | jackpot_optimizer.py | 🟡 MEDIUM | Logic | 5 min |
| 14. Enum validation | constants.py | 🟡 LOW | Defensive | 5 min |
| 15. Magic numbers | prediction_service.py | 🟡 LOW | Clarity | 2 min |

**Total estimated fix time: ~110 minutes**

## Recommended Fix Order

1. **First (Blocking):** Issues 1, 2, 3, 4, 5 — prevent import/runtime crashes
2. **Then (High impact):** Issues 6, 7, 8, 9 — correctness & logic
3. **Then (Robustness):** Issues 10, 12, 13, 14 — defensive programming
4. **Finally (Polish):** Issues 11, 15 — code quality

