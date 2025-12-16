# Lottery Prediction System

A machine learning-based system for analyzing and predicting lottery numbers using ensemble methods.

## Features

- Historical lottery data analysis
- Ensemble machine learning models (XGBoost, Random Forest, Gradient Boosting)
- Feature engineering based on number frequencies and patterns
- Configurable model parameters via YAML
- Production-ready modular architecture

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
python run_prediction.py
```

## Configuration

Edit `config/model_config.yaml` to adjust:
- Model parameters (n_estimators, learning_rate, etc.)
- Data validation rules
- Feature engineering settings

## Project Structure

```
├── src/
│   └── predictor/
│       ├── lottery_predictor.py    # Main prediction class
│       ├── data_processor.py       # Data preprocessing
│       └── model_trainer.py        # Model training
├── config/
│   └── model_config.yaml          # Configuration
├── data/
│   └── lottery_history.csv        # Historical data
├── run_prediction.py              # Main entry point
└── requirements.txt               # Dependencies
```

## Disclaimer

This system is for educational and research purposes only. Lottery numbers are random by design, and no system can guarantee winning predictions.
