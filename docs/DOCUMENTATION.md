# Lottery Prediction System

> An educational machine learning system for analyzing and predicting lottery numbers using an ensemble of gradient boosting models with game-theoretic jackpot sharing optimization.

---

## Table of Contents

1. [Overview](#overview)
2. [Project Structure](#project-structure)
3. [Architecture](#architecture)
4. [Installation](#installation)
5. [Quick Start](#quick-start)
6. [CLI Reference](#cli-reference)
7. [Python API](#python-api)
8. [Configuration](#configuration)
9. [Feature Engineering](#feature-engineering)
10. [Jackpot Sharing Optimization](#jackpot-sharing-optimization)
11. [Model Persistence](#model-persistence)
12. [Testing](#testing)
13. [Docker](#docker)
14. [Error Handling](#error-handling)
15. [Extending the System](#extending-the-system)
16. [Disclaimer](#disclaimer)

---

## Overview

The system trains an ensemble of three regressors (XGBoost, Random Forest, Gradient Boosting) — one per lottery position — on historical draw data. It then generates predictions for the next draw using frequency-based feature engineering and optionally applies a game-theoretic optimizer to minimize expected jackpot sharing.

**Key capabilities:**
- 1,365+ historical draws ingested from CSV
- Per-position ensemble regression (6 models for 6/58 lottery)
- Frequency, pattern, and hot/cold feature engineering
- Jackpot sharing risk scoring based on human bias patterns
- Anti-popular number set generation
- Model persistence (XGBoost → `.json`, sklearn → `.joblib`)
- Single CLI entry point with four subcommands
- Docker support for both production and dev/test workflows

---

## Project Structure

```
658/
├── src/
│   └── predictor/
│       ├── __init__.py                  # Public exports
│       ├── interfaces.py                # Abstract base classes
│       ├── constants.py                 # LotteryType, FilePaths, ColumnNames, ModelDefaults
│       ├── exceptions.py                # Custom exception hierarchy
│       ├── config_manager.py            # YAML config loader → LotteryConfig
│       ├── prediction_service.py        # PredictionService — core DI predictor
│       ├── prediction_orchestrator.py   # Coordinates PredictionService calls
│       ├── prediction_analyzer.py       # Pure stateless frequency/confidence analysis
│       ├── report_formatter.py          # Human-readable report generation
│       ├── system_factory.py            # PredictionSystemFactory — wires all components
│       ├── consolidated_predictor.py    # High-level unified interface
│       ├── jackpot_optimizer.py         # JackpotSharingOptimizer
│       ├── validators.py                # DataValidator, ConfigValidator, ModelValidator
│       ├── model_trainer.py             # ModelTrainer (used by evaluator)
│       ├── data_processor.py            # DataProcessor (used by evaluator)
│       ├── evaluator.py                 # ModelEvaluator — backtesting and metrics
│       ├── data/
│       │   ├── loaders.py               # CSVDataLoader, DatabaseDataLoader
│       │   └── validators.py            # LotteryDataValidator
│       ├── features/
│       │   └── engineers.py             # LotteryFeatureEngineer
│       ├── models/
│       │   └── factory.py               # SklearnModelFactory
│       └── strategies/
│           └── prediction.py            # UniqueLotteryPredictionStrategy, TopKPredictionStrategy
│
├── tests/
│   ├── __init__.py
│   ├── test_predictor.py                # PredictionService, validator, trainer tests
│   └── test_validation.py               # Comprehensive validator unit tests
│
├── config/
│   └── model_config.yaml                # Hyperparameters and validation config
│
├── data/
│   ├── lottery_history.csv              # Historical draw data (1,365+ draws)
│   └── raw/                             # Raw source data
│
├── models/                              # Saved model artifacts
├── outputs/                             # Generated predictions, reports, plots
│
├── cli.py                               # Single CLI entry point
├── Dockerfile                           # Python 3.12-slim, multi-stage build
├── docker-compose.yml                   # predictor + dev services
├── Makefile                             # Development task runner
├── setup.py                             # Package setup
├── requirements.txt                     # Production dependencies
├── requirements-dev.txt                 # Dev dependencies
└── docs/
    └── DOCUMENTATION.md                 # This file
```

---

## Architecture

The system is built around a clean dependency-injection architecture. All components are defined as abstract interfaces and injected — nothing is instantiated internally.

### Component Diagram

```
PredictionSystemFactory.create_lottery_predictor(config_path)
  │
  └── PredictionService
        ├── CSVDataLoader           (DataLoader ABC)
        ├── LotteryDataValidator    (DataValidator ABC)
        ├── LotteryFeatureEngineer  (FeatureEngineer ABC)
        ├── SklearnModelFactory     (ModelFactory ABC)
        │     └── VotingRegressor(XGBRegressor, RandomForestRegressor, GradientBoostingRegressor)
        ├── UniqueLotteryPredictionStrategy  (PredictionStrategy ABC)
        └── JackpotSharingOptimizer
```

### Reporting Layer

```
PredictionOrchestrator   ← trains PredictionService, collects raw prediction sets
PredictionAnalyzer       ← pure frequency/confidence analysis (no I/O)
ReportFormatter          ← composes orchestrator + analyzer into human-readable output
```

### Design Patterns

| Pattern | Where Used |
|---|---|
| Dependency Injection | `PredictionService.__init__` — all deps injected |
| Factory | `PredictionSystemFactory`, `SklearnModelFactory` |
| Strategy | `PredictionStrategy` ABC — `UniqueLotteryPredictionStrategy`, `TopKPredictionStrategy` |
| Abstract Factory | `ModelFactory` ABC |

### Data Flow

```
CSV file
  → CSVDataLoader.load()
  → LotteryDataValidator.validate()
  → LotteryFeatureEngineer.create_features()
      → _extract_numbers()              # parse COMBINATIONS → num_1..num_6
      → _create_frequency_features()   # freq_1..freq_58 rolling counts
      → _create_pattern_features()     # sum_numbers, odd_count, low_count
  → PredictionService._prepare_training_data()
      → X[:-1], y[1:]                  # draw N features → predict draw N+1
  → VotingRegressor.fit() × 6          # one model per lottery position
  → PredictionService.prepare_features()   # latest draw features
  → UniqueLotteryPredictionStrategy.predict()
  → (optional) JackpotSharingOptimizer.optimize_selection()
```

---

## Installation

**Requirements:** Python 3.12+

```bash
python3.12 -m venv venv
source venv/bin/activate

pip install -r requirements.txt

# For development
pip install -r requirements-dev.txt
pip install -e .
```

**Production dependencies:**
- `xgboost` — gradient boosting regressor
- `scikit-learn` — Random Forest, Gradient Boosting, VotingRegressor, StandardScaler
- `pandas` — data loading and feature engineering
- `numpy` — numerical operations
- `pyyaml` — config file parsing
- `joblib` — model serialization

---

## Quick Start

```bash
python cli.py predict    # standard + optimized predictions
python cli.py optimize   # jackpot-sharing optimized + anti-popular sets
python cli.py report     # full summary report
python cli.py evaluate   # model performance evaluation
```

All commands accept optional `--config` and `--data` flags:

```bash
python cli.py predict --config config/model_config.yaml --data data/lottery_history.csv
```

---

## CLI Reference

| Command | Description |
|---|---|
| `predict` | Trains models, prints standard + optimized predictions |
| `optimize` | Prints jackpot-optimized prediction and 3 anti-popular sets |
| `report` | Full summary report with confidence scores and risk analysis |
| `evaluate` | Backtests model on last 20 draws, prints metrics |

**Flags (all commands):**

| Flag | Default | Description |
|---|---|---|
| `--config` | `config/model_config.yaml` | Path to YAML config file |
| `--data` | `data/lottery_history.csv` | Path to historical data CSV |

---

## Python API

### Basic Usage

```python
from src.predictor import PredictionSystemFactory

service = PredictionSystemFactory.create_lottery_predictor('config/model_config.yaml')
service.train('data/lottery_history.csv', model_config={})

features = service.prepare_features('data/lottery_history.csv')

print(sorted(service.predict(features)))            # standard
print(sorted(service.predict_optimized(features)))  # jackpot-sharing optimized
```

### Anti-Popular Sets

```python
sets = service.predict_anti_popular(features, count=3)
for i, pred in enumerate(sets, 1):
    print(f"Set {i}: {sorted(pred)}")
```

### Full Report

```python
from src.predictor import PredictionOrchestrator, PredictionAnalyzer, ReportFormatter

orch = PredictionOrchestrator(service)
orch.train('data/lottery_history.csv')
print(ReportFormatter(orch, PredictionAnalyzer()).summary())
```

### High-Level Interface

```python
from src.predictor import ConsolidatedPredictor

predictor = ConsolidatedPredictor('config/model_config.yaml')
predictor.train()

results = predictor.get_all_predictions()
# keys: basic, advanced, optimized, analysis, recommendations

print(sorted(predictor.get_quick_prediction()))
print(predictor.get_summary_report())
```

### Model Persistence

```python
service.save('models/run_2026_03_28')   # XGBoost → .json, sklearn → .joblib
service.load('models/run_2026_03_28')   # restore without retraining

features = service.prepare_features('data/lottery_history.csv')
print(sorted(service.predict(features)))
```

---

## Configuration

`config/model_config.yaml`:

```yaml
lottery:
  min_number: 1
  max_number: 58
  numbers_per_draw: 6

data:
  validation:
    required_columns:
      - LOTTO GAME
      - COMBINATIONS
      - DRAW DATE

models:
  xgboost:
    n_estimators: 100
    learning_rate: 0.1
    max_depth: 6
    early_stopping_rounds: 10
  random_forest:
    n_estimators: 100
    max_depth: 10
  gradient_boosting:
    n_estimators: 100
    learning_rate: 0.1
    max_depth: 6

prediction:
  strategy: "unique"        # "unique" or "top_k"
  confidence_threshold: 0.7
```

To support a different lottery, update the `lottery` section — feature engineering, model count, and validation adjust automatically:

```yaml
lottery:
  min_number: 1
  max_number: 69
  numbers_per_draw: 5   # e.g. Powerball
```

---

## Feature Engineering

`LotteryFeatureEngineer` creates three groups of features from the raw `COMBINATIONS` column.

### 1. Number Extraction
Parses `"12-23-34-45-56-07"` → `num_1=12, num_2=23, ..., num_6=7`

### 2. Frequency Features (`freq_1` … `freq_58`)
For each number 1–58, a binary indicator of whether it appeared in that draw. These capture which numbers are "hot" or "cold" at any point in the sequence.

### 3. Pattern Features

| Feature | Description |
|---|---|
| `sum_numbers` | Sum of all drawn numbers |
| `odd_count` | Count of odd numbers in the draw |
| `low_count` | Count of numbers ≤ 29 (lower half of range) |

### Training Setup

One-step-ahead formulation:
- **Input X**: features from draw N
- **Target y**: numbers drawn at draw N+1

Six separate `VotingRegressor` models are trained — one per lottery position.

---

## Jackpot Sharing Optimization

`JackpotSharingOptimizer` scores each candidate set based on how likely other players are to pick the same numbers, using documented human biases.

### Number-Level Bias Multipliers

| Pattern | Multiplier |
|---|---|
| Birthday numbers (1–31) | 3.5× |
| Lucky numbers (7, 11, 13, 21, 23) | 2.8× |
| Visual ticket patterns | 2.2× |
| Multiples of 5 or 10 | 1.8× |
| Consecutive sequences | 1.5× |
| Middle range (20–40) | 1.3× |
| Edge numbers (≤5 or ≥55) | 0.7× |

### Combination-Level Penalties

| Pattern | Penalty |
|---|---|
| Consecutive number pairs | +2.0 per pair |
| Full arithmetic sequence | +3.0 |
| All-odd or all-even | +2.5 |
| 4+ birthday numbers | +1.5 per birthday number |
| 3+ multiples of 5 | +1.2 per multiple |

### Key Methods

```python
optimizer.optimize_selection(candidates, historical_data)  # → lowest-risk candidate
optimizer.generate_anti_popular_prediction(count)          # → List[np.ndarray]
optimizer.analyze_sharing_risk(prediction)                 # → Dict with 'overall_risk'
optimizer.compare_strategies(candidates)                   # → pd.DataFrame
```

---

## Model Persistence

| Model | Format | Reason |
|---|---|---|
| `XGBRegressor` | `.json` | Stable across XGBoost versions |
| sklearn models | `.joblib` | Standard sklearn persistence |
| `StandardScaler` | `.joblib` | Paired with each model |

Avoid pickle for long-term storage — not stable across Python or library version changes.

Files saved per position `i`: `model_i.json`, `scaler_i.joblib`

---

## Testing

```bash
make test              # run all tests
make test-coverage     # run with HTML coverage report

python -m pytest tests/test_predictor.py -v   # specific file
```

| Test file | Coverage |
|---|---|
| `test_predictor.py` | `LotteryDataValidator`, `ModelTrainer` ensemble, `PredictionService` (init, train, predict, untrained guard) |
| `test_validation.py` | `DataValidator` (empty, missing cols, NaN, infinite), `ConfigValidator` (file, lottery, model params), `ModelValidator` (predictions, training data), system validation |

---

## Docker

```bash
# Production — runs python cli.py predict
docker compose up lottery-predictor

# Dev/test — installs dev deps and runs pytest with coverage
docker compose up lottery-predictor-dev

# Build and run manually
docker build -t lottery-predictor:latest .
docker run --rm lottery-predictor:latest python cli.py report
```

The Dockerfile uses a two-stage build:
1. **Builder** (`python:3.12-slim`) — installs all deps into `/opt/venv`
2. **Runtime** (`python:3.12-slim`) — copies only the venv and app code; runs as non-root `appuser`

---

## Error Handling

All exceptions inherit from `LotteryPredictionError` and are automatically logged.

| Exception | Raised when |
|---|---|
| `DataProcessingError` | CSV loading or preprocessing fails |
| `ModelTrainingError` | Model fitting fails |
| `PredictionError` | Prediction generation fails |
| `ValidationError` | Data or config validation fails |
| `ConfigurationError` | YAML config is missing or malformed |

```python
from src.predictor.exceptions import LotteryPredictionError

try:
    service.train('data/lottery_history.csv', model_config={})
except LotteryPredictionError as e:
    print(e.message)
    print(e.details)
```

---

## Extending the System

### New lottery type

Add to `LotteryConstants.CONFIGS` in `constants.py` and the `LotteryType` enum:

```python
LotteryType.MY_LOTTERY: {
    "min_number": 1, "max_number": 45, "numbers_per_draw": 6, "name": "My Lottery"
}
```

### New prediction strategy

Subclass `PredictionStrategy` and inject via factory:

```python
class MyStrategy(PredictionStrategy):
    def predict(self, models, features):
        ...
```

### New model type

Add a method to `SklearnModelFactory`, include it in `_create_ensemble()`, and add its config to `model_config.yaml`.

### New data source

Subclass `DataLoader` and inject via `PredictionSystemFactory`:

```python
class MyDataLoader(DataLoader):
    def load(self, source: str) -> pd.DataFrame:
        ...
```

---

## Disclaimer

For educational and research purposes only. Lottery draws are random by design — no statistical model or machine learning system can predict random outcomes or guarantee winning numbers.
