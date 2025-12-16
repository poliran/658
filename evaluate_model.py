"""Model evaluation script."""
from src.predictor import LotteryPredictor, ModelEvaluator
from src.predictor.constants import FilePaths, DEFAULT_LOTTERY
from src.predictor.exceptions import LotteryPredictionError
import logging
import json

logging.basicConfig(level=logging.INFO)

def main():
    """Run model evaluation."""
    try:
        # Initialize components
        predictor = LotteryPredictor(FilePaths.DEFAULT_CONFIG_FILE, DEFAULT_LOTTERY)
        evaluator = ModelEvaluator()
        
        logging.info("Starting model evaluation...")
        
        # Perform backtesting
        results = evaluator.backtest_model(
            predictor, 
            FilePaths.DEFAULT_DATA_FILE, 
            test_size=20
        )
        
        # Generate report
        report = evaluator.generate_report(results)
        
        # Display results
        logging.info("Evaluation Results:")
        for key, value in report.items():
            logging.info(f"{key}: {value:.4f}")
        
        # Save detailed results
        with open('evaluation_results.json', 'w') as f:
            json.dump({
                'summary': report,
                'detailed_results': results
            }, f, indent=2, default=str)
        
        logging.info("Results saved to evaluation_results.json")
        
    except LotteryPredictionError as e:
        logging.error(f"Evaluation failed: {e.message}")
        if e.details:
            logging.error(f"Details: {e.details}")
        raise
    except Exception as e:
        logging.error(f"Unexpected error: {str(e)}")
        raise

if __name__ == "__main__":
    main()
