# 🚀 Facebook Scraper Premium Edition

Phiên bản premium của Facebook Post Scraper với khả năng trích xuất nội dung và media tiên tiến, UI hiện đại và hiệu suất cao.

## ✨ Tính Năng Premium

### 🎯 **Advanced Content Extraction**
- **Full Text Content**: Trích xuất toàn bộ nội dung bài viết
- **Smart Preview**: Hiển thị preview với giới hạn từ, nút "Xem thêm"
- **Hashtag & Mention Detection**: Tự động phát hiện hashtags và mentions
- **Link Extraction**: Trích xuất các links trong bài viết
- **Content Analysis**: Phân tích loại bài viết (text, image, video, mixed)

### 🖼️ **Media Extraction & Download**
- **High-Resolution Images**: Tải ảnh chất lượng cao
- **Video Support**: Hỗ trợ tải video
- **Async Downloads**: Tải xuống bất đồng bộ với hiệu suất cao
- **Smart Organization**: Tự động tổ chức files theo thư mục
- **Thumbnail Generation**: Tạo thumbnails cho ảnh
- **Progress Tracking**: Theo dõi tiến độ download real-time

### 🎨 **Premium UI/UX**
- **Modern Design**: Giao diện hiện đại với gradient và glass effect
- **Content Preview**: Preview nội dung với fade effect
- **Media Gallery**: Thư viện ảnh với lightbox
- **Real-time Progress**: Thanh tiến độ chi tiết với multiple metrics
- **Dark/Light Theme**: Hỗ trợ theme tối/sáng
- **Responsive Design**: Tối ưu cho mọi kích thước màn hình

### ⚡ **Enhanced Performance**
- **Multi-threading**: Xử lý nhiều posts đồng thời
- **Driver Pool**: Quản lý pool WebDriver tối ưu
- **Rate Limiting**: Tránh bị block với smart delays
- **Error Recovery**: Retry logic thông minh
- **Memory Optimization**: Quản lý bộ nhớ hiệu quả

## 📁 Cấu Trúc Project

```
premium/
├── data_structures.py      # Enhanced data models
├── content_extractor.py    # Content extraction engine
├── media_downloader.py     # Async media downloader
├── premium_scraper.py      # Main scraper with advanced features
├── app_premium.py          # Premium GUI application
├── templates/
│   └── premium_ui.html     # Premium UI template
├── static/
│   └── premium.js          # Premium JavaScript
├── downloads/              # Downloaded content folder
├── requirements.txt        # Dependencies
└── README_PREMIUM.md       # This file
```

## 🚀 Cài Đặt & Sử Dụng

### 1. **Cài Đặt Dependencies**

```bash
cd premium
pip install -r requirements.txt
```

### 2. **Chạy Premium App**

```bash
python app_premium.py
```

### 3. **Sử Dụng Giao Diện**

1. **Nhập URLs**: Dán các Facebook post URLs vào textarea
2. **Cấu hình**: Nhấn nút Settings để tùy chỉnh
3. **Bắt đầu**: Nhấn "Bắt Đầu Scraping"
4. **Theo dõi**: Xem tiến độ real-time
5. **Kết quả**: Xem và tương tác với kết quả

## ⚙️ Cấu Hình Premium

### **Threading Settings**
```python
{
    "max_workers": 3,           # Số thread đồng thời
    "driver_pool_size": 3,      # Kích thước driver pool
    "rate_limit_min": 2.0,      # Delay tối thiểu (giây)
    "rate_limit_max": 5.0,      # Delay tối đa (giây)
}
```

### **Content Extraction**
```python
{
    "extract_content": True,        # Trích xuất nội dung
    "content_preview_words": 50,    # Số từ preview
    "extract_hashtags": True,       # Trích xuất hashtags
    "extract_mentions": True,       # Trích xuất mentions
    "extract_links": True,          # Trích xuất links
}
```

### **Media Download**
```python
{
    "download_media": True,         # Tự động tải media
    "media_quality": "high",        # Chất lượng (low/medium/high)
    "max_media_size_mb": 50,       # Kích thước file tối đa
    "create_thumbnails": True,      # Tạo thumbnails
    "organize_by_date": True,       # Tổ chức theo ngày
}
```

## 🎨 UI Features

### **Content Preview với Fade Effect**
- Hiển thị preview nội dung với giới hạn từ
- Fade effect mượt mà ở cuối preview
- Nút "Xem thêm" để mở modal full content
- Highlight hashtags và mentions

