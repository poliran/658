import pickle
import joblib
import numpy as np
import pandas as pd
import json
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout, Bidirectional, BatchNormalization, GRU, Conv1D, MaxPooling1D, Flatten, Reshape, Activation
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau
from tensorflow.keras.regularizers import l2
from tensorflow.keras.optimizers import Adam
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import KFold
from sklearn.decomposition import PCA
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from statsmodels.tsa.seasonal import seasonal_decompose
from statsmodels.tsa.stattools import acf, pacf
from sklearn.impute import SimpleImputer
import logging

class LotteryPredictor:
    def __init__(self, file_path):
        self.file_path = file_path
        self.X_scaled = None
        self.scaler = None
        self.pca = None
        self.binary_model = None
        self.categorical_model = None

    def load_and_preprocess_data(self):
        try:
            with open(self.file_path, 'r') as f:
                data = json.load(f)
            
            df = pd.DataFrame(data)
            print("Loaded DataFrame columns:", df.columns)
            print("DataFrame info:")
            df.info()
            
            df['DRAW DATE'] = pd.to_datetime(df['DRAW DATE'])
            df = df.sort_values('DRAW DATE')
            
            engineered_features = self._engineer_features(df)
            
            if engineered_features.empty:
                logging.warning("No engineered features were created.")
            
            combinations = np.array([num for d in data for num in d['COMBINATIONS']])
            combinations_reshaped = combinations.reshape(-1, 6)
            
            engineered_features_repeated = np.repeat(engineered_features.values, 6, axis=0)
            engineered_features_repeated = engineered_features_repeated[:len(combinations_reshaped) * 6].reshape(-1, 6 * engineered_features.shape[1])
            
            X = np.hstack((combinations_reshaped, engineered_features_repeated))
            X = X.astype(float)
            X = np.nan_to_num(X, nan=np.nan)
            X = X[:, ~np.all(np.isnan(X) | (X == 0), axis=0)]
            
            if X.shape[1] == 0:
                raise ValueError("All columns contain only NaN or zero values. Cannot proceed with the analysis.")
            
            imputer = SimpleImputer(strategy='mean')
            X_imputed = imputer.fit_transform(X)
            
            pca = PCA(n_components=0.95)
            X_pca = pca.fit_transform(X_imputed)
            
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X_pca)
            
            self.X_scaled = X_scaled
            self.scaler = scaler
            self.pca = pca
            
            return X_scaled

        except Exception as e:
            logging.error(f"Error in load_and_preprocess_data: {str(e)}")
            raise

    def _engineer_features(self, df):
        engineered_features = pd.DataFrame()
        
        # Basic date features
        engineered_features['day_of_week'] = df['DRAW DATE'].dt.dayofweek
        engineered_features['month'] = df['DRAW DATE'].dt.month
        engineered_features['year'] = df['DRAW DATE'].dt.year
        engineered_features['day_of_month'] = df['DRAW DATE'].dt.day
        engineered_features['quarter'] = df['DRAW DATE'].dt.quarter
        engineered_features['is_weekend'] = df['DRAW DATE'].dt.dayofweek.isin([5, 6]).astype(int)
        engineered_features['days_since_last_draw'] = df['DRAW DATE'].diff().dt.days
        
        # Check if NUMBER columns exist
        number_columns = [col for col in df.columns if col.startswith('NUMBER')]
        
        if number_columns:
            # Calculate rolling statistics for the last 5 draws
            for col in number_columns:
                engineered_features[f'rolling_mean_{col}'] = df[col].rolling(window=5).mean()
                engineered_features[f'rolling_std_{col}'] = df[col].rolling(window=5).std()
            
            # Calculate the sum and mean of all numbers in each draw
            engineered_features['sum_of_numbers'] = df[number_columns].sum(axis=1)
            engineered_features['mean_of_numbers'] = df[number_columns].mean(axis=1)
            
            # Calculate the difference between consecutive numbers in each draw
            for i in range(len(number_columns) - 1):
                engineered_features[f'diff_{i+1}_{i+2}'] = df[number_columns[i+1]] - df[number_columns[i]]
        else:
            logging.warning("No NUMBER columns found in the DataFrame. Some features will not be calculated.")
        
        return engineered_features

    def prepare_classification_data(self, categorical=False):
        if categorical:
            y = np.zeros((self.X_scaled.shape[0], 6, 58))
            for i, combination in enumerate(self.X_scaled[:, :6]):
                for j, num in enumerate(combination):
                    y[i, j, int(num) - 1] = 1
        else:
            y = np.zeros((self.X_scaled.shape[0], 58))
            for i, combination in enumerate(self.X_scaled[:, :6]):
                y[i, combination.astype(int) - 1] = 1
        return self.X_scaled, y

    def create_model(self, input_shape, units=64, dropout_rate=0.3, learning_rate=0.001, loss_type='binary'):
        if loss_type == 'categorical':
            model = Sequential([
                Flatten(input_shape=input_shape),
                Dense(units, activation='relu'),
                BatchNormalization(),
                Dropout(dropout_rate),
                Dense(32, activation='relu'),
                BatchNormalization(),
                Dense(6 * 58, activation='relu'),
                Reshape((6, 58)),
                Activation('softmax')
            ])
        else:
            model = Sequential([
                Flatten(input_shape=input_shape),
                Dense(units, activation='relu'),
                BatchNormalization(),
                Dropout(dropout_rate),
                Dense(32, activation='relu'),
                BatchNormalization(),
                Dense(58, activation='sigmoid')
            ])
        
        loss = 'categorical_crossentropy' if loss_type == 'categorical' else 'binary_crossentropy'
        
        model.compile(optimizer=Adam(learning_rate=learning_rate), 
                      loss=loss,
                      metrics=['accuracy'])
        return model

    def lottery_accuracy(self, y_true, y_pred, categorical=False):
        print(f"y_true shape: {y_true.shape}")
        print(f"y_pred shape: {y_pred.shape}")
        if categorical:
            y_true_set = set(np.argmax(y_true, axis=2).flatten())
            y_pred_set = set(np.argmax(y_pred, axis=2).flatten())
        else:
            y_true_set = set(np.where(y_true == 1)[1])
            y_pred_set = set(np.argsort(y_pred.flatten())[-6:])
        print(f"y_true_set: {y_true_set}")
        print(f"y_pred_set: {y_pred_set}")
        return len(y_true_set.intersection(y_pred_set)) / 6

    def cross_validate_model(self, X, y, n_splits=5, model_type='binary'):
        kf = KFold(n_splits=n_splits, shuffle=True, random_state=42)
        scores = []

        for fold, (train_index, val_index) in enumerate(kf.split(X)):
            X_train, X_val = X[train_index], X[val_index]
            y_train, y_val = y[train_index], y[val_index]

            print(f"X_train shape: {X_train.shape}")
            print(f"y_train shape: {y_train.shape}")
            print(f"X_val shape: {X_val.shape}")
            print(f"y_val shape: {y_val.shape}")

            model = self.create_model(X_train.shape[1:], loss_type=model_type)
            history = model.fit(X_train, y_train, epochs=100, batch_size=32, validation_data=(X_val, y_val),
                                callbacks=[EarlyStopping(patience=10), ReduceLROnPlateau(factor=0.2, patience=5)])
            
            val_pred = model.predict(X_val)
            print(f"val_pred shape: {val_pred.shape}")
            
            score = self.lottery_accuracy(y_val, val_pred, categorical=(model_type == 'categorical'))
            scores.append(score)
            print(f"Fold {fold + 1} Accuracy: {score:.4f}")

        print(f"Mean Accuracy: {np.mean(scores):.4f} (+/- {np.std(scores):.4f})")
        return scores

    def train_models(self):
        X_binary, y_binary = self.prepare_classification_data(categorical=False)
        X_categorical, y_categorical = self.prepare_classification_data(categorical=True)

        self.binary_model = self.create_model(X_binary.shape[1:], loss_type='binary')
        self.binary_history = self.binary_model.fit(X_binary, y_binary, epochs=100, batch_size=32, validation_split=0.2, 
                                                    callbacks=[EarlyStopping(patience=20), ReduceLROnPlateau(factor=0.2, patience=5)])

        self.categorical_model = self.create_model(X_categorical.shape[1:], loss_type='categorical')
        self.categorical_history = self.categorical_model.fit(X_categorical, y_categorical, epochs=100, batch_size=32, validation_split=0.2, 
                                                              callbacks=[EarlyStopping(patience=20), ReduceLROnPlateau(factor=0.2, patience=5)])

    def predict_next_draw(self):
        last_sequence = self.X_scaled[-1].reshape((1, -1))
        binary_prediction = self.binary_model.predict(last_sequence)
        categorical_prediction = self.categorical_model.predict(last_sequence.reshape((1,) + self.X_scaled.shape[1:]))

        binary_numbers = np.argsort(binary_prediction[0])[-6:] + 1
        categorical_numbers = np.argsort(categorical_prediction[0].sum(axis=0))[-6:] + 1

        return (sorted(binary_numbers), binary_prediction[0]), (sorted(categorical_numbers), categorical_prediction[0])

    def plot_results(self):
        self._plot_accuracy()
        self._plot_loss()
        self._plot_predicted_frequencies()

    def _plot_accuracy(self):
        plt.figure(figsize=(10, 6))
        plt.plot(self.binary_history.history['accuracy'], label='Binary Model Accuracy')
        plt.plot(self.binary_history.history['val_accuracy'], label='Binary Model Validation Accuracy')
        plt.title('Binary Model Accuracy and Validation Accuracy')
        plt.xlabel('Epoch')
        plt.ylabel('Accuracy')
        plt.legend(loc='lower right')
        plt.show()

        plt.figure(figsize=(10, 6))
        plt.plot(self.categorical_history.history['accuracy'], label='Categorical Model Accuracy')
        plt.plot(self.categorical_history.history['val_accuracy'], label='Categorical Model Validation Accuracy')
        plt.title('Categorical Model Accuracy and Validation Accuracy')
        plt.xlabel('Epoch')
        plt.ylabel('Accuracy')
        plt.legend(loc='lower right')
        plt.show()

    def _plot_loss(self):
        plt.figure(figsize=(10, 6))
        plt.plot(self.binary_history.history['loss'], label='Binary Model Loss')
        plt.plot(self.binary_history.history['val_loss'], label='Binary Model Validation Loss')
        plt.title('Binary Model Loss and Validation Loss')
        plt.xlabel('Epoch')
        plt.ylabel('Loss')
        plt.legend(loc='upper right')
        plt.show()

        plt.figure(figsize=(10, 6))
        plt.plot(self.categorical_history.history['loss'], label='Categorical Model Loss')
        plt.plot(self.categorical_history.history['val_loss'], label='Categorical Model Validation Loss')
        plt.title('Categorical Model Loss and Validation Loss')
        plt.xlabel('Epoch')
        plt.ylabel('Loss')
        plt.legend(loc='upper right')
        plt.show()

    def _plot_predicted_frequencies(self):
        last_sequence = self.X_scaled[-1].reshape((1, -1))
        binary_prediction = self.binary_model.predict(last_sequence)

        plt.figure(figsize=(15, 6))
        plt.bar(range(1, 59), binary_prediction[0])
        plt.title('Predicted Frequencies for the Next Draw (Binary Model)')
        plt.xlabel('Number')
        plt.ylabel('Probability')
        plt.xticks(range(1, 59, 5))  # Show every 5th number on x-axis for readability
        plt.show()

        # Optionally, you can add a plot for the top 6 predicted numbers
        top_6_indices = np.argsort(binary_prediction[0])[-6:]
        top_6_probs = binary_prediction[0][top_6_indices]

        plt.figure(figsize=(10, 6))
        plt.bar(top_6_indices + 1, top_6_probs)
        plt.title('Top 6 Predicted Numbers for the Next Draw (Binary Model)')
        plt.xlabel('Number')
        plt.ylabel('Probability')
        plt.xticks(top_6_indices + 1)
        plt.show()

    def save_models(self):
        self.binary_model.save('binary_model.keras')
        self.categorical_model.save('categorical_model.keras')
        joblib.dump(self.scaler, 'scaler.pkl')
        joblib.dump(self.pca, 'pca.pkl')
        with open('binary_model_history.pkl', 'wb') as f:
            pickle.dump(self.binary_history.history, f)
        with open('categorical_model_history.pkl', 'wb') as f:
            pickle.dump(self.categorical_history.history, f)

