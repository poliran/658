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
import matplotlib.pyplot as plt
import seaborn as sns

# Configure logging
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

    def load_and_preprocess_data(self, file_path: str) -> pd.DataFrame:
        try:
            df = pd.read_csv(file_path, sep=r'\s{2,}', engine='python', skiprows=1, header=None)
            df.columns = ["COMBINATIONS", "DRAW DATE"]
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

    def create_correlation_features(self, df: pd.DataFrame) -> pd.DataFrame:
        df_features = df.copy()
        for i in range(1, 6):
            df_features[f'diff_{i}'] = df_features[f'num{i+1}'] - df_features[f'num{i}']
            df_features[f'increasing_{i}'] = (df_features[f'num{i+1}'] > df_features[f'num{i}']).astype(int)
        df_features['number_range'] = df_features[['num1', 'num2', 'num3', 'num4', 'num5', 'num6']].max(axis=1) - df_features[['num1', 'num2', 'num3', 'num4', 'num5', 'num6']].min(axis=1)
        df_features['number_mean'] = df_features[['num1', 'num2', 'num3', 'num4', 'num5', 'num6']].mean(axis=1)
        df_features['number_std'] = df_features[['num1', 'num2', 'num3', 'num4', 'num5', 'num6']].std(axis=1)

        # Additional feature engineering
        df_features['num_frequencies'] = df_features.apply(lambda row: sum([row['num1'], row['num2'], row['num3'], row['num4'], row['num5'], row['num6']].count(x) for x in range(1, 59)), axis=1)
        df_features['odd_numbers'] = df_features.apply(lambda row: sum([x % 2 != 0 for x in [row['num1'], row['num2'], row['num3'], row['num4'], row['num5'], row['num6']]]), axis=1)
        df_features['prime_numbers'] = df_features.apply(lambda row: sum([self.is_prime(x) for x in [row['num1'], row['num2'], row['num3'], row['num4'], row['num5'], row['num6']]]), axis=1)
        df_features['consecutive_numbers'] = df_features.apply(lambda row: sum([x + 1 == y for x, y in zip([row['num1'], row['num2'], row['num3'], row['num4'], row['num5']], [row['num2'], row['num3'], row['num4'], row['num5'], row['num6']])]), axis=1)
        df_features['number_pairs'] = df_features.apply(lambda row: sum([x == y for x, y in zip([row['num1'], row['num2'], row['num3'], row['num4'], row['num5']], [row['num2'], row['num3'], row['num4'], row['num5'], row['num6']])]), axis=1)
        df_features['number_triples'] = df_features.apply(lambda row: sum([x == y == z for x, y, z in zip([row['num1'], row['num2'], row['num3']], [row['num2'], row['num3'], row['num4']], [row['num3'], row['num4'], row['num5']])]), axis=1)
        # Number ranking feature
        df_features['num_rank_1'] = df_features['num1'].rank(method='dense', ascending=False)
        df_features['num_rank_2'] = df_features['num2'].rank(method='dense', ascending=False)
        df_features['num_rank_3'] = df_features['num3'].rank(method='dense', ascending=False)
        df_features['num_rank_4'] = df_features['num4'].rank(method='dense', ascending=False)
        df_features['num_rank_5'] = df_features['num5'].rank(method='dense', ascending=False)
        df_features['num_rank_6'] = df_features['num6'].rank(method='dense', ascending=False)

        return df_features

    def is_prime(self, n: int) -> bool:
        if n <= 1:
            return False
        if n <= 3:
            return True
        if n % 2 == 0 or n % 3 == 0:
            return False
        i = 5
        while i * i <= n:
            if n % i == 0 or n % (i + 2) == 0:
                return False
            i += 6
        return True

    def _validate_models_and_features(self, next_draw_features):
            """
            Validate the models and input features.

            Args:
                next_draw_features (pd.DataFrame): The input features for prediction.
            """
            if not isinstance(next_draw_features, pd.DataFrame):
                raise ValueError("Input features must be a pandas DataFrame")
            
            # Validate the shape of the input features
            required_columns = ['day_of_week', 'month', 'year', 'draw_interval']
            if set(required_columns).issubset(set(next_draw_features.columns)):
                return next_draw_features
            else:
                raise ValueError(f"Missing columns: {required_columns}")


    def analyze_correlations(self) -> None:
        corr_matrix = self.df[self.feature_columns].corr()
        plt.figure(figsize=(12, 10))
        plt.imshow(corr_matrix, cmap='coolwarm', interpolation='nearest')
        plt.colorbar()
        plt.title('Correlation Matrix')
        plt.show()    

    def analyze_number_frequency(self) -> Counter:
        number_frequency = Counter(self.df[['num1', 'num2', 'num3', 'num4', 'num5', 'num6']].values.ravel())
        most_common_numbers = number_frequency.most_common(10)
        least_common_numbers = sorted(number_frequency.items(), key=lambda item: item[1])[:10]
        logging.info(f"Most common numbers: {most_common_numbers}")
        logging.info(f"Least common numbers: {least_common_numbers}")
        return number_frequency

    def train_models(self) -> None:
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

    def generate_predictions(self, next_draw_features: pd.DataFrame) -> np.ndarray:
        self._validate_models_and_features(next_draw_features)

        top_num = [58, 2, 25, 50, 42, 56, 10, 47, 44, 5, 29, 19, 37, 9, 48, 30, 11, 3, 43, 46, 14, 34, 21, 55, 6, 4, 32, 40, 35]
        predictions = []

        for i in range(6):
            scaled_features = self.scalers[i].transform(next_draw_features)
            pred = self.models[i].predict(scaled_features)[0]
            
            # Prioritize top numbers
            if pred in top_num and pred not in predictions:
                predictions.append(pred)
            else:
                # Find the closest top number to the prediction that is not already in predictions
                closest_top_num = min([num for num in top_num if num not in predictions], key=lambda x: abs(x - pred), default=None)
                if closest_top_num is not None:
                    predictions.append(closest_top_num)
                else:
                    # If all top numbers are already in predictions, use the original prediction
                    predictions.append(pred)

        return np.array(predictions)

    def _find_next_available_number(self, existing_numbers: list, top_numbers: list, start: int = 1) -> int:
        all_numbers = set(range(start, 59))  # Assuming the lottery numbers range from 1 to 58
        available_numbers = list(all_numbers - set(existing_numbers))
        
        # Prioritize numbers from top_numbers
        priority_numbers = [n for n in available_numbers if n in top_numbers]
        
        if priority_numbers:
            return min(priority_numbers)
        else:
            return min(available_numbers)

    def generate_unique_number(self, existing_numbers: list, top_numbers: list) -> int:
        return self._find_next_available_number(existing_numbers, top_numbers)

    def adjust_prediction(self, pred: np.ndarray, last_combination: list, top_numbers: list,) -> list:
        pred = np.round(pred).astype(int)
        pred = np.clip(pred, 1, 58)
        pred = np.sort(pred)
        unique_pred = []
        for num in pred:
            if num not in unique_pred and num not in last_combination:
                unique_pred.append(num)
            else:
                next_num = self._find_next_available_number(unique_pred + last_combination, top_numbers, num + 1)
                unique_pred.append(next_num)
        while len(unique_pred) < 6:
            next_num = self._find_next_available_number(unique_pred + last_combination, top_numbers, max(unique_pred) + 1)
            unique_pred.append(next_num)
        return unique_pred

    def plot_number_frequency(self, number_frequency: Counter) -> None:
        numbers, frequencies = zip(*sorted(number_frequency.items()))
        plt.figure(figsize=(12, 6))
        plt.bar(numbers, frequencies)
        plt.title('Frequency of Numbers in Ultra Lotto 6/58')
        plt.xlabel('Number')
        plt.ylabel('Frequency')
        plt.show()

def main() -> None:
    predictor = LotteryPredictor()
    df = predictor.load_and_preprocess_data('658.txt')
    number_frequency = predictor.analyze_number_frequency()
    predictor.plot_number_frequency(number_frequency)
    df_features = predictor.create_correlation_features(df)
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
    top_numbers = [num for num, _ in number_frequency.most_common(29)]
    bottom_numbers = [num for num, _ in number_frequency.most_common()[-29:]]
    final_prediction = predictor.adjust_prediction(raw_predictions, last_combination, top_numbers)

    logging.info(f"Predicted numbers for next draw ({next_draw_date.date()}): {final_prediction}")
    logging.info(f"Last combination: {last_combination}")
    logging.info(f"Top numbers: {top_numbers}")
    logging.info(f"Bottom numbers: {bottom_numbers}")
    logging.info(f"Number frequency: {number_frequency}")
    logging.info(f"Raw predictions: {raw_predictions}")
    logging.info(f"Adjusted prediction: {final_prediction}")
    logging.info("Program execution completed successfully.")

if __name__ == "__main__":
    main()



