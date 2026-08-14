# Copilot Instructions for Lottery Prediction System

## Build, Test, and Lint

### Setup
```bash
# Install dependencies (requires Python 3.8+)
pip install -r requirements.txt

# Install development dependencies (includes pytest, black, flake8, mypy)
pip install -r requirements-dev.txt
```

### Testing
```bash
# Run all tests
make test

# Run with coverage report
make test-coverage

# Run a specific test file or class
python -m pytest tests/test_predictor.py -v
python -m pytest tests/test_predictor.py::TestDataProcessor -v

# Run tests matching a pattern
python -m pytest tests/ -k "test_validate" -v
```

### Linting and Formatting
```bash
# Check code style (flake8)
make lint

# Auto-format code (black)
make format

# Run all checks (lint + test)
make check

# Type checking (mypy)
python -m mypy src/ --ignore-missing-imports

# Pre-commit hooks (runs all linters)
pre-commit run --all-files
```

### Main CLI Commands
```bash
# Generate standard and optimized predictions
python cli.py predict

# Jackpot-sharing optimized predictions with anti-popular sets
python cli.py optimize

# Full summary report
python cli.py report

# Model performance evaluation
python cli.py evaluate

# Custom config and data paths
python cli.py predict --config config/custom_config.yaml --data data/custom_data.csv
```

## Architecture Overview

### Core Design Pattern
The system uses **dependency injection (DI)** with abstract interfaces to enable clean, testable code:
- **Interfaces** (`src/predictor/interfaces.py`): Abstract base classes for all major components
- **Implementations**: Concrete classes that implement interfaces
- **Factory Pattern** (`system_factory.py`): Assembles fully configured components
- **Strategy Pattern** (`strategies/prediction.py`): Pluggable prediction algorithms

### High-Level Flow
```
User Input (CLI) → PredictionOrchestrator → PredictionService
                       ↓
    Loads data via DataLoader → validates via DataValidator
                       ↓
    Engineers features via FeatureEngineer → creates models via ModelFactory
                       ↓
    Trains ensemble (XGBoost, Random Forest, Gradient Boosting)
                       ↓
    Generates predictions via PredictionStrategy
                       ↓
    Optimizes via JackpotSharingOptimizer (game-theoretic approach)
```

### Key Modules

| Module | Purpose |
|--------|---------|
| `src/predictor/system_factory.py` | Creates fully-wired `PredictionService` from config |
| `src/predictor/prediction_service.py` | Core service: trains models, makes predictions |
| `src/predictor/prediction_orchestrator.py` | Orchestrates the prediction workflow |
| `src/predictor/data/loaders.py` | Loads CSV data into DataFrames |
| `src/predictor/data/validators.py` | Validates lottery data structure and content |
| `src/predictor/features/engineers.py` | Creates features (frequencies, patterns, etc.) |
| `src/predictor/models/factory.py` | Creates XGBoost, Random Forest, Gradient Boosting models |
| `src/predictor/strategies/prediction.py` | Prediction strategies (unique number selection, top-k, etc.) |
| `src/predictor/jackpot_optimizer.py` | Game-theoretic jackpot sharing optimization |
| `src/predictor/config_manager.py` | Parses YAML config files |
| `config/model_config.yaml` | Configuration: model parameters, lottery settings, validation rules |

### Data Flow Example
```python
# 1. Factory creates fully configured service from YAML config
service = PredictionSystemFactory.create_lottery_predictor('config/model_config.yaml')

# 2. Train: load CSV → validate → engineer features → fit ensemble
service.train('data/lottery_history.csv')

# 3. Predict: prepare features → pass to strategy → generate predictions
features = service.prepare_features('data/lottery_history.csv')
predictions = service.predict(features)

# 4. Optimize: game-theoretic adjustment for jackpot sharing
optimized = service.predict_optimized(features)
anti_popular = service.predict_anti_popular(features, count=3)
```

## Key Conventions

### Configuration-Driven
- **All** model parameters are defined in `config/model_config.yaml`
- Updating model settings requires YAML edits, not code changes
- `ConfigManager` parses and validates YAML on instantiation

