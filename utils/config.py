# utils/config.py - Updated version
import os
from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class GoogleMapsConfig:
    search_query: str
    location: str
    headless: bool = False
    scroll_iterations: int = 20
    scroll_delay: int = 2
    wait_time: int = 5
    detail_wait_time: int = 3
    result_delay: int = 2
    # Recovery settings
    max_retries: int = 3
    recovery_wait: int = 5
    # Selector options
    use_alternative_selectors: bool = True
    debug_screenshots: bool = False
    debug_dir: str = "debug_screenshots"

@dataclass
class Config:
    google_maps: GoogleMapsConfig
    output_file: str = "coffee_shops_data.csv"