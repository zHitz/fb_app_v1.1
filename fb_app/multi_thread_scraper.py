import time
import random
import logging
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from typing import List, Dict, Any, Callable, Optional
from dataclasses import dataclass
from queue import Queue

from driver_pool import DriverPool
from facebook_scrapper import extract_data, save_to_csv, save_to_json, save_to_txt

@dataclass
class ScrapeTask:
    """Represents a single scraping task"""
    url: str
    task_id: int
    retry_count: int = 0
    max_retries: int = 3

@dataclass
class ScrapeResult:
    """Represents the result of a scraping task"""
    task_id: int
    url: str
    data: Dict[str, Any]
    success: bool
    error_message: Optional[str] = None
    processing_time: float = 0.0

class ProgressTracker:
    """Thread-safe progress tracking"""
    
    def __init__(self, total_tasks: int):
        self.total_tasks = total_tasks
        self.completed_tasks = 0
        self.failed_tasks = 0
        self.lock = threading.Lock()
        self.start_time = time.time()
        
    def update_progress(self, success: bool = True):
        """Update progress counters"""
        with self.lock:
            self.completed_tasks += 1
            if not success:
                self.failed_tasks += 1
    
    def get_progress(self) -> Dict[str, Any]:
        """Get current progress information"""
        with self.lock:
            elapsed_time = time.time() - self.start_time
            success_rate = ((self.completed_tasks - self.failed_tasks) / max(self.completed_tasks, 1)) * 100
            
            return {
                'total_tasks': self.total_tasks,
                'completed_tasks': self.completed_tasks,
                'failed_tasks': self.failed_tasks,
                'success_rate': round(success_rate, 2),
                'elapsed_time': round(elapsed_time, 2),
                'estimated_remaining': self._estimate_remaining_time(elapsed_time)
            }
    
    def _estimate_remaining_time(self, elapsed_time: float) -> float:
        """Estimate remaining time based on current progress"""
        if self.completed_tasks == 0:
            return 0.0
        
        avg_time_per_task = elapsed_time / self.completed_tasks
        remaining_tasks = self.total_tasks - self.completed_tasks
        return round(avg_time_per_task * remaining_tasks, 2)

