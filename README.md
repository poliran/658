# Lottery Prediction System

A production-ready machine learning system for analyzing and predicting lottery numbers using ensemble methods.

## Features

- Historical lottery data analysis (1,365+ draws)
- Ensemble machine learning models (XGBoost, Random Forest, Gradient Boosting)
- Feature engineering based on number frequencies and patterns
- Configurable model parameters via YAML
- Comprehensive testing and evaluation framework
- Clean, modular architecture

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run prediction
python run_prediction.py

# Evaluate model performance
python evaluate_model.py

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
from src.predictor import LotteryPredictor

# Initialize predictor
predictor = LotteryPredictor('config/model_config.yaml')

# Train models
predictor.train('data/lottery_history.csv')

# Generate predictions
features = predictor.data_processor.prepare_next_draw_features()
predictions = predictor.predict(features)
print(f"Predicted numbers: {sorted(predictions)}")
```

### Command Line

```bash
# Generate predictions
python run_prediction.py

# Evaluate model performance
python evaluate_model.py
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

## Disclaimer

This system is for educational and research purposes only. Lottery numbers are random by design, and no system can guarantee winning predictions.
