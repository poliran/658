import unittest
import pandas as pd
from random_forest import load_and_preprocess_data, extract_numbers, prepare_dataset, analyze_historical_data

class TestRandomForestFunctions(unittest.TestCase):

    def setUp(self):
        # Sample data for testing
        self.sample_data = {
            'DRAW DATE': ['01/01/2020', '01/08/2020'],
            'COMBINATIONS': ['1-2-3-4-5-6', '7-8-9-10-11-12'],
            'WINNERS': [3, 4]
        }
        self.df = pd.DataFrame(self.sample_data)

    def test_load_and_preprocess_data(self):
        # Test if the function loads and preprocesses data correctly
        df = load_and_preprocess_data('658.txt')  # Assuming a test file exists
        self.assertIn('DRAW DATE', df.columns)
        self.assertEqual(df['DRAW DATE'].dtype, 'datetime64[ns]')

    def test_extract_numbers(self):
        # Test if the function extracts numbers correctly
        result = extract_numbers('1-2-3-4-5-6')
        self.assertEqual(result, [1, 2, 3, 4, 5, 6])
        self.assertEqual(extract_numbers(None), [])

    def test_prepare_dataset(self):
        # Test if the dataset is prepared correctly
        prepared_df = prepare_dataset(self.df)
        self.assertEqual(prepared_df.shape[1], 7)  # Check if it has 7 columns
        self.assertEqual(prepared_df['winners'].iloc[0], 3)

    def test_analyze_historical_data(self):
        # Test if the historical analysis is correct
        analysis = analyze_historical_data(self.df)
        self.assertEqual(analysis['average_winners'], 3.5)
        self.assertEqual(len(analysis['most_common']), 3)

if __name__ == '__main__':
    unittest.main()