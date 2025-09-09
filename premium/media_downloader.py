import os
import asyncio
import aiohttp
import aiofiles
import hashlib
import mimetypes
from pathlib import Path
from typing import List, Optional, Tuple, Dict, Any
import logging
from datetime import datetime
import json

from data_structures import MediaItem, MediaType, PostData

class MediaDownloader:
    """Advanced media downloader with async support and progress tracking"""
    
    def __init__(self, base_folder: str = "downloads", max_concurrent: int = 5):
        self.base_folder = Path(base_folder)
        self.max_concurrent = max_concurrent
        self.logger = logging.getLogger(__name__)
        
        # Create base folder
        self.base_folder.mkdir(exist_ok=True)
        
        # Download session
        self.session = None
        
        # Progress tracking
        self.download_progress = {}
        
    async def __aenter__(self):
        """Async context manager entry"""
        timeout = aiohttp.ClientTimeout(total=30, connect=10)
        connector = aiohttp.TCPConnector(limit=20, limit_per_host=5)
        
        self.session = aiohttp.ClientSession(
            timeout=timeout,
            connector=connector,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()

    def create_post_folder(self, post_data: PostData) -> Path:
        """Create organized folder structure for a post"""
        try:
            # Generate folder name
            timestamp = post_data.scrape_timestamp.strftime("%Y%m%d_%H%M%S")
            user_name = self._sanitize_filename(post_data.user_name or "unknown")
            post_id = post_data.post_id or f"post_{timestamp}"
            
            folder_name = f"{timestamp}_{user_name}_{post_id}"
            post_folder = self.base_folder / folder_name
            
            # Create folder structure
            post_folder.mkdir(exist_ok=True)
            (post_folder / "images").mkdir(exist_ok=True)
            (post_folder / "videos").mkdir(exist_ok=True)
            (post_folder / "thumbnails").mkdir(exist_ok=True)
            
            return post_folder
            
        except Exception as e:
            self.logger.error(f"Error creating post folder: {e}")
            # Fallback to simple folder
            fallback_folder = self.base_folder / f"post_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            fallback_folder.mkdir(exist_ok=True)
            return fallback_folder

    async def download_post_media(self, post_data: PostData, progress_callback=None) -> Tuple[List[str], List[str]]:
        """
        Download all media for a post
        
        Args:
            post_data: PostData with media_items
            progress_callback: Optional callback for progress updates
            
        Returns:
            Tuple of (successful_downloads, failed_downloads)
        """
        if not post_data.media_items:
            return [], []
        
        # Create post folder
        post_folder = self.create_post_folder(post_data)
        post_data.local_folder = str(post_folder)
        
        # Save post metadata
        await self._save_post_metadata(post_data, post_folder)
        
        # Download media items
        successful = []
        failed = []
        
        # Use semaphore to limit concurrent downloads
        semaphore = asyncio.Semaphore(self.max_concurrent)
        
        tasks = []
        for i, media_item in enumerate(post_data.media_items):
            task = self._download_single_media(
                media_item, post_folder, i, semaphore, progress_callback
            )
            tasks.append(task)
        
        # Execute downloads concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        for i, result in enumerate(results):
            media_item = post_data.media_items[i]
            
            if isinstance(result, Exception):
                self.logger.error(f"Download failed for {media_item.url}: {result}")
                media_item.download_status = "failed"
                media_item.error_message = str(result)
                failed.append(media_item.url)
            elif result:
                media_item.local_path = result
                media_item.download_status = "completed"
                successful.append(result)
            else:
                media_item.download_status = "failed"
                media_item.error_message = "Unknown error"
                failed.append(media_item.url)
        
        self.logger.info(f"Downloaded {len(successful)} media files, {len(failed)} failed")
        return successful, failed

    async def _download_single_media(self, media_item: MediaItem, post_folder: Path, 
                                   index: int, semaphore: asyncio.Semaphore, 
                                   progress_callback=None) -> Optional[str]:
        """Download a single media item"""
        async with semaphore:
            try:
                media_item.download_status = "downloading"
                
                # Generate filename
                filename = self._generate_filename(media_item, index)
                
                # Determine subfolder
                if media_item.type == MediaType.IMAGE:
                    subfolder = post_folder / "images"
                elif media_item.type == MediaType.VIDEO:
                    subfolder = post_folder / "videos"
                else:
                    subfolder = post_folder
                
                file_path = subfolder / filename
                
                # Download file
                success = await self._download_file(media_item.url, file_path, progress_callback)
                
                if success:
                    # Get file info
                    file_stats = file_path.stat()
                    media_item.size_bytes = file_stats.st_size
                    media_item.filename = filename
                    
                    self.logger.info(f"Downloaded: {filename} ({file_stats.st_size} bytes)")
                    return str(file_path)
                else:
                    return None
                    
            except Exception as e:
                self.logger.error(f"Error downloading {media_item.url}: {e}")
                media_item.error_message = str(e)
                return None

    async def _download_file(self, url: str, file_path: Path, progress_callback=None) -> bool:
        """Download file with progress tracking"""
        try:
            async with self.session.get(url) as response:
                if response.status == 200:
                    total_size = int(response.headers.get('content-length', 0))
                    downloaded = 0
                    
                    async with aiofiles.open(file_path, 'wb') as file:
                        async for chunk in response.content.iter_chunked(8192):
                            await file.write(chunk)
                            downloaded += len(chunk)
                            
                            # Progress callback
                            if progress_callback and total_size > 0:
                                progress = (downloaded / total_size) * 100
                                progress_callback(url, progress, downloaded, total_size)
                    
                    return True
                else:
                    self.logger.warning(f"HTTP {response.status} for {url}")
                    return False
                    
        except Exception as e:
            self.logger.error(f"Download error for {url}: {e}")
            return False

    def _generate_filename(self, media_item: MediaItem, index: int) -> str:
        """Generate filename for media item"""
        try:
            # Extract extension from URL
            url_path = media_item.url.split('?')[0]  # Remove query params
            extension = Path(url_path).suffix.lower()
            
            # If no extension, guess from content type or media type
            if not extension:
                if media_item.type == MediaType.IMAGE:
                    extension = '.jpg'
                elif media_item.type == MediaType.VIDEO:
                    extension = '.mp4'
                else:
                    extension = '.bin'
            
            # Generate base name
            media_type = media_item.type.value
            timestamp = datetime.now().strftime("%H%M%S")
            
            filename = f"{media_type}_{index:03d}_{timestamp}{extension}"
            
            return self._sanitize_filename(filename)
            
        except Exception as e:
            self.logger.error(f"Error generating filename: {e}")
            return f"media_{index:03d}_{datetime.now().strftime('%H%M%S')}.bin"

    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename for filesystem"""
        # Remove/replace invalid characters
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        
        # Limit length
        if len(filename) > 200:
            name, ext = os.path.splitext(filename)
            filename = name[:200-len(ext)] + ext
        
        return filename.strip()

    async def _save_post_metadata(self, post_data: PostData, post_folder: Path):
        """Save post metadata to JSON file"""
        try:
            metadata = {
                'post_info': {
                    'url': post_data.original_url,
                    'final_url': post_data.final_url,
                    'post_id': post_data.post_id,
                    'user_name': post_data.user_name,
                    'user_profile_url': post_data.user_profile_url,
                    'post_type': post_data.post_type.value if post_data.post_type else None,
                    'scrape_timestamp': post_data.scrape_timestamp.isoformat(),
                    'post_timestamp': post_data.post_timestamp.isoformat() if post_data.post_timestamp else None,
                },
                'content': {
                    'full_text': post_data.content.full_text if post_data.content else None,
                    'preview_text': post_data.content.preview_text if post_data.content else None,
                    'word_count': post_data.content.word_count if post_data.content else 0,
                    'hashtags': post_data.content.hashtags if post_data.content else [],
                    'mentions': post_data.content.mentions if post_data.content else [],
                    'links': post_data.content.links if post_data.content else [],
                },
                'stats': {
                    'likes': post_data.stats.likes,
                    'comments': post_data.stats.comments,
                    'shares': post_data.stats.shares,
                    'reactions': post_data.stats.reactions,
                },
                'media': [
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
                        'error_message': item.error_message,
                    }
                    for item in post_data.media_items
                ]
            }
            
            metadata_file = post_folder / "metadata.json"
            async with aiofiles.open(metadata_file, 'w', encoding='utf-8') as f:
                await f.write(json.dumps(metadata, indent=2, ensure_ascii=False))
            
            post_data.metadata_file = str(metadata_file)
            
            # Also save content as text file if exists
            if post_data.content and post_data.content.full_text:
                content_file = post_folder / "content.txt"
                async with aiofiles.open(content_file, 'w', encoding='utf-8') as f:
                    await f.write(f"Bài viết của {post_data.user_name}\n")
                    await f.write("=" * 50 + "\n\n")
                    await f.write(post_data.content.full_text)
                    await f.write(f"\n\n" + "=" * 50 + "\n")
                    await f.write(f"Stats: {post_data.stats.likes} likes, {post_data.stats.comments} comments, {post_data.stats.shares} shares\n")
                    await f.write(f"Scraped: {post_data.scrape_timestamp}\n")
                
                post_data.content_file = str(content_file)
            
        except Exception as e:
            self.logger.error(f"Error saving metadata: {e}")

    async def create_thumbnails(self, post_data: PostData):
        """Create thumbnails for images (optional feature)"""
        try:
            from PIL import Image
            
            thumbnail_folder = Path(post_data.local_folder) / "thumbnails"
            thumbnail_folder.mkdir(exist_ok=True)
            
            for media_item in post_data.media_items:
                if (media_item.type == MediaType.IMAGE and 
                    media_item.local_path and 
                    Path(media_item.local_path).exists()):
                    
                    try:
                        # Create thumbnail
                        with Image.open(media_item.local_path) as img:
                            img.thumbnail((300, 300), Image.Resampling.LANCZOS)
                            
                            thumbnail_path = thumbnail_folder / f"thumb_{Path(media_item.local_path).name}"
                            img.save(thumbnail_path, optimize=True, quality=85)
                            
                            self.logger.info(f"Created thumbnail: {thumbnail_path}")
                            
                    except Exception as e:
                        self.logger.warning(f"Failed to create thumbnail for {media_item.local_path}: {e}")
                        
        except ImportError:
            self.logger.warning("PIL not available, skipping thumbnail creation")
        except Exception as e:
            self.logger.error(f"Error creating thumbnails: {e}")

    def get_download_stats(self, post_data: PostData) -> Dict[str, Any]:
        """Get download statistics for a post"""
        total_files = len(post_data.media_items)
        completed = sum(1 for item in post_data.media_items if item.download_status == "completed")
        failed = sum(1 for item in post_data.media_items if item.download_status == "failed")
        total_size = sum(item.size_bytes or 0 for item in post_data.media_items if item.size_bytes)
        
        return {
            'total_files': total_files,
            'completed': completed,
            'failed': failed,
            'pending': total_files - completed - failed,
            'success_rate': (completed / total_files * 100) if total_files > 0 else 0,
            'total_size_bytes': total_size,
            'total_size_mb': round(total_size / (1024 * 1024), 2),
        }

# Utility functions
async def download_media_batch(media_items: List[MediaItem], base_folder: str = "downloads") -> Dict[str, Any]:
    """Download a batch of media items"""
    async with MediaDownloader(base_folder) as downloader:
        # Create dummy post data for batch download
        from data_structures import PostData
        post_data = PostData(
            original_url="batch_download",
            media_items=media_items
        )
        
        successful, failed = await downloader.download_post_media(post_data)
        
        return {
            'successful': successful,
            'failed': failed,
            'stats': downloader.get_download_stats(post_data)
        } 