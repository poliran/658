import pandas as pd
import random
from collections import Counter
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.metrics import mean_squared_error, accuracy_score, precision_score, recall_score, f1_score
from sklearn.feature_selection import RFE
from sklearn.decomposition import PCA
import joblib

def load_and_preprocess_data(file_path):
    # Use comma as the separator
    df = pd.read_csv(file_path, sep=',')  # Change sep='\t' to sep=','
    
    # Check the columns in the DataFrame
    print("Columns in DataFrame:", df.columns.tolist())
    
    # Update the column name if necessary
    df['DRAW DATE'] = pd.to_datetime(df['DRAW DATE'], format='%m/%d/%Y')  # Ensure this matches the actual column name
    return df

def extract_numbers(combination, separator='-'):
    return [int(num) for num in combination.split(separator) if num.isdigit()] if isinstance(combination, str) else []

def prepare_dataset(df):
    data = [extract_numbers(row['COMBINATIONS']) + [row['WINNERS']] 
            for _, row in df.iterrows() if len(extract_numbers(row['COMBINATIONS'])) == 6]
    return pd.DataFrame(data, columns=['num1', 'num2', 'num3', 'num4',  'num5', 'num6', 'winners'])

def train_model(X, y):
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # Hyperparameter tuning using GridSearchCV
    param_grid = {
        'n_estimators': [50, 100, 200],
        'max_depth': [None, 10, 20],
        'min_samples_split': [2, 5, 10],
        'min_samples_leaf': [1, 2, 4],
        'max_features': ['sqrt', 'log2']
    }

    grid_search = GridSearchCV(estimator=RandomForestRegressor(random_state=42, n_jobs=-1),
                               param_grid=param_grid, cv=5, scoring='neg_mean_squared_error')
    grid_search.fit(X_train, y_train)

    best_params = grid_search.best_params_
    print(f"Best hyperparameters found: {best_params}")

    # Use the best model
    model = grid_search.best_estimator_
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    mse = mean_squared_error(y_test, y_pred)
    print(f'Mean Squared Error: {mse:.2f}')

    # Additional Feature Selection and PCA
    feature_importances = model.feature_importances_
    print("Feature Importances:", feature_importances)

    # Recursive Feature Elimination (RFE)
    rfe = RFE(model, n_features_to_select=5)
    rfe.fit(X, y)
    selected_features = X.columns[rfe.support_]
    print("Selected Features:", selected_features)

    # Principal Component Analysis (PCA)
    pca = PCA(n_components=5)
    X_pca = pca.fit_transform(X)
    
    # Evaluation Metrics
    accuracy = accuracy_score(y_test, y_pred.round())
    precision = precision_score(y_test, y_pred.round(), average='weighted', zero_division=1)
    recall = recall_score(y_test, y_pred.round(), average='weighted')
    f1 = f1_score(y_test, y_pred.round(), average='weighted')

    print("Accuracy:", accuracy)
    print("Precision:", precision)
    print("Recall:", recall)
    print("F1 Score:", f1)

    return model

def analyze_historical_data(df):
    all_numbers = [num for combo in df['COMBINATIONS'] for num in extract_numbers(combo)]
    number_frequency = Counter(all_numbers)
    return {
        'most_common': number_frequency.most_common(3),
        'least_common': number_frequency.most_common()[:-4:-1],
        'average_winners': df['WINNERS'].mean()
    }

def generate_recommendations(numbers, historical_analysis, model):
    if not numbers:
        print("Warning: No valid numbers found in the latest combination.")
        numbers = [random.randint(1, 58) for _ in range(6)]
    
    recommendations = []
    for _ in range(2):
        recommended_numbers = []
        if random.random() < 0.3:
            recommended_numbers.extend([num for num, _ in historical_analysis['most_common']])
        elif random.random() < 0.2:
            recommended_numbers.extend([num for num, _ in historical_analysis['least_common']])
        
        while len(recommended_numbers) < 6:
            recommended_numbers.append(random.randint(1, 58))
        
        recommendations.append(sorted(recommended_numbers))
    
    return recommendations

def main():
    # Load and preprocess data
    df = load_and_preprocess_data('658.txt')
    data_df = prepare_dataset(df)

    # Train model
    X = data_df[['num1', 'num2', 'num3', 'num4', 'num5', 'num6']]
    y = data_df['winners']

    if len(X) == 0 or len(y) == 0:
        print("Error: Empty dataset after preparing X and y.")
        return

    model = train_model(X, y)

    # Save trained model
    joblib.dump(model, 'random_forest_model.pkl')

    # Analyze historical data and generate recommendations
    historical_analysis = analyze_historical_data(df)
    latest_draw = df.iloc[0]
    latest_combination = latest_draw['COMBINATIONS']
    latest_numbers = extract_numbers(latest_combination)

    # Display results
    print(f"Latest Winning Combination ({latest_draw['DRAW DATE'].date()}): {latest_combination}")
    print(f"Extracted numbers: {latest_numbers}")
    print(f"Number of winners: {latest_draw['WINNERS']}")
    print(f"\nHistorical Analysis:")
    print(f"Most common numbers: {historical_analysis['most_common']}")
    print(f"Least common numbers: {historical_analysis['least_common']}")
    print(f"Average number of winners: {historical_analysis['average_winners']:.2f}")

    recommendations = generate_recommendations(latest_numbers, historical_analysis, model)
    print("\nRecommendations for Future Draws:")
    for idx, recommended_numbers in enumerate(recommendations, 1):
        print(f"Set {idx}: {'-'.join(map(str, recommended_numbers))}")

    print("\nRemember: 6/58 Today.")

if __name__ == "__main__":
    main()
