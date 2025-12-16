"""Model evaluation script."""
from src.predictor import LotteryPredictor, ModelEvaluator
import logging
import json

logging.basicConfig(level=logging.INFO)

def main():
    """Run model evaluation."""
    try:
        # Initialize components
        predictor = LotteryPredictor('config/model_config.yaml')
        evaluator = ModelEvaluator()
        
        logging.info("Starting model evaluation...")
        
        # Perform backtesting
        results = evaluator.backtest_model(
            predictor, 
            'data/lottery_history.csv', 
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
        
    except Exception as e:
        logging.error(f"Evaluation failed: {str(e)}")
        raise

if __name__ == "__main__":
    main()