### Abstract Interfaces First
- All major components have ABC interfaces in `interfaces.py`
- Implementations (e.g., `CSVDataLoader`, `LotteryDataValidator`) extend these interfaces
- New implementations must follow the interface contract

### Factory Assembly
- Never instantiate `PredictionService` directly—use `PredictionSystemFactory.create_lottery_predictor()`
- Factory handles wiring all dependencies and validating the config file
- This ensures consistency across all prediction workflows

### Logging
- All modules use Python's `logging` module (not print statements)
- Set up with `logging.basicConfig()` in `cli.py`
- Components retrieve logger with `log = logging.getLogger(__name__)`

### Testing Conventions
- Tests use `unittest.TestCase` with `setUp()` for fixtures
- Test data is generated inline or use small sample CSVs in `data/`
- Avoid mocking; test real components with small datasets
- Test files: `tests/test_predictor.py`, `tests/test_validation.py`

### Code Style
- **Line length**: 100 characters (enforced by Black and Flake8)
- **Imports**: Organized by Black/isort (stdlib, third-party, local)
- **Pre-commit**: Runs Black, isort, Flake8, mypy, Bandit, yamllint automatically
- **Docstrings**: Function docstrings required (checked by Flake8-docstrings)

### Error Handling
- Custom exceptions in `src/predictor/exceptions.py`
- Validators raise exceptions for data issues (e.g., `LotteryDataValidator` raises on invalid data)
- CLI catches exceptions and logs them; crashes gracefully

### Feature Engineering
- Features are lottery-specific: draw date, number frequencies, patterns
- `LotteryFeatureEngineer.create_features()` returns a DataFrame with engineered columns
- Features are stored and reused during prediction (avoid recomputation)

### Model Management
- Trained models are saved to `models/` directory via `joblib`
- One model per position (position 1, 2, 3, etc.)
- Ensemble: predictions from XGBoost, Random Forest, Gradient Boosting are combined
- Strategy (`UniqueLotteryPredictionStrategy`) selects unique numbers from ensemble output

## Docker & Containerization

### Quick Reference
```bash
# Build the Docker image
docker build -t lottery-predictor:latest .

# Run prediction in container
docker run --rm lottery-predictor:latest python cli.py predict

# Run with custom config/data (mount volumes)
docker run --rm -v $(pwd)/config:/app/config -v $(pwd)/data:/app/data \
  lottery-predictor:latest python cli.py predict --config config/custom.yaml

# Run with Docker Compose (includes services if needed)
docker-compose up lottery-predictor
```

### Multi-Stage Build
The `Dockerfile` uses multi-stage builds:
1. **Build stage**: Installs dependencies, runs tests
2. **Runtime stage**: Lean final image with only production dependencies

Key files:
- `Dockerfile`: Multi-stage build with test layer
- `docker-compose.yml`: Production services
- `docker-compose.dev.yml`: Development environment with volume mounts
- `.dockerignore`: Excludes build artifacts, venv, etc.

### Environment Variables
- `PYTHONUNBUFFERED=1`: Ensures Python output streams unbuffered (see logs immediately)
- `MODEL_CONFIG_PATH`: Override config file path (default: `config/model_config.yaml`)
- `DATA_PATH`: Override data file path (default: `data/lottery_history.csv`)

### Volumes
- `/app/models/`: Persists trained models across container restarts
- `/app/outputs/`: Stores prediction results
- `/app/config/`: Configuration files
- `/app/data/`: Input lottery data

### Development Workflow
```bash
# Start dev environment (auto-reload on code changes)
docker-compose -f docker-compose.dev.yml up

# Run tests inside container
docker-compose -f docker-compose.dev.yml run --rm lottery-predictor make test

# Execute shell inside running container
docker exec -it <container_id> /bin/bash
```

## Performance Tuning

### Data Loading & Feature Engineering
- **Bottleneck**: Feature engineering is linear in dataset size (O(n))
- **Optimization**: Cache engineered features to avoid recomputation
  - `service.prepare_features()` returns cached DataFrame if source unchanged
  - Use `service._training_data` for in-memory features during prediction

