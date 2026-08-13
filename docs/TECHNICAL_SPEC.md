# Technical Specification — Lottery Prediction System

**Version:** 1.0.0  
**Python:** 3.12+  
**Status:** Production-ready (educational)

---

## 1. System Overview

The system is a supervised machine learning pipeline that trains an ensemble of per-position regressors on historical lottery draw data and generates predictions for the next draw. A game-theoretic optimizer post-processes predictions to minimize expected jackpot sharing.

### Scope

- Input: CSV of historical lottery draws
- Output: Sorted integer arrays of predicted lottery numbers
- Supported lottery: Ultra Lotto 6/58 (configurable)
- Interface: CLI (`cli.py`) and Python API

---

## 2. Architecture

### 2.1 Layered Design

```
┌─────────────────────────────────────────────┐
│  CLI / Python API                           │  Entry layer
├─────────────────────────────────────────────┤
│  ConsolidatedPredictor                      │  High-level facade
│  PredictionOrchestrator                     │  Coordination
│  PredictionAnalyzer  │  ReportFormatter     │  Analysis / Presentation
├─────────────────────────────────────────────┤
│  PredictionService                          │  Core domain logic
├──────────────┬──────────────────────────────┤
│  Data layer  │  Model layer  │  Optimizer   │  Infrastructure
└──────────────┴──────────────────────────────┘
```

### 2.2 Dependency Graph

```
PredictionSystemFactory
  └─ PredictionService
       ├─ CSVDataLoader           implements DataLoader (ABC)
       ├─ LotteryDataValidator    implements DataValidator (ABC)
       ├─ LotteryFeatureEngineer  implements FeatureEngineer (ABC)
       ├─ SklearnModelFactory     implements ModelFactory (ABC)
       │    └─ VotingRegressor
       │         ├─ XGBRegressor
       │         ├─ RandomForestRegressor
       │         └─ GradientBoostingRegressor
       ├─ UniqueLotteryPredictionStrategy  implements PredictionStrategy (ABC)
       └─ JackpotSharingOptimizer
```

### 2.3 Design Patterns

| Pattern | Implementation |
|---|---|
| Dependency Injection | `PredictionService.__init__` accepts all dependencies as parameters |
| Abstract Factory | `ModelFactory` ABC → `SklearnModelFactory` |
| Factory Method | `PredictionSystemFactory.create_lottery_predictor()` |
| Strategy | `PredictionStrategy` ABC → `UniqueLotteryPredictionStrategy`, `TopKPredictionStrategy` |
| Facade | `ConsolidatedPredictor` wraps the full stack behind a simple interface |

---

## 3. Module Specifications

### 3.1 `interfaces.py`

Defines all abstract base classes. No concrete logic.

| Class | Abstract Methods | Purpose |
|---|---|---|
| `DataLoader` | `load(source) → DataFrame` | Data ingestion contract |
| `DataValidator` | `validate(data) → bool` | Data quality contract |
| `FeatureEngineer` | `create_features(data) → DataFrame` | Feature creation contract |
| `ModelFactory` | `create_model(type, config) → Any` | Model instantiation contract |
| `PredictionStrategy` | `predict(models, features) → ndarray` | Prediction algorithm contract |
| `LotteryConfig` | — (dataclass) | `min_number`, `max_number`, `numbers_per_draw`, `number_range` |

---

### 3.2 `prediction_service.py` — `PredictionService`

Core domain class. All state is explicit; no hidden state after training.

**Constructor parameters:**

| Parameter | Type | Description |
|---|---|---|
| `data_loader` | `DataLoader` | Loads raw CSV data |
| `data_validator` | `DataValidator` | Validates required columns |
| `feature_engineer` | `FeatureEngineer` | Creates frequency/pattern features |
| `model_factory` | `ModelFactory` | Instantiates ensemble models |
| `prediction_strategy` | `PredictionStrategy` | Generates unique number predictions |
| `config` | `LotteryConfig` | Lottery parameters |
| `optimizer` | `JackpotSharingOptimizer` (optional) | Sharing risk optimizer |

**Public methods:**

| Method | Signature | Description |
|---|---|---|
| `train` | `(data_source: str, model_config: Dict) → None` | Loads data, engineers features, fits 6 models |
| `prepare_features` | `(data_source: str) → ndarray` | Returns feature vector for latest draw |
| `predict` | `(features: ndarray) → ndarray` | Standard prediction via strategy |
| `predict_optimized` | `(features: ndarray) → ndarray` | Lowest sharing-risk prediction |
| `predict_anti_popular` | `(features: ndarray, count: int) → List[ndarray]` | Anti-popular prediction sets |
| `save` | `(directory: str) → None` | Persists models to disk |
| `load` | `(directory: str) → None` | Restores models from disk |

