import numpy as np
import pandas as pd
import json
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout, Bidirectional, BatchNormalization, GRU, Conv1D, MaxPooling1D, Flatten
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau
from tensorflow.keras.regularizers import l2
from tensorflow.keras.optimizers import Adam
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import TimeSeriesSplit
from sklearn.decomposition import PCA
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from statsmodels.tsa.seasonal import seasonal_decompose
from statsmodels.tsa.stattools import acf, pacf
from sklearn.impute import SimpleImputer
from sklearn.model_selection import RandomizedSearchCV

def load_and_preprocess_data(file_path):
    with open(file_path, 'r') as f:
        data = json.load(f)
    
    df = pd.DataFrame(data)
    df['DRAW DATE'] = pd.to_datetime(df['DRAW DATE'])
    df = df.sort_values('DRAW DATE')
    
    def engineer_features(df):
        def is_prime(n):
            if n < 2:
                return False
            for i in range(2, int(n ** 0.5) + 1):
                if n % i == 0:
                    return False
            return True

        features = []
        
        # Time-based features
        features.extend([
            df['DRAW DATE'].dt.year,
            df['DRAW DATE'].dt.quarter,
            df['DRAW DATE'].dt.month,
            df['DRAW DATE'].dt.isocalendar().week,
            df['DRAW DATE'].dt.dayofweek,
            df['DRAW DATE'].dt.dayofyear,
            (df['DRAW DATE'].dt.dayofweek >= 5).astype(int)  # Weekend indicator
        ])
        
        # Combination-based features
        features.extend([
            df['COMBINATIONS'].apply(lambda x: sum(x)),
            df['COMBINATIONS'].apply(lambda x: np.prod(x)),
            df['COMBINATIONS'].apply(lambda x: sum(1 for num in x if num % 2 == 0)),  # Count of even numbers
            df['COMBINATIONS'].apply(lambda x: sum(1 for num in x if num % 2 != 0))   # Count of odd numbers
        ])
        
        # Statistical features
        features.extend([
            df['COMBINATIONS'].apply(lambda x: stats.skew(x)),
            df['COMBINATIONS'].apply(lambda x: stats.kurtosis(x))
        ])
        
        # Range-based features
        features.extend([
            df['COMBINATIONS'].apply(lambda x: max(x) - min(x)),
            df['COMBINATIONS'].apply(lambda x: max(x)),
            df['COMBINATIONS'].apply(lambda x: min(x))
        ])
        
        # Frequency-based features
        all_numbers = [num for combo in df['COMBINATIONS'] for num in combo]
        number_freq = pd.Series(all_numbers).value_counts(normalize=True)
        features.append(df['COMBINATIONS'].apply(lambda x: sum(number_freq[num] for num in x) / 6))
        
        # Positional features
        for i in range(6):
            features.append(df['COMBINATIONS'].apply(lambda x: x[i]))
        
        # Rolling statistics
        for window in [5, 10, 20]:
            features.extend([
                df['COMBINATIONS'].apply(lambda x: np.mean(x)).rolling(window=window).mean(),
                df['COMBINATIONS'].apply(lambda x: np.std(x)).rolling(window=window).mean()
            ])
        
        # Lag features
        for lag in [1, 2, 3]:
            features.extend([
                df['COMBINATIONS'].apply(lambda x: np.mean(x)).shift(lag),
                df['COMBINATIONS'].apply(lambda x: np.std(x)).shift(lag)
            ])
        
        # Difference features
        mean_series = df['COMBINATIONS'].apply(lambda x: np.mean(x))
        features.extend([
            mean_series.diff(),
            mean_series.diff().diff()
        ])
        
        # Autocorrelation features
        acf_values = acf(mean_series.dropna(), nlags=5)
        pacf_values = pacf(mean_series.dropna(), nlags=5)
        for i in range(1, len(acf_values)):
            features.append(pd.Series(acf_values[i], index=mean_series.index))
        for i in range(1, len(pacf_values)):
            features.append(pd.Series(pacf_values[i], index=mean_series.index))
        
        # Cyclical features
        features.extend([
            np.sin(2 * np.pi * df['DRAW DATE'].dt.month / 12),
            np.cos(2 * np.pi * df['DRAW DATE'].dt.month / 12),
            np.sin(2 * np.pi * df['DRAW DATE'].dt.dayofyear / 365),
            np.cos(2 * np.pi * df['DRAW DATE'].dt.dayofyear / 365)
        ])
        
        # Frequency-based features
        for window in [10, 30, 100]:
            for i in range(6):
                def rolling_frequency(x):
                    counts = x.value_counts(normalize=True)
                    return counts.get(x.iloc[-1], 0)  # Return frequency of the last value
                
                freq = df['COMBINATIONS'].apply(lambda x: x[i]).rolling(window=window).apply(rolling_frequency)
                features.append(freq)
        
        # Hot/Cold features
        for window in [10, 30, 100]:
            for i in range(6):
                hot_cold = df['COMBINATIONS'].apply(lambda x: x[i]).rolling(window=window).apply(lambda x: (x == x.iloc[-1]).sum() / len(x))
                features.append(hot_cold)
        
        # Pair-based features
        for i in range(5):
            features.append(df['COMBINATIONS'].apply(lambda x: abs(x[i] - x[i+1])))
        
        # Previous combinations
        for i in range(1, 6):
            for j in range(6):
                features.append(df['COMBINATIONS'].shift(i).apply(lambda x: x[j] if isinstance(x, list) else np.nan))
        
        # Cumulative sum feature
        cum_sum = df['COMBINATIONS'].apply(lambda x: sum(x)).cumsum()
        features.append(cum_sum)
        
        # Other custom features
        features.extend([
            df['COMBINATIONS'].apply(lambda x: sum([n**2 for n in x])),  # Sum of squares
            df['COMBINATIONS'].apply(lambda x: max(x) - min(x)),  # Difference between max and min
            df['COMBINATIONS'].apply(lambda x: sum([n for n in x if n % 2 == 0]) / len([n for n in x if n % 2 == 0]) if len([n for n in x if n % 2 == 0]) > 0 else 0),  # Average of even numbers
            df['COMBINATIONS'].apply(lambda x: sum([n for n in x if n % 2 != 0]) / len([n for n in x if n % 2 != 0]) if len([n for n in x if n % 2 != 0]) > 0 else 0),  # Average of odd numbers
            df['COMBINATIONS'].apply(lambda x: sum(1 for n in x if is_prime(n)))  # Number of prime numbers
        ])
        
        return pd.concat(features, axis=1)
    
    # Apply feature engineering
    engineered_features = engineer_features(df)
    
    # Combine original combinations with engineered features
    combinations = np.array([num for d in data for num in d['COMBINATIONS']])
    combinations_reshaped = combinations.reshape(-1, 6)
    
    # Ensure engineered_features has the same number of rows as combinations_reshaped
    engineered_features_repeated = np.repeat(engineered_features.values, 6, axis=0)
    engineered_features_repeated = engineered_features_repeated[:len(combinations_reshaped) * 6].reshape(-1, 6 * engineered_features.shape[1])
    
    X = np.hstack((combinations_reshaped, engineered_features_repeated))
    
    # Convert X to float type
    X = X.astype(float)
    
    # Handle missing data
    X = np.nan_to_num(X, nan=np.nan)  # Replace inf with NaN
    
    # Remove columns with all zeros or all NaNs
    X = X[:, ~np.all(np.isnan(X) | (X == 0), axis=0)]
    
    if X.shape[1] == 0:
        raise ValueError("All columns contain only NaN or zero values. Cannot proceed with the analysis.")
    
    print(f"Shape of X after preprocessing: {X.shape}")
    print(f"Number of NaN values: {np.isnan(X).sum()}")
    
    # Impute missing values
    imputer = SimpleImputer(strategy='mean')
    X_imputed = imputer.fit_transform(X)
    
    print(f"Shape of X after imputation: {X_imputed.shape}")
    print(f"Number of NaN values after imputation: {np.isnan(X_imputed).sum()}")
    
    # Dimensionality reduction
    pca = PCA(n_components=0.95)
    X_pca = pca.fit_transform(X_imputed)
    
    print(f"Shape of X after PCA: {X_pca.shape}")
    
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X_pca)
    
    print(f"Shape of X after scaling: {X_scaled.shape}")
    
    return X_scaled, scaler, pca

