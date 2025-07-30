from src.predictor.lottery_predictor import LotteryPredictor
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def main():
    try:
        # Initialize predictor
        predictor = LotteryPredictor('config/model_config.yaml')
        
        # Train the model
        logging.info("Starting model training...")
        predictor.train('data/lottery_history.csv')
        
        # Generate predictions
        logging.info("Generating predictions...")
        next_draw_features = predictor.data_processor.prepare_next_draw_features()
        predictions = predictor.predict(next_draw_features)
        
        logging.info(f"Predicted numbers for next draw: {sorted(predictions)}")
        
    except Exception as e:
        logging.error(f"Error in prediction system: {str(e)}")
        raise

if __name__ == "__main__":
    main()