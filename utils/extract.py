# utils/extract.py - Fixed version
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import logging
import re
from typing import List, Dict, Any, Optional
import pandas as pd

from utils.config import GoogleMapsConfig

logger = logging.getLogger(__name__)

class GoogleMapsExtractor:
    """Class responsible for extracting data from Google Maps"""
    
    def __init__(self, config: GoogleMapsConfig):
        self.config = config
        self.driver = None
        self.results = []
        
    def setup_driver(self) -> None:
        """Initialize the Selenium WebDriver with appropriate options"""
        chrome_options = Options()
        if self.config.headless:
            chrome_options.add_argument("--headless")
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_argument("--disable-notifications")
        
        webdriver_service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=webdriver_service, options=chrome_options)
        logger.info("WebDriver initialized successfully")
        
    def navigate_to_google_maps(self) -> None:
        """Navigate to Google Maps and handle any initial setup screens"""
        self.driver.get("https://www.google.com/maps")
        logger.info("Navigated to Google Maps")
        
        # Handle first-time setup if it appears
        try:
            continue_button = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Continue')]"))
            )
            continue_button.click()
            logger.info("Clicked Continue on first-time setup")
            time.sleep(2)
        except Exception:
            logger.info("No first-time setup screen found")
    
    def search_for_places(self) -> None:
        """Search for places using the configured query"""
        search_box = self._find_search_box()
        if not search_box:
            raise Exception("Could not find search box with any selector")
            
        search_query = f"{self.config.search_query} in {self.config.location}"
        search_box.clear()
        search_box.send_keys(search_query)
        search_box.send_keys(Keys.ENTER)
        logger.info(f"Searching for: {search_query}")
        time.sleep(10)  # Allow time for results to load
            
    def _find_search_box(self):
        """Attempt to find the search box using multiple selectors"""
        selectors = [
            (By.ID, "searchboxinput"),
            (By.CSS_SELECTOR, "input[name='q']"),
            (By.CSS_SELECTOR, "input.searchboxinput"),
            (By.XPATH, "//input[@id='searchboxinput']")
        ]
        
        for by, selector in selectors:
            try:
                logger.debug(f"Trying to find search box with {by}: {selector}")
                search_box = WebDriverWait(self.driver, self.config.wait_time).until(
                    EC.presence_of_element_located((by, selector))
                )
                if search_box:
                    logger.info(f"Found search box using {by}: {selector}")
                    return search_box
            except Exception:
                continue
                
        return None
    
    def scroll_results(self) -> None:
        """Scroll through results to load more data"""
        try:
            results_list = WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div[role='feed']"))
            )
            logger.info("Found results list, starting to scroll...")
            
            for i in range(self.config.scroll_iterations):
                logger.debug(f"Scroll attempt {i+1}")
                self.driver.execute_script('arguments[0].scrollTop = arguments[0].scrollHeight', results_list)
                time.sleep(self.config.scroll_delay)
                
            logger.info("Finished scrolling")
        except Exception as e:
            logger.error(f"Error during scrolling: {e}")
            raise
    
    def extract_place_cards(self) -> List[Dict[str, Any]]:
        """Extract data from all place cards found in the results"""
        # First try to find cards with the original selector
        cards = self.driver.find_elements(By.CSS_SELECTOR, "div.Nv2PK")
        
        # If no cards found, try alternative selectors
        if not cards:
            alternative_selectors = [
                "div.DxyBCb.kA9KIf",
                "div[role='article']",
                "div.V0h1Ob-haAclf",
                "div.bfdHYd"
            ]
            
            for selector in alternative_selectors:
                cards = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if cards:
                    logger.info(f"Found {len(cards)} place cards with alternative selector: {selector}")
                    break
        
        if not cards:
            logger.warning("No place cards found with any selector")
            return []
            
        logger.info(f"Found {len(cards)} place cards")
        
        results = []
        for idx, card in enumerate(cards):
            try:
                place_data = self._extract_single_place(idx, card)
                if place_data:
                    results.append(place_data)
                    self.results.append(place_data)  # Store result in case of errors
            except Exception as e:
                logger.error(f"Error extracting data from card {idx+1}: {e}")
                continue
                
        return results
    
    def _go_back_to_list(self) -> bool:
        """Try multiple methods to go back to the results list"""
        back_button_selectors = [
            (By.CSS_SELECTOR, "button[jsaction='pane.place.backToList']"),
            (By.CSS_SELECTOR, "button[aria-label='Back']"),
            (By.CSS_SELECTOR, "button.VfPpkd-icon-LgbsSe"),
            (By.XPATH, "//button[contains(@jsaction, 'backToList')]"),
            (By.XPATH, "//button[contains(@aria-label, 'Back')]")
        ]
        
        for by, selector in back_button_selectors:
            try:
                button = self.driver.find_element(by, selector)
                button.click()
                time.sleep(self.config.result_delay)
                return True
            except:
                continue
        
        # If no back button works, try using browser back button
        try:
            self.driver.back()
            time.sleep(self.config.result_delay)
            return True
        except:
            return False
    
    def _restart_browser_and_search(self) -> None:
        """Restart the browser and redo the search if navigation breaks"""
        try:
            self.driver.quit()
        except:
            pass
            
        self.setup_driver()
        self.navigate_to_google_maps()
        self.search_for_places()
        self.scroll_results()
    
    def _extract_name(self) -> str:
        """Extract the place name"""
        name_selectors = [
            (By.CSS_SELECTOR, "h1.DUwDvf"),
            (By.CSS_SELECTOR, "h1.fontHeadlineLarge"),
            (By.XPATH, "//h1[contains(@class, 'fontHeadline')]")
        ]
        
        for by, selector in name_selectors:
            try:
                name = WebDriverWait(self.driver, self.config.wait_time).until(
                    EC.presence_of_element_located((by, selector))
                ).text.strip()
                if name:
                    return name
            except:
                continue
                
        return "No name"
    
    def _extract_address(self) -> str:
        """Extract the place address using multiple possible selectors"""
        address_selectors = [
            (By.CSS_SELECTOR, "button[data-item-id='address']"),
            (By.CSS_SELECTOR, "div.QSFF4-text.gm2-body-2"),
            (By.CSS_SELECTOR, "div.W4Efsd span"),
            (By.XPATH, "//button[contains(@data-item-id, 'address')]"),
            (By.XPATH, "//div[contains(@class, 'rogA2c')]"),
            (By.XPATH, "//div[contains(text(), 'Address: ')]/../following-sibling::div")
        ]
        
        for by, selector in address_selectors:
            try:
                address = self.driver.find_element(by, selector).text.strip()
                if address:
                    return address
            except:
                continue
                
        return "No address"
    
    def _extract_rating(self) -> str:
        """Extract the place rating using multiple possible selectors"""
        rating_selectors = [
            (By.CSS_SELECTOR, "div.F7nice span span span"),
            (By.CSS_SELECTOR, "span[aria-label*='stars']"),
            (By.CSS_SELECTOR, "span.MW4etd"),
            (By.XPATH, "//div[contains(@class, 'F7nice')]//span"),
            (By.XPATH, "//span[contains(@aria-label, 'stars')]")
        ]
        
        for by, selector in rating_selectors:
            try:
                rating = self.driver.find_element(by, selector).text.strip()
                if rating:
                    return rating
            except:
                continue
                
        return "No rating"
    
   # Perbaikan untuk class GoogleMapsExtractor

    def _extract_single_place(self, idx: int, card) -> Optional[Dict[str, Any]]:
        """Extract data from a single place card"""
        try:
            # Scroll card into view and click it
            self.driver.execute_script("arguments[0].scrollIntoView();", card)
            time.sleep(1)
            card.click()
            time.sleep(self.config.detail_wait_time)
            
            # Extract place details
            place_data = {
                "name": self._extract_name(),
                "address": self._extract_address(),
                "rating": self._extract_rating(),
                "coordinates": self._extract_coordinates(),
                # Hapus raw_html karena menyebabkan error
                # "raw_html": self._get_raw_details_html()
            }
            
            logger.info(f"[{idx+1}] {place_data['name']} | {place_data['rating']} | {place_data['coordinates']}")
            
            # Try to go back to the list with multiple methods
            success = self._go_back_to_list()
            if not success:
                # If we can't go back, restart the browser and search again
                logger.warning("Couldn't go back to list. Restarting browser.")
                self._restart_browser_and_search()
            
            return place_data
        except Exception as e:
            logger.error(f"Failed to extract place at index {idx}: {e}")
            # Try to go back to the list or restart browser if necessary
            try:
                success = self._go_back_to_list()
                if not success:
                    self._restart_browser_and_search()
            except:
                self._restart_browser_and_search()
            return None

    def _extract_coordinates(self) -> str:
        """Extract coordinates using multiple methods to ensure accuracy"""
        # Method 1: Try to extract from URL (current implementation)
        current_url = self.driver.current_url
        coords_match = re.search(r'@(-?\d+\.\d+),(-?\d+\.\d+)', current_url)
        
        if coords_match:
            lat, lng = coords_match.groups()
            return f"{lat},{lng}"
        
        # Method 2: Try to extract from share link (most reliable)
        try:
            # Click share button
            share_button_selectors = [
                (By.XPATH, "//button[contains(@jsaction, 'share')]"),
                (By.XPATH, "//button[contains(@aria-label, 'Share')]"),
                (By.CSS_SELECTOR, "button[jsaction*='share']"),
                (By.CSS_SELECTOR, "button[aria-label*='Share']"),
                (By.CSS_SELECTOR, "button[data-value='Share']")
            ]
            
            for by, selector in share_button_selectors:
                try:
                    share_button = WebDriverWait(self.driver, 3).until(
                        EC.element_to_be_clickable((by, selector))
                    )
                    share_button.click()
                    time.sleep(1)
                    break
                except:
                    continue
            
            # Get share link
            share_link_selectors = [
                (By.CSS_SELECTOR, "input[aria-label*='Share']"),
                (By.CSS_SELECTOR, "input.Gou1Yb"),
                (By.XPATH, "//input[contains(@aria-label, 'link')]"),
                (By.CSS_SELECTOR, "input[readonly]")
            ]
            
            for by, selector in share_link_selectors:
                try:
                    share_input = WebDriverWait(self.driver, 3).until(
                        EC.presence_of_element_located((by, selector))
                    )
                    share_url = share_input.get_attribute('value')
                    
                    # Extract coordinates from share URL
                    coords_match = re.search(r'!3d(-?\d+\.\d+)!4d(-?\d+\.\d+)', share_url)
                    if coords_match:
                        lat, lng = coords_match.groups()
                        # Close the share dialog by pressing escape
                        webdriver.ActionChains(self.driver).send_keys(Keys.ESCAPE).perform()
                        return f"{lat},{lng}"
                    
                    # Alternative pattern in Google Maps URLs
                    coords_match = re.search(r'@(-?\d+\.\d+),(-?\d+\.\d+)', share_url)
                    if coords_match:
                        lat, lng = coords_match.groups()
                        # Close the share dialog by pressing escape
                        webdriver.ActionChains(self.driver).send_keys(Keys.ESCAPE).perform()
                        return f"{lat},{lng}"
                    
                    # Close the share dialog by pressing escape
                    webdriver.ActionChains(self.driver).send_keys(Keys.ESCAPE).perform()
                except:
                    continue
            
            # Try to close share dialog if open
            try:
                webdriver.ActionChains(self.driver).send_keys(Keys.ESCAPE).perform()
            except:
                pass
        except Exception as e:
            logger.debug(f"Couldn't extract coordinates from share link: {e}")
        
        # Method 3: Extract from script tags (more reliable than URL in some cases)
        try:
            script_tags = self.driver.find_elements(By.TAG_NAME, "script")
            for script in script_tags:
                try:
                    script_content = script.get_attribute("innerHTML")
                    # Look for coordinate patterns in script content
                    coords_match = re.search(r'"latitude":(-?\d+\.\d+),"longitude":(-?\d+\.\d+)', script_content)
                    if coords_match:
                        lat, lng = coords_match.groups()
                        return f"{lat},{lng}"
                except:
                    continue
        except Exception as e:
            logger.debug(f"Couldn't extract coordinates from script tags: {e}")
        
        # If all extraction methods fail, look for meta tags with geo information
        try:
            meta_tags = self.driver.find_elements(By.TAG_NAME, "meta")
            for meta in meta_tags:
                try:
                    if meta.get_attribute("property") == "og:latitude":
                        lat = meta.get_attribute("content")
                        lng_meta = self.driver.find_element(By.CSS_SELECTOR, "meta[property='og:longitude']")
                        lng = lng_meta.get_attribute("content")
                        if lat and lng:
                            return f"{lat},{lng}"
                except:
                    continue
        except:
            pass
        
        return "No coordinates"

    # Optional: Implementasi fungsi get_raw_details_html jika dibutuhkan
    def _get_raw_details_html(self) -> str:
        """Get raw HTML of the details panel for further processing if needed"""
        try:
            details_panel = self.driver.find_element(By.CSS_SELECTOR, "div.m6QErb.DxyBCb.kA9KIf.dS8AEf")
            return details_panel.get_attribute('innerHTML')
        except:
            try:
                details_panel = self.driver.find_element(By.CSS_SELECTOR, "div.kAEsAc")
                return details_panel.get_attribute('innerHTML')
            except:
                try:
                    # Mencoba selector lain yang mungkin berisi detail panel
                    details_panel = self.driver.find_element(By.CSS_SELECTOR, "div[role='main']")
                    return details_panel.get_attribute('innerHTML')
                except:
                    return ""
    
    def close(self) -> None:
        """Close the WebDriver"""
        if self.driver:
            self.driver.quit()
            logger.info("WebDriver closed")
    
    def extract(self) -> List[Dict[str, Any]]:
        """Main extraction method that orchestrates the extraction process"""
        try:
            self.setup_driver()
            self.navigate_to_google_maps()
            self.search_for_places()
            self.scroll_results()
            results = self.extract_place_cards()
            return results
        except Exception as e:
            logger.error(f"Extraction failed: {e}")
            # If extraction fails but we've already collected some results, return them
            if self.results:
                logger.info(f"Returning {len(self.results)} partial results despite error")
                return self.results
            raise
        finally:
            self.close()

    def load(self, data: pd.DataFrame, output_csv: str, output_json: str) -> bool:
        """Main load method that orchestrates the loading process"""
        if data.empty:
            logger.warning("No data to load")
            return False
        
        csv_success = self.save_to_csv(data, output_csv)
        json_success = self.save_to_json(data, output_json)
        
        return csv_success and json_success