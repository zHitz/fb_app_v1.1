# Facebook Post Scraper - Multi-Thread Edition

Phiên bản multi-threading của Facebook Post Scraper với khả năng xử lý nhiều bài viết cùng lúc, tăng tốc độ scraping đáng kể.

## ✨ Tính năng chính

### 🚀 Multi-Threading
- **Concurrent Processing**: Xử lý nhiều URL cùng lúc
- **Configurable Thread Limit**: Giới hạn số thread (mặc định 3-5)
- **Driver Pool Management**: Quản lý pool các WebDriver instances
- **Rate Limiting**: Tránh bị block bởi Facebook

### 📊 Progress Tracking
- **Real-time Progress**: Hiển thị tiến độ real-time
- **Success Rate Monitoring**: Theo dõi tỷ lệ thành công
- **Time Estimation**: Ước tính thời gian còn lại
- **Error Handling**: Xử lý lỗi comprehensive

### 🛠️ Advanced Features
- **Retry Logic**: Thử lại các request thất bại
- **Resource Management**: Tự động cleanup resources
- **Multiple Output Formats**: TXT, CSV, JSON
- **Settings Configuration**: Cấu hình linh hoạt

## 📁 Cấu trúc File

```
fb_app/
├── driver_pool.py           # Quản lý pool WebDriver
├── multi_thread_scraper.py  # Core multi-threading logic
├── app_multi.py             # GUI app với multi-threading
├── index_multi.html         # UI cho multi-threading
├── run_multi.py             # Command-line runner
├── facebook_scrapper.py     # Original scraper logic
└── requirements.txt         # Dependencies
```

## 🚀 Cách sử dụng

### 1. GUI Application (Khuyến nghị)

```bash
# Chạy ứng dụng GUI với multi-threading
python app_multi.py
```

**Tính năng GUI:**
- ✅ Real-time progress tracking
- ✅ Settings configuration
- ✅ Stop/Resume functionality
- ✅ Multiple save formats
- ✅ Dark/Light theme
- ✅ Error reporting

### 2. Command Line

```bash
# Chạy từ command line với 3 workers (mặc định)
python run_multi.py

# Chạy với số workers tùy chỉnh
python run_multi.py 5
```

### 3. Programmatic Usage

```python
from multi_thread_scraper import MultiThreadScraper, create_progress_callback

# URLs to scrape
urls = [
    "https://facebook.com/post1",
    "https://facebook.com/post2",
    "https://facebook.com/post3"
]

# Create progress callback
progress_callback = create_progress_callback()

# Initialize scraper
scraper = MultiThreadScraper(
    max_workers=3,
    driver_pool_size=3,
    rate_limit_delay=(2, 5),
    max_retries=3,
    progress_callback=progress_callback
)

try:
    # Perform scraping
    results = scraper.scrape_urls(urls)
    
    # Save results
    scraper.save_results(results, "txt")
    
finally:
    # Cleanup
    scraper.shutdown()
```

## ⚙️ Cấu hình

### Cài đặt cơ bản

| Tham số | Mặc định | Mô tả |
|---------|----------|--------|
| `max_workers` | 3 | Số lượng thread tối đa |
| `driver_pool_size` | 3 | Số lượng WebDriver instances |
| `rate_limit_delay` | (2, 5) | Delay giữa các request (giây) |
| `max_retries` | 3 | Số lần thử lại khi thất bại |

### Cài đặt nâng cao

```python
# Tùy chỉnh cấu hình cho hiệu suất tối ưu
config = {
    'max_workers': 5,           # Tăng số workers
    'driver_pool_size': 5,      # Tăng pool size
    'rate_limit_min': 1,        # Giảm delay tối thiểu
    'rate_limit_max': 3,        # Giảm delay tối đa
    'max_retries': 2            # Giảm số lần retry
}
```

## 📊 Performance Comparison