# Prepare sequences
def prepare_sequences(X_scaled, n_input):
    if X_scaled.shape[1] == 1:
        return tf.data.Dataset.from_tensor_slices((
            tf.constant(np.array([X_scaled[i:i+n_input].flatten() for i in range(len(X_scaled) - n_input)])),
            tf.constant(np.array([X_scaled[i+n_input, 0] for i in range(len(X_scaled) - n_input)]))
        )).repeat()
    else:
        return tf.data.Dataset.from_tensor_slices((
            tf.constant(np.array([X_scaled[i:i+n_input] for i in range(len(X_scaled) - n_input)])),
            tf.constant(np.array([X_scaled[i+n_input, :6] for i in range(len(X_scaled) - n_input)]))
        )).repeat()

# Define model building function
def create_model(input_shape, units=64, dropout_rate=0.3, learning_rate=0.001):
    if input_shape[1] == 1:
        # Simpler model for single feature
        model = Sequential([
            LSTM(units, activation='tanh', input_shape=input_shape),
            BatchNormalization(),
            Dropout(dropout_rate),
            Dense(32, activation='swish', kernel_regularizer=l2(0.01)),
            BatchNormalization(),
            Dense(16, activation='swish', kernel_regularizer=l2(0.01)),
            BatchNormalization(),
            Dense(6)
        ])
    else:
        # Original complex model for multiple features
        model = Sequential([
            Conv1D(filters=64, kernel_size=3, activation='swish', input_shape=input_shape),
            MaxPooling1D(pool_size=2),
            Bidirectional(LSTM(units, activation='tanh', return_sequences=True, kernel_regularizer=l2(0.01))),
            BatchNormalization(),
            Dropout(dropout_rate),
            Bidirectional(GRU(units//2, activation='tanh', return_sequences=True, kernel_regularizer=l2(0.01))),
            BatchNormalization(),
            Dropout(dropout_rate),
            Flatten(),
            Dense(32, activation='swish', kernel_regularizer=l2(0.01)),
            BatchNormalization(),
            Dense(16, activation='swish', kernel_regularizer=l2(0.01)),
            BatchNormalization(),
            Dense(6)
        ])
    model.compile(optimizer=Adam(learning_rate=learning_rate), loss='mse', metrics=['mae'])
    return model

# Custom loss function
def weighted_mse(y_true, y_pred):
    weights = tf.range(1, 7, dtype=tf.float32) / 21  # Increasing weights for each number
    return tf.reduce_mean(weights * tf.square(y_true - y_pred))

# Plotting function
def plot_results(history, y_test, y_pred, predicted_numbers):
    # Plot training & validation loss values
    plt.figure(figsize=(12, 8))
    plt.subplot(2, 2, 1)
    plt.plot(history.history['loss'])
    plt.plot(history.history['val_loss'])
    plt.title('Model loss')
    plt.ylabel('Loss')
    plt.xlabel('Epoch')
    plt.legend(['Train', 'Validation'], loc='upper right')

    # Plot true vs predicted values
    plt.subplot(2, 2, 2)
    y_test_flat = y_test.flatten()
    y_pred_flat = y_pred.flatten()
    
    print(f"Shape of y_test: {y_test.shape}")
    print(f"Shape of y_pred: {y_pred.shape}")
    print(f"Length of y_test_flat: {len(y_test_flat)}")
    print(f"Length of y_pred_flat: {len(y_pred_flat)}")
    
    min_length = min(len(y_test_flat), len(y_pred_flat))
    plt.scatter(y_test_flat[:min_length], y_pred_flat[:min_length])
    plt.plot([y_test_flat[:min_length].min(), y_test_flat[:min_length].max()], 
             [y_test_flat[:min_length].min(), y_test_flat[:min_length].max()], 'r--', lw=2)
    plt.title('True vs Predicted')
    plt.xlabel('True Values')
    plt.ylabel('Predictions')

    # Plot predicted numbers
    plt.subplot(2, 2, 3)
    plt.bar(range(1, 7), predicted_numbers)
    plt.title('Predicted Numbers for Next Draw')
    plt.xlabel('Position')
    plt.ylabel('Number')

    plt.tight_layout()
    plt.show()

# Main execution
if __name__ == "__main__":
    try:
        # Load and preprocess data
        X_scaled, scaler, pca = load_and_preprocess_data('combinations_date.json')
        
        n_features = X_scaled.shape[1]
        n_samples = X_scaled.shape[0]
        n_input = min(100, n_samples - 1) if n_features > 1 else min(1000, n_samples - 1)
        input_shape = (n_input, n_features)
        
        # Prepare dataset
        dataset = prepare_sequences(X_scaled, n_input)
        dataset = dataset.shuffle(buffer_size=1000).batch(32).prefetch(tf.data.AUTOTUNE)
        
        # Implement TimeSeriesSplit for cross-validation
        tscv = TimeSeriesSplit(n_splits=5, test_size=max(1, len(X_scaled) // 10))
        
        # Define the hyperparameter space
        param_dist = {
            'units': [32, 64, 128],
            'dropout_rate': [0.2, 0.3, 0.4],
            'learning_rate': [0.0001, 0.001, 0.01],
            'batch_size': [16, 32, 64],
            'epochs': [30, 50, 100]
        }
        
        # Perform manual hyperparameter tuning
        best_score = float('inf')
        best_params = {}
        
        for _ in range(10):  # Number of random search iterations
            params = {k: np.random.choice(v) for k, v in param_dist.items()}
            model = create_model(input_shape=input_shape, units=int(params['units']), dropout_rate=params['dropout_rate'], learning_rate=params['learning_rate'])
            
            early_stopping = EarlyStopping(monitor='val_loss', patience=20, restore_best_weights=True)
            reduce_lr = ReduceLROnPlateau(monitor='val_loss', factor=0.2, patience=5, min_lr=0.0001)
            
            history = model.fit(X_scaled, X_scaled[:, :6], epochs=params['epochs'], batch_size=params['batch_size'], validation_split=0.2, callbacks=[early_stopping, reduce_lr])
            
            val_loss = history.history['val_loss'][-1]
            if val_loss < best_score:
                best_score = val_loss
                best_params = params
        
        print("Best parameters:", best_params)
        
        # Use the best parameters to create and train the final model
        final_model = create_model(input_shape=input_shape, units=int(best_params['units']), dropout_rate=best_params['dropout_rate'], learning_rate=best_params['learning_rate'])
        
        early_stopping = EarlyStopping(monitor='val_loss', patience=20, restore_best_weights=True)
        reduce_lr = ReduceLROnPlateau(monitor='val_loss', factor=0.2, patience=5, min_lr=0.0001)
        
        history = final_model.fit(X_scaled, X_scaled[:, :6], epochs=best_params['epochs'], batch_size=best_params['batch_size'], validation_split=0.2, callbacks=[early_stopping, reduce_lr])
        
        # Generate prediction for the next combination
        last_sequence = X_scaled[-n_input:].reshape((1, n_input, n_features))
        prediction = final_model.predict(last_sequence)
        
        # Process prediction
        predicted_numbers = prediction[0]
        predicted_numbers = np.round(predicted_numbers).astype(int)
        predicted_numbers = np.clip(predicted_numbers, 1, 55)  # Ensure numbers are within valid range
        predicted_numbers = np.unique(predicted_numbers)  # Remove duplicates
        
        # If we have less than 6 unique numbers, add random numbers until we have 6
        while len(predicted_numbers) < 6:
            new_number = np.random.randint(1, 56)
            if new_number not in predicted_numbers:
                predicted_numbers = np.append(predicted_numbers, new_number)
        
        # Sort the predicted numbers
        predicted_numbers.sort()
        
        print("Predicted numbers for the next draw:", predicted_numbers)
        
        # Plot results
        if n_features == 1:
            reshaped_X = np.array([X_scaled[i:i+n_input] for i in range(n_samples - n_input + 1)])
            y_pred = final_model.predict(reshaped_X)
            y_test = X_scaled[n_input-1:, :6]
        else:
            y_pred = final_model.predict(X_scaled)
            y_test = X_scaled[:, :6]

        print(f"Shape of y_test before plotting: {y_test.shape}")
        print(f"Shape of y_pred before plotting: {y_pred.shape}")
        plot_results(history, y_test, y_pred, predicted_numbers)

        # Error Analysis
        if n_features == 1:
            reshaped_X = np.array([X_scaled[i:i+n_input] for i in range(n_samples - n_input + 1)])
            y_pred = final_model.predict(reshaped_X)
            y_test = X_scaled[n_input-1:, :6]
        else:
            y_pred = final_model.predict(X_scaled)
            y_test = X_scaled[:, :6]

        mape = np.mean(np.abs((y_test - y_pred) / y_test)) * 100
        smape = np.mean(2 * np.abs(y_pred - y_test) / (np.abs(y_pred) + np.abs(y_test))) * 100
        print(f"MAPE: {mape:.2f}%")
        print(f"SMAPE: {smape:.2f}%")

        # Uncertainty Estimation using Monte Carlo Dropout
        mc_predictions = []
        for _ in range(100):
            if n_features == 1:
                mc_pred = final_model(last_sequence.reshape((1, n_input, n_features)), training=True)
            else:
                mc_pred = final_model(last_sequence.reshape((1, n_input, n_features)), training=True)
            mc_predictions.append(mc_pred.numpy())
        mc_mean = np.mean(mc_predictions, axis=0)
        mc_std = np.std(mc_predictions, axis=0)
        print("Monte Carlo Dropout Results:")
        print(f"Mean prediction: {mc_mean}")
        print(f"Standard deviation: {mc_std}")

        # Feature importance
        feature_importance = np.abs(final_model.layers[-1].get_weights()[0]).mean(axis=1)
        feature_names = ['Feature ' + str(i) for i in range(n_features)]
        plt.figure(figsize=(10, 6))
        plt.bar(feature_names, feature_importance)
        plt.title('Feature Importance')
        plt.xlabel('Features')
        plt.ylabel('Importance')
        plt.xticks(rotation=90)
        plt.tight_layout()
        plt.savefig('feature_importance.png')
        plt.close()
        print("Feature importance plot saved as 'feature_importance.png'")

        # Seasonality and Trend Analysis
        time_series = X_scaled[:, 0]  # Assuming the first feature is the main time series
        result = seasonal_decompose(time_series, model='additive', period=30)
        fig, (ax1, ax2, ax3, ax4) = plt.subplots(4, 1, figsize=(12, 16))

        ax1.plot(result.observed)
        ax1.set_title('Observed')
        ax1.set_xlabel('')

        ax2.plot(result.trend)
        ax2.set_title('Trend')
        ax2.set_xlabel('')

        ax3.plot(result.seasonal)
        ax3.set_title('Seasonal')
        ax3.set_xlabel('')

        ax4.plot(result.resid)
        ax4.set_title('Residual')

        plt.tight_layout()
        plt.savefig('time_series_decomposition.png')
        plt.close()
        print("Time series decomposition plot saved as 'time_series_decomposition.png'")

        # Residual Analysis
        residuals = y_test - y_pred
        plt.figure(figsize=(10, 6))
        plt.scatter(y_pred.flatten(), residuals.flatten())
        plt.title('Residual Plot')
        plt.xlabel('Predicted Values')
        plt.ylabel('Residuals')
        plt.axhline(y=0, color='r', linestyle='--')
        plt.tight_layout()
        plt.savefig('residual_plot.png')
        plt.close()
        print("Residual plot saved as 'residual_plot.png'")

        # Model Summary
        final_model.summary()

        print("Analysis complete. Check the generated plots for insights.")
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        import traceback
        traceback.print_exc()