**Training internals:**
- One `VotingRegressor` + `StandardScaler` pair trained per lottery position (6 total)
- One-step-ahead formulation: features from draw N → target numbers from draw N+1
- `X[:-1], y[1:]` split ensures no data leakage

---

### 3.3 `system_factory.py` — `PredictionSystemFactory`

Single static factory method. Reads config, constructs all components, injects into `PredictionService`.

```
create_lottery_predictor(config_path, lottery_type=DEFAULT_LOTTERY)
  → ConfigManager(config_path)
  → LotteryConfig, required_columns
  → CSVDataLoader()
  → LotteryDataValidator(required_columns)
  → LotteryFeatureEngineer(lottery_config)
  → SklearnModelFactory()
  → UniqueLotteryPredictionStrategy(lottery_config)
  → JackpotSharingOptimizer(lottery_type)
  → PredictionService(all above)
```

---

### 3.4 `features/engineers.py` — `LotteryFeatureEngineer`

Transforms raw DataFrame into ML-ready feature matrix. All mutations use `df.assign()` (pandas 3.0 safe).

**Feature groups:**

| Group | Columns | Description |
|---|---|---|
| Number extraction | `num_1` … `num_6` | Parsed from `COMBINATIONS` string `"12-23-34-45-56-07"` |
| Frequency | `freq_1` … `freq_58` | Binary: did number N appear in this draw |
| Pattern | `sum_numbers` | Sum of all 6 drawn numbers |
| Pattern | `odd_count` | Count of odd numbers |
| Pattern | `low_count` | Count of numbers ≤ 29 |

**Total features per row:** 6 (num) + 58 (freq) + 3 (pattern) = **67 features**

---

### 3.5 `models/factory.py` — `SklearnModelFactory`

Creates sklearn-compatible models from config dict.

| Model type key | Class | Default params |
|---|---|---|
| `xgboost` | `XGBRegressor` | `n_estimators=100, lr=0.1, max_depth=6, tree_method='hist'` |
| `random_forest` | `RandomForestRegressor` | `n_estimators=100, max_depth=10` |
| `gradient_boosting` | `GradientBoostingRegressor` | `n_estimators=100, lr=0.1, max_depth=6` |
| `ensemble` | `VotingRegressor` | All three above, `n_jobs=-1` |

All models use `random_state=42` for reproducibility.

---

### 3.6 `strategies/prediction.py`

**`UniqueLotteryPredictionStrategy`** (default):
- Runs each of the 6 per-position models
- Clamps prediction to `[min_number, max_number]`
- If predicted number already used, searches outward `±offset` until an unused number is found
- Returns `np.sort(predictions)`

**`TopKPredictionStrategy`**:
- Aggregates all model predictions via mean
- Selects top-K indices by score
- Returns `np.sort(top_indices + min_number)`

---

### 3.7 `jackpot_optimizer.py` — `JackpotSharingOptimizer`

Scores prediction sets by expected jackpot sharing risk using human bias modelling.

**Popularity score formula (per number):**

```
base_score = 1.0
× 3.5  if num in birthdays (1–31)
× 2.8  if num in lucky_numbers (7, 11, 13, 21, 23)
× 2.2  if num in visual_patterns
× 1.8  if num in multiples (5, 10, 15, ...)
× 1.5  if num in sequences
× 1.3  if 20 ≤ num ≤ 40
× 0.7  if num ≤ 5 or num ≥ 55
```

**Combination penalties (additive):**

```
+2.0 per consecutive pair
+3.0 if full arithmetic sequence
+2.5 if all-odd or all-even
+1.5 per birthday number if ≥ 4 birthday numbers
+1.2 per multiple-of-5 if ≥ 3 multiples
```

**`sharing_risk = sum(popularity_scores) + combination_penalties`**

**Public methods:**

| Method | Returns | Description |
|---|---|---|
| `optimize_selection(candidates, data)` | `ndarray` | Lowest-risk candidate, fine-tuned |
| `generate_anti_popular_prediction(count)` | `List[ndarray]` | Sets maximally avoiding popular clusters |
| `analyze_sharing_risk(prediction)` | `Dict` | Risk breakdown including `overall_risk` float |
| `compare_strategies(candidates)` | `DataFrame` | Risk scores for all candidates |

