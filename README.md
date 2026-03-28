# Lottery Prediction System

A production-ready machine learning system for analyzing and predicting lottery numbers using ensemble. Educational purpose.

## Features

- Historical lottery data analysis (1,365+ draws)
- Ensemble machine learning models (XGBoost, Random Forest, Gradient Boosting)
- Feature engineering based on number frequencies and patterns
- **Game-theoretic jackpot sharing optimization**
- Configurable model parameters via YAML
- Comprehensive testing and evaluation framework
- Clean, modular architecture

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Generate predictions
python cli.py predict

# Jackpot-sharing optimized predictions
python cli.py optimize

# Full summary report
python cli.py report

# Evaluate model performance
python cli.py evaluate

# Run tests
make test
```

## Installation

1. Clone the repository
2. Create virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Basic Prediction

```python
from src.predictor import PredictionSystemFactory

service = PredictionSystemFactory.create_lottery_predictor('config/model_config.yaml')
service.train('data/lottery_history.csv', model_config={})

features = service.prepare_features('data/lottery_history.csv')
print(f"Predicted numbers: {sorted(service.predict(features))}")
print(f"Optimized numbers: {sorted(service.predict_optimized(features))}")
```

### Jackpot Sharing Optimization

```python
anti_popular = service.predict_anti_popular(features, count=3)
for i, pred in enumerate(anti_popular, 1):
    print(f"Anti-popular set {i}: {sorted(pred)}")
```

### Command Line

```bash
python cli.py predict    # Standard + optimized predictions
python cli.py optimize   # Jackpot-sharing optimized + anti-popular sets
python cli.py report     # Full summary report
python cli.py evaluate   # Model performance evaluation
```

## Project Structure

```
├── src/predictor/              # Core prediction modules
├── tests/                      # Unit tests
├── config/                     # Configuration files
├── data/                       # Historical and processed data
├── models/                     # Saved model artifacts
├── outputs/                    # Generated results
├── scripts/                    # Utility and legacy scripts
├── docs/                       # Documentation
└── notebooks/                  # Analysis notebooks
```

See [docs/PROJECT_STRUCTURE.md](docs/PROJECT_STRUCTURE.md) for detailed structure.

## Configuration

Edit `config/model_config.yaml` to adjust:
- Model parameters (n_estimators, learning_rate, etc.)
- Data validation rules
- Feature engineering settings

## Development

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run tests
make test

# Run linting
make lint

# Format code
make format

# Clean up
make clean
```

## Documentation

- [Project Structure](docs/PROJECT_STRUCTURE.md)
- [Implementation Summary](docs/COMPLETION_SUMMARY.md)
- [Jackpot Optimization](docs/JACKPOT_OPTIMIZATION.md)

## Disclaimer

This system is for educational and research purposes only. Lottery numbers are random by design, and no system can guarantee winning predictions.
