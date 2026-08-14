import tempfile
import os
import unittest
from src.predictor.system_factory import PredictionSystemFactory
import yaml


class TestEndToEnd(unittest.TestCase):
    def setUp(self):
        # Minimal config with small models for speed
        from src.predictor.constants import ColumnNames
        self.config = {
            'lottery': {
                'min_number': 1,
                'max_number': 58,
                'numbers_per_draw': 6,
            },
            'data': {
                'validation': {
                    'required_columns': [
                        ColumnNames.LOTTO_GAME,
                        ColumnNames.COMBINATIONS,
                        ColumnNames.DRAW_DATE,
                    ]
                }
            },
            'models': {
                'xgboost': {'n_estimators': 5, 'learning_rate': 0.1, 'max_depth': 3},
                'random_forest': {'n_estimators': 5, 'max_depth': 3},
                'gradient_boosting': {'n_estimators': 5, 'learning_rate': 0.1, 'max_depth': 3},
            }
        }
        self.config_file = tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False)
        yaml.dump(self.config, self.config_file)
        self.config_file.close()

        # Create synthetic data: 30 draws
        rows = []
        for i in range(30):
            nums = [(i + j) % 58 + 1 for j in range(6)]
            combo = '-'.join(f"{n:02d}" for n in nums)
            month = (i % 12) + 1
            day = (i % 28) + 1
            rows.append(f"Ultra Lotto 6/58,{combo},{month}/{day}/2024,1000000,0")

        from src.predictor.constants import ColumnNames
        header = (
            f"{ColumnNames.LOTTO_GAME},{ColumnNames.COMBINATIONS},"
            f"{ColumnNames.DRAW_DATE},{ColumnNames.JACKPOT},{ColumnNames.WINNERS}\n"
        )
        self.data_file = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
        self.data_file.write(header + '\n'.join(rows))
        self.data_file.close()

    def tearDown(self):
        os.unlink(self.config_file.name)
        os.unlink(self.data_file.name)

    def test_train_save_load_predict(self):
        service = PredictionSystemFactory.create_lottery_predictor(self.config_file.name)
        model_config = self.config['models']
        # train
        service.train(self.data_file.name, model_config=model_config)
        self.assertTrue(service.is_trained)

        # save
        tmpdir = tempfile.mkdtemp()
        service.save(tmpdir)
        # create fresh service and load
        service2 = PredictionSystemFactory.create_lottery_predictor(self.config_file.name)
        service2.load(tmpdir)
        self.assertTrue(service2.is_trained)
        self.assertEqual(len(service2.models), service.config['numbers_per_draw'])

        # predict
        features = service2.prepare_features(self.data_file.name)
        preds = service2.predict(features)
        self.assertEqual(len(preds), service.config['numbers_per_draw'])


if __name__ == '__main__':
    unittest.main()