---

### 3.8 Reporting Layer

**`PredictionOrchestrator`**
- Wraps `PredictionService`, calls `train()` and `prepare_features()`
- `get_predictions()` returns: `standard`, `optimized`, `anti_popular` (×3), `multiple_sets` (×5), `risk_analysis`

**`PredictionAnalyzer`**
- Stateless. Takes prediction dict, returns frequency map and confidence tiers:
  - High confidence: number appeared in ≥ 40% of prediction sets
  - Medium: 20–40%
  - Low: < 20%

**`ReportFormatter`**
- Composes orchestrator + analyzer output into a formatted string report
- Merges high-confidence numbers into the optimized recommendation

**`ConsolidatedPredictor`**
- High-level facade over `PredictionService` via factory
- `get_all_predictions()` → `{basic, advanced, optimized, analysis, recommendations}`
- `get_quick_prediction()` → single optimized `ndarray`
- `get_summary_report()` → formatted string

---

### 3.9 `validators.py`

Three validator classes, all static methods:

**`DataValidator`**

| Method | Validates |
|---|---|
| `validate_file_path(path, extensions)` | File exists, extension allowed |
| `validate_dataframe(df, required_cols, lottery_type)` | Columns present, min rows, no all-NaN |
| `validate_features(features)` | Not None, no NaN, no infinite |
| `validate_lottery_numbers(numbers, lottery_type)` | Count, range, uniqueness |

**`ConfigValidator`**

| Method | Validates |
|---|---|
| `validate_config_file(path)` | File exists, valid YAML, required sections |
| `validate_lottery_config(config)` | min/max/numbers_per_draw present and sane |
| `validate_model_config(config)` | n_estimators > 0, 0 < lr ≤ 1, max_depth > 0 |

**`ModelValidator`**

| Method | Validates |
|---|---|
| `validate_training_data(X, y)` | Shapes match, minimum 50 samples |
| `validate_predictions(predictions, lottery_type)` | Count, range, uniqueness |

---

### 3.10 `exceptions.py`

All exceptions inherit from `LotteryPredictionError(Exception)`. Each logs automatically on construction.

```
LotteryPredictionError
├── DataProcessingError
├── ModelTrainingError
├── PredictionError
├── ValidationError
└── ConfigurationError
```

Each carries `.message: str` and `.details: dict`.

---

## 4. Data Specification

### 4.1 Input CSV Schema

| Column | Type | Example | Required |
|---|---|---|---|
| `LOTTO GAME` | string | `Ultra Lotto 6/58` | Yes |
| `COMBINATIONS` | string | `12-23-34-45-56-07` | Yes |
| `DRAW DATE` | string (parseable by pandas) | `3/28/2026` | Yes |
| `JACKPOT (PHP)` | numeric | `50000000` | No |
| `WINNERS` | numeric | `0` | No |

Minimum rows required: **50** (enforced by `ModelValidator`)

### 4.2 Feature Matrix Shape

For a dataset of N draws:
- `X`: shape `(N-1, 61)` — 58 freq features + 3 pattern features
- `y`: shape `(N-1, 6)` — 6 target positions

### 4.3 Model Artifacts

Saved per lottery position `i` (0-indexed):

| File | Format | Contents |
|---|---|---|
| `model_i.json` | XGBoost JSON | Booster weights for position i |
| `scaler_i.joblib` | joblib | Fitted `StandardScaler` for position i |

---

## 5. Configuration Specification

`config/model_config.yaml` — full schema:

```yaml
lottery:
  min_number: int       # lower bound (inclusive), default 1
  max_number: int       # upper bound (inclusive), default 58
  numbers_per_draw: int # count of numbers per draw, default 6

data:
  validation:
    required_columns: List[str]   # columns that must exist in input CSV

models:
  xgboost:
    n_estimators: int             # number of boosting rounds
    learning_rate: float          # shrinkage (0, 1]
    max_depth: int                # tree depth
    early_stopping_rounds: int    # optional
  random_forest:
    n_estimators: int
    max_depth: int
  gradient_boosting:
    n_estimators: int
    learning_rate: float
    max_depth: int

prediction:
  strategy: "unique" | "top_k"
  confidence_threshold: float     # currently informational only
```

---

## 6. CLI Specification

Entry point: `cli.py`

