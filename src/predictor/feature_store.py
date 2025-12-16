"""Memory-efficient feature store for large datasets."""
import numpy as np
import pandas as pd
from typing import Dict, List, Optional
import h5py
from pathlib import Path

class FeatureStore:
    """Efficient storage and retrieval of computed features."""
    
    def __init__(self, store_path: str = "features.h5"):
        self.store_path = Path(store_path)
        self._memory_cache = {}
        self._cache_size_limit = 1000  # rows
    
    def store_features(self, df: pd.DataFrame, dataset_name: str) -> None:
        """Store features efficiently using HDF5."""
        with h5py.File(self.store_path, 'a') as f:
            # Store numeric data efficiently
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            
            if dataset_name in f:
                del f[dataset_name]
            
            grp = f.create_group(dataset_name)
            
            # Store numeric data with compression
            for col in numeric_cols:
                data = df[col].values
                grp.create_dataset(
                    col, 
                    data=data, 
                    compression='gzip',
                    compression_opts=9,
                    dtype=self._optimize_dtype(data)
                )
            
            # Store metadata
            grp.attrs['columns'] = list(numeric_cols)
            grp.attrs['shape'] = df.shape
    
    def load_features(self, dataset_name: str, 
                     columns: Optional[List[str]] = None) -> pd.DataFrame:
        """Load features efficiently with optional column selection."""
        cache_key = f"{dataset_name}_{hash(tuple(columns or []))}"
        
        # Check memory cache first
        if cache_key in self._memory_cache:
            return self._memory_cache[cache_key]
        
        with h5py.File(self.store_path, 'r') as f:
            if dataset_name not in f:
                raise KeyError(f"Dataset {dataset_name} not found")
            
            grp = f[dataset_name]
            available_cols = grp.attrs['columns']
            
            # Load only requested columns
            cols_to_load = columns or available_cols
            data = {}
            
            for col in cols_to_load:
                if col in grp:
                    data[col] = grp[col][:]
            
            df = pd.DataFrame(data)
            
            # Cache if small enough
            if len(df) <= self._cache_size_limit:
                self._memory_cache[cache_key] = df
            
            return df
    
    def _optimize_dtype(self, data: np.ndarray) -> np.dtype:
        """Optimize data type for storage efficiency."""
        if data.dtype == np.int64:
            if data.min() >= 0 and data.max() <= 255:
                return np.uint8
            elif data.min() >= -128 and data.max() <= 127:
                return np.int8
            elif data.min() >= -32768 and data.max() <= 32767:
                return np.int16
            else:
                return np.int32
        elif data.dtype == np.float64:
            return np.float32
        
        return data.dtype
    
    def get_feature_stats(self, dataset_name: str) -> Dict:
        """Get statistics about stored features."""
        with h5py.File(self.store_path, 'r') as f:
            if dataset_name not in f:
                return {}
            
            grp = f[dataset_name]
            stats = {
                'columns': list(grp.attrs['columns']),
                'shape': tuple(grp.attrs['shape']),
                'size_mb': sum(grp[col].size * grp[col].dtype.itemsize 
                              for col in grp.keys()) / (1024 * 1024)
            }
            
            return stats
    
    def clear_cache(self) -> None:
        """Clear memory cache."""
        self._memory_cache.clear()

class SparseFeatureProcessor:
    """Process sparse frequency features efficiently."""
    
    @staticmethod
    def create_sparse_frequencies(numbers_array: np.ndarray) -> np.ndarray:
        """Create sparse frequency representation."""
        n_rows, n_positions = numbers_array.shape
        
        # Use sparse representation - only store non-zero frequencies
        from scipy.sparse import csr_matrix
        
        # Create frequency matrix more efficiently
        row_indices = []
        col_indices = []
        data = []
        
        for row in range(n_rows):
            for pos in range(n_positions):
                number = numbers_array[row, pos]
                if 1 <= number <= 58:  # Valid lottery number
                    row_indices.append(row)
                    col_indices.append(number - 1)  # 0-indexed
                    data.append(1)
        
        # Create sparse matrix
        sparse_freq = csr_matrix(
            (data, (row_indices, col_indices)), 
            shape=(n_rows, 58),
            dtype=np.uint8
        )
        
        return sparse_freq
    
    @staticmethod
    def aggregate_frequencies(sparse_freq, window_size: int = 10) -> np.ndarray:
        """Aggregate frequencies over rolling windows efficiently."""
        from scipy.sparse import vstack
        
        n_rows = sparse_freq.shape[0]
        aggregated = []
        
        for i in range(window_size, n_rows):
            window_data = sparse_freq[i-window_size:i]
            window_sum = window_data.sum(axis=0).A1  # Convert to dense array
            aggregated.append(window_sum)
        
        return np.array(aggregated)