### Model Training
- **XGBoost**: Most computationally expensive; adjust `n_estimators` in config
  - For large datasets (>5k rows): reduce `n_estimators` from 100 to 50–75
  - Increase `max_depth` gradually; diminishing returns above 8–10
- **Early stopping**: XGBoost uses `early_stopping_rounds: 10` (prevent overfitting + save time)
- **Parallelization**: Models use `n_jobs=-1` where applicable (all CPU cores)

### Memory Usage
- **DataFrame memory**: Lottery data with 1,365 draws + engineered features = ~5–10 MB
- **Models**: Joblib pickle files are small (~2–5 MB per model)
- **Predictions**: Ensemble predictions (3 models × 6 positions = 18 arrays) = ~100 KB per prediction

### Scaling Considerations
- **Small datasets** (<100 draws): Models overfit; reduce `max_depth` and `n_estimators`
- **Large datasets** (>10k draws): Training time dominates; profile with `python -m cProfile cli.py predict`
- **Batch predictions**: Loop over multiple datasets and aggregate results

### Profiling
```bash
# Profile CLI execution
python -m cProfile -s cumulative cli.py predict > profile.txt

# Profile specific function
python -c "
from src.predictor.system_factory import PredictionSystemFactory
import cProfile
service = PredictionSystemFactory.create_lottery_predictor('config/model_config.yaml')
cProfile.run('service.train(\"data/lottery_history.csv\")')
"
```

## Troubleshooting

### Common Issues

#### "ConfigurationNotFound" or "FileNotFoundError: Configuration file not found"
- **Cause**: `--config` path doesn't exist or is relative to wrong directory
- **Fix**: Use absolute paths or verify you're in the project root
  ```bash
  pwd  # Ensure you're in /Users/keith/Documents/personal/projects/658
  python cli.py predict --config $(pwd)/config/model_config.yaml
  ```

#### "ValidationError: Missing required columns"
- **Cause**: CSV doesn't have expected columns (LOTTO GAME, COMBINATIONS, DRAW DATE)
- **Fix**: Check the CSV header and update `config/model_config.yaml` if using custom data
  ```bash
  head -1 data/lottery_history.csv  # Print header
  ```
- **Custom columns**: Edit `config/model_config.yaml` → `data.validation.required_columns`

#### "ModuleNotFoundError: No module named 'xgboost'"
- **Cause**: Development dependencies not installed
- **Fix**: Install all dependencies
  ```bash
  pip install -r requirements-dev.txt
  ```

#### Model predictions are all the same
- **Cause**: Feature scaling issue or underfitting
- **Fix**: 
  1. Verify data has variance: `pandas.read_csv('data/lottery_history.csv')['COMBINATIONS'].nunique()`
  2. Increase `n_estimators` in config
  3. Decrease `learning_rate` (slower training, better convergence)

#### Tests fail with "ImportError: No module named 'src'"
- **Cause**: Running tests from wrong directory or venv not activated
- **Fix**: 
  ```bash
  cd /Users/keith/Documents/personal/projects/658  # Project root
  source venv/bin/activate  # Activate venv
  make test
  ```

#### Pre-commit hook fails on code formatting
- **Cause**: Black or isort reformatted code differently
- **Fix**: Re-stage the reformatted files and commit
  ```bash
  git add .  # Stage reformatted changes
  git commit -m "Format code"
  ```

### Debugging Tips

#### Enable verbose logging
```python
import logging
logging.basicConfig(level=logging.DEBUG)  # Instead of INFO
```

#### Inspect intermediate data
```python
from src.predictor.system_factory import PredictionSystemFactory
service = PredictionSystemFactory.create_lottery_predictor('config/model_config.yaml')
service.train('data/lottery_history.csv')

# Inspect engineered features
features = service.prepare_features('data/lottery_history.csv')
print(features.describe())  # Statistics
print(features.head())      # First rows

# Inspect model predictions
raw_predictions = [model.predict(features) for model, scaler in service.models]
print(raw_predictions)
```

