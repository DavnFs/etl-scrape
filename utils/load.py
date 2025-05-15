# load.py
import pandas as pd
import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)

class DataLoader:
    """Class responsible for loading the transformed data"""
    
    def save_to_csv(self, data: pd.DataFrame, output_file: str) -> bool:
        """Save the data to a CSV file"""
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(output_file) or '.', exist_ok=True)
            
            # Save to CSV
            data.to_csv(output_file, index=False)
            logger.info(f"Data successfully saved to {output_file}")
            return True
        except Exception as e:
            logger.error(f"Failed to save data to CSV: {e}")
            return False

    def save_to_json(self, data: pd.DataFrame, output_file: str) -> bool:
        """Save the data to a JSON file"""
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(output_file) or '.', exist_ok=True)
            
            # Save to JSON
            data.to_json(output_file, orient='records', lines=True)
            logger.info(f"Data successfully saved to {output_file}")
            return True
        except Exception as e:
            logger.error(f"Failed to save data to JSON: {e}")
            return False
    
    def load(self, data: pd.DataFrame, output_csv: str, output_json: str) -> bool:
        """Main load method that orchestrates the loading process"""
        if data.empty:
            logger.warning("No data to load")
            return False
            
        csv_success = self.save_to_csv(data, output_csv)
        json_success = self.save_to_json(data, output_json)
        
        return csv_success and json_success
