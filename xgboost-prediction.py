import pandas as pd
import numpy as np
from collections import Counter
from xgboost import XGBRegressor
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error
import matplotlib.pyplot as plt
from datetime import timedelta
import logging

logging.basicConfig(level=logging.INFO)

class LotteryPredictor:
    def __init__(self):
        self.df = None
        self.models = []
        self.scalers = []
        self.feature_columns = ['day_of_week', 'month', 'year', 'draw_interval',
                                'diff_1', 'diff_2', 'diff_3', 'diff_4', 'diff_5',
                                'increasing_1', 'increasing_2', 'increasing_3', 'increasing_4', 'increasing_5',
                                'number_range', 'number_mean', 'number_std']

    def load_and_preprocess_data(self, file_path):
        try:
            df = pd.read_csv(file_path, sep=r'\s{2,}', engine='python', skiprows=1, header=None)
            df.columns = ["COMBINATIONS", "DRAW DATE", "JACKPOT (PHP)", "WINNERS"]
            df["DRAW DATE"] = pd.to_datetime(df["DRAW DATE"], format="%m/%d/%Y", errors='coerce')
            df = df.sort_values(by="DRAW DATE")
            df['draw_interval'] = df["DRAW DATE"].diff().dt.days.fillna(0)
            df[['num1', 'num2', 'num3', 'num4', 'num5', 'num6']] = df['COMBINATIONS'].str.extract(r'(\d+)-(\d+)-(\d+)-(\d+)-(\d+)-(\d+)', expand=True).astype(int)
            df['day_of_week'] = df['DRAW DATE'].dt.dayofweek
            df['month'] = df['DRAW DATE'].dt.month
            df['year'] = df['DRAW DATE'].dt.year
            self.df = self.create_correlation_features(df)
            logging.info("Data loaded and preprocessed successfully.")
            return self.df
        except Exception as e:
            logging.error(f"Error in load_and_preprocess_data: {str(e)}")
            raise

    def create_correlation_features(self, df):
        df_features = df.copy()
        for i in range(1, 6):
            df_features[f'diff_{i}'] = df_features[f'num{i+1}'] - df_features[f'num{i}']
        for i in range(1, 6):
            df_features[f'increasing_{i}'] = (df_features[f'num{i+1}'] > df_features[f'num{i}']).astype(int)
            df_features['number_range'] = df_features[['num1', 'num2', 'num3', 'num4', 'num5', 'num6']].max(axis=1) - df_features[['num1', 'num2', 'num3', 'num4', 'num5', 'num6']].min(axis=1)
            df_features['number_mean'] = df_features[['num1', 'num2', 'num3', 'num4', 'num5', 'num6']].mean(axis=1)
            df_features['number_std'] = df_features[['num1', 'num2', 'num3', 'num4', 'num5', 'num6']].std(axis=1)
        return df_features

    def analyze_correlations(self):
        corr_matrix = self.df[self.feature_columns].corr()
        plt.figure(figsize=(12, 10))
        plt.imshow(corr_matrix, cmap='coolwarm', interpolation='nearest')
        plt.colorbar()
        plt.title('Correlation Matrix')
        plt.show()    

    def analyze_number_frequency(self):
        number_frequency = Counter(self.df[['num1', 'num2', 'num3', 'num4', 'num5', 'num6']].values.ravel())
        most_common_numbers = number_frequency.most_common(10)
        least_common_numbers = sorted(number_frequency.items(), key=lambda item: item[1])[:10]
        logging.info(f"Most common numbers: {most_common_numbers}")
        logging.info(f"Least common numbers: {least_common_numbers}")
        return number_frequency

    def train_models(self):
        X = self.df[self.feature_columns]
        for i in range(1, 7):
            y = self.df[f'num{i}']
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
            scaler = StandardScaler()
            X_train_scaled = scaler.fit_transform(X_train)
            X_test_scaled = scaler.transform(X_test)
            model = XGBRegressor(random_state=42)
            model.fit(X_train_scaled, y_train)
            self.models.append(model)
            self.scalers.append(scaler)
            train_predictions = model.predict(X_train_scaled)
            test_predictions = model.predict(X_test_scaled)
            train_mse = mean_squared_error(y_train, train_predictions)
            test_mse = mean_squared_error(y_test, test_predictions)
            logging.info(f"Model {i} - Train MSE: {train_mse:.4f}, Test MSE: {test_mse:.4f}")

    def generate_predictions(self, next_draw_features):
        if len(self.models) != 6 or len(self.scalers) != 6:
            raise ValueError("Models and scalers not properly initialized. Call train_models() first.")
        
        if not isinstance(next_draw_features, pd.DataFrame) or not all(col in next_draw_features.columns for col in self.feature_columns):
            raise ValueError(f"next_draw_features must be a DataFrame with columns: {self.feature_columns}")

        predictions = []
        for i in range(6):
            scaled_features = self.scalers[i].transform(next_draw_features)
            pred = self.models[i].predict(scaled_features)[0]
            predictions.append(pred)
        return np.array(predictions)

    def generate_unique_number(self, existing_numbers, top_numbers, bottom_numbers):
        all_numbers = set(range(1, 59))  # Assuming the lottery numbers range from 1 to 58
        available_numbers = list(all_numbers - set(existing_numbers))
        
        if not available_numbers:
            raise ValueError("No unique numbers available")
        
        # Prioritize numbers from top_numbers and bottom_numbers
        priority_numbers = [n for n in available_numbers if n in top_numbers or n in bottom_numbers]
        
        if priority_numbers:
            return np.random.choice(priority_numbers)
        else:
            return np.random.choice(available_numbers)

    def adjust_prediction(self, pred, last_combination, top_numbers, bottom_numbers):
        #pred = np.round(pred).astype(int)  # Round predictions to nearest integeri
        pred = np.clip(pred, 1, 58).astype(int)
        unique_pred = []
        
        for num in pred:
            if num < 1 or num > 58:  # Ensure number is within valid range
                num = np.random.randint(1, 59)
            
            while num in unique_pred or num in last_combination:
                num = self.generate_unique_number(unique_pred + last_combination, top_numbers, bottom_numbers)
            
            unique_pred.append(num)
        
        # Ensure we have exactly 6 unique numbers
        while len(unique_pred) < 6:
            num = self.generate_unique_number(unique_pred + last_combination, top_numbers, bottom_numbers)
            unique_pred.append(num)
        
        return sorted(unique_pred)

    def plot_number_frequency(self, number_frequency):
        numbers, frequencies = zip(*sorted(number_frequency.items()))
        plt.figure(figsize=(12, 6))
        plt.bar(numbers, frequencies)
        plt.title('Frequency of Numbers in Ultra Lotto 6/58')
        plt.xlabel('Number')
        plt.ylabel('Frequency')
        plt.show()

