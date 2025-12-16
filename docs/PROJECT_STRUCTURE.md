# Project Structure

```
lottery-prediction-system/
├── src/                          # Source code
│   └── predictor/               # Main prediction package
│       ├── __init__.py
│       ├── lottery_predictor.py # Main predictor class
│       ├── data_processor.py    # Data processing
│       ├── model_trainer.py     # Model training
│       └── evaluator.py         # Model evaluation
│
├── tests/                       # Unit tests
│   ├── __init__.py
│   └── test_predictor.py
│
├── config/                      # Configuration files
│   └── model_config.yaml       # Model parameters
│
├── data/                        # Data directory
│   ├── lottery_history.csv     # Historical lottery data
│   ├── raw/                    # Raw data files
│   └── processed/              # Processed data files
│
├── models/                      # Saved model files
│   ├── *.pkl                   # Pickled models
│   ├── *.keras                 # Keras models
│   └── *.h5                    # HDF5 models
│
├── outputs/                     # Generated outputs
│   ├── *.png                   # Plots and visualizations
│   ├── *.json                  # Analysis results
│   └── *.txt                   # Text outputs
│
├── scripts/                     # Utility scripts
│   ├── legacy/                 # Legacy experimental code
│   ├── webscraping/           # Web scraping scripts
│   └── analysis/              # Data analysis scripts
│
├── docs/                        # Documentation
│   ├── README.md               # Main documentation
│   ├── PROJECT_STRUCTURE.md    # This file
│   └── COMPLETION_SUMMARY.md   # Implementation summary
│
├── notebooks/                   # Jupyter notebooks (future)
│
├── run_prediction.py           # Main entry point
├── evaluate_model.py           # Model evaluation script
├── setup.py                    # Package setup
├── Makefile                    # Development tasks
├── requirements.txt            # Dependencies
├── requirements-dev.txt        # Development dependencies
├── .gitignore                  # Git ignore rules
└── .vscode/                    # VS Code settings
```

## Directory Descriptions

- **src/**: Core application source code
- **tests/**: Unit tests and test utilities
- **config/**: Configuration files and settings
- **data/**: All data files (historical, raw, processed)
- **models/**: Trained model artifacts
- **outputs/**: Generated files (plots, results, reports)
- **scripts/**: Utility scripts and legacy code
- **docs/**: Project documentation
- **notebooks/**: Jupyter notebooks for analysis (future use)

## Key Files

- `run_prediction.py`: Main script to generate predictions
- `evaluate_model.py`: Script to evaluate model performance
- `setup.py`: Package installation configuration
- `Makefile`: Common development tasks
- `requirements.txt`: Production dependencies
- `requirements-dev.txt`: Development dependencies
