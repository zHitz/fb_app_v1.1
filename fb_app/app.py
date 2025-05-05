import webview
import logging
from facebook_scrapper import setup_driver, extract_data

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class Api:
    def __init__(self):
        self.driver = None
        logging.info("API initialized")

    def scrape(self, url):
        """
        Scrape a Facebook post URL and return the data.
        
        Args:
            url (str): The Facebook post URL to scrape
            
        Returns:
            dict: Scraped data or error information
        """
        try:
            logging.info(f"Starting scrape for URL: {url}")
            
            # Setup driver if not already set
            if not self.driver:
                self.driver = setup_driver()
            
            # Extract data
            result = extract_data(self.driver, url)
            logging.info(f"Successfully scraped data for URL: {url}")
            
            return {
                'success': True,
                'data': result
            }
            
        except Exception as e:
            logging.error(f"Error scraping URL {url}: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    def cleanup(self):
        """Clean up resources"""
        try:
            if self.driver:
                self.driver.quit()
                self.driver = None
                logging.info("Driver cleaned up successfully")
        except Exception as e:
            logging.error(f"Error during cleanup: {str(e)}")

def main():
    # Initialize API
    api = Api()
    
    # Create window with API
    window = webview.create_window(
        "Facebook Post Scraper",
        "index.html",
        js_api=api,
        width=1000,
        height=800,
        resizable=True,
        min_size=(800, 600)
    )
    
    # Start the application
    webview.start()

if __name__ == '__main__':
    main()