def main():
    predictor = LotteryPredictor()
    df = predictor.load_and_preprocess_data('658.txt')
    number_frequency = predictor.analyze_number_frequency()
    predictor.plot_number_frequency(number_frequency)
    predictor.train_models()

    last_draw_date = df['DRAW DATE'].iloc[-1]
    last_draw_interval = df['draw_interval'].iloc[-1]
    next_draw_date = last_draw_date + timedelta(days=last_draw_interval)

    next_draw_features = pd.DataFrame({
        'day_of_week': [next_draw_date.dayofweek],
        'month': [next_draw_date.month],
        'year': [next_draw_date.year],
        'draw_interval': [last_draw_interval],
        'diff_1': [0], 'diff_2': [0], 'diff_3': [0], 'diff_4': [0], 'diff_5': [0],
        'increasing_1': [0], 'increasing_2': [0], 'increasing_3': [0], 'increasing_4': [0], 'increasing_5': [0],
        'number_range': [0], 'number_mean': [0], 'number_std': [0]
    })

    raw_predictions = predictor.generate_predictions(next_draw_features)
    last_combination = df.iloc[-1][['num1', 'num2', 'num3', 'num4', 'num5', 'num6']].tolist()
    top_numbers = [num for num, _ in number_frequency.most_common(10)]
    bottom_numbers = [num for num, _ in number_frequency.most_common()[-10:]]
    final_prediction = predictor.adjust_prediction(raw_predictions, last_combination, top_numbers, bottom_numbers)

    logging.info(f"Predicted numbers for next draw ({next_draw_date.date()}): {final_prediction}")

if __name__ == "__main__":
    main()

