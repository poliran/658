#!/usr/bin/env python3
"""Script to clean up legacy code and organize project structure."""
import os
import shutil
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LegacyCleanup:
    """Handles cleanup of legacy code and project organization."""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.archive_dir = self.project_root / "archive"
        
    def create_archive_structure(self):
        """Create archive directory structure."""
        directories = [
            self.archive_dir / "experimental",
            self.archive_dir / "deprecated",
            self.archive_dir / "old_models",
            self.archive_dir / "old_notebooks"
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory: {directory}")
    
    def identify_legacy_files(self):
        """Identify files that should be archived."""
        legacy_patterns = [
            # Large monolithic files
            "xgboost-prediction.py",
            "xg.py",
            
            # Duplicate implementations
            "webscrape*.py",
            "test_selenium.py",
            "parse_saved_html.py",
            
            # Experimental analysis
            "analyze.py",
            "combinations.py",
            "transition.py",
            "holt_winters_prediction.py",
            "extract.py",
            "sort658.py",
            "grok.py",
            
            # Old model files
            "test_random_forest.py",
            "repeat_combo.py",
            
            # Data files that should be in data/
            "iot_sensor.csv",
        ]
        
        legacy_files = []
        for pattern in legacy_patterns:
            if "*" in pattern:
                # Handle glob patterns
                matches = list(self.project_root.glob(f"**/{pattern}"))
                legacy_files.extend(matches)
            else:
                # Handle exact matches
                matches = list(self.project_root.glob(f"**/{pattern}"))
                legacy_files.extend(matches)
        
        return [f for f in legacy_files if f.exists() and not str(f).startswith(str(self.archive_dir))]
    
    def move_legacy_files(self):
        """Move legacy files to archive."""
        legacy_files = self.identify_legacy_files()
        
        for file_path in legacy_files:
            try:
                # Determine destination based on file type/location
                if "webscrape" in file_path.name or "selenium" in file_path.name:
                    dest_dir = self.archive_dir / "experimental" / "webscraping"
                elif file_path.suffix == ".py" and "test" in file_path.name:
                    dest_dir = self.archive_dir / "experimental" / "testing"
                elif file_path.suffix in [".pkl", ".h5", ".keras"]:
                    dest_dir = self.archive_dir / "old_models"
                elif file_path.suffix == ".csv":
                    dest_dir = self.archive_dir / "experimental" / "data"
                else:
                    dest_dir = self.archive_dir / "experimental"
                
                dest_dir.mkdir(parents=True, exist_ok=True)
                dest_path = dest_dir / file_path.name
                
                # Handle name conflicts
                counter = 1
                while dest_path.exists():
                    stem = file_path.stem
                    suffix = file_path.suffix
                    dest_path = dest_dir / f"{stem}_{counter}{suffix}"
                    counter += 1
                
                shutil.move(str(file_path), str(dest_path))
                logger.info(f"Moved {file_path} -> {dest_path}")
                
            except Exception as e:
                logger.error(f"Failed to move {file_path}: {e}")
    
    def create_deprecated_notice(self):
        """Create DEPRECATED.md file listing archived files."""
        deprecated_md = self.project_root / "DEPRECATED.md"
        
        content = """# Deprecated Files

This document lists files that have been moved to the `archive/` directory.

## Archived Files

### Experimental Code
- `xgboost-prediction.py` - Original monolithic implementation
- `xg.py` - Alternative XGBoost implementation
- `grok.py` - Experimental prediction logic
- `analyze.py` - Ad-hoc data analysis
- `combinations.py` - Combination analysis
- `transition.py` - Transition probability analysis
- `holt_winters_prediction.py` - Time series approach

### Web Scraping Implementations
- `webscrape*.py` - Multiple web scraping attempts
- `test_selenium.py` - Selenium testing
- `parse_saved_html.py` - HTML parsing utilities

### Testing & Validation
- `test_random_forest.py` - Random forest testing
- `repeat_combo.py` - Combination repeat analysis

### Data Files
- `iot_sensor.csv` - Unrelated sensor data

## Migration Notes

These files were moved to maintain project cleanliness while preserving
historical implementations for reference.

### Current Implementation
The production system now uses:
- `src/predictor/` - Main prediction modules
- `run_prediction.py` - Entry point
- `evaluate_model.py` - Model evaluation

### Accessing Archived Code
Archived files can be found in:
```
archive/
├── experimental/
├── deprecated/
├── old_models/
└── old_notebooks/
```
"""
        
        with open(deprecated_md, 'w') as f:
            f.write(content)
        
        logger.info(f"Created {deprecated_md}")
    
    def cleanup_empty_directories(self):
        """Remove empty directories after cleanup."""
        for root, dirs, files in os.walk(self.project_root, topdown=False):
            for directory in dirs:
                dir_path = Path(root) / directory
                try:
                    if not any(dir_path.iterdir()) and dir_path != self.archive_dir:
                        dir_path.rmdir()
                        logger.info(f"Removed empty directory: {dir_path}")
                except OSError:
                    pass  # Directory not empty or permission issue
    
    def run_cleanup(self):
        """Execute complete cleanup process."""
        logger.info("Starting legacy code cleanup...")
        
        self.create_archive_structure()
        self.move_legacy_files()
        self.create_deprecated_notice()
        self.cleanup_empty_directories()
        
        logger.info("Legacy cleanup completed!")
        logger.info(f"Archived files moved to: {self.archive_dir}")

def main():
    """Main cleanup execution."""
    cleanup = LegacyCleanup()
    cleanup.run_cleanup()

if __name__ == "__main__":
    main()
