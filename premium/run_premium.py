#!/usr/bin/env python3
"""
Premium Facebook Scraper - Command Line Runner
Advanced content extraction and media download
"""

import sys
import asyncio
import logging
from pathlib import Path

# Add parent directory to path for imports
sys.path.append('../fb_app')

from premium_scraper import PremiumScraper, create_premium_progress_callback
from data_structures import ScraperConfig

def read_urls_from_file(filename="links.txt"):
    """Read URLs from a text file."""
    urls = []
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            for line in file:
                cleaned_line = line.strip()
                if cleaned_line:
                    urls.append(cleaned_line)
        print(f"✓ Đọc được {len(urls)} URLs từ {filename}")
    except FileNotFoundError:
        print(f"❌ Không tìm thấy file '{filename}'")
        return []
    except Exception as e:
        print(f"❌ Lỗi đọc file: {e}")
        return []
    return urls

def print_banner():
    """Print premium banner"""
    print("=" * 80)
    print("🚀 FACEBOOK SCRAPER PREMIUM EDITION")
    print("   Advanced Content & Media Extraction")
    print("=" * 80)
    print()

def print_config(config: ScraperConfig):
    """Print current configuration"""
    print("⚙️  CẤU HÌNH PREMIUM:")
    print(f"   • Max Workers: {config.max_workers}")
    print(f"   • Driver Pool: {config.driver_pool_size}")
    print(f"   • Rate Limit: {config.rate_limit_min}-{config.rate_limit_max}s")
    print(f"   • Content Extraction: {'✓' if config.extract_content else '✗'}")
    print(f"   • Media Download: {'✓' if config.download_media else '✗'}")
    print(f"   • Media Quality: {config.media_quality}")
    print(f"   • Max File Size: {config.max_media_size_mb}MB")
    print(f"   • Create Thumbnails: {'✓' if config.create_thumbnails else '✗'}")
    print(f"   • Download Folder: {config.base_download_folder}")
    print()

