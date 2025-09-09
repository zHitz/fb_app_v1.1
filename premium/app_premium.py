import webview
import logging
import threading
import time
import asyncio
import os
import subprocess
import platform
from pathlib import Path
from typing import List, Dict, Any, Optional

from premium_scraper import PremiumScraper
from data_structures import ScraperConfig, ScrapeResult, ProgressData

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('premium_scraper.log'),
        logging.StreamHandler()
    ]
)

class PremiumApi:
    """Premium API for advanced Facebook scraping with content and media extraction"""
    
    def __init__(self):
        self.scraper: Optional[PremiumScraper] = None
        self.current_task_id: Optional[str] = None
        self.results_cache: List[ScrapeResult] = []
        self.is_scraping = False
        self.lock = threading.Lock()
        self.logger = logging.getLogger(__name__)
        
        # Create downloads directory
        self.downloads_dir = Path("downloads")
        self.downloads_dir.mkdir(exist_ok=True)
        
        self.logger.info("Premium API initialized")

    def start_premium_scraping(self, urls: List[str], config: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Start premium scraping with content and media extraction
        
        Args:
            urls: List of Facebook URLs to scrape
            config: Premium configuration options
            
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
                self.current_task_id = f"premium_task_{int(time.time())}"
                self.results_cache = []

            self.logger.info(f"Starting premium scraping task {self.current_task_id} with {len(urls)} URLs")
            
            # Parse configuration
            scraper_config = self._parse_config(config or {})
            
            # Initialize premium scraper
            self.scraper = PremiumScraper(scraper_config)
            
            # Set progress callback
            def progress_callback(progress: ProgressData, result: Optional[ScrapeResult] = None):
                with self.lock:
                    if result:
                        self.results_cache.append(result)

            self.scraper.set_progress_callback(progress_callback)
            
            # Start scraping in background thread
            def scraping_worker():
                try:
                    # Run async scraping
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    
                    results = loop.run_until_complete(self.scraper.scrape_urls(urls))
                    
                    with self.lock:
                        self.results_cache = results
                        self.is_scraping = False
                    
                    self.logger.info(f"Premium scraping task {self.current_task_id} completed with {len(results)} results")
                    
                except Exception as e:
                    self.logger.error(f"Error in premium scraping worker: {e}")
                    with self.lock:
                        self.is_scraping = False
                finally:
                    loop.close()
            
            thread = threading.Thread(target=scraping_worker, daemon=True)
            thread.start()
            
            return {
                'success': True,
                'task_id': self.current_task_id,
                'message': f'Premium scraping started with {scraper_config.max_workers} workers'
            }
            
        except Exception as e:
            with self.lock:
                self.is_scraping = False
            self.logger.error(f"Error starting premium scraping: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    def get_premium_progress(self) -> Dict[str, Any]:
        """Get current premium scraping progress"""
        with self.lock:
            if self.scraper:
                progress = self.scraper.get_progress()
                return {
                    'is_scraping': self.is_scraping,
                    'task_id': self.current_task_id,
                    'progress': {
                        'total_tasks': progress.total_tasks,
                        'completed_tasks': progress.completed_tasks,
                        'failed_tasks': progress.failed_tasks,
                        'success_rate': progress.success_rate,
                        'elapsed_time': progress.elapsed_time,
                        'estimated_remaining': progress.estimated_remaining,
                        'content_extracted': progress.content_extracted,
                        'content_failed': progress.content_failed,
                        'media_found': progress.media_found,
                        'media_downloaded': progress.media_downloaded,
                        'media_failed': progress.media_failed,
                        'total_download_size': progress.total_download_size,
                        'current_activity': progress.current_activity,
                        'current_url': progress.current_url
                    },
                    'results_count': len(self.results_cache)
                }
            else:
                return {
                    'is_scraping': self.is_scraping,
                    'task_id': self.current_task_id,
                    'progress': {
                        'total_tasks': 0,
                        'completed_tasks': 0,
                        'failed_tasks': 0,
                        'success_rate': 0.0,
                        'elapsed_time': 0.0,
                        'estimated_remaining': 0.0,
                        'content_extracted': 0,
                        'content_failed': 0,
                        'media_found': 0,
                        'media_downloaded': 0,
                        'media_failed': 0,
                        'total_download_size': 0,
                        'current_activity': 'Idle',
                        'current_url': None
                    },
                    'results_count': len(self.results_cache)
                }

    def get_premium_results(self) -> Dict[str, Any]:
        """Get premium scraping results"""
        with self.lock:
            results_data = []
            for result in self.results_cache:
                # Convert result to serializable format
                result_dict = {
                    'task_id': result.task_id,
                    'url': result.url,
                    'success': result.success,
                    'error_message': result.error_message,
                    'processing_time': result.processing_time,
                    'media_downloaded': result.media_downloaded,
                    'media_failed': result.media_failed,
                    'total_download_size': result.total_download_size,
                    'post_data': {
                        'original_url': result.post_data.original_url,
                        'final_url': result.post_data.final_url,
                        'post_id': result.post_data.post_id,
                        'user_name': result.post_data.user_name,
                        'user_id': result.post_data.user_id,
                        'user_profile_url': result.post_data.user_profile_url,
                        'post_type': result.post_data.post_type.value if result.post_data.post_type else None,
                        'media_count': result.post_data.media_count,
                        'local_folder': result.post_data.local_folder,
                        'content_file': result.post_data.content_file,
                        'metadata_file': result.post_data.metadata_file,
                        'success': result.post_data.success,
                        'error_message': result.post_data.error_message,
                        'processing_time': result.post_data.processing_time,
                        'content': self._serialize_content(result.post_data.content),
                        'stats': self._serialize_stats(result.post_data.stats),
                        'media_items': self._serialize_media_items(result.post_data.media_items),
                        'scrape_timestamp': result.post_data.scrape_timestamp.isoformat(),
                        'post_timestamp': result.post_data.post_timestamp.isoformat() if result.post_data.post_timestamp else None,
                    }
                }
                results_data.append(result_dict)
            
            return {
                'success': True,
                'results': results_data,
                'total_count': len(results_data)
            }

    def stop_premium_scraping(self) -> Dict[str, Any]:
        """Stop current premium scraping process"""
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
            
            self.logger.info(f"Premium scraping task {self.current_task_id} stopped by user")
            
            return {
                'success': True,
                'message': 'Premium scraping process stopped'
            }
            
        except Exception as e:
            self.logger.error(f"Error stopping premium scraping: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    def save_premium_results(self, format_type: str = "json") -> Dict[str, Any]:
        """Save premium results to file"""
        try:
            with self.lock:
                if not self.results_cache:
                    return {
                        'success': False,
                        'error': 'No results to save'
                    }
                
                results_copy = self.results_cache.copy()
            
            # Use scraper's save method if available
            if self.scraper:
                # Convert ScrapeResult back to expected format for saving
                # This is a simplified approach - in practice, you might want to enhance the save methods
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                filename = f"premium_results_{timestamp}.{format_type}"
                
                if format_type.lower() == "json":
                    import json
                    results_data = self.get_premium_results()
                    with open(filename, 'w', encoding='utf-8') as f:
                        json.dump(results_data['results'], f, indent=2, ensure_ascii=False)
                elif format_type.lower() == "csv":
                    import csv
                    with open(filename, 'w', newline='', encoding='utf-8') as f:
                        if results_copy:
                            fieldnames = ['url', 'user_name', 'post_type', 'likes', 'comments', 'shares', 
                                        'content_text', 'media_count', 'media_downloaded', 'success', 'error_message']
                            writer = csv.DictWriter(f, fieldnames=fieldnames)
                            writer.writeheader()
                            
                            for result in results_copy:
                                writer.writerow({
                                    'url': result.post_data.original_url,
                                    'user_name': result.post_data.user_name,
                                    'post_type': result.post_data.post_type.value if result.post_data.post_type else 'unknown',
                                    'likes': result.post_data.stats.likes if result.post_data.stats else '0',
                                    'comments': result.post_data.stats.comments if result.post_data.stats else '0',
                                    'shares': result.post_data.stats.shares if result.post_data.stats else '0',
                                    'content_text': result.post_data.content.full_text if result.post_data.content else '',
                                    'media_count': result.post_data.media_count,
                                    'media_downloaded': result.media_downloaded,
                                    'success': result.success,
                                    'error_message': result.error_message or ''
                                })
                else:  # txt format
                    with open(filename, 'w', encoding='utf-8') as f:
                        for result in results_copy:
                            data = result.post_data
                            f.write(f"Bài viết của {data.user_name or 'Unknown'}\n")
                            f.write(f"URL: {data.original_url}\n")
                            if data.content and data.content.full_text:
                                f.write(f"Nội dung: {data.content.full_text}\n")
                            f.write(f"Stats: {data.stats.likes if data.stats else '0'} likes, ")
                            f.write(f"{data.stats.comments if data.stats else '0'} comments, ")
                            f.write(f"{data.stats.shares if data.stats else '0'} shares\n")
                            f.write(f"Media: {data.media_count} items, {result.media_downloaded} downloaded\n")
                            if data.local_folder:
                                f.write(f"Folder: {data.local_folder}\n")
                            f.write("-" * 80 + "\n\n")
                
                return {
                    'success': True,
                    'message': f'Results saved to {filename}',
                    'count': len(results_copy),
                    'filename': filename
                }
            else:
                return {
                    'success': False,
                    'error': 'Scraper not initialized'
                }
                
        except Exception as e:
            self.logger.error(f"Error saving premium results: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    def open_download_folder(self) -> Dict[str, Any]:
        """Open the downloads folder"""
        try:
            downloads_path = self.downloads_dir.absolute()
            
            if platform.system() == "Windows":
                os.startfile(downloads_path)
            elif platform.system() == "Darwin":  # macOS
                subprocess.run(["open", downloads_path])
            else:  # Linux
                subprocess.run(["xdg-open", downloads_path])
            
            return {'success': True}
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Could not open folder: {str(e)}'
            }

    def open_post_folder(self, folder_path: str) -> Dict[str, Any]:
        """Open a specific post folder"""
        try:
            folder_path = Path(folder_path)
            
            if not folder_path.exists():
                return {
                    'success': False,
                    'error': 'Folder does not exist'
                }
            
            if platform.system() == "Windows":
                os.startfile(folder_path)
            elif platform.system() == "Darwin":  # macOS
                subprocess.run(["open", folder_path])
            else:  # Linux
                subprocess.run(["xdg-open", folder_path])
            
            return {'success': True}
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Could not open folder: {str(e)}'
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
                
            self.logger.info("Premium API cleanup completed successfully")
            
        except Exception as e:
            self.logger.error(f"Error during premium cleanup: {str(e)}")

    # Helper methods
    def _parse_config(self, config: Dict[str, Any]) -> ScraperConfig:
        """Parse configuration dictionary to ScraperConfig"""
        return ScraperConfig(
            max_workers=min(config.get('max_workers', 2), 2),  # Limit to max 2 workers to prevent crashes
            driver_pool_size=min(config.get('driver_pool_size', 2), 2),  # Limit pool size
            rate_limit_min=config.get('rate_limit_min', 2.0),
            rate_limit_max=config.get('rate_limit_max', 5.0),
            max_retries=config.get('max_retries', 3),
            extract_content=config.get('extract_content', True),
            content_preview_words=config.get('content_preview_words', 50),
            extract_hashtags=config.get('extract_hashtags', True),
            extract_mentions=config.get('extract_mentions', True),
            download_media=config.get('download_media', True),
            media_quality=config.get('media_quality', 'high'),
            max_media_size_mb=config.get('max_media_size_mb', 50),
            create_thumbnails=config.get('create_thumbnails', True),
            organize_by_date=config.get('organize_by_date', True),
            base_download_folder=str(self.downloads_dir)
        )

    def _serialize_content(self, content):
        """Serialize PostContent for JSON"""
        if not content:
            return None
        
        return {
            'full_text': content.full_text,
            'preview_text': content.preview_text,
            'word_count': content.word_count,
            'has_more': content.has_more,
            'hashtags': content.hashtags,
            'mentions': content.mentions,
            'links': content.links
        }

    def _serialize_stats(self, stats):
        """Serialize PostStats for JSON"""
        if not stats:
            return None
        
        return {
            'likes': stats.likes,
            'comments': stats.comments,
            'shares': stats.shares,
            'reactions': stats.reactions
        }

    def _serialize_media_items(self, media_items):
        """Serialize MediaItems for JSON"""
        if not media_items:
            return []
        
        return [
            {
                'url': item.url,
                'type': item.type.value,
                'filename': item.filename,
                'local_path': item.local_path,
                'size_bytes': item.size_bytes,
                'width': item.width,
                'height': item.height,
                'duration': item.duration,
                'thumbnail_url': item.thumbnail_url,
                'download_status': item.download_status,
                'error_message': item.error_message
            }
            for item in media_items
        ]

    # Legacy compatibility methods
    def scrape(self, url: str) -> Dict[str, Any]:
        """Legacy single URL scraping for backward compatibility"""
        try:
            result = self.start_premium_scraping([url])
            if not result['success']:
                return result
            
            # Wait for completion with timeout
            timeout = 120  # 2 minutes timeout
            start_time = time.time()
            
            while time.time() - start_time < timeout:
                progress = self.get_premium_progress()
                if not progress['is_scraping']:
                    break
                time.sleep(1)
            
            # Get results
            results = self.get_premium_results()
            if results['success'] and results['results']:
                return {
                    'success': True,
                    'data': results['results'][0]['post_data']
                }
            else:
                return {
                    'success': False,
                    'error': 'No results returned'
                }
                
        except Exception as e:
            self.logger.error(f"Error in legacy scrape method: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

def main():
    # Initialize Premium API
    api = PremiumApi()
    
    # Create window with API
    window = webview.create_window(
        "Facebook Scraper Premium - Advanced Content & Media Extraction",
        "templates/premium_ui.html",
        js_api=api,
        width=1400,
        height=1000,
        resizable=True,
        min_size=(1200, 800)
    )
    
    # Cleanup on window close
    def on_window_closed():
        api.cleanup()
    
    window.events.closed += on_window_closed
    
    # Start the application
    webview.start(debug=False)

if __name__ == '__main__':
    main() 