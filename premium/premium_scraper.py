import time
import random
import logging
import threading
import asyncio
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from typing import List, Dict, Any, Callable, Optional
from pathlib import Path

# Selenium imports
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException, NoSuchElementException

from data_structures import (
    PostData, ScrapeTask, ScrapeResult, ProgressData, ScraperConfig,
    PostType, PostStats, MediaItem
)
from content_extractor import ContentExtractor
from media_downloader import MediaDownloader

# Import from parent directory
import sys
sys.path.append('../fb_app')
from driver_pool import DriverPool

class PremiumScraper:
    """Premium multi-threaded Facebook scraper with content and media extraction"""
    
    def __init__(self, config: ScraperConfig = None):
        self.config = config or ScraperConfig()
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self.driver_pool = DriverPool(
            pool_size=self.config.driver_pool_size,
            max_retries=self.config.max_retries
        )
        
        self.content_extractor = ContentExtractor(
            preview_words=self.config.content_preview_words
        )
        
        # Progress tracking
        self.progress_data = ProgressData(total_tasks=0)
        self.progress_lock = threading.Lock()
        self.progress_callback = None
        
        # Control flags
        self.shutdown_event = threading.Event()
        self.is_running = False
        
        # Rate limiting
        self.scrape_semaphore = threading.Semaphore(self.config.max_workers)
        self.download_semaphore = threading.Semaphore(self.config.max_workers * 2)  # Allow more downloads

    def set_progress_callback(self, callback: Callable[[ProgressData, Optional[ScrapeResult]], None]):
        """Set progress callback function"""
        self.progress_callback = callback

    async def scrape_urls(self, urls: List[str]) -> List[ScrapeResult]:
        """
        Main scraping method with enhanced features
        
        Args:
            urls: List of Facebook URLs to scrape
            
        Returns:
            List of ScrapeResult objects with full data
        """
        if not urls:
            self.logger.warning("No URLs provided for scraping")
            return []
        
        self.is_running = True
        self.shutdown_event.clear()
        
        # Initialize progress
        with self.progress_lock:
            self.progress_data = ProgressData(total_tasks=len(urls))
            self.progress_data.current_activity = "Initializing scraping..."
        
        # Create tasks
        tasks = [
            ScrapeTask(
                url=url,
                task_id=i,
                max_retries=self.config.max_retries,
                extract_content=self.config.extract_content,
                download_media=self.config.download_media,
                media_quality=self.config.media_quality,
                max_media_size_mb=self.config.max_media_size_mb
            )
            for i, url in enumerate(urls)
        ]
        
        self.logger.info(f"Starting premium scraping of {len(urls)} URLs")
        
        try:
            # Run scraping with thread pool
            with ThreadPoolExecutor(max_workers=self.config.max_workers) as executor:
                # Submit all tasks
                future_to_task = {
                    executor.submit(self._scrape_single_task, task): task
                    for task in tasks
                }
                
                results = []
                
                # Process completed tasks
                for future in as_completed(future_to_task):
                    if self.shutdown_event.is_set():
                        self.logger.info("Shutdown requested, cancelling remaining tasks")
                        break
                    
                    task = future_to_task[future]
                    
                    try:
                        result = future.result()
                        if result:
                            results.append(result)
                            
                            # Update progress
                            self._update_progress(result)
                            
                            # Notify callback
                            if self.progress_callback:
                                with self.progress_lock:
                                    self.progress_callback(self.progress_data, result)
                    
                    except Exception as e:
                        self.logger.error(f"Error processing task {task.task_id}: {e}")
                        
                        # Create error result
                        error_result = ScrapeResult(
                            task_id=task.task_id,
                            url=task.url,
                            post_data=PostData(original_url=task.url, error_message=str(e)),
                            success=False,
                            error_message=str(e)
                        )
                        results.append(error_result)
                        self._update_progress(error_result)
            
            # Sort results by task_id
            results.sort(key=lambda x: x.task_id)
            
            # Final progress update
            with self.progress_lock:
                self.progress_data.current_activity = "Scraping completed"
                if self.progress_callback:
                    self.progress_callback(self.progress_data, None)
            
            self.logger.info(f"Premium scraping completed: {len(results)} results")
            return results
            
        except Exception as e:
            self.logger.error(f"Error in premium scraping: {e}")
            return []
        
        finally:
            self.is_running = False

    def _scrape_single_task(self, task: ScrapeTask) -> Optional[ScrapeResult]:
        """Scrape a single URL with enhanced extraction"""
        start_time = time.time()
        driver = None
        
        try:
            # Rate limiting
            with self.scrape_semaphore:
                if self.shutdown_event.is_set():
                    return None
                
                # Update current activity
                with self.progress_lock:
                    self.progress_data.current_activity = f"Processing {task.url[:50]}..."
                    self.progress_data.current_url = task.url
                
                # Get driver
                driver = self.driver_pool.get_driver(timeout=30)
                
                # Add delay for rate limiting
                delay = random.uniform(self.config.rate_limit_min, self.config.rate_limit_max)
                time.sleep(delay)
                
                self.logger.info(f"Processing task {task.task_id}: {task.url}")
                
                # Perform enhanced extraction
                post_data = self._extract_enhanced_data(driver, task)
                
                processing_time = time.time() - start_time
                post_data.processing_time = processing_time
                
                # Download media if requested
                if task.download_media and post_data.media_items:
                    asyncio.run(self._download_media_for_post(post_data))
                
                # Create result
                result = ScrapeResult(
                    task_id=task.task_id,
                    url=task.url,
                    post_data=post_data,
                    success=post_data.success,
                    error_message=post_data.error_message,
                    processing_time=processing_time,
                    media_downloaded=sum(1 for item in post_data.media_items if item.download_status == "completed"),
                    media_failed=sum(1 for item in post_data.media_items if item.download_status == "failed"),
                    total_download_size=sum(item.size_bytes or 0 for item in post_data.media_items)
                )
                
                self.logger.info(f"Task {task.task_id} completed in {processing_time:.2f}s - Success: {result.success}")
                return result
        
        except Exception as e:
            processing_time = time.time() - start_time
            error_msg = f"Error processing task {task.task_id}: {str(e)}"
            self.logger.error(error_msg)
            
            # Retry logic
            if task.retry_count < task.max_retries and not self.shutdown_event.is_set():
                task.retry_count += 1
                self.logger.info(f"Retrying task {task.task_id} (attempt {task.retry_count}/{task.max_retries})")
                
                # Exponential backoff
                retry_delay = min(self.config.retry_delay_base ** task.retry_count, 10)
                time.sleep(retry_delay)
                
                return self._scrape_single_task(task)
            else:
                # Create error result
                post_data = PostData(
                    original_url=task.url,
                    error_message=str(e),
                    success=False
                )
                
                return ScrapeResult(
                    task_id=task.task_id,
                    url=task.url,
                    post_data=post_data,
                    success=False,
                    error_message=str(e),
                    processing_time=processing_time
                )
        
        finally:
            if driver:
                self.driver_pool.return_driver(driver)

    def _extract_enhanced_data(self, driver, task: ScrapeTask) -> PostData:
        """Enhanced data extraction with content and media"""
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        from selenium.webdriver.common.by import By
        from selenium.common.exceptions import TimeoutException
        from bs4 import BeautifulSoup
        
        post_data = PostData(original_url=task.url)
        wait = WebDriverWait(driver, 10)
        
        try:
            # Navigate to URL
            driver.get(task.url)
            post_data.final_url = driver.current_url
            
            # Check if it's a video page
            is_video = self._is_video_page(wait)
            
            # Get page source for BeautifulSoup
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            dialog_soup = soup.find('div', {'role': 'dialog'}) if not is_video else soup
            
            if not dialog_soup and not is_video:
                post_data.error_message = "Could not find post content"
                return post_data
            
            # Extract basic info
            post_data.user_name = self._extract_username(driver, is_video)
            post_data.post_id = self._extract_post_id(post_data.final_url)
            
            # Extract stats
            post_data.stats = self._extract_stats(driver, dialog_soup, is_video)
            
            # Extract content if requested
            if task.extract_content:
                with self.progress_lock:
                    self.progress_data.current_activity = f"Extracting content for post {task.task_id}..."
                
                post_data.content = self.content_extractor.extract_post_content(driver, dialog_soup)
                
                if post_data.content:
                    with self.progress_lock:
                        self.progress_data.content_extracted += 1
                else:
                    with self.progress_lock:
                        self.progress_data.content_failed += 1
            
            # Extract media URLs if needed
            if self.config.download_media:  # Only extract if download is enabled
                with self.progress_lock:
                    self.progress_data.current_activity = f"Finding media for post {task.task_id}..."
                
                post_data.media_items = self.content_extractor.extract_media_urls(driver, dialog_soup)
                post_data.media_count = len(post_data.media_items)
                
                with self.progress_lock:
                    self.progress_data.media_found += len(post_data.media_items)
            else:
                # Skip media extraction when download is disabled
                post_data.media_items = []
                post_data.media_count = 0
            
            # Detect post type
            post_data.post_type = self.content_extractor.detect_post_type(post_data.content, post_data.media_items)
            
            # Extract timestamp
            post_data.post_timestamp = self.content_extractor.extract_post_timestamp(driver, dialog_soup)
            
            post_data.success = True
            
        except Exception as e:
            post_data.error_message = str(e)
            post_data.success = False
            self.logger.error(f"Error in enhanced extraction: {e}")
        
        return post_data

    async def _download_media_for_post(self, post_data: PostData):
        """Download media for a single post"""
        if not post_data.media_items:
            return
        
        try:
            with self.progress_lock:
                self.progress_data.current_activity = f"Downloading {len(post_data.media_items)} media files..."
            
            # Use MediaDownloader
            async with MediaDownloader(self.config.base_download_folder) as downloader:
                
                def download_progress_callback(url, progress, downloaded, total):
                    # Update download progress
                    pass  # Could implement detailed progress tracking here
                
                successful, failed = await downloader.download_post_media(
                    post_data, 
                    progress_callback=download_progress_callback
                )
                
                # Update progress
                with self.progress_lock:
                    self.progress_data.media_downloaded += len(successful)
                    self.progress_data.media_failed += len(failed)
                    
                    # Calculate total download size
                    total_size = sum(item.size_bytes or 0 for item in post_data.media_items if item.size_bytes)
                    self.progress_data.total_download_size += total_size
                
                # Create thumbnails if requested
                if self.config.create_thumbnails:
                    await downloader.create_thumbnails(post_data)
                
                self.logger.info(f"Downloaded {len(successful)} media files, {len(failed)} failed for post {post_data.original_url}")
        
        except Exception as e:
            self.logger.error(f"Error downloading media for post: {e}")
            # Mark all media as failed
            for item in post_data.media_items:
                if item.download_status == "pending":
                    item.download_status = "failed"
                    item.error_message = str(e)

    def _is_video_page(self, wait):
        """Check if current page is a video page"""
        try:
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support import expected_conditions as EC
            from selenium.common.exceptions import TimeoutException
            
            wait.until(EC.presence_of_element_located((By.XPATH, "//div[@role='dialog']")))
            return False  # Has dialog, it's a regular post
        except TimeoutException:
            return True  # No dialog, it's a video page

    def _extract_username(self, driver, is_video: bool) -> Optional[str]:
        """Extract username based on page type - improved logic from working version"""
        wait = WebDriverWait(driver, 10)
        
        try:
            if is_video:
                # Video page username extraction
                try:
                    xpath = "/html/body/div[1]/div/div[1]/div/div[3]/div/div/div[1]/div[2]/div/div/div/div[1]/div/div/div[2]/div[1]/div[1]/div[2]/div/div[1]/span/div/h2/span/span[1]/span/a/strong/span"
                    element = driver.find_element(By.XPATH, xpath)
                    username = element.text.strip()
                    self.logger.info(f"Extracted video username: {username}")
                    return username or "Not found"
                except:
                    self.logger.warning("Video username extraction failed")
                    return "Not found"
            else:
                # Regular post username extraction - using working logic from original app
                try:
                    user_element = wait.until(EC.visibility_of_element_located((By.XPATH, "//div[@role='dialog']//span[contains(text(), 'Bài viết của')]")))
                    user_text = user_element.text.strip()
                    username = user_text.replace("Bài viết của ", "") if user_text.startswith("Bài viết của ") else user_text
                    username = username or "Unknown"
                    self.logger.info(f"Extracted post username: {username}")
                    return username
                except (NoSuchElementException, TimeoutException):
                    self.logger.warning("Post username not found with primary method")
                    
                    # Fallback methods
                    try:
                        # Try alternative selectors
                        selectors = [
                            "//div[@role='dialog']//h2//span//a//strong//span",
                            "//div[@role='dialog']//h3//span//a//strong//span", 
                            "//div[@role='dialog']//strong[contains(@class, 'x1heor9g')]//span",
                            "//div[@role='dialog']//a[contains(@role, 'link')]//strong//span"
                        ]
                        
                        for selector in selectors:
                            try:
                                element = wait.until(EC.presence_of_element_located((By.XPATH, selector)))
                                username = element.text.strip()
                                if username and len(username) > 0:
                                    self.logger.info(f"Extracted username with fallback: {username}")
                                    return username
                            except:
                                continue
                                
                    except:
                        pass
                    
                    self.logger.warning("All username extraction methods failed")
                    return "Not found"
            
        except Exception as e:
            self.logger.error(f"Username extraction error: {e}")
            return "Unknown"

    def _extract_post_id(self, url: str) -> Optional[str]:
        """Extract post ID from URL"""
        try:
            import re
            # Try to extract post ID from various URL patterns
            patterns = [
                r'/posts/(\d+)',
                r'/permalink\.php\?story_fbid=(\d+)',
                r'fbid=(\d+)',
                r'/(\d+)/?$'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, url)
                if match:
                    return match.group(1)
            
            return None
        except Exception:
            return None

    def _extract_stats(self, driver, dialog_soup, is_video: bool) -> PostStats:
        """Extract engagement statistics"""
        stats = PostStats()
        
        try:
            if is_video:
                # Video stats extraction (reuse existing logic)
                from selenium.webdriver.support.ui import WebDriverWait
                from selenium.webdriver.support import expected_conditions as EC
                from selenium.webdriver.common.by import By
                from selenium.common.exceptions import TimeoutException
                
                wait = WebDriverWait(driver, 5)
                
                # Likes
                try:
                    likes_xpath = "/html/body/div[1]/div/div[1]/div/div[3]/div/div/div[1]/div[2]/div/div/div/div[1]/div/div/div[1]/div[2]/div[2]/div/div/div[2]/div/div[1]/div/span/span/span"
                    likes_element = wait.until(EC.presence_of_element_located((By.XPATH, likes_xpath)))
                    stats.likes = likes_element.text.strip()
                except TimeoutException:
                    stats.likes = "0"
                
                # Comments
                try:
                    comments_xpath = "/html/body/div[1]/div/div[1]/div/div[3]/div/div/div[1]/div[2]/div/div/div/div[1]/div/div/div[1]/div[2]/div[2]/div/div/div[2]/div/div[3]/span/div/span/span"
                    comments_element = wait.until(EC.presence_of_element_located((By.XPATH, comments_xpath)))
                    comments_text = comments_element.text.strip()
                    stats.comments = comments_text.split('bình luận')[0].split('comment')[0].strip()
                except TimeoutException:
                    stats.comments = "0"
                
            else:
                # Regular post stats extraction (reuse existing logic)
                from selenium.webdriver.support.ui import WebDriverWait
                from selenium.webdriver.support import expected_conditions as EC
                from selenium.webdriver.common.by import By
                from selenium.common.exceptions import TimeoutException, NoSuchElementException
                
                wait = WebDriverWait(driver, 5)
                
                # Comments
                try:
                    comments_xpath = "//div[@role='dialog']//span[contains(text(), 'bình luận') or contains(text(), 'comment')]"
                    comments_element = wait.until(EC.visibility_of_element_located((By.XPATH, comments_xpath)))
                    comments_text = comments_element.text.strip()
                    stats.comments = comments_text.split('bình luận')[0].split('comment')[0].strip()
                except (NoSuchElementException, TimeoutException):
                    stats.comments = "0"
                
                # Shares
                try:
                    shares_xpath = "//div[@role='dialog']//span[contains(text(), 'lượt chia sẻ') or contains(text(), 'share')]"
                    shares_element = wait.until(EC.visibility_of_element_located((By.XPATH, shares_xpath)))
                    shares_text = shares_element.text.strip()
                    stats.shares = shares_text.split('lượt chia sẻ')[0].split('share')[0].strip()
                except (NoSuchElementException, TimeoutException):
                    stats.shares = "0"
                
                # Likes (complex extraction logic)
                try:
                    likes_xpath = "/html/body/div[1]/div/div[1]/div/div[5]/div/div/div[2]/div/div/div/div/div/div/div/div[2]/div[2]/div/div/div/div/div/div/div/div/div/div/div/div/div[13]/div/div/div[4]/div/div/div[1]/div/div[1]/div/div[1]/div/span/div/span[2]/span/span"
                    likes_element = wait.until(EC.visibility_of_element_located((By.XPATH, likes_xpath)))
                    stats.likes = likes_element.text.strip()
                except (NoSuchElementException, TimeoutException):
                    # Fallback strategies...
                    stats.likes = "0"
        
        except Exception as e:
            self.logger.error(f"Error extracting stats: {e}")
        
        return stats

    def _update_progress(self, result: ScrapeResult):
        """Update progress tracking"""
        with self.progress_lock:
            self.progress_data.completed_tasks += 1
            
            if not result.success:
                self.progress_data.failed_tasks += 1
            
            # Calculate success rate
            if self.progress_data.completed_tasks > 0:
                success_count = self.progress_data.completed_tasks - self.progress_data.failed_tasks
                self.progress_data.success_rate = (success_count / self.progress_data.completed_tasks) * 100
            
            # Update time estimates
            elapsed = time.time() - getattr(self.progress_data, '_start_time', time.time())
            self.progress_data.elapsed_time = elapsed
            
            if self.progress_data.completed_tasks > 0:
                avg_time = elapsed / self.progress_data.completed_tasks
                remaining_tasks = self.progress_data.total_tasks - self.progress_data.completed_tasks
                self.progress_data.estimated_remaining = avg_time * remaining_tasks

    def get_progress(self) -> ProgressData:
        """Get current progress data"""
        with self.progress_lock:
            return self.progress_data

    def shutdown(self):
        """Gracefully shutdown the scraper"""
        self.logger.info("Shutting down premium scraper")
        self.shutdown_event.set()
        self.is_running = False
        
        # Cleanup driver pool
        if hasattr(self, 'driver_pool'):
            self.driver_pool.cleanup()
        
        self.logger.info("Premium scraper shutdown completed")

# Utility function
def create_premium_progress_callback():
    """Create enhanced progress callback for premium features"""
    def progress_callback(progress: ProgressData, result: Optional[ScrapeResult] = None):
        completed = progress.completed_tasks
        total = progress.total_tasks
        success_rate = progress.success_rate
        elapsed = progress.elapsed_time
        
        print(f"Progress: {completed}/{total} ({success_rate:.1f}% success) - {elapsed:.1f}s elapsed")
        print(f"Content: {progress.content_extracted} extracted, {progress.content_failed} failed")
        print(f"Media: {progress.media_found} found, {progress.media_downloaded} downloaded, {progress.media_failed} failed")
        print(f"Download size: {progress.total_download_size / (1024*1024):.1f} MB")
        print(f"Activity: {progress.current_activity}")
        
        if result:
            status = "✓" if result.success else "✗"
            media_info = f"({result.media_downloaded} media)" if result.media_downloaded > 0 else ""
            print(f"  {status} Task {result.task_id}: {result.url[:50]}... {media_info} ({result.processing_time:.2f}s)")
        
        print("-" * 80)
    
    return progress_callback 