async def main():
    """Main premium scraping function"""
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('premium_scraper.log'),
            logging.StreamHandler()
        ]
    )
    
    print_banner()
    
    # Read URLs
    urls = read_urls_from_file("links.txt")
    if not urls:
        print("❌ Không có URLs để xử lý. Vui lòng thêm URLs vào links.txt")
        return
    
    # Configuration from command line arguments
    max_workers = 3
    extract_content = True
    download_media = True
    media_quality = "high"
    
    # Parse command line arguments
    if len(sys.argv) > 1:
        try:
            max_workers = int(sys.argv[1])
            print(f"📊 Sử dụng {max_workers} workers")
        except ValueError:
            print(f"⚠️  Worker count không hợp lệ: {sys.argv[1]}, sử dụng mặc định: {max_workers}")
    
    if len(sys.argv) > 2:
        extract_content = sys.argv[2].lower() in ['true', '1', 'yes', 'on']
        print(f"📝 Content extraction: {'✓' if extract_content else '✗'}")
    
    if len(sys.argv) > 3:
        download_media = sys.argv[3].lower() in ['true', '1', 'yes', 'on']
        print(f"💾 Media download: {'✓' if download_media else '✗'}")
    
    if len(sys.argv) > 4:
        media_quality = sys.argv[4].lower()
        if media_quality not in ['low', 'medium', 'high']:
            media_quality = 'high'
        print(f"🎥 Media quality: {media_quality}")
    
    # Create premium configuration
    config = ScraperConfig(
        max_workers=max_workers,
        driver_pool_size=max_workers,
        rate_limit_min=2.0,
        rate_limit_max=5.0,
        max_retries=3,
        extract_content=extract_content,
        content_preview_words=50,
        extract_hashtags=True,
        extract_mentions=True,
        extract_links=True,
        download_media=download_media,
        media_quality=media_quality,
        max_media_size_mb=50,
        create_thumbnails=True,
        organize_by_date=True,
        base_download_folder="downloads"
    )
    
    print_config(config)
    
    # Create premium progress callback
    progress_callback = create_premium_progress_callback()
    
    # Initialize premium scraper
    scraper = PremiumScraper(config)
    scraper.set_progress_callback(progress_callback)
    
    try:
        print("🚀 Bắt đầu Premium Scraping...")
        print("-" * 80)
        
        # Perform premium scraping
        results = await scraper.scrape_urls(urls)
        
        print("-" * 80)
        print("🎉 Premium Scraping hoàn thành!")
        print()
        
        # Detailed summary
        successful = sum(1 for r in results if r.success)
        failed = len(results) - successful
        total_content = sum(1 for r in results if r.success and r.post_data.content)
        total_media_found = sum(r.post_data.media_count for r in results if r.success)
        total_media_downloaded = sum(r.media_downloaded for r in results)
        total_download_size = sum(r.total_download_size for r in results)
        
        print("📊 TỔNG KẾT PREMIUM:")
        print(f"   • Tổng posts xử lý: {len(results)}")
        print(f"   • Thành công: {successful}")
        print(f"   • Thất bại: {failed}")
        print(f"   • Tỷ lệ thành công: {(successful/len(results)*100):.1f}%")
        print()
        
        if extract_content:
            print("📝 CONTENT EXTRACTION:")
            print(f"   • Posts có content: {total_content}")
            print(f"   • Tỷ lệ trích xuất: {(total_content/max(successful,1)*100):.1f}%")
            print()
        
        if download_media:
            print("💾 MEDIA DOWNLOAD:")
            print(f"   • Media tìm thấy: {total_media_found}")
            print(f"   • Media đã tải: {total_media_downloaded}")
            print(f"   • Tỷ lệ download: {(total_media_downloaded/max(total_media_found,1)*100):.1f}%")
            print(f"   • Tổng dung lượng: {total_download_size/1024/1024:.1f} MB")
            print()
        
        # Save results
        print("💾 Đang lưu kết quả...")
        
        # Create output directory
        output_dir = Path("output")
        output_dir.mkdir(exist_ok=True)
        
        # Save in multiple formats
        timestamp = asyncio.get_event_loop().time()
        
        # JSON format (detailed)
        import json
        json_data = []
        for result in results:
            json_data.append({
                'url': result.url,
                'success': result.success,
                'user_name': result.post_data.user_name if result.success else None,
                'post_type': result.post_data.post_type.value if result.success and result.post_data.post_type else None,
                'content': {
                    'full_text': result.post_data.content.full_text if result.success and result.post_data.content else None,
                    'word_count': result.post_data.content.word_count if result.success and result.post_data.content else 0,
                    'hashtags': result.post_data.content.hashtags if result.success and result.post_data.content else [],
                    'mentions': result.post_data.content.mentions if result.success and result.post_data.content else [],
                } if result.success and result.post_data.content else None,
                'stats': {
                    'likes': result.post_data.stats.likes if result.success and result.post_data.stats else '0',
                    'comments': result.post_data.stats.comments if result.success and result.post_data.stats else '0',
                    'shares': result.post_data.stats.shares if result.success and result.post_data.stats else '0',
                } if result.success and result.post_data.stats else None,
                'media': {
                    'total_found': result.post_data.media_count if result.success else 0,
                    'downloaded': result.media_downloaded,
                    'failed': result.media_failed,
                    'total_size_mb': round(result.total_download_size / 1024 / 1024, 2)
                },
                'files': {
                    'local_folder': result.post_data.local_folder if result.success else None,
                    'content_file': result.post_data.content_file if result.success else None,
                    'metadata_file': result.post_data.metadata_file if result.success else None,
                },
                'processing_time': result.processing_time,
                'error_message': result.error_message
            })
        
        json_file = output_dir / f"premium_results_{int(timestamp)}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, indent=2, ensure_ascii=False)
        
        # CSV format (summary)
        import csv
        csv_file = output_dir / f"premium_summary_{int(timestamp)}.csv"
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            fieldnames = ['url', 'success', 'user_name', 'post_type', 'likes', 'comments', 'shares', 
                         'content_words', 'media_found', 'media_downloaded', 'download_size_mb', 
                         'local_folder', 'processing_time', 'error_message']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for result in results:
                writer.writerow({
                    'url': result.url,
                    'success': result.success,
                    'user_name': result.post_data.user_name if result.success else '',
                    'post_type': result.post_data.post_type.value if result.success and result.post_data.post_type else '',
                    'likes': result.post_data.stats.likes if result.success and result.post_data.stats else '0',
                    'comments': result.post_data.stats.comments if result.success and result.post_data.stats else '0',
                    'shares': result.post_data.stats.shares if result.success and result.post_data.stats else '0',
                    'content_words': result.post_data.content.word_count if result.success and result.post_data.content else 0,
                    'media_found': result.post_data.media_count if result.success else 0,
                    'media_downloaded': result.media_downloaded,
                    'download_size_mb': round(result.total_download_size / 1024 / 1024, 2),
                    'local_folder': result.post_data.local_folder if result.success else '',
                    'processing_time': round(result.processing_time, 2),
                    'error_message': result.error_message or ''
                })
        
        # TXT format (readable)
        txt_file = output_dir / f"premium_readable_{int(timestamp)}.txt"
        with open(txt_file, 'w', encoding='utf-8') as f:
            f.write("🚀 FACEBOOK SCRAPER PREMIUM - KẾT QUẢ\n")
            f.write("=" * 80 + "\n\n")
            
            for i, result in enumerate(results, 1):
                f.write(f"📝 POST #{i}\n")
                f.write("-" * 40 + "\n")
                f.write(f"URL: {result.url}\n")
                
                if result.success:
                    data = result.post_data
                    f.write(f"✓ Thành công\n")
                    f.write(f"👤 Người đăng: {data.user_name or 'Unknown'}\n")
                    f.write(f"📊 Loại bài viết: {data.post_type.value if data.post_type else 'unknown'}\n")
                    
                    if data.content:
                        f.write(f"📝 Nội dung ({data.content.word_count} từ):\n")
                        f.write(f"{data.content.full_text[:200]}{'...' if len(data.content.full_text) > 200 else ''}\n")
                        if data.content.hashtags:
                            f.write(f"🏷️  Hashtags: {', '.join(data.content.hashtags)}\n")
                        if data.content.mentions:
                            f.write(f"👥 Mentions: {', '.join(data.content.mentions)}\n")
                    
                    if data.stats:
                        f.write(f"❤️  {data.stats.likes} likes, 💬 {data.stats.comments} comments, 🔄 {data.stats.shares} shares\n")
                    
                    if data.media_count > 0:
                        f.write(f"🖼️  Media: {data.media_count} tìm thấy, {result.media_downloaded} đã tải\n")
                        if result.total_download_size > 0:
                            f.write(f"💾 Dung lượng: {result.total_download_size/1024/1024:.1f} MB\n")
                        if data.local_folder:
                            f.write(f"📁 Thư mục: {data.local_folder}\n")
                    
                    f.write(f"⏱️  Thời gian xử lý: {result.processing_time:.2f}s\n")
                else:
                    f.write(f"❌ Thất bại: {result.error_message}\n")
                
                f.write("\n")
        
        print(f"✅ Kết quả đã được lưu:")
        print(f"   • JSON (chi tiết): {json_file}")
        print(f"   • CSV (tóm tắt): {csv_file}")
        print(f"   • TXT (dễ đọc): {txt_file}")
        
        if download_media and any(r.post_data.local_folder for r in results if r.success):
            print(f"   • Media files: downloads/ folder")
        
        # Show failed URLs if any
        if failed > 0:
            print()
            print("❌ CÁC URLs THẤT BẠI:")
            for result in results:
                if not result.success:
                    print(f"   • {result.url}: {result.error_message}")
        
        print()
        print("🎉 Hoàn thành Premium Scraping!")
        
    except KeyboardInterrupt:
        print("\n⚠️  Người dùng dừng scraping")
    except Exception as e:
        print(f"\n❌ Lỗi trong quá trình scraping: {e}")
        logging.error(f"Unexpected error: {e}")
    finally:
        # Cleanup
        print("\n🧹 Đang dọn dẹp...")
        scraper.shutdown()
        print("✅ Hoàn tất!")

def print_usage():
    """Print usage information"""
    print("🚀 FACEBOOK SCRAPER PREMIUM - COMMAND LINE")
    print()
    print("Usage:")
    print("  python run_premium.py [workers] [extract_content] [download_media] [media_quality]")
    print()
    print("Arguments:")
    print("  workers         : Số workers (1-10, mặc định: 3)")
    print("  extract_content : true/false (mặc định: true)")
    print("  download_media  : true/false (mặc định: true)")
    print("  media_quality   : low/medium/high (mặc định: high)")
    print()
    print("Examples:")
    print("  python run_premium.py                    # Mặc định")
    print("  python run_premium.py 5                  # 5 workers")
    print("  python run_premium.py 3 true false       # Không tải media")
    print("  python run_premium.py 2 true true medium # Chất lượng trung bình")
    print()
    print("Requirements:")
    print("  • File links.txt chứa các Facebook URLs")
    print("  • Mỗi URL trên một dòng riêng")
    print("  • Chrome browser đã cài đặt")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] in ['-h', '--help', 'help']:
        print_usage()
    else:
        asyncio.run(main()) 