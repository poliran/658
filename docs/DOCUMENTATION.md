# Lottery Prediction System — Documentation

> Educational ML system for analyzing and predicting lottery numbers using ensemble models.

---

## Project Structure

```
├── src/predictor/              # Core prediction package
│   ├── interfaces.py           # Abstract base classes (DataLoader, DataValidator, etc.)
│   ├── prediction_service.py   # PredictionService — main DI-based predictor
│   ├── prediction_orchestrator.py  # Coordinates PredictionService calls
│   ├── prediction_analyzer.py  # Pure stateless frequency/confidence analysis
│   ├── report_formatter.py     # Human-readable report generation
│   ├── system_factory.py       # PredictionSystemFactory — wires all components
│   ├── consolidated_predictor.py   # High-level unified interface
│   ├── jackpot_optimizer.py    # Game-theoretic jackpot sharing optimizer
│   ├── config_manager.py       # YAML config loader
│   ├── constants.py            # LotteryType, LotteryConstants, FilePaths, ColumnNames
│   ├── exceptions.py           # Custom exception hierarchy
│   ├── validators.py           # Data, config, model validators
│   ├── model_trainer.py        # ModelTrainer (legacy stack, used by evaluator)
│   ├── data_processor.py       # DataProcessor (legacy stack, used by evaluator)
│   ├── evaluator.py            # ModelEvaluator — backtesting and metrics
│   ├── data/
│   │   ├── loaders.py          # CSVDataLoader
│   │   └── validators.py       # LotteryDataValidator
│   ├── features/
│   │   └── engineers.py        # LotteryFeatureEngineer
│   ├── models/
│   │   └── factory.py          # SklearnModelFactory (XGBoost, RF, GB ensemble)
│   └── strategies/
│       └── prediction.py       # UniqueLotteryPredictionStrategy, TopKPredictionStrategy
├── tests/
│   ├── test_predictor.py       # PredictionService, DataValidator, ModelTrainer tests
│   └── test_validation.py      # Validator unit tests
├── config/
│   └── model_config.yaml       # Model hyperparameters and data validation config
├── data/
│   └── lottery_history.csv     # Historical draw data (1,365+ draws)
├── models/                     # Saved model artifacts
├── outputs/                    # Generated predictions and reports
├── archive/                    # Retired code (lottery_predictor.py, experimental/)
├── cli.py                      # Single CLI entry point
├── Dockerfile                  # Python 3.12-slim, multi-stage build
├── docker-compose.yml          # predictor + dev services
├── Makefile                    # test, lint, format, clean targets
├── requirements.txt            # Production dependencies
└── requirements-dev.txt        # Dev dependencies (pytest, coverage, etc.)
```

---

## Architecture

The system uses a clean dependency-injection architecture built around these layers:

```
PredictionSystemFactory
  └── PredictionService          ← main entry point for predictions
        ├── CSVDataLoader
        ├── LotteryDataValidator
        ├── LotteryFeatureEngineer
        ├── SklearnModelFactory  ← XGBoost + RandomForest + GradientBoosting ensemble
        ├── UniqueLotteryPredictionStrategy
        └── JackpotSharingOptimizer

PredictionOrchestrator           ← coordinates PredictionService, returns raw sets
PredictionAnalyzer               ← pure frequency/confidence analysis
ReportFormatter                  ← formats orchestrator + analyzer output
```

**Design patterns applied:**
- Strategy — `PredictionStrategy` ABC with swappable implementations
- Factory — `SklearnModelFactory`, `PredictionSystemFactory`
- Dependency Injection — all `PredictionService` dependencies injected, not created internally

---

## Quick Start

```bash
pip install -r requirements.txt

python cli.py predict    # Standard + optimized predictions
python cli.py optimize   # Jackpot-sharing optimized + anti-popular sets
python cli.py report     # Full summary report
python cli.py evaluate   # Model performance evaluation
```

---

## Usage

### Python API

```python
from src.predictor import PredictionSystemFactory

service = PredictionSystemFactory.create_lottery_predictor('config/model_config.yaml')
service.train('data/lottery_history.csv', model_config={})

features = service.prepare_features('data/lottery_history.csv')
print(sorted(service.predict(features)))
print(sorted(service.predict_optimized(features)))

# Anti-popular sets (minimize jackpot sharing)
for i, pred in enumerate(service.predict_anti_popular(features, count=3), 1):
    print(f"Set {i}: {sorted(pred)}")
```

### Model Persistence

```python
service.save('models/my_run')   # XGBoost → .json, sklearn → .joblib
service.load('models/my_run')
```

### Full Report

```python
from src.predictor import PredictionOrchestrator, PredictionAnalyzer, ReportFormatter

orch = PredictionOrchestrator(service)
orch.train('data/lottery_history.csv')
print(ReportFormatter(orch, PredictionAnalyzer()).summary())
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
    required_columns: [LOTTO GAME, COMBINATIONS, DRAW DATE]

models:
  xgboost:
    n_estimators: 100
    learning_rate: 0.1
    max_depth: 6
  random_forest:
    n_estimators: 100
    max_depth: 10
  gradient_boosting:
    n_estimators: 100
    learning_rate: 0.1
    max_depth: 6
```

---

## Jackpot Sharing Optimization

`JackpotSharingOptimizer` uses game-theoretic scoring to minimize expected jackpot sharing by:

- Penalizing birthday numbers (1–31) — heavily over-picked by players
- Penalizing commonly "lucky" numbers (7, 11, 13, 21, 23)
- Penalizing visual ticket patterns, consecutive sequences, multiples of 5/10
- Penalizing all-odd or all-even combinations

`predict_optimized(features)` selects the candidate with lowest sharing risk.
`predict_anti_popular(features, count)` generates sets that maximally avoid popular number clusters.

---

## Development

```bash
make test      # run pytest
make lint      # flake8
make format    # black
make clean     # remove __pycache__, .pyc, build artifacts
```

### Docker

```bash
docker compose up lottery-predictor      # run predictions
docker compose up lottery-predictor-dev  # run tests with coverage
```

---

## Disclaimer

For educational and research purposes only. Lottery draws are random by design — no system can guarantee winning predictions.
