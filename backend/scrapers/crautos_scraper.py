from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium. webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from bs4 import BeautifulSoup
from backend.config.settings import settings
from backend.utils.logger import logger
from typing import List, Dict, Optional
import time
import re
from datetime import datetime


class CRAutosScraper:
    
    def __init__(self, headless: bool = None, max_pages: int = None):
        self.headless = headless if headless is not None else settings. SCRAPER_HEADLESS
        self.max_pages = max_pages if max_pages is not None else settings.SCRAPER_MAX_PAGES
        self.base_url = settings.CRAUTOS_USED_CARS_URL
        self.cars_data = []
        self. driver = None
        
    def setup_driver(self):
        """Setup Chrome driver with options"""
        chrome_options = Options()
        
        if self.headless:
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
        
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            logger.info("Chrome driver initialized successfully")
        except Exception as e:
            logger. error(f"Error initializing Chrome driver: {e}")
            raise
    
    def close_driver(self):
        """Close the Chrome driver"""
        if self.driver:
            self.driver.quit()
            logger.info("Chrome driver closed")
    
    def scrape_all_cars(self) -> List[Dict]:
        """Scrape all cars from CRAutos"""
        self.setup_driver()
        
        try:
            logger.info("Starting scraping process...")
            page_num = 1
            
            while page_num <= self.max_pages:
                logger.info(f"Scraping page {page_num}/{self.max_pages}")
                
                cars = self._scrape_page(page_num)
                
                if not cars:
                    logger.info(f"No more cars found on page {page_num}. Stopping.")
                    break
                
                self.cars_data.extend(cars)
                logger.info(f"Found {len(cars)} cars on page {page_num}. Total: {len(self.cars_data)}")
                
                # Delay between requests
                time.sleep(settings. SCRAPER_DELAY_SECONDS)
                page_num += 1
            
            logger.info(f"Scraping completed. Total cars: {len(self.cars_data)}")
            return self.cars_data
            
        except Exception as e:
            logger.error(f"Error during scraping:  {e}")
            raise
        finally:
            self.close_driver()
    
    def _scrape_page(self, page_num: int) -> List[Dict]:
        """Scrape a single page"""
        try:
            url = f"{self.base_url}?p={page_num}"
            self.driver.get(url)
            
            # Wait for page to load
            WebDriverWait(self.driver, settings.SCRAPER_TIMEOUT).until(
                EC.presence_of_element_located((By. CLASS_NAME, "inventory"))
            )
            
            # Parse page content
            soup = BeautifulSoup(self.driver. page_source, 'html. parser')
            inventories = soup.find_all('div', class_='inventory')
            
            if not inventories:
                return []
            
            cars = []
            for inv in inventories:
                car_data = self._extract_car_data(inv)
                if car_data:
                    cars.append(car_data)
            
            return cars
            
        except TimeoutException: 
            logger.warning(f"Timeout loading page {page_num}")
            return []
        except Exception as e:
            logger.error(f"Error scraping page {page_num}: {e}")
            return []
    
    def _extract_car_data(self, inventory_element) -> Optional[Dict]:
        """Extract data from a single car listing"""
        try:
            car_data = {
                'fecha_extraccion': datetime.now().isoformat()
            }
            
            # Extract title
            title_elem = inventory_element.find('div', class_='title')
            if title_elem:
                title_text = title_elem.get_text(strip=True)
                car_data['titulo_completo'] = title_text
                
                # Parse title to extract marca, modelo, año
                parsed = self._parse_title(title_text)
                car_data. update(parsed)
            else:
                return None
            
            # Extract car ID from detail link
            detail_link = inventory_element.find('a', href=re.compile(r'/autosusados/detalles\. cfm'))
            if detail_link: 
                href = detail_link.get('href', '')
                car_data['url_detalle'] = settings.CRAUTOS_BASE_URL + href if href.startswith('/') else href
                
                # Extract car_id from URL
                match = re.search(r'id=(\d+)', href)
                if match:
                    car_data['car_id'] = match.group(1)
            
            # Extract price
            price_elem = inventory_element.find('div', class_='price')
            if price_elem:
                price_text = price_elem.get_text(strip=True)
                car_data['precio'] = price_text
                car_data['precio_numerico'] = self._parse_price(price_text)
            
            # Extract image
            img_elem = inventory_element.find('img', class_='preview')
            if img_elem: 
                car_data['url_imagen'] = img_elem. get('src', '')
            
            # Extract attributes (transmision, combustible, etc.)
            options_table = inventory_element.find('table', class_='options-primary')
            if options_table: 
                attributes = self._extract_attributes(options_table)
                car_data.update(attributes)
            
            # Extract seller info
            seller_elem = inventory_element.find('div', class_='seller-name')
            if seller_elem: 
                car_data['vendedor'] = seller_elem.get_text(strip=True)
            
            phone_elem = inventory_element.find('div', class_='phone')
            if phone_elem: 
                car_data['telefono'] = phone_elem.get_text(strip=True)
            
            return car_data
            
        except Exception as e:
            logger.error(f"Error extracting car data: {e}")
            return None
    
    def _parse_title(self, title:  str) -> Dict:
        """Parse car title to extract marca, modelo, año"""
        parts = title.strip().split()
        
        result = {
            'marca': '',
            'modelo': '',
            'año': ''
        }
        
        if not parts:
            return result
        
        # First part is usually the brand
        result['marca'] = parts[0]
        
        # Last part that's a 4-digit number is usually the year
        for i in range(len(parts) - 1, -1, -1):
            if parts[i].isdigit() and len(parts[i]) == 4:
                result['año'] = parts[i]
                # Everything between brand and year is the model
                if i > 1:
                    result['modelo'] = ' '.join(parts[1:i])
                break
        
        # If no year found, assume everything after brand is model
        if not result['año'] and len(parts) > 1:
            result['modelo'] = ' '.join(parts[1:])
        
        return result
    
    def _parse_price(self, price_text: str) -> Optional[float]:
        """Parse price text to numeric value"""
        try:
            # Remove non-numeric characters except dots and commas
            cleaned = re. sub(r'[^\d.,]', '', price_text)
            # Remove commas
            cleaned = cleaned.replace(',', '')
            return float(cleaned) if cleaned else None
        except: 
            return None
    
    def _extract_attributes(self, options_table) -> Dict:
        """Extract attributes from options table"""
        attributes = {}
        
        try:
            rows = options_table.find_all('tr')
            
            for row in rows:
                text = row.get_text(strip=True)
                
                if 'Transmisión' in text or 'Transmision' in text:
                    value = text.split(': ')[-1].strip()
                    attributes['transmision'] = value
                
                elif 'Combustible' in text: 
                    value = text.split(':')[-1].strip()
                    attributes['combustible'] = value
                
                elif 'Kilometraje' in text:
                    value = text.split(':')[-1].strip()
                    attributes['kilometraje'] = value
                    attributes['kilometraje_numerico'] = self._parse_kilometraje(value)
                
                elif 'Estilo' in text:
                    value = text.split(':')[-1].strip()
                    attributes['estilo'] = value
                
                elif 'Puertas' in text:
                    value = text.split(':')[-1].strip()
                    attributes['puertas'] = self._parse_doors(value)
                
                elif 'Provincia' in text:
                    value = text.split(':')[-1].strip()
                    attributes['provincia'] = value
                
                elif 'Cilindrada' in text:
                    value = text.split(':')[-1].strip()
                    # You can add cilindrada field if needed
                
                elif 'Financiado' in text:
                    attributes['es_financiado'] = 'Sí' in text or 'Si' in text
                
                elif 'Recibe' in text:
                    attributes['recibe_vehiculo'] = 'Sí' in text or 'Si' in text
        
        except Exception as e: 
            logger.error(f"Error extracting attributes: {e}")
        
        return attributes
    
    def _parse_kilometraje(self, km_text: str) -> Optional[int]:
        """Parse kilometraje to numeric value"""
        try: 
            cleaned = re.sub(r'[^\d]', '', km_text)
            return int(cleaned) if cleaned else None
        except:
            return None
    
    def _parse_doors(self, doors_text: str) -> Optional[int]:
        """Parse doors to numeric value"""
        try: 
            match = re.search(r'\d+', doors_text)
            return int(match.group()) if match else None
        except:
            return None