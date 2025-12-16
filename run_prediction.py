from src.predictor.lottery_predictor import LotteryPredictor
from src.predictor.constants import FilePaths, DEFAULT_LOTTERY
from src.predictor.validators import validate_prediction_input, validate_system_requirements
from src.predictor.exceptions import LotteryPredictionError
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def main():
    try:
        # Validate system requirements first
        validate_system_requirements()
        
        # Validate input before processing
        validate_prediction_input(FilePaths.DEFAULT_DATA_FILE, DEFAULT_LOTTERY)
        
        # Initialize predictor
        predictor = LotteryPredictor(FilePaths.DEFAULT_CONFIG_FILE, DEFAULT_LOTTERY)
        
        # Train the model
        logging.info("Starting model training...")
        predictor.train(FilePaths.DEFAULT_DATA_FILE)
        
        # Generate predictions
        logging.info("Generating predictions...")
        next_draw_features = predictor.data_processor.prepare_next_draw_features()
        predictions = predictor.predict(next_draw_features, use_improved_strategy=True)
        
        logging.info(f"Predicted numbers for next draw: {sorted(predictions)}")
        
        # Show additional prediction sets
        logging.info("Generating alternative predictions...")
        multiple_predictions = predictor.predict_multiple(next_draw_features, count=3)
        for i, pred in enumerate(multiple_predictions[1:], 2):  # Skip first as it's similar to main
            logging.info(f"Alternative set {i}: {sorted(pred)}")
        
    except LotteryPredictionError as e:
        logging.error(f"Prediction system error: {e.message}")
        if e.details:
            logging.error(f"Details: {e.details}")
        raise
    except Exception as e:
        logging.error(f"Unexpected error: {str(e)}")
        raise

if __name__ == "__main__":
    main()