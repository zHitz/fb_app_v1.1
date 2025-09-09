from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum

class PostType(Enum):
    TEXT = "text"
    IMAGE = "image" 
    VIDEO = "video"
    MIXED = "mixed"
    LINK = "link"
    UNKNOWN = "unknown"

class MediaType(Enum):
    IMAGE = "image"
    VIDEO = "video"
    GIF = "gif"

@dataclass
class MediaItem:
    """Represents a single media item (image/video)"""
    url: str
    type: MediaType
    filename: Optional[str] = None
    local_path: Optional[str] = None
    size_bytes: Optional[int] = None
    width: Optional[int] = None
    height: Optional[int] = None
    duration: Optional[float] = None  # For videos
    thumbnail_url: Optional[str] = None
    download_status: str = "pending"  # pending, downloading, completed, failed
    error_message: Optional[str] = None

@dataclass
class PostContent:
    """Represents post text content"""
    full_text: str
    preview_text: str  # First N words for preview
    word_count: int
    has_more: bool = False
    hashtags: List[str] = field(default_factory=list)
    mentions: List[str] = field(default_factory=list)
    links: List[str] = field(default_factory=list)

@dataclass
class PostStats:
    """Post engagement statistics"""
    likes: str = "0"
    comments: str = "0"
    shares: str = "0"
    reactions: Dict[str, str] = field(default_factory=dict)  # like, love, haha, etc.
    
@dataclass
class PostData:
    """Enhanced post data structure for premium features"""
    # Basic info
    original_url: str
    final_url: Optional[str] = None
    post_id: Optional[str] = None
    user_name: Optional[str] = None
    user_id: Optional[str] = None
    user_profile_url: Optional[str] = None
    
    # Content
    content: Optional[PostContent] = None
    post_type: PostType = PostType.UNKNOWN
    
    # Media
    media_items: List[MediaItem] = field(default_factory=list)
    media_count: int = 0
    
    # Stats
    stats: PostStats = field(default_factory=PostStats)
    
    # Timestamps
    post_timestamp: Optional[datetime] = None
    scrape_timestamp: datetime = field(default_factory=datetime.now)
    
    # Technical info
    processing_time: float = 0.0
    success: bool = False
    error_message: Optional[str] = None
    
    # File paths
    local_folder: Optional[str] = None
    content_file: Optional[str] = None
    metadata_file: Optional[str] = None

@dataclass
class ScrapeTask:
    """Enhanced scraping task"""
    url: str
    task_id: int
    retry_count: int = 0
    max_retries: int = 3
    
    # Premium options
    extract_content: bool = True
    download_media: bool = True
    media_quality: str = "high"  # low, medium, high
    max_media_size_mb: int = 50
    
@dataclass
class ScrapeResult:
    """Enhanced scraping result"""
    task_id: int
    url: str
    post_data: PostData
    success: bool
    error_message: Optional[str] = None
    processing_time: float = 0.0
    
    # Download stats
    media_downloaded: int = 0
    media_failed: int = 0
    total_download_size: int = 0  # bytes

@dataclass
class ProgressData:
    """Enhanced progress tracking"""
    # Basic progress
    total_tasks: int
    completed_tasks: int = 0
    failed_tasks: int = 0
    success_rate: float = 0.0
    elapsed_time: float = 0.0
    estimated_remaining: float = 0.0
    
    # Content extraction progress
    content_extracted: int = 0
    content_failed: int = 0
    
    # Media download progress
    media_found: int = 0
    media_downloaded: int = 0
    media_failed: int = 0
    total_download_size: int = 0  # bytes
    current_downloads: int = 0
    
    # Current activity
    current_activity: str = "Initializing..."
    current_url: Optional[str] = None

@dataclass
class ScraperConfig:
    """Premium scraper configuration"""
    # Threading
    max_workers: int = 3
    driver_pool_size: int = 3
    
    # Rate limiting
    rate_limit_min: float = 2.0
    rate_limit_max: float = 5.0
    download_rate_limit: float = 1.0
    
    # Retry logic
    max_retries: int = 3
    retry_delay_base: float = 2.0
    
    # Content extraction
    extract_content: bool = True
    content_preview_words: int = 50
    extract_hashtags: bool = True
    extract_mentions: bool = True
    extract_links: bool = True
    
    # Media download
    download_media: bool = True
    media_quality: str = "high"  # low, medium, high
    max_media_size_mb: int = 50
    allowed_media_types: List[str] = field(default_factory=lambda: ["image", "video"])
    create_thumbnails: bool = True
    
    # File organization
    organize_by_date: bool = True
    organize_by_user: bool = False
    base_download_folder: str = "downloads"
    
    # Output formats
    save_metadata: bool = True
    save_content_txt: bool = True
    export_formats: List[str] = field(default_factory=lambda: ["json", "csv"])

# Utility functions for data structures
def create_preview_text(full_text: str, max_words: int = 50) -> tuple[str, bool]:
    """Create preview text with word limit"""
    if not full_text:
        return "", False
        
    words = full_text.split()
    if len(words) <= max_words:
        return full_text, False
        
    preview = " ".join(words[:max_words])
    return preview + "...", True

def extract_hashtags(text: str) -> List[str]:
    """Extract hashtags from text"""
    import re
    return re.findall(r'#\w+', text)

def extract_mentions(text: str) -> List[str]:
    """Extract mentions from text"""
    import re
    return re.findall(r'@\w+', text)

def extract_links(text: str) -> List[str]:
    """Extract URLs from text"""
    import re
    url_pattern = re.compile(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')
    return url_pattern.findall(text)

def create_post_content(full_text: str, preview_words: int = 50) -> PostContent:
    """Create PostContent from raw text"""
    preview_text, has_more = create_preview_text(full_text, preview_words)
    
    return PostContent(
        full_text=full_text,
        preview_text=preview_text,
        word_count=len(full_text.split()),
        has_more=has_more,
        hashtags=extract_hashtags(full_text),
        mentions=extract_mentions(full_text),
        links=extract_links(full_text)
    ) 