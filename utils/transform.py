# transform.py
import pandas as pd
import re
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

class DataTransformer:
    """Class responsible for transforming and cleaning the extracted data"""
    
    def clean_and_transform(self, raw_data: List[Dict[str, Any]]) -> pd.DataFrame:
        """Clean and transform the raw extracted data"""
        if not raw_data:
            logger.warning("No data to transform")
            return pd.DataFrame()
            
        logger.info(f"Transforming {len(raw_data)} records")
        
        # Convert to DataFrame
        df = pd.DataFrame(raw_data)
        
        # Remove raw HTML as it's no longer needed after transformation
        if 'raw_html' in df.columns:
            df = df.drop('raw_html', axis=1)
        
        # Apply transformations
        df = self._clean_names(df)
        df = self._extract_numeric_rating(df)
        df = self._split_coordinates(df)
        
        # Add metadata
        df['extraction_timestamp'] = pd.Timestamp.now()
        
        logger.info(f"Transformation complete, resulting in {len(df)} records")
        return df
    
    def _clean_names(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean up the name field"""
        if 'name' in df.columns:
            df['name'] = df['name'].str.strip()
            df['name'] = df['name'].replace('No name', None)
        return df
    
    def _extract_numeric_rating(self, df: pd.DataFrame) -> pd.DataFrame:
        """Extract numeric rating from rating string"""
        if 'rating' in df.columns:
            # Create a new column for numeric rating
            df['rating_numeric'] = None
            
            # Extract numeric rating using regex
            for idx, rating in enumerate(df['rating']):
                if rating and rating != 'No rating':
                    match = re.search(r'(\d+(\.\d+)?)', str(rating))
                    if match:
                        df.at[idx, 'rating_numeric'] = float(match.group(1))
            
            # Convert to proper numeric type
            df['rating_numeric'] = pd.to_numeric(df['rating_numeric'], errors='coerce')
        
        return df
    
    def _split_coordinates(self, df: pd.DataFrame) -> pd.DataFrame:
        """Split coordinates into latitude and longitude"""
        if 'coordinates' in df.columns:
            # Initialize new columns
            df['latitude'] = None
            df['longitude'] = None
            
            # Extract coordinates
            for idx, coord in enumerate(df['coordinates']):
                if coord and coord != 'No coordinates':
                    try:
                        lat, lng = coord.split(',')
                        df.at[idx, 'latitude'] = float(lat)
                        df.at[idx, 'longitude'] = float(lng)
                    except Exception as e:
                        logger.warning(f"Failed to parse coordinates '{coord}': {e}")
            
            # Convert to proper numeric types
            df['latitude'] = pd.to_numeric(df['latitude'], errors='coerce')
            df['longitude'] = pd.to_numeric(df['longitude'], errors='coerce')
        
        return df

