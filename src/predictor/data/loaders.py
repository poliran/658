"""Data loading implementations."""
import pandas as pd
from ..interfaces import DataLoader

class CSVDataLoader(DataLoader):
    """CSV file data loader."""
    
    def load(self, source: str) -> pd.DataFrame:
        """Load data from CSV file."""
        try:
            return pd.read_csv(source)
        except Exception as e:
            raise ValueError(f"Failed to load CSV from {source}: {e}")

class DatabaseDataLoader(DataLoader):
    """Database data loader (future implementation)."""
    
    def load(self, source: str) -> pd.DataFrame:
        """Load data from database."""
        raise NotImplementedError("Database loading not implemented")
