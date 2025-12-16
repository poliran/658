# Deprecated Files

This document lists files that have been moved to the `archive/` directory.

## Archived Files

### Experimental Code
- `xgboost-prediction.py` - Original monolithic implementation
- `xg.py` - Alternative XGBoost implementation
- `grok.py` - Experimental prediction logic
- `analyze.py` - Ad-hoc data analysis
- `combinations.py` - Combination analysis
- `transition.py` - Transition probability analysis
- `holt_winters_prediction.py` - Time series approach

### Web Scraping Implementations
- `webscrape*.py` - Multiple web scraping attempts
- `test_selenium.py` - Selenium testing
- `parse_saved_html.py` - HTML parsing utilities

### Testing & Validation
- `test_random_forest.py` - Random forest testing
- `repeat_combo.py` - Combination repeat analysis

### Data Files
- `iot_sensor.csv` - Unrelated sensor data

## Migration Notes

These files were moved to maintain project cleanliness while preserving
historical implementations for reference.

### Current Implementation
The production system now uses:
- `src/predictor/` - Main prediction modules
- `run_prediction.py` - Entry point
- `evaluate_model.py` - Model evaluation

### Accessing Archived Code
Archived files can be found in:
```
archive/
├── experimental/
├── deprecated/
├── old_models/
└── old_notebooks/
```