```
python cli.py <command> [--config PATH] [--data PATH]
```

| Command | Action | Output |
|---|---|---|
| `predict` | Train + predict | Standard and optimized number sets |
| `optimize` | Train + optimize | Jackpot-optimized set + 3 anti-popular sets |
| `report` | Train + full report | Formatted summary via `ReportFormatter` |
| `evaluate` | Backtest | Metrics via `ModelEvaluator` |

All commands share `--config` (default: `config/model_config.yaml`) and `--data` (default: `data/lottery_history.csv`).

---

## 7. Dependency Versions

| Package | Pinned range in requirements.txt | Actual tested version |
|---|---|---|
| `numpy` | `>=1.21.0,<2.0.0` | 2.4.3 (venv rebuilt) |
| `pandas` | `>=1.3.0,<3.0.0` | 3.0.x |
| `scikit-learn` | `>=0.24.2,<2.0.0` | 1.8.0 |
| `xgboost` | `>=1.5.0,<3.0.0` | 3.2.0 |
| `pyyaml` | `>=5.4.1,<7.0.0` | — |
| `joblib` | transitive via sklearn | — |

> Note: `requirements.txt` upper bounds are stale — actual installed versions exceed them. The bounds should be updated to reflect tested versions.

---

## 8. Known Constraints and Limitations

| Constraint | Detail |
|---|---|
| Lottery randomness | Lottery draws are statistically independent. No ML model can predict them. This system is educational. |
| Feature stationarity | Frequency features assume historical patterns are informative — this is not statistically valid for true random draws. |
| One-step-ahead only | The model predicts one draw ahead. Multi-step prediction is not implemented. |
| No online learning | Models must be fully retrained on new data; there is no incremental update path. |
| `requirements.txt` version bounds | Upper bounds are outdated; actual installed versions exceed them without issue, but the file should be updated. |
| `setup.py` entry points | References deleted scripts (`run_prediction:main`, `evaluate_model:main`). Should be updated to `cli:main`. |
| `ModelEvaluator.backtest_model` | Still references `predictor.data_processor` — couples evaluator to the legacy `DataProcessor` stack. |

---

## 9. Testing

### 9.1 Test Files

| File | Class | Tests |
|---|---|---|
| `tests/test_predictor.py` | `TestDataProcessor` | Validator success/failure |
| | `TestModelTrainer` | Model creation, ensemble creation |
| | `TestPredictionService` | Factory init, end-to-end predict, untrained guard |
| `tests/test_validation.py` | `TestDataValidator` | File path, dataframe, features, lottery numbers |
| | `TestConfigValidator` | Config file, lottery config, model config |
| | `TestModelValidator` | Predictions, training data |
| | `TestSystemValidation` | System requirements, prediction input |

### 9.2 Running Tests

```bash
python -m pytest tests/ -v              # all tests
python -m pytest tests/ --cov=src       # with coverage
```

Current status: **31 tests, 31 passing**

---

## 10. Docker

### 10.1 Dockerfile

Two-stage build:

| Stage | Base image | Purpose |
|---|---|---|
| `builder` | `python:3.12-slim` | Install deps into `/opt/venv` |
| runtime | `python:3.12-slim` | Copy venv + app code, run as `appuser` (uid 1000) |

Default command: `python cli.py predict`

### 10.2 docker-compose.yml

| Service | Purpose | Command |
|---|---|---|
| `lottery-predictor` | Production prediction run | `python cli.py predict` (default CMD) |
| `lottery-predictor-dev` | CI / test run | `pip install -r requirements-dev.txt && pytest tests/ -v --cov=src --cov-report=html` |

Both services mount `src/`, `config/`, `data/`, `models/`, `cli.py`, `outputs/` as volumes.

---

## 11. Outstanding Technical Debt

| Item | Priority | Description |
|---|---|---|
| `requirements.txt` version bounds | Low | Upper bounds are stale; update to match tested versions |
| `setup.py` entry points | Low | References deleted scripts; update to `cli:main` |
| `ModelEvaluator` coupling | Medium | `backtest_model()` uses `predictor.data_processor` — should be refactored to use `PredictionService` |
| `ConsolidatedPredictor` redundancy | Low | Overlaps significantly with `PredictionOrchestrator`; consider consolidating |
| No integration tests | Medium | Only unit tests exist; no end-to-end test covering train → predict → save → load |
| `TopKPredictionStrategy` untested | Low | Implemented but not covered by any test |
