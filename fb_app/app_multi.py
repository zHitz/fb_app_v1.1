import webview
import logging
import threading
import time
from typing import List, Dict, Any, Optional
from multi_thread_scraper import MultiThreadScraper, ScrapeResult

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraper_multi.log'),
        logging.StreamHandler()
    ]
)

class MultiThreadApi:
    def __init__(self):
        self.scraper: Optional[MultiThreadScraper] = None
        self.current_task_id: Optional[str] = None
        self.progress_data: Dict[str, Any] = {}
        self.results_cache: List[ScrapeResult] = []
        self.is_scraping = False
        self.lock = threading.Lock()
        logging.info("Multi-thread API initialized")

    def start_scraping(self, urls: List[str], config: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Start multi-threaded scraping process
        
        Args:
            urls: List of Facebook URLs to scrape
            config: Configuration options (max_workers, rate_limit, etc.)
            
        Returns:
            dict: Status and task information
        """
        try:
            with self.lock:
                if self.is_scraping:
                    return {
                        'success': False,
                        'error': 'Scraping is already in progress'
                    }
                
                self.is_scraping = True
                self.current_task_id = f"task_{int(time.time())}"
                self.results_cache = []
                self.progress_data = {
                    'total_tasks': len(urls),
                    'completed_tasks': 0,
                    'failed_tasks': 0,
                    'success_rate': 0.0,
                    'elapsed_time': 0.0,
                    'estimated_remaining': 0.0
                }

            logging.info(f"Starting scraping task {self.current_task_id} with {len(urls)} URLs")
            
            # Parse configuration
            if config is None:
                config = {}
            
            max_workers = config.get('max_workers', 3)
            driver_pool_size = config.get('driver_pool_size', 3)
            rate_limit_min = config.get('rate_limit_min', 2)
            rate_limit_max = config.get('rate_limit_max', 5)
            max_retries = config.get('max_retries', 3)
            
            # Create progress callback
            def progress_callback(progress: Dict[str, Any], result: Optional[ScrapeResult] = None):
                with self.lock:
                    self.progress_data = progress
                    if result:
                        self.results_cache.append(result)

            # Initialize scraper
            self.scraper = MultiThreadScraper(
                max_workers=max_workers,
                driver_pool_size=driver_pool_size,
                rate_limit_delay=(rate_limit_min, rate_limit_max),
                max_retries=max_retries,
                progress_callback=progress_callback
            )
            
            # Start scraping in background thread
            def scraping_worker():
                try:
                    results = self.scraper.scrape_urls(urls)
                    
                    with self.lock:
                        self.results_cache = results
                        self.is_scraping = False
                    
                    logging.info(f"Scraping task {self.current_task_id} completed with {len(results)} results")
                    
                except Exception as e:
                    logging.error(f"Error in scraping worker: {e}")
                    with self.lock:
                        self.is_scraping = False
                        self.progress_data['error'] = str(e)
            
            thread = threading.Thread(target=scraping_worker, daemon=True)
            thread.start()
            
            return {
                'success': True,
                'task_id': self.current_task_id,
                'message': f'Scraping started with {max_workers} workers'
            }
            
        except Exception as e:
            with self.lock:
                self.is_scraping = False
            logging.error(f"Error starting scraping: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    def get_progress(self) -> Dict[str, Any]:
        """Get current scraping progress"""
        with self.lock:
            return {
                'is_scraping': self.is_scraping,
                'task_id': self.current_task_id,
                'progress': self.progress_data.copy(),
                'results_count': len(self.results_cache)
            }

    def get_results(self) -> Dict[str, Any]:
        """Get scraping results"""
        with self.lock:
            results_data = []
            for result in self.results_cache:
                results_data.append({
                    'task_id': result.task_id,
                    'url': result.url,
                    'success': result.success,
                    'data': result.data,
                    'error_message': result.error_message,
                    'processing_time': result.processing_time
                })
            
            return {
                'success': True,
                'results': results_data,
                'total_count': len(results_data)
            }

    def stop_scraping(self) -> Dict[str, Any]:
        """Stop current scraping process"""
        try:
            with self.lock:
                if not self.is_scraping:
                    return {
                        'success': False,
                        'error': 'No scraping process is currently running'
                    }
                
                if self.scraper:
                    self.scraper.shutdown()
                
                self.is_scraping = False
            
            logging.info(f"Scraping task {self.current_task_id} stopped by user")
            
            return {
                'success': True,
                'message': 'Scraping process stopped'
            }
            
        except Exception as e:
            logging.error(f"Error stopping scraping: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    def save_results(self, format_type: str = "txt") -> Dict[str, Any]:
        """Save current results to file"""
        try:
            with self.lock:
                if not self.results_cache:
                    return {
                        'success': False,
                        'error': 'No results to save'
                    }
                
                results_copy = self.results_cache.copy()
            
            if self.scraper:
                self.scraper.save_results(results_copy, format_type)
                
                return {
                    'success': True,
                    'message': f'Results saved in {format_type} format',
                    'count': len(results_copy)
                }
            else:
                return {
                    'success': False,
                    'error': 'Scraper not initialized'
                }
                
        except Exception as e:
            logging.error(f"Error saving results: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    def get_driver_status(self) -> Dict[str, Any]:
        """Get driver pool status"""
        try:
            if self.scraper:
                status = self.scraper.get_driver_pool_status()
                return {
                    'success': True,
                    'status': status
                }
            else:
                return {
                    'success': False,
                    'error': 'Scraper not initialized'
                }
                
        except Exception as e:
            logging.error(f"Error getting driver status: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    def cleanup(self):
        """Clean up resources"""
        try:
            with self.lock:
                if self.scraper:
                    self.scraper.shutdown()
                    self.scraper = None
                
                self.is_scraping = False
                self.results_cache = []
                self.progress_data = {}
                
            logging.info("API cleanup completed successfully")
            
        except Exception as e:
            logging.error(f"Error during cleanup: {str(e)}")

    # Legacy single URL scraping for backward compatibility
    def scrape(self, url: str) -> Dict[str, Any]:
        """
        Legacy single URL scraping method for backward compatibility
        
        Args:
            url: Single Facebook URL to scrape
            
        Returns:
            dict: Scraped data or error information
        """
        try:
            # Use multi-threading for single URL too
            result = self.start_scraping([url])
            if not result['success']:
                return result
            
            # Wait for completion (with timeout)
            timeout = 60  # 60 seconds timeout
            start_time = time.time()
            
            while time.time() - start_time < timeout:
                progress = self.get_progress()
                if not progress['is_scraping']:
                    break
                time.sleep(1)
            
            # Get results
            results = self.get_results()
            if results['success'] and results['results']:
                return {
                    'success': True,
                    'data': results['results'][0]['data']
                }
            else:
                return {
                    'success': False,
                    'error': 'No results returned'
                }
                
        except Exception as e:
            logging.error(f"Error in legacy scrape method: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

def main():
    # Initialize API
    api = MultiThreadApi()
    
    # Create window with API
    window = webview.create_window(
        "Facebook Post Scraper - Multi-Thread",
        "index_multi.html",
        js_api=api,
        width=1200,
        height=900,
        resizable=True,
        min_size=(1000, 700)
    )
    
    # Cleanup on window close
    def on_window_closed():
        api.cleanup()
    
    window.events.closed += on_window_closed
    
    # Start the application
    webview.start()

if __name__ == '__main__':
    main() 