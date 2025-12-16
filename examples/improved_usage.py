"""Example usage of the improved prediction system."""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.predictor.system_factory import PredictionSystemFactory

def main():
    """Demonstrate improved architecture usage."""
    
    # Create predictor using factory
    predictor = PredictionSystemFactory.create_lottery_predictor(
        'config/improved_config.yaml'
    )
    
    # Train the model
    print("Training model...")
    predictor.train('data/lottery_history.csv', predictor.config_manager.get_model_config())
    
    # Generate predictions
    print("Generating predictions...")
    predictions = predictor.predict()
    
    print(f"Predicted numbers: {predictions}")

if __name__ == "__main__":
    main()