#### Check model training state
```python
service.is_trained  # True/False
service._training_data.shape  # (rows, cols)
len(service.models)  # Number of trained models
```

### Performance Issues

#### Slow prediction generation
- **Profile**: Use cProfile (see Profiling section above)
- **Common cause**: Feature engineering recomputation
- **Fix**: Ensure `prepare_features()` is called once and reused
  ```python
  features = service.prepare_features(data_source)
  pred1 = service.predict(features)
  pred2 = service.predict_optimized(features)  # Reuses features
  ```

#### Out of memory on large datasets
- **Cause**: Loading entire CSV + features + models simultaneously
- **Fix**: 
  1. Reduce `n_estimators` in config (fewer trees = smaller models)
  2. Stream data instead of loading all at once (modify `CSVDataLoader`)
  3. Delete old model artifacts: `make clean`

#### Tests timeout
- **Cause**: Model training takes too long in test fixture
- **Fix**: Use smaller test config with fewer estimators
  ```python
  # In test setUp()
  test_config = {
      "models": {"xgboost": {"n_estimators": 5, "max_depth": 3}}
  }
  ```

### Validation and Data Issues

#### "Data validation failed"
- **Cause**: Missing or malformed rows
- **Fix**: Clean data before using
  ```bash
  # Remove empty rows
  python -c "
  import pandas as pd
  df = pd.read_csv('data/lottery_history.csv')
  df = df.dropna()
  df.to_csv('data/lottery_history.csv', index=False)
  "
  ```

#### Numbers outside lottery range (1–58)
- **Cause**: Data parsing or format issue in COMBINATIONS column
- **Fix**: Validate data parsing
  ```python
  from src.predictor.data.loaders import CSVDataLoader
  loader = CSVDataLoader()
  data = loader.load('data/lottery_history.csv')
  print(data[['COMBINATIONS']].head(10))
  ```

#### Predictions contain duplicates
- **Cause**: Strategy not enforcing uniqueness
- **Fix**: Verify `UniqueLotteryPredictionStrategy` is configured
  - Check `config/model_config.yaml` → `prediction.strategy: "unique"`
  - If duplicates persist, debug `strategies/prediction.py` → `predict()` method

## CI/CD Pipeline

### GitHub Actions Workflows

The project uses 4 main GitHub Actions workflows for continuous integration:

#### 1. **ci.yml** — Full CI Pipeline
**Triggered**: On `push` to main/master, or `pull_request`  
**Jobs**:
- **lint-and-test**: Multi-version testing (Python 3.10, 3.11, 3.12)
  - Runs Flake8 linting (`src/` and `tests/`)
  - Runs Black formatting check
  - Runs pytest with coverage reporting (XML + term output)
  - Tests all CLI commands: `predict`, `optimize`, `report`, `evaluate`
- **docker-build**: Docker image build verification
  - Builds image tagged `lottery-predictor:ci`
  - Runs container health checks and prediction commands

#### 2. **tests.yml** — Comprehensive Test Suite
**Triggered**: On `push` to main/master/develop, or `pull_request`  
**Also scheduled**: Daily at 2 AM UTC (cron job)  
**Jobs**:
- **test**: Multi-version unit tests with coverage upload
  - Runs pytest across Python 3.10, 3.11, 3.12
  - Generates coverage reports (XML, HTML, term-missing)
  - Uploads to Codecov for tracking
  - Saves test artifacts (junit.xml, htmlcov/) for 30 days
- **integration-test**: CLI command end-to-end tests
  - Tests each command: predict, optimize, report, evaluate
- **test-summary**: Final pass/fail gate

#### 3. **quality.yml** — Code Quality Checks
**Triggered**: On `push` to main/master/develop, or `pull_request`  
**Jobs**:
- **lint**: Flake8, Black, isort (with `continue-on-error: true`)
  - Max line length: 120 characters
- **type-check**: mypy type checking
  - Ignores missing type stubs (`--ignore-missing-imports`)