class MultiThreadScraper:
    """Multi-threaded Facebook scraper with rate limiting and error handling"""
    
    def __init__(self, 
                 max_workers: int = 3,
                 driver_pool_size: int = 3,
                 rate_limit_delay: tuple = (2, 5),
                 max_retries: int = 3,
                 progress_callback: Optional[Callable] = None):
        
        self.max_workers = max_workers
        self.rate_limit_delay = rate_limit_delay
        self.max_retries = max_retries
        self.progress_callback = progress_callback
        
        # Initialize driver pool
        self.driver_pool = DriverPool(pool_size=driver_pool_size)
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        
        # Threading controls
        self.shutdown_event = threading.Event()
        self.rate_limiter = threading.Semaphore(max_workers)
        
    def scrape_urls(self, urls: List[str]) -> List[ScrapeResult]:
        """
        Scrape multiple URLs concurrently
        
        Args:
            urls: List of Facebook URLs to scrape
            
        Returns:
            List of ScrapeResult objects
        """
        if not urls:
            self.logger.warning("No URLs provided for scraping")
            return []
        
        # Create scraping tasks
        tasks = [ScrapeTask(url=url, task_id=i, max_retries=self.max_retries) 
                for i, url in enumerate(urls)]
        
        # Initialize progress tracker
        progress_tracker = ProgressTracker(len(tasks))
        
        # Results storage
        results = []
        results_lock = threading.Lock()
        
        self.logger.info(f"Starting multi-threaded scraping of {len(urls)} URLs with {self.max_workers} workers")
        
        try:
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                # Submit all tasks
                future_to_task = {
                    executor.submit(self._scrape_single_url, task, progress_tracker, results_lock, results): task
                    for task in tasks
                }
                
                # Process completed tasks
                for future in as_completed(future_to_task):
                    if self.shutdown_event.is_set():
                        self.logger.info("Shutdown event received, cancelling remaining tasks")
                        break
                        
                    task = future_to_task[future]
                    try:
                        result = future.result()
                        if result:
                            with results_lock:
                                results.append(result)
                                
                        # Update progress and notify callback
                        progress = progress_tracker.get_progress()
                        if self.progress_callback:
                            self.progress_callback(progress, result)
                            
                    except Exception as e:
                        self.logger.error(f"Unexpected error processing task {task.task_id}: {e}")
                        
        except KeyboardInterrupt:
            self.logger.info("Keyboard interrupt received, shutting down gracefully")
            self.shutdown_event.set()
            
        except Exception as e:
            self.logger.error(f"Error in multi-threaded scraping: {e}")
            
        finally:
            # Final progress update
            final_progress = progress_tracker.get_progress()
            self.logger.info(f"Scraping completed: {final_progress}")
            
        # Sort results by task_id to maintain order
        results.sort(key=lambda x: x.task_id)
        return results
    
    def _scrape_single_url(self, 
                          task: ScrapeTask, 
                          progress_tracker: ProgressTracker,
                          results_lock: threading.Lock,
                          results: List[ScrapeResult]) -> Optional[ScrapeResult]:
        """
        Scrape a single URL with retry logic and rate limiting
        
        Args:
            task: ScrapeTask to process
            progress_tracker: Progress tracking instance
            results_lock: Thread lock for results list
            results: Shared results list
            
        Returns:
            ScrapeResult or None
        """
        driver = None
        start_time = time.time()
        
        try:
            # Rate limiting
            with self.rate_limiter:
                if self.shutdown_event.is_set():
                    return None
                
                # Get driver from pool
                driver = self.driver_pool.get_driver(timeout=30)
                
                # Add random delay for rate limiting
                delay = random.uniform(*self.rate_limit_delay)
                time.sleep(delay)
                
                self.logger.info(f"Processing task {task.task_id}: {task.url}")
                
                # Perform scraping
                data = extract_data(driver, task.url)
                processing_time = time.time() - start_time
                
                # Create result
                result = ScrapeResult(
                    task_id=task.task_id,
                    url=task.url,
                    data=data,
                    success=data.get('error_message') is None,
                    error_message=data.get('error_message'),
                    processing_time=processing_time
                )
                
                # Update progress
                progress_tracker.update_progress(result.success)
                
                self.logger.info(f"Task {task.task_id} completed in {processing_time:.2f}s - Success: {result.success}")
                
                return result
                
        except Exception as e:
            processing_time = time.time() - start_time
            error_msg = f"Error processing task {task.task_id}: {str(e)}"
            self.logger.error(error_msg)
            
            # Check if we should retry
            if task.retry_count < task.max_retries and not self.shutdown_event.is_set():
                task.retry_count += 1
                self.logger.info(f"Retrying task {task.task_id} (attempt {task.retry_count}/{task.max_retries})")
                
                # Exponential backoff for retries
                retry_delay = min(2 ** task.retry_count, 10)
                time.sleep(retry_delay)
                
                # Recursive retry
                return self._scrape_single_url(task, progress_tracker, results_lock, results)
            else:
                # Create error result
                result = ScrapeResult(
                    task_id=task.task_id,
                    url=task.url,
                    data={'error_message': str(e), 'original_url': task.url},
                    success=False,
                    error_message=str(e),
                    processing_time=processing_time
                )
                
                progress_tracker.update_progress(False)
                return result
                
        finally:
            # Return driver to pool
            if driver:
                self.driver_pool.return_driver(driver)
    
    def save_results(self, results: List[ScrapeResult], format_type: str = "txt"):
        """
        Save scraping results to file
        
        Args:
            results: List of ScrapeResult objects
            format_type: Output format ("txt", "csv", "json")
        """
        if not results:
            self.logger.warning("No results to save")
            return
        
        # Convert results to data format
        data_list = [result.data for result in results]
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        try:
            if format_type.lower() == "csv":
                filename = f"facebook_data_multi_{timestamp}.csv"
                save_to_csv(data_list, filename)
            elif format_type.lower() == "json":
                filename = f"facebook_data_multi_{timestamp}.json"
                save_to_json(data_list, filename)
            else:  # default to txt
                filename = f"facebook_data_multi_{timestamp}.txt"
                save_to_txt(data_list, filename)
                
            self.logger.info(f"Results saved to {filename}")
            
        except Exception as e:
            self.logger.error(f"Error saving results: {e}")
    
    def get_driver_pool_status(self) -> Dict[str, Any]:
        """Get current driver pool status"""
        return self.driver_pool.get_pool_status()
    
    def shutdown(self):
        """Gracefully shutdown the scraper"""
        self.logger.info("Shutting down multi-thread scraper")
        self.shutdown_event.set()
        
        # Cleanup driver pool
        if hasattr(self, 'driver_pool'):
            self.driver_pool.cleanup()
        
        self.logger.info("Multi-thread scraper shutdown completed")

def create_progress_callback():
    """Create a simple progress callback function"""
    def progress_callback(progress: Dict[str, Any], result: Optional[ScrapeResult] = None):
        completed = progress['completed_tasks']
        total = progress['total_tasks']
        success_rate = progress['success_rate']
        elapsed = progress['elapsed_time']
        
        print(f"Progress: {completed}/{total} ({success_rate}% success) - Elapsed: {elapsed}s")
        
        if result:
            status = "✓" if result.success else "✗"
            print(f"  {status} Task {result.task_id}: {result.url[:50]}... ({result.processing_time:.2f}s)")
    
    return progress_callback

# Example usage
if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Example URLs (replace with actual URLs)
    urls = [
        "https://facebook.com/example1",
        "https://facebook.com/example2",
        "https://facebook.com/example3"
    ]
    
    # Create scraper with progress callback
    progress_callback = create_progress_callback()
    scraper = MultiThreadScraper(
        max_workers=3,
        driver_pool_size=3,
        progress_callback=progress_callback
    )
    
    try:
        # Perform scraping
        results = scraper.scrape_urls(urls)
        
        # Save results
        scraper.save_results(results, "txt")
        
        print(f"\nScraping completed! Processed {len(results)} URLs")
        
    finally:
        # Cleanup
        scraper.shutdown() 