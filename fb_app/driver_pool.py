import threading
import logging
from queue import Queue, Empty
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import WebDriverException
import time

class DriverPool:
    """Thread-safe WebDriver pool for concurrent scraping"""
    
    def __init__(self, pool_size=3, max_retries=3):
        self.pool_size = pool_size
        self.max_retries = max_retries
        self.driver_queue = Queue()
        self.active_drivers = set()
        self.lock = threading.Lock()
        self.logger = logging.getLogger(__name__)
        
        # Initialize driver pool
        self._initialize_pool()
    
    def _create_driver(self):
        """Create a new WebDriver instance with optimized settings"""
        chrome_options = Options()
        
        # Anti-detection measures
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument('--disable-infobars')
        chrome_options.add_argument('--disable-notifications')
        
        # Performance optimizations
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--disable-software-rasterizer')
        chrome_options.add_argument('--disable-features=VizDisplayCompositor')
        chrome_options.add_argument('--disable-features=IsolateOrigins,site-per-process')
        chrome_options.page_load_strategy = 'eager'
        
        # Use existing Chrome profile
        user_data_dir = r"C:\Users\PC9\AppData\Local\Google\Chrome\User Data\ScraperProfile"
        profile_directory = "Kanagiri"
        chrome_options.add_argument(f"--user-data-dir={user_data_dir}")
        chrome_options.add_argument(f"--profile-directory={profile_directory}")
        
        # Set realistic User-Agent
        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        chrome_options.add_argument(f'user-agent={user_agent}')
        
        # Run in headless mode
        chrome_options.add_argument('--headless=new')
        chrome_options.add_argument('--window-size=1920,1080')
        
        try:
            driver = webdriver.Chrome(options=chrome_options)
            # Optimize timeouts for faster connection
            driver.set_page_load_timeout(8)  # Reduced from 15 to 8 seconds
            driver.implicitly_wait(3)  # Add implicit wait
            self.logger.info("WebDriver created successfully")
            return driver
        except WebDriverException as e:
            self.logger.error(f"Failed to create WebDriver: {e}")
            raise
    
    def _initialize_pool(self):
        """Initialize the driver pool with specified number of drivers"""
        self.logger.info(f"Initializing driver pool with {self.pool_size} drivers")
        
        for i in range(self.pool_size):
            try:
                driver = self._create_driver()
                self.driver_queue.put(driver)
                self.logger.info(f"Driver {i+1}/{self.pool_size} added to pool")
            except Exception as e:
                self.logger.error(f"Failed to create driver {i+1}: {e}")
                # Continue with fewer drivers if some fail
                continue
        
        self.logger.info(f"Driver pool initialized with {self.driver_queue.qsize()} drivers")
    
    def get_driver(self, timeout=30):
        """Get a driver from the pool"""
        try:
            driver = self.driver_queue.get(timeout=timeout)
            with self.lock:
                self.active_drivers.add(driver)
            self.logger.debug("Driver acquired from pool")
            return driver
        except Empty:
            self.logger.error("No drivers available in pool")
            raise Exception("No drivers available in pool")
    
    def return_driver(self, driver):
        """Return a driver to the pool"""
        if driver is None:
            return
            
        try:
            with self.lock:
                if driver in self.active_drivers:
                    self.active_drivers.remove(driver)
            
            # Check if driver is still functional
            if self._is_driver_healthy(driver):
                self.driver_queue.put(driver)
                self.logger.debug("Driver returned to pool")
            else:
                self.logger.warning("Driver unhealthy, creating replacement")
                driver.quit()
                # Create replacement driver
                try:
                    new_driver = self._create_driver()
                    self.driver_queue.put(new_driver)
                    self.logger.info("Replacement driver created and added to pool")
                except Exception as e:
                    self.logger.error(f"Failed to create replacement driver: {e}")
                    
        except Exception as e:
            self.logger.error(f"Error returning driver to pool: {e}")
    
    def _is_driver_healthy(self, driver):
        """Check if driver is still functional"""
        try:
            driver.current_url
            return True
        except Exception:
            return False
    
    def cleanup(self):
        """Clean up all drivers in the pool"""
        self.logger.info("Cleaning up driver pool")
        
        # Clean up active drivers
        with self.lock:
            for driver in list(self.active_drivers):
                try:
                    driver.quit()
                except Exception as e:
                    self.logger.error(f"Error closing active driver: {e}")
            self.active_drivers.clear()
        
        # Clean up queued drivers
        while not self.driver_queue.empty():
            try:
                driver = self.driver_queue.get_nowait()
                driver.quit()
            except Empty:
                break
            except Exception as e:
                self.logger.error(f"Error closing queued driver: {e}")
        
        self.logger.info("Driver pool cleanup completed")
    
    def get_pool_status(self):
        """Get current pool status"""
        return {
            'available_drivers': self.driver_queue.qsize(),
            'active_drivers': len(self.active_drivers),
            'total_capacity': self.pool_size
        } 