- **security**: Bandit security scanner
  - Scans for common vulnerabilities

#### 4. **docker.yml** — Container Build & Push
**Triggered**: On `push` to main/master, or workflow_dispatch  
**Jobs**:
- Builds multi-stage Docker image
- Runs tests inside container
- Optionally pushes to Docker registry

### Workflow Status Badges
Add to README.md:
```markdown
![CI Pipeline](https://github.com/poliran/658/actions/workflows/ci.yml/badge.svg)
![Tests](https://github.com/poliran/658/actions/workflows/tests.yml/badge.svg)
![Quality](https://github.com/poliran/658/actions/workflows/quality.yml/badge.svg)
```

### Local Pre-Commit Workflow
Before pushing, run locally:
```bash
# Install pre-commit hooks
pre-commit install

# Run all hooks on staged files
pre-commit run

# Run on all files (before first commit)
pre-commit run --all-files

# Skip hooks temporarily (not recommended)
git commit --no-verify
```

### Debugging CI Failures

#### "Tests failed on Python 3.12 but pass locally"
- **Cause**: Python version mismatch or environment difference
- **Fix**:
  ```bash
  # Install the same Python version
  pyenv install 3.12.0
  pyenv shell 3.12.0
  python -m pytest tests/
  ```

#### "Codecov upload failed"
- **Cause**: Coverage.xml not generated or CI token invalid
- **Fix**: Ensure pytest coverage step runs successfully locally
  ```bash
  python -m pytest tests/ --cov=src --cov-report=xml
  ```

#### "Docker build times out"
- **Cause**: Large dependencies or network issues
- **Fix**: Optimize Dockerfile or enable Docker layer caching in GitHub Actions

---

## Model Evaluation & Interpretation

### Evaluation Metrics

The `ModelEvaluator` class tracks prediction accuracy using multiple metrics:

#### 1. **Exact Match Rate**
- **Definition**: Percentage of predicted numbers that appear in actual draw
- **Formula**: (# of predicted numbers in actual draw) / (total numbers drawn)
- **Example**: Predicted [1, 5, 12, 35, 42, 58], Actual [5, 12, 18, 35, 44, 52]
  - Exact matches: [5, 12, 35] = 3 matches
  - Exact match rate: 3/6 = 50%
- **Interpretation**: Higher is better; 100% means all predictions are in the actual draw

#### 2. **Position Accuracy**
- **Definition**: Percentage of predictions that match actual numbers in exact position
- **Formula**: (# of position matches) / (total positions)
- **Example**: If predicted position 1 is 5 and actual position 1 is 5, that's 1 match
- **Interpretation**: Harder to achieve than exact match rate; indicates strong predictive signal

#### 3. **Mean Squared Error (MSE)**
- **Definition**: Average squared difference between predicted and actual numbers
- **Formula**: Σ((predicted - actual)²) / n
- **Interpretation**: Lower is better; measures magnitude of prediction errors

#### 4. **Mean Absolute Error (MAE)**
- **Definition**: Average absolute difference between predicted and actual numbers
- **Formula**: Σ|predicted - actual| / n
- **Interpretation**: More interpretable than MSE; average "distance" from correct number

### Running Evaluations

```bash
# Evaluate model on default data
python cli.py evaluate

# Evaluate with custom config/data
python cli.py evaluate --config config/custom.yaml --data data/custom_data.csv

# Programmatic evaluation
python -c "
from src.predictor.evaluator import ModelEvaluator
evaluator = ModelEvaluator('config/model_config.yaml')
metrics = evaluator.evaluate('data/lottery_history.csv')
print(metrics)
"
```

### Interpreting Results

#### Expected Baseline Performance
- **Exact match rate**: 15–25% (random baseline ≈ 10% for 6 out of 58)
- **Position accuracy**: 5–15% (very difficult; random baseline ≈ 2%)
- **MAE**: 10–20 (numbers range 1–58)

#### Red Flags
| Symptom | Likely Cause |
|---------|--------------|
| Exact match rate < 10% | Model is underfitting; check data quality and features |
| Position accuracy > 50% | Data leakage or test set contamination |
| MAE > 25 | Model ignoring lottery constraints; check feature engineering |
| Zero variance predictions | Strategy or scaling bug; inspect `predict()` method |

### Backtesting

The `ModelEvaluator.backtest_model()` method performs walk-forward validation:
- Splits data into training and test windows
- Trains model on historical data, evaluates on future draws
- Produces per-draw accuracy metrics

**Note**: Backtesting is complex due to data pipeline dependencies; see `CODE_REVIEW_BUGS.md` for implementation status.

---

## Jupyter Notebooks for Exploratory Analysis

### Setup
```bash
# Install Jupyter
pip install jupyter jupyterlab

# Start Jupyter server
jupyter notebook

# Or use JupyterLab (modern interface)
jupyter lab
```

### Key Analysis Workflows

#### 1. **Exploratory Data Analysis (EDA)**
Create `notebooks/01_eda.ipynb`:
```python
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Load data
df = pd.read_csv('data/lottery_history.csv')
print(df.info())
print(df.describe())

# Number frequency distribution
numbers = []
for combo in df['COMBINATIONS']:
    numbers.extend([int(n.strip()) for n in combo.split('-')])

plt.figure(figsize=(12, 6))
pd.Series(numbers).value_counts().sort_index().plot(kind='bar')
plt.title('Lottery Number Frequency')
plt.xlabel('Number')
plt.ylabel('Frequency')
plt.show()
```

#### 2. **Feature Inspection**
Create `notebooks/02_feature_engineering.ipynb`:
```python
from src.predictor.system_factory import PredictionSystemFactory

service = PredictionSystemFactory.create_lottery_predictor('config/model_config.yaml')
features = service.prepare_features('data/lottery_history.csv')

print("Engineered features:")
print(features.describe())
print(f"\nShape: {features.shape}")

# Correlation with outcomes
import numpy as np
outcome_col = 'num_1'  # First position
correlation = features.corr()[outcome_col].sort_values(ascending=False)
print("\nFeature correlations with position 1:")
print(correlation)
```

#### 3. **Model Performance Analysis**
Create `notebooks/03_model_performance.ipynb`:
```python
from src.predictor.evaluator import ModelEvaluator
import pandas as pd

evaluator = ModelEvaluator('config/model_config.yaml')
metrics = evaluator.evaluate('data/lottery_history.csv')

# Plot metrics over time (if backtest enabled)
results_df = pd.DataFrame(evaluator.evaluation_history)
results_df[['exact_match_rate', 'position_accuracy', 'mae']].plot()
plt.title('Model Performance Over Time')
plt.ylabel('Metric Value')
plt.xlabel('Draw Number')
plt.show()
```

#### 4. **Hyperparameter Tuning**
Create `notebooks/04_hyperparameter_search.ipynb`:
```python
import yaml
from src.predictor.system_factory import PredictionSystemFactory

# Test different n_estimators
for n_est in [50, 100, 150]:
    config = yaml.safe_load(open('config/model_config.yaml'))
    config['models']['xgboost']['n_estimators'] = n_est
    
    # Temporarily save modified config
    yaml.dump(config, open('config/test_config.yaml', 'w'))
    
    service = PredictionSystemFactory.create_lottery_predictor('config/test_config.yaml')
    service.train('data/lottery_history.csv')
    
    print(f"n_estimators={n_est}: Training complete, is_trained={service.is_trained}")
```

### Best Practices

1. **Separate concerns**: One notebook per analysis (EDA, features, performance, tuning)
2. **Persist analysis**: Export figures and key metrics to `outputs/`
3. **Version configs**: When testing config changes, save versions to track experiments
4. **Document assumptions**: Add markdown cells explaining data preprocessing choices
5. **Avoid production code in notebooks**: Use notebooks for exploration; move validated logic to `src/`

### Sharing Results

Export notebook results for documentation:
```python
# Save plots
plt.savefig('outputs/feature_correlations.png', dpi=300, bbox_inches='tight')

# Export DataFrame to CSV
results_df.to_csv('outputs/model_metrics.csv', index=False)

# Convert notebook to HTML (from CLI)
# jupyter nbconvert --to html notebooks/01_eda.ipynb --output-dir outputs/
```

---

## Contributing Guidelines

### Development Workflow

#### 1. **Setup Development Environment**
```bash
# Clone repository
git clone https://github.com/poliran/658.git
cd 658

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install all dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install

# Verify setup
make check  # Runs lint + tests
```

#### 2. **Create Feature Branch**
```bash
# Start from latest main
git checkout main
git pull origin main

# Create descriptive branch
git checkout -b feature/improve-xgboost-tuning
# or
git checkout -b fix/duplicates-in-predictions
```

#### 3. **Make Changes**
- Follow code style (Black, isort, Flake8)
- Add/update tests for new functionality
- Update docstrings
- Update configuration files if needed

#### 4. **Verify Changes Locally**
```bash
# Run all checks
make check

# Run full test suite
make test

# Test CLI commands
python cli.py predict
python cli.py optimize

# Try in Docker
docker build -t lottery-predictor:dev .
docker run --rm lottery-predictor:dev make test
```

#### 5. **Commit with Meaningful Messages**
```bash
git add .
git commit -m "feature: improve XGBoost early stopping threshold

- Reduce early_stopping_rounds from 10 to 5 for faster convergence
- Add config validation in ConfigManager
- Update tests for new parameter

Fixes #42"
```

Include:
- **Type**: feature, fix, docs, refactor, test, chore
- **Scope**: component name (optional)
- **Description**: What changed and why
- **Issue reference**: `Fixes #XX` or `Closes #XX`

#### 6. **Push & Create Pull Request**
```bash
git push origin feature/improve-xgboost-tuning
```

Then open PR on GitHub with:
- Clear title: "Feature: Improve XGBoost early stopping"
- Description: What changed, why, and how to test
- Link to issues: "Fixes #42"
- Checklist:
  ```markdown
  - [ ] Tests pass locally
  - [ ] Code follows style guide
  - [ ] Documentation updated
  - [ ] No breaking changes
  ```

### Code Review Checklist

When reviewing PRs, check:

| Item | Questions |
|------|-----------|
| **Correctness** | Does it solve the problem? Are there edge cases? |
| **Tests** | Are new features/fixes tested? Is coverage > 80%? |
| **Style** | Does it follow Black/isort/Flake8 rules? |
| **Interfaces** | Do implementations follow ABC contracts? |
| **Docs** | Are docstrings updated? Is config documentation clear? |
| **Performance** | Are there performance regressions? |
| **Backwards compatibility** | Do changes break existing workflows? |

### Adding New Features

#### Checklist
- [ ] Create interface (ABC) in `src/predictor/interfaces.py` if new component type
- [ ] Implement concrete class with full docstrings
- [ ] Add unit tests in `tests/`
- [ ] Update `config/model_config.yaml` with new parameters (if applicable)
- [ ] Update README.md or `docs/` with usage examples
- [ ] Run full test suite: `make test`
- [ ] Get code review approval before merge

#### Example: Adding a New Prediction Strategy

1. **Define interface** (already exists in `interfaces.py`):
```python
class PredictionStrategy(ABC):
    @abstractmethod
    def predict(self, models: List, features: np.ndarray) -> np.ndarray:
        """Generate predictions using the strategy."""
```

2. **Implement strategy** in `src/predictor/strategies/prediction.py`:
```python
class TopKLotteryPredictionStrategy(PredictionStrategy):
    """Select top-k predicted numbers by confidence score."""
    
    def __init__(self, k: int = 6):
        self.k = k
    
    def predict(self, models: List, features: np.ndarray) -> np.ndarray:
        """Select top-k numbers by aggregated prediction score."""
        # Implementation here
        pass
```

3. **Update factory** in `system_factory.py`:
```python
strategy_name = config.get("prediction", {}).get("strategy", "unique")
if strategy_name == "top_k":
    strategy = TopKLotteryPredictionStrategy(k=6)
else:
    strategy = UniqueLotteryPredictionStrategy()
```

4. **Test thoroughly**:
```python
def test_top_k_strategy():
    strategy = TopKLotteryPredictionStrategy(k=6)
    # Mock models and features
    result = strategy.predict(mock_models, mock_features)
    assert len(result) == 6
    assert all(1 <= n <= 58 for n in result)
```

5. **Update config**:
```yaml
prediction:
  strategy: "top_k"  # or "unique"
  top_k: 6
```

### Documentation Standards

- **Module docstrings**: Explain purpose and usage
- **Class docstrings**: Describe class role and key methods
- **Function docstrings**: Args, Returns, Raises sections (Google style)
- **Inline comments**: Only for non-obvious logic
- **Type hints**: Always include (checked by mypy)

Example:
```python
def predict_optimized(self, features: pd.DataFrame) -> List[int]:
    """Generate jackpot-optimized lottery predictions.
    
    Uses game-theoretic approach to reduce overlap with popular numbers,
    increasing expected jackpot share if this prediction wins.
    
    Args:
        features: Engineered features DataFrame from prepare_features().
    
    Returns:
        List of 6 unique lottery numbers (1–58).
    
    Raises:
        ValueError: If features are invalid or model is untrained.
    """
```

### Issue Labels & Triaging

Use GitHub labels for organization:
- **bug**: Something broken
- **feature**: New capability
- **docs**: Documentation
- **refactor**: Code cleanup
- **performance**: Speed/efficiency
- **help wanted**: Community contribution opportunity
- **good first issue**: Beginner-friendly
- **blocked**: Waiting on external factor

### Release Process

1. **Update version** in `setup.py` (e.g., 1.0.0 → 1.1.0)
2. **Update CHANGELOG** (if exists)
3. **Create git tag**: `git tag v1.1.0`
4. **Push to GitHub**: `git push origin v1.1.0`
5. **GitHub Actions** automatically builds and publishes (if configured)

---

## Copilot assistant guidance (project-specific)

This project includes specific expectations for Copilot CLI sessions to reduce friction and keep work reproducible. Add or follow these rules when interacting with the repo via the Copilot CLI:

- Rename branch/session before edits: Use the built-in rename_branch (for git branches) or rename_session tools instead of raw git branch commands. This makes worktrackable and avoids accidental changes to the main checkout.
- Pre-tool short preamble: Before any tool invocation (view, edit, bash, grep, session_store_sql, etc.), include a one-line explanation of the next action and why — a short human-readable preToolPreamble helps reviewers understand intent.
- Ask questions via ask_user tool: When a human decision is required, always use the ask_user tool (with choices when predictable) — do not ask freeform questions in plain chat text.
- Batch parallel reads/edits: When reading or editing multiple files or ranges, call the view/edit tools in a single grouped response to leverage parallelism and avoid repeated round-trips.
- Prefer direct tools for simple tasks: Use glob/grep/view/edit for short searches and small edits. Reserve the task/explore agents for multi-step, long-running, or independent research tasks only.
- Large file handling: Use view_range for files >20KB and avoid reading entire large files. When viewing multiple ranges, include all view_range calls together.
- Use targeted CLI/test commands: Prefer running a single test or a small targeted make/test invocation (e.g., `python -m pytest tests/test_predictor.py::TestDataProcessor -v`) rather than full-suite runs unless validating broad changes.
- Session artifacts: Put transient artifacts (plans, task lists, scratch files) in the session-state artifacts directory (the environment exposes an artifacts_dir). Avoid committing session-only files to the repo.
- Commit metadata: Include the co-author trailer `Co-authored-by: Copilot App <223556219+Copilot@users.noreply.github.com>` in commits made by Copilot unless explicitly requested otherwise.

These additions are intended to codify the interaction patterns observed in prior sessions and reduce repeated clarifications. If desired, further automation (pre-commit checks, CI gates) can enforce some of these rules.
