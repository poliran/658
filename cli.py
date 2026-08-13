"""cli.py — single entry point for the lottery prediction system.

Usage:
    python cli.py predict   [--config CONFIG] [--data DATA]
    python cli.py optimize  [--config CONFIG] [--data DATA]
    python cli.py report    [--config CONFIG] [--data DATA]
    python cli.py evaluate  [--config CONFIG] [--data DATA]
"""
import argparse
import logging

from src.predictor.system_factory import PredictionSystemFactory
from src.predictor.prediction_orchestrator import PredictionOrchestrator
from src.predictor.prediction_analyzer import PredictionAnalyzer
from src.predictor.report_formatter import ReportFormatter
from src.predictor.constants import FilePaths
from src.predictor.evaluator import ModelEvaluator

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
log = logging.getLogger(__name__)


def _build_orchestrator(config: str, data: str) -> PredictionOrchestrator:
    service = PredictionSystemFactory.create_lottery_predictor(config)
    orch = PredictionOrchestrator(service)
    orch.train(data)
    return orch


def cmd_predict(args):
    orch = _build_orchestrator(args.config, args.data)
    result = orch.get_predictions()
    log.info(f"Standard prediction:  {sorted(int(n) for n in result['standard'])}")
    log.info(f"Optimized prediction: {sorted(int(n) for n in result['optimized'])}")


def cmd_optimize(args):
    orch = _build_orchestrator(args.config, args.data)
    result = orch.get_predictions()
    log.info(f"Jackpot-optimized: {sorted(int(n) for n in result['optimized'])}")
    log.info("Anti-popular sets:")
    for i, pred in enumerate(result["anti_popular"], 1):
        log.info(f"  Set {i}: {sorted(int(n) for n in pred)}")


def cmd_report(args):
    orch = _build_orchestrator(args.config, args.data)
    analyzer = PredictionAnalyzer()
    formatter = ReportFormatter(orch, analyzer)
    print(formatter.summary())


def cmd_evaluate(args):
    evaluator = ModelEvaluator(args.config)
    evaluator.evaluate(args.data)


def main():
    parser = argparse.ArgumentParser(description="Lottery Prediction System")
    parser.add_argument("--config", default=FilePaths.DEFAULT_CONFIG_FILE)
    parser.add_argument("--data", default=FilePaths.DEFAULT_DATA_FILE)
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("predict", help="Generate standard and optimized predictions")
    sub.add_parser("optimize", help="Jackpot-sharing optimized predictions")
    sub.add_parser("report", help="Full summary report")
    sub.add_parser("evaluate", help="Evaluate model performance")

    args = parser.parse_args()
    {"predict": cmd_predict, "optimize": cmd_optimize, "report": cmd_report, "evaluate": cmd_evaluate}[
        args.command
    ](args)


if __name__ == "__main__":
    main()