| Metric | Single Thread | Multi-Thread (3 workers) | Improvement |
|--------|---------------|---------------------------|-------------|
| **Speed** | 1x | 3-5x | 300-500% |
| **Resource Usage** | Low | Medium | Optimized |
| **Stability** | High | High | Maintained |
| **Error Recovery** | Basic | Advanced | Enhanced |

## 🔧 Troubleshooting

### Common Issues

1. **"No drivers available in pool"**
   ```python
   # Giải pháp: Tăng driver_pool_size hoặc giảm max_workers
   scraper = MultiThreadScraper(
       max_workers=2,
       driver_pool_size=3
   )
   ```

2. **High memory usage**
   ```python
   # Giải pháp: Giảm số workers và tăng rate limit
   scraper = MultiThreadScraper(
       max_workers=2,
       rate_limit_delay=(3, 7)
   )
   ```

3. **Getting blocked by Facebook**
   ```python
   # Giải pháp: Tăng rate limiting
   scraper = MultiThreadScraper(
       max_workers=2,
       rate_limit_delay=(5, 10)
   )
   ```

### Logging

Kiểm tra logs để debug:

```bash
# GUI app logs
tail -f scraper_multi.log

# Command line logs
tail -f scraper_multi.log
```

## 🛡️ Best Practices

### 1. Tối ưu hiệu suất
- Bắt đầu với 3 workers, tăng dần nếu cần
- Monitor CPU và memory usage
- Sử dụng rate limiting phù hợp

### 2. Tránh bị block
- Không sử dụng quá nhiều workers (>5)
- Tăng delay giữa requests nếu cần
- Sử dụng different user profiles nếu có thể

### 3. Error handling
- Luôn sử dụng try-catch khi gọi API
- Implement proper cleanup
- Monitor logs for issues

## 📈 Monitoring & Analytics

### Progress Tracking
```python
def custom_progress_callback(progress, result=None):
    print(f"Progress: {progress['completed_tasks']}/{progress['total_tasks']}")
    print(f"Success Rate: {progress['success_rate']}%")
    print(f"Elapsed: {progress['elapsed_time']}s")
    
    if result:
        status = "✓" if result.success else "✗"
        print(f"  {status} {result.url} ({result.processing_time:.2f}s)")
```

### Driver Pool Status
```python
# Kiểm tra trạng thái driver pool
status = scraper.get_driver_pool_status()
print(f"Available drivers: {status['available_drivers']}")
print(f"Active drivers: {status['active_drivers']}")
```

## 🔄 Migration từ Single-Thread

Để migrate từ phiên bản single-thread:

1. **Thay thế import:**
   ```python
   # Cũ
   from facebook_scrapper import main
   
   # Mới
   from multi_thread_scraper import MultiThreadScraper
   ```

2. **Cập nhật code:**
   ```python
   # Cũ
   for url in urls:
       result = extract_data(driver, url)
   
   # Mới
   scraper = MultiThreadScraper()
   results = scraper.scrape_urls(urls)
   ```

3. **Backward compatibility:**
   ```python
   # API cũ vẫn hoạt động với app_multi.py
   api.scrape(single_url)  # Sử dụng multi-threading internally
   ```

## 🆘 Support

Nếu gặp vấn đề:

1. Kiểm tra logs: `scraper_multi.log`
2. Verify Chrome profile path trong `driver_pool.py`
3. Đảm bảo đủ RAM cho multiple drivers
4. Giảm số workers nếu system không ổn định

## 📝 Changelog

### v1.1 - Multi-Thread Edition
- ✅ Added multi-threading support
- ✅ Implemented driver pool management
- ✅ Added progress tracking
- ✅ Enhanced error handling
- ✅ Created new GUI interface
- ✅ Added command-line runner
- ✅ Improved resource management

---

**Note**: Công cụ này chỉ dành cho mục đích giáo dục. Hãy tuân thủ Terms of Service của Facebook khi sử dụng. 