def main():
    logging.basicConfig(level=logging.INFO)
    try:
        predictor = LotteryPredictor('combinations_date.json')
        predictor.load_and_preprocess_data()

        print("Binary Model Cross-Validation:")
        X_binary, y_binary = predictor.prepare_classification_data(categorical=False)
        print(f"X_binary shape: {X_binary.shape}")
        print(f"y_binary shape: {y_binary.shape}")
        binary_cv_scores = predictor.cross_validate_model(X_binary, y_binary, model_type='binary')

        print("\nCategorical Model Cross-Validation:")
        X_categorical, y_categorical = predictor.prepare_classification_data(categorical=True)
        print(f"X_categorical shape: {X_categorical.shape}")
        print(f"y_categorical shape: {y_categorical.shape}")
        categorical_cv_scores = predictor.cross_validate_model(X_categorical, y_categorical, model_type='categorical')

        predictor.train_models()
        (binary_numbers, binary_probs), (categorical_numbers, categorical_probs) = predictor.predict_next_draw()

        print("Binary Model Predicted numbers for the next draw:", binary_numbers)
        print("Categorical Model Predicted numbers for the next draw:", categorical_numbers)

        predictor.plot_results()
        predictor.save_models()

    except Exception as e:
        logging.error(f"An error occurred: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()