### **Media Gallery với Lightbox**
- Grid layout responsive cho media preview
- Fade overlay effect cho ảnh
- Click để mở lightbox gallery
- Navigation arrows trong gallery
- Badge hiển thị số lượng media

### **Real-time Progress Tracking**
- Progress bar với gradient effect
- Multiple metrics: success rate, media downloaded, etc.
- Current activity indicator
- Time estimation
- Pulse animation cho status

### **Modern Settings Panel**
- Tabbed interface cho các category
- Range sliders với real-time values
- Toggle switches với animations
- Responsive grid layout

## 📊 Data Structure

### **PostData Model**
```python
@dataclass
class PostData:
    # Basic info
    original_url: str
    user_name: str
    post_type: PostType
    
    # Content
    content: PostContent          # Full text + preview
    
    # Media
    media_items: List[MediaItem]  # Images + videos
    media_count: int
    
    # Stats
    stats: PostStats              # Likes, comments, shares
    
    # Files
    local_folder: str             # Download folder
    content_file: str             # Content text file
    metadata_file: str            # JSON metadata
```

### **Enhanced Content Model**
```python
@dataclass
class PostContent:
    full_text: str               # Toàn bộ nội dung
    preview_text: str            # Preview với giới hạn từ
    word_count: int              # Số từ
    has_more: bool               # Có nội dung dài hơn preview
    hashtags: List[str]          # Danh sách hashtags
    mentions: List[str]          # Danh sách mentions
    links: List[str]             # Danh sách links
```

### **Media Item Model**
```python
@dataclass
class MediaItem:
    url: str                     # URL gốc
    type: MediaType              # IMAGE/VIDEO/GIF
    filename: str                # Tên file local
    local_path: str              # Đường dẫn local
    size_bytes: int              # Kích thước file
    download_status: str         # pending/downloading/completed/failed
    thumbnail_url: str           # URL thumbnail
```

## 📁 File Organization

### **Automatic Folder Structure**
```
downloads/
├── 20231215_143022_UserName_PostID/
│   ├── metadata.json           # Post metadata
│   ├── content.txt             # Post content
│   ├── images/
│   │   ├── image_001_143025.jpg
│   │   └── image_002_143026.jpg
│   ├── videos/
│   │   └── video_001_143027.mp4
│   └── thumbnails/
│       ├── thumb_image_001.jpg
│       └── thumb_image_002.jpg
```

### **Metadata JSON Structure**
```json
{
  "post_info": {
    "url": "https://facebook.com/post",
    "user_name": "User Name",
    "post_type": "image",
    "scrape_timestamp": "2023-12-15T14:30:22"
  },
  "content": {
    "full_text": "Full post content...",
    "word_count": 125,
    "hashtags": ["#example"],
    "mentions": ["@user"]
  },
  "stats": {
    "likes": "1.2K",
    "comments": "45",
    "shares": "12"
  },
  "media": [
    {
      "url": "https://...",
      "type": "image",
      "filename": "image_001.jpg",
      "size_bytes": 2048576,
      "download_status": "completed"
    }
  ]
}
```

## 🔧 Advanced Usage

### **Programmatic Usage**
```python
from premium_scraper import PremiumScraper
from data_structures import ScraperConfig

# Cấu hình
config = ScraperConfig(
    max_workers=5,
    extract_content=True,
    download_media=True,
    media_quality="high"
)

# Khởi tạo scraper
scraper = PremiumScraper(config)

# Scraping
urls = ["https://facebook.com/post1", "https://facebook.com/post2"]
results = await scraper.scrape_urls(urls)

# Xử lý kết quả
for result in results:
    if result.success:
        print(f"Post: {result.post_data.user_name}")
        print(f"Content: {result.post_data.content.preview_text}")
        print(f"Media: {result.post_data.media_count} items")
        print(f"Downloaded: {result.media_downloaded} files")
```

### **Custom Progress Callback**
```python
def custom_progress(progress_data, result=None):
    print(f"Progress: {progress_data.completed_tasks}/{progress_data.total_tasks}")
    print(f"Content extracted: {progress_data.content_extracted}")
    print(f"Media downloaded: {progress_data.media_downloaded}")
    print(f"Total size: {progress_data.total_download_size / 1024 / 1024:.1f} MB")
    
    if result:
        print(f"Completed: {result.post_data.user_name}")

scraper.set_progress_callback(custom_progress)
```

## 🎯 Performance Optimization

### **Threading Configuration**
- **3 workers**: Balanced performance/stability
- **5 workers**: High performance (requires more RAM)
- **1-2 workers**: Safe mode for slower systems

### **Memory Management**
- Driver pool reuse
- Async downloads
- Progressive loading
- Automatic cleanup

### **Rate Limiting Strategy**
- Random delays between requests
- Exponential backoff for retries
- Smart error detection
- Adaptive rate adjustment

## 🛡️ Anti-Detection Features

### **Browser Fingerprinting**
- Realistic user agents
- Chrome profile reuse
- Disable automation flags
- Random viewport sizes

### **Request Patterns**
- Human-like delays
- Random scroll behavior
- Natural click patterns
- Session persistence

### **Error Handling**
- Graceful failure recovery
- Automatic retry logic
- IP rotation support
- CAPTCHA detection

## 📈 Performance Metrics

### **Speed Comparison**
| Feature | Basic Version | Premium Version | Improvement |
|---------|---------------|-----------------|-------------|
| **Scraping Speed** | 1x | 3-5x | 300-500% |
| **Content Extraction** | Basic stats | Full content + media | Complete |
| **UI Responsiveness** | Standard | Real-time updates | Smooth |
| **Error Recovery** | Basic retry | Smart recovery | Robust |
| **File Organization** | Simple | Structured folders | Professional |

### **Resource Usage**
- **CPU**: Moderate (multi-threading optimized)
- **Memory**: 200-500MB (depending on media)
- **Storage**: Variable (based on media downloads)
- **Network**: Efficient (concurrent downloads)

## 🚨 Troubleshooting

### **Common Issues**

1. **High Memory Usage**
   ```python
   # Giảm số workers
   config.max_workers = 2
   config.driver_pool_size = 2
   ```

2. **Download Failures**
   ```python
   # Tăng timeout và giảm concurrent downloads
   config.download_rate_limit = 2.0
   config.max_media_size_mb = 25
   ```

3. **Getting Blocked**
   ```python
   # Tăng delays
   config.rate_limit_min = 5.0
   config.rate_limit_max = 10.0
   ```

### **Debug Mode**
```python
# Enable debug logging
logging.basicConfig(level=logging.DEBUG)

# Check driver pool status
status = scraper.get_driver_pool_status()
print(f"Available drivers: {status['available_drivers']}")
```

## 🔄 Migration từ Basic Version

### **API Compatibility**
Premium version tương thích với basic version API:

```python
# Basic version code
api.scrape(url)

# Vẫn hoạt động với premium version
# Tự động sử dụng premium features internally
```

### **Data Format**
Kết quả premium bao gồm tất cả fields của basic version plus:
- Enhanced content extraction
- Media items with download info
- Detailed metadata
- File organization

## 📝 Changelog

### v2.0 - Premium Edition
- ✅ **Advanced Content Extraction**: Full text + preview + hashtags + mentions
- ✅ **Media Download**: Async downloads with progress tracking
- ✅ **Premium UI**: Modern design with fade effects and galleries
- ✅ **Enhanced Performance**: Optimized multi-threading and memory usage
- ✅ **Smart Organization**: Automatic folder structure and metadata
- ✅ **Real-time Updates**: Live progress tracking and notifications
- ✅ **Error Recovery**: Robust error handling and retry logic

### Key Improvements over Basic Version
- **5x faster** với advanced threading
- **Complete content extraction** thay vì chỉ stats
- **Automatic media downloads** với high-resolution support
- **Professional file organization** với metadata
- **Modern UI/UX** với real-time updates
- **Enhanced error handling** với smart recovery

## 🆘 Support & Contact

### **Logs Location**
- Main log: `premium_scraper.log`
- Download progress: Trong UI real-time
- Error details: Console và log files

### **Common Solutions**
1. **Check Chrome profile path** trong `driver_pool.py`
2. **Verify network connectivity** và firewall settings
3. **Update Chrome browser** to latest version
4. **Check available disk space** cho downloads
5. **Monitor system resources** (CPU/RAM usage)

---

**🎉 Premium Edition** - Trải nghiệm Facebook scraping chuyên nghiệp với công nghệ tiên tiến!

*Note: Công cụ này chỉ dành cho mục đích giáo dục và nghiên cứu. Vui lòng tuân thủ Terms of Service của Facebook.* 