import argparse
import logging
import sys
from datetime import datetime
from typing import Dict, Any

from utils.config import Config, GoogleMapsConfig
from utils.extract import GoogleMapsExtractor
from utils.transform import DataTransformer
from utils.load import DataLoader

# Set up logging
def setup_logging(log_level: str = "INFO") -> None:
    """Configure logging for the ETL pipeline"""
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    log_level_map = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR
    }
    
    level = log_level_map.get(log_level.upper(), logging.INFO)
    
    # Configure logging to console and file
    logging.basicConfig(
        level=level,
        format=log_format,
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(f"logs/gmaps_etl_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
        ]
    )

def parse_arguments() -> Dict[str, Any]:
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Google Maps ETL Pipeline")
    
    # General settings
    parser.add_argument("--search-query", default="coffee shop", help="What to search for (e.g., 'coffee shop')")
    parser.add_argument("--location", default="Semarang, Indonesia", help="Location to search in")
    parser.add_argument("--output-file", default="coffee_shops_data.csv", help="Output file path")
    parser.add_argument("--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"], 
                        help="Logging level")
    
    # Extraction settings
    parser.add_argument("--headless", action="store_true", help="Run Chrome in headless mode")
    parser.add_argument("--scroll-iterations", type=int, default=20, 
                        help="Number of times to scroll down to load more results")
    parser.add_argument("--scroll-delay", type=int, default=2, 
                        help="Delay between scrolls in seconds")
    
    return vars(parser.parse_args())

def create_config(args: Dict[str, Any]) -> Config:
    """Create configuration from arguments"""
    google_maps_config = GoogleMapsConfig(
        search_query=args["search_query"],
        location=args["location"],
        headless=args["headless"],
        scroll_iterations=args["scroll_iterations"],
        scroll_delay=args["scroll_delay"]
    )

    
    return Config(
        google_maps=google_maps_config,
        output_file=args["output_file"]
    )

def run_pipeline(config: Config) -> bool:
    """Run the ETL pipeline with the given configuration"""
    logger = logging.getLogger(__name__)
    logger.info("Starting Google Maps ETL pipeline")
    
    try:
        # Extract
        logger.info("Starting extraction phase")
        extractor = GoogleMapsExtractor(config.google_maps)
        raw_data = extractor.extract()
        logger.info(f"Extraction complete: {len(raw_data)} records extracted")
        
        # Transform
        logger.info("Starting transformation phase")
        transformer = DataTransformer()
        transformed_data = transformer.clean_and_transform(raw_data)
        logger.info(f"Transformation complete: {len(transformed_data)} records transformed")
        
        # Load
        data_loader = DataLoader()
        data_loader.load(transformed_data, "output/semarang_coffee_shops.csv", "output/semarang_coffee_shops.json")
        
    except Exception as e:
        logger.error(f"ETL pipeline failed: {e}", exc_info=True)
        return False

def main() -> None:
    """Main entry point"""
    args = parse_arguments()
    setup_logging(args["log_level"])
    config = create_config(args)
    
    success = run_pipeline(config)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()