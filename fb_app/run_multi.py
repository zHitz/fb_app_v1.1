#!/usr/bin/env python3
"""
Simple command-line runner for multi-threaded Facebook scraper
"""

import sys
import logging
from multi_thread_scraper import MultiThreadScraper, create_progress_callback

def read_urls_from_file(filename="links.txt"):
    """Read URLs from a text file."""
    urls = []
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            for line in file:
                cleaned_line = line.strip()
                if cleaned_line:
                    urls.append(cleaned_line)
        print(f"Read {len(urls)} URLs from {filename}")
    except FileNotFoundError:
        print(f"Error: File '{filename}' not found.")
        return []
    except Exception as e:
        print(f"Error reading URLs: {e}")
        return []
    return urls

def main():
    """Main function to run multi-threaded scraping"""
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('scraper_multi.log'),
            logging.StreamHandler()
        ]
    )
    
    print("=== Facebook Multi-Thread Scraper ===")
    print()
    
    # Read URLs from file
    urls = read_urls_from_file("links.txt")
    if not urls:
        print("No URLs to process. Please add URLs to links.txt and try again.")
        return
    
    # Configuration
    max_workers = 3
    driver_pool_size = 3
    rate_limit_min = 2
    rate_limit_max = 5
    max_retries = 3
    
    # Allow command line configuration
    if len(sys.argv) > 1:
        try:
            max_workers = int(sys.argv[1])
            print(f"Using {max_workers} workers")
        except ValueError:
            print(f"Invalid worker count: {sys.argv[1]}, using default: {max_workers}")
    
    print(f"Configuration:")
    print(f"  - Max Workers: {max_workers}")
    print(f"  - Driver Pool Size: {driver_pool_size}")
    print(f"  - Rate Limit: {rate_limit_min}-{rate_limit_max} seconds")
    print(f"  - Max Retries: {max_retries}")
    print(f"  - Total URLs: {len(urls)}")
    print()
    
    # Create progress callback
    progress_callback = create_progress_callback()
    
    # Initialize scraper
    scraper = MultiThreadScraper(
        max_workers=max_workers,
        driver_pool_size=driver_pool_size,
        rate_limit_delay=(rate_limit_min, rate_limit_max),
        max_retries=max_retries,
        progress_callback=progress_callback
    )
    
    try:
        print("Starting multi-threaded scraping...")
        print("-" * 50)
        
        # Perform scraping
        results = scraper.scrape_urls(urls)
        
        print("-" * 50)
        print(f"Scraping completed!")
        print()
        
        # Summary
        successful = sum(1 for r in results if r.success)
        failed = len(results) - successful
        
        print(f"Summary:")
        print(f"  - Total processed: {len(results)}")
        print(f"  - Successful: {successful}")
        print(f"  - Failed: {failed}")
        print(f"  - Success rate: {(successful/len(results)*100):.1f}%")
        print()
        
        # Save results
        print("Saving results...")
        scraper.save_results(results, "txt")
        scraper.save_results(results, "csv")
        scraper.save_results(results, "json")
        
        print("Results saved in multiple formats!")
        
        # Show failed URLs if any
        if failed > 0:
            print()
            print("Failed URLs:")
            for result in results:
                if not result.success:
                    print(f"  - {result.url}: {result.error_message}")
        
    except KeyboardInterrupt:
        print("\nScraping interrupted by user")
    except Exception as e:
        print(f"Error during scraping: {e}")
        logging.error(f"Unexpected error: {e}")
    finally:
        # Cleanup
        print("\nCleaning up...")
        scraper.shutdown()
        print("Done!")

if __name__ == "__main__":
    main() 