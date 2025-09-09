import re
import time
import logging
from typing import List, Optional, Tuple
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from bs4 import BeautifulSoup

from data_structures import PostContent, MediaItem, MediaType, PostType, create_post_content

class ContentExtractor:
    """Advanced content extractor for Facebook posts"""
    
    def __init__(self, preview_words: int = 50):
        self.preview_words = preview_words
        self.logger = logging.getLogger(__name__)
        
        # Content selectors - multiple strategies
        self.CONTENT_SELECTORS = [
            "//div[@role='dialog']//div[@data-ad-preview='message']",
            "//div[@role='dialog']//div[contains(@class, 'userContent')]",
            "//div[@role='dialog']//span[contains(@class, 'x193iq5w')]",
            "//div[@role='dialog']//div[contains(@class, 'x1iorvi4')]//span",
            "//div[@role='dialog']//div[@data-testid='post_message']",
        ]
        
        # Media selectors
        self.IMAGE_SELECTORS = [
            "//div[@role='dialog']//img[contains(@src, 'fbcdn')]",
            "//div[@role='dialog']//img[contains(@class,'scaledImageFitWidth')]",
            "//div[@role='dialog']//img[contains(@class,'img')]",
            "//div[@role='dialog']//div[@data-testid='photo-viewer']//img",
        ]
        
        self.VIDEO_SELECTORS = [
            "//div[@role='dialog']//video",
            "//div[@role='dialog']//div[@data-video-id]",
            "//div[@role='dialog']//div[contains(@class, 'video')]//video",
        ]
        
        # Timestamp selectors
        self.TIMESTAMP_SELECTORS = [
            "//div[@role='dialog']//a[contains(@href, '/posts/')]",
            "//div[@role='dialog']//a[contains(@aria-label, 'ago')]",
            "//div[@role='dialog']//span[contains(text(), 'ago')]",
        ]

    def extract_post_content(self, driver: webdriver.Chrome, dialog_soup: BeautifulSoup) -> Optional[PostContent]:
        """
        Extract post text content with preview functionality
        
        Args:
            driver: Selenium WebDriver instance
            dialog_soup: BeautifulSoup parsed dialog
            
        Returns:
            PostContent object or None if no content found
        """
        try:
            # Strategy 1: Try Selenium with multiple selectors
            full_text = self._extract_text_selenium(driver)
            
            # Strategy 2: Try BeautifulSoup if Selenium fails
            if not full_text:
                full_text = self._extract_text_beautifulsoup(dialog_soup)
            
            # Strategy 3: Handle "See More" buttons
            if not full_text:
                full_text = self._extract_text_with_see_more(driver)
            
            if full_text:
                # Clean and process text
                full_text = self._clean_text(full_text)
                
                # Create PostContent with preview
                content = create_post_content(full_text, self.preview_words)
                
                self.logger.info(f"Extracted content: {content.word_count} words, preview: {len(content.preview_text)} chars")
                return content
            else:
                self.logger.warning("No post content found")
                return None
                
        except Exception as e:
            self.logger.error(f"Error extracting post content: {e}")
            return None

    def _extract_text_selenium(self, driver: webdriver.Chrome) -> Optional[str]:
        """Extract text using Selenium with multiple selectors"""
        wait = WebDriverWait(driver, 5)
        
        for selector in self.CONTENT_SELECTORS:
            try:
                element = wait.until(EC.presence_of_element_located((By.XPATH, selector)))
                text = element.text.strip()
                if text and len(text) > 10:  # Minimum content length
                    return text
            except (TimeoutException, NoSuchElementException):
                continue
        
        return None

    def _extract_text_beautifulsoup(self, dialog_soup: BeautifulSoup) -> Optional[str]:
        """Extract text using BeautifulSoup as fallback"""
        try:
            # Try various class patterns
            content_patterns = [
                {'data-ad-preview': 'message'},
                {'class': lambda x: x and 'userContent' in ' '.join(x)},
                {'class': lambda x: x and 'x193iq5w' in ' '.join(x)},
                {'data-testid': 'post_message'},
            ]
            
            for pattern in content_patterns:
                elements = dialog_soup.find_all('div', pattern)
                for element in elements:
                    text = element.get_text(strip=True)
                    if text and len(text) > 10:
                        return text
            
            return None
        except Exception as e:
            self.logger.error(f"Error in BeautifulSoup text extraction: {e}")
            return None

    def _extract_text_with_see_more(self, driver: webdriver.Chrome) -> Optional[str]:
        """Handle 'See More' buttons to get full content"""
        try:
            # Look for "See More" buttons
            see_more_selectors = [
                "//div[@role='dialog']//div[contains(text(), 'See more') or contains(text(), 'See More')]",
                "//div[@role='dialog']//span[contains(text(), 'Xem thêm')]",
                "//div[@role='dialog']//div[@role='button'][contains(text(), 'more')]"
            ]
            
            for selector in see_more_selectors:
                try:
                    see_more_btn = driver.find_element(By.XPATH, selector)
                    if see_more_btn.is_displayed():
                        # Click to expand
                        driver.execute_script("arguments[0].click();", see_more_btn)
                        time.sleep(1)  # Wait for expansion
                        
                        # Try to extract full text again
                        return self._extract_text_selenium(driver)
                except (NoSuchElementException, Exception):
                    continue
            
            return None
        except Exception as e:
            self.logger.error(f"Error handling See More: {e}")
            return None

    def _clean_text(self, text: str) -> str:
        """Clean and normalize extracted text"""
        if not text:
            return ""
        
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove common Facebook UI elements
        ui_patterns = [
            r'See more',
            r'See less',
            r'Xem thêm',
            r'Ẩn bớt',
            r'Like.*Comment.*Share',
            r'Thích.*Bình luận.*Chia sẻ',
        ]
        
        for pattern in ui_patterns:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)
        
        return text.strip()

    def extract_media_urls(self, driver: webdriver.Chrome, dialog_soup: BeautifulSoup) -> List[MediaItem]:
        """
        Extract media URLs (images and videos) from post
        
        Args:
            driver: Selenium WebDriver instance
            dialog_soup: BeautifulSoup parsed dialog
            
        Returns:
            List of MediaItem objects
        """
        media_items = []
        
        try:
            # Extract images
            images = self._extract_images(driver, dialog_soup)
            media_items.extend(images)
            
            # Extract videos
            videos = self._extract_videos(driver, dialog_soup)
            media_items.extend(videos)
            
            self.logger.info(f"Found {len(media_items)} media items ({len(images)} images, {len(videos)} videos)")
            
        except Exception as e:
            self.logger.error(f"Error extracting media URLs: {e}")
        
        return media_items

    def _extract_images(self, driver: webdriver.Chrome, dialog_soup: BeautifulSoup) -> List[MediaItem]:
        """Extract image URLs"""
        images = []
        
        try:
            # Strategy 1: Selenium extraction
            for selector in self.IMAGE_SELECTORS:
                try:
                    img_elements = driver.find_elements(By.XPATH, selector)
                    for img in img_elements:
                        src = img.get_attribute('src')
                        if self._is_valid_image_url(src):
                            # Get high resolution URL
                            high_res_url = self._get_high_res_image_url(src)
                            
                            media_item = MediaItem(
                                url=high_res_url,
                                type=MediaType.IMAGE,
                                width=img.get_attribute('width'),
                                height=img.get_attribute('height')
                            )
                            
                            if media_item not in images:  # Avoid duplicates
                                images.append(media_item)
                                
                except Exception as e:
                    self.logger.warning(f"Error with image selector {selector}: {e}")
                    continue
            
            # Strategy 2: BeautifulSoup fallback
            if not images:
                images.extend(self._extract_images_beautifulsoup(dialog_soup))
            
        except Exception as e:
            self.logger.error(f"Error extracting images: {e}")
        
        return images

    def _extract_videos(self, driver: webdriver.Chrome, dialog_soup: BeautifulSoup) -> List[MediaItem]:
        """Extract video URLs"""
        videos = []
        
        try:
            for selector in self.VIDEO_SELECTORS:
                try:
                    video_elements = driver.find_elements(By.XPATH, selector)
                    for video in video_elements:
                        src = video.get_attribute('src')
                        if self._is_valid_video_url(src):
                            media_item = MediaItem(
                                url=src,
                                type=MediaType.VIDEO,
                                width=video.get_attribute('width'),
                                height=video.get_attribute('height')
                            )
                            
                            # Try to get thumbnail
                            poster = video.get_attribute('poster')
                            if poster:
                                media_item.thumbnail_url = poster
                            
                            if media_item not in videos:
                                videos.append(media_item)
                                
                except Exception as e:
                    self.logger.warning(f"Error with video selector {selector}: {e}")
                    continue
        
        except Exception as e:
            self.logger.error(f"Error extracting videos: {e}")
        
        return videos

    def _extract_images_beautifulsoup(self, dialog_soup: BeautifulSoup) -> List[MediaItem]:
        """Extract images using BeautifulSoup"""
        images = []
        
        try:
            img_tags = dialog_soup.find_all('img')
            for img in img_tags:
                src = img.get('src')
                if self._is_valid_image_url(src):
                    high_res_url = self._get_high_res_image_url(src)
                    
                    media_item = MediaItem(
                        url=high_res_url,
                        type=MediaType.IMAGE,
                        width=img.get('width'),
                        height=img.get('height')
                    )
                    
                    if media_item not in images:
                        images.append(media_item)
        
        except Exception as e:
            self.logger.error(f"Error in BeautifulSoup image extraction: {e}")
        
        return images

    def _is_valid_image_url(self, url: Optional[str]) -> bool:
        """Check if URL is a valid image URL"""
        if not url:
            return False
        
        # Must be Facebook CDN
        if 'fbcdn' not in url:
            return False
        
        # Must have image extension or be Facebook image URL
        image_patterns = [
            r'\.(jpg|jpeg|png|gif|webp)',
            r'fbcdn.*\.(jpg|jpeg|png|gif|webp)',
            r'scontent.*\.(jpg|jpeg|png|gif|webp)',
        ]
        
        return any(re.search(pattern, url, re.IGNORECASE) for pattern in image_patterns)

    def _is_valid_video_url(self, url: Optional[str]) -> bool:
        """Check if URL is a valid video URL"""
        if not url:
            return False
        
        # Must be Facebook CDN or video URL
        if not any(domain in url for domain in ['fbcdn', 'facebook.com', 'video']):
            return False
        
        # Must have video extension or be Facebook video URL
        video_patterns = [
            r'\.(mp4|webm|ogg|mov)',
            r'video',
            r'fbcdn.*video',
        ]
        
        return any(re.search(pattern, url, re.IGNORECASE) for pattern in video_patterns)

    def _get_high_res_image_url(self, url: str) -> str:
        """Convert thumbnail URL to high resolution URL"""
        try:
            # Facebook CDN URL patterns
            if 'fbcdn' in url:
                # Remove size restrictions
                url = re.sub(r'_s\d+x\d+', '', url)  # Remove size parameters
                url = re.sub(r'_n\.', '_o.', url)    # Change to original size
                url = re.sub(r'_t\.', '_o.', url)    # Change thumbnail to original
            
            return url
        except Exception:
            return url

    def extract_post_timestamp(self, driver: webdriver.Chrome, dialog_soup: BeautifulSoup) -> Optional[datetime]:
        """Extract post timestamp"""
        try:
            for selector in self.TIMESTAMP_SELECTORS:
                try:
                    element = driver.find_element(By.XPATH, selector)
                    
                    # Try to get timestamp from various attributes
                    timestamp_attrs = ['data-utime', 'title', 'aria-label']
                    for attr in timestamp_attrs:
                        timestamp_str = element.get_attribute(attr)
                        if timestamp_str:
                            # Parse timestamp
                            parsed_time = self._parse_timestamp(timestamp_str)
                            if parsed_time:
                                return parsed_time
                
                except (NoSuchElementException, Exception):
                    continue
            
            return None
        except Exception as e:
            self.logger.error(f"Error extracting timestamp: {e}")
            return None

    def _parse_timestamp(self, timestamp_str: str) -> Optional[datetime]:
        """Parse timestamp string to datetime"""
        try:
            # Try Unix timestamp first
            if timestamp_str.isdigit():
                return datetime.fromtimestamp(int(timestamp_str))
            
            # Try various date formats
            date_formats = [
                '%Y-%m-%d %H:%M:%S',
                '%Y-%m-%dT%H:%M:%S',
                '%d/%m/%Y %H:%M',
                '%m/%d/%Y %H:%M',
            ]
            
            for fmt in date_formats:
                try:
                    return datetime.strptime(timestamp_str, fmt)
                except ValueError:
                    continue
            
            return None
        except Exception:
            return None

    def detect_post_type(self, content: Optional[PostContent], media_items: List[MediaItem]) -> PostType:
        """Detect post type based on content and media"""
        try:
            has_text = content and content.full_text.strip()
            has_images = any(item.type == MediaType.IMAGE for item in media_items)
            has_videos = any(item.type == MediaType.VIDEO for item in media_items)
            has_links = content and content.links
            
            if has_videos and has_images:
                return PostType.MIXED
            elif has_videos:
                return PostType.VIDEO
            elif has_images:
                return PostType.IMAGE
            elif has_links:
                return PostType.LINK
            elif has_text:
                return PostType.TEXT
            else:
                return PostType.UNKNOWN
                
        except Exception:
            return PostType.UNKNOWN 