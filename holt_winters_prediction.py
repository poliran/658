import pandas as pd
import numpy as np
from datetime import datetime
from statsmodels.tsa.holtwinters import ExponentialSmoothing

# Load data from 'iot_sensor.csv'
df = pd.read_csv('iot_sensor.csv')

# Parse the DATE column and set it as the index
df['DATE'] = pd.to_datetime(df['DATE'], format='%d/%m/%y')
df = df.set_index('DATE')

# Sort the DataFrame by the date index
df = df.sort_index()

# Analyze each sensor separately using Holt-Winters method
predictions = {}
for sensor in ['N1', 'N2', 'N3', 'N4', 'N5', 'N6']:
    # Fit Holt-Winters model
    model = ExponentialSmoothing(
        df[sensor],
        seasonal_periods=12,  # Monthly seasonality
        trend='add',
        seasonal='add'
    ).fit()
    
    # Make prediction for two periods ahead
    pred = model.forecast(2)
    
    # Get the prediction for the next 2 periods
    pred_1 = int(round(max(min(pred.iloc[0], df[sensor].max()), df[sensor].min())))
    pred_2 = int(round(max(min(pred.iloc[1], df[sensor].max()), df[sensor].min())))
    
    predictions[sensor] = (pred_1, pred_2)

# Calculate basic statistics for validation
stats = {}
for sensor in ['N1', 'N2', 'N3', 'N4', 'N5', 'N6']:
    stats[sensor] = {
        'mean': df[sensor].mean(),
        'std': df[sensor].std(),
        'min': df[sensor].min(),
        'max': df[sensor].max()
    }

# Output the predictions
print("Predictions for the next 2 periods:")
for sensor, (pred_1, pred_2) in predictions.items():
    print(f"{sensor}: {pred_1}, {pred_2}")

# Output the validation statistics
print("\nValidation Statistics:")
for sensor, stat in stats.items():
    print(f"\n{sensor}:")
    for metric, value in stat.items():
        print(f"{metric}: {value:.2f}")