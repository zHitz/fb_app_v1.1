import time
import random
import csv
import json
import logging
import re
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException, WebDriverException
from bs4 import BeautifulSoup


# Configure logging
logging.basicConfig(
    filename='scraper.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def setup_driver():
    """Set up Selenium WebDriver with Chrome Options."""
    chrome_options = Options()

    # Anti-detection measures
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_argument('--disable-infobars')
    chrome_options.add_argument('--disable-notifications')

    # Use existing Chrome profile
    user_data_dir = r"C:\Users\PC9\AppData\Local\Google\Chrome\User Data\ScraperProfile"
    profile_directory = "Kanagiri"
    chrome_options.add_argument(f"--user-data-dir={user_data_dir}")
    chrome_options.add_argument(f"--profile-directory={profile_directory}")

    # Set a realistic User-Agent
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    chrome_options.add_argument(f'user-agent={user_agent}')

    # # Run in headless mode
    # chrome_options.add_argument('--headless=new')  # New headless mode for Chrome 109+
    # chrome_options.add_argument('--window-size=1920,1080')  # Set window size for headless mode

    # Initialize driver
    try:
        driver = webdriver.Chrome(options=chrome_options)
        logging.info("WebDriver initialized successfully in headless mode")
        return driver
    except WebDriverException as e:
        logging.error(f"Failed to initialize WebDriver: {e}")
        raise

def read_urls_from_file(filename="links.txt"):
    """Read URLs from a text file."""
    urls = []
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            for line in file:
                cleaned_line = line.strip()
                if cleaned_line:
                    urls.append(cleaned_line)
        logging.info(f"Read {len(urls)} URLs from {filename}")
    except FileNotFoundError:
        logging.error(f"File '{filename}' not found.")
        print(f"Error: File '{filename}' not found.")
    except Exception as e:
        logging.error(f"Error reading URLs: {e}")
        print(f"Error reading URLs: {e}")
    return urls

from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

def is_video_page(driver, wait):
    try:
        # 1. Kiểm tra dialog của post
        wait.until(EC.presence_of_element_located((By.XPATH, "//div[@role='dialog']")))
        logging.info("Detected dialog popup — this is likely a shared post.")
        return False  # Không phải video
    except TimeoutException:
        logging.info("No dialog popup detected — checking for video elements...")

    # 2. Kiểm tra các thành phần đặc trưng của video
    try:
        # Cách 1: Kiểm tra thẻ <video>
        driver.find_element(By.TAG_NAME, "video")
        logging.info("Video tag found — this is a video share.")
        return True
    except NoSuchElementException:
        pass

    try:
        # Cách 2: Kiểm tra div chứa nút Play (có aria-label)
        driver.find_element(By.XPATH, "//div[@aria-label='Play' or contains(@aria-label,'Xem')]")
        logging.info("Play button found — this is a video share.")
        return True
    except NoSuchElementException:
        pass

    logging.warning("No video elements found — unknown or unsupported format.")
    return False


from selenium.common.exceptions import NoSuchElementException

def get_video_stats(driver, timeout=10):
    stats = {}
    xpaths = {
        "likes": "/html/body/div[1]/div/div[1]/div/div[3]/div/div/div[1]/div[2]/div/div/div/div[1]/div/div/div[1]/div[2]/div[2]/div/div/div[2]/div/div[1]/div/span/span/span",
        "comments": "/html/body/div[1]/div/div[1]/div/div[3]/div/div/div[1]/div[2]/div/div/div/div[1]/div/div/div[1]/div[2]/div[2]/div/div/div[2]/div/div[3]/span/div/span/span"
    }

    for key, xpath in xpaths.items():
        try:
            element = WebDriverWait(driver, timeout).until(
                EC.presence_of_element_located((By.XPATH, xpath))
            )
            stats[key] = element.text.strip()
        except TimeoutException:
            logging.warning(f"Could not find {key} element.")
            stats[key] = None

    logging.info(f"Extracted stats: {stats}")
    return stats



def extract_data(driver, url):
    data = {
        'original_url': url,
        'final_url': None,
        'user_name': None,
        'likes': "0",
        'comments': "0",
        'shares': "0",
        'scrape_timestamp': datetime.now().isoformat(),
        'error_message': None
    }

    wait = WebDriverWait(driver, 15)

    try:
        driver.get(url)
        try:
            wait.until(EC.url_contains('facebook.com/'))
            data['final_url'] = driver.current_url
            logging.info(f"Redirected to: {data['final_url']}")
        except TimeoutException:
            logging.warning(f"Redirect timeout for URL: {url}")
            data['error_message'] = "Redirect Timeout"
            return data


        if is_video_page(driver, wait):
            logging.info("Video page detected, trying to extract data from video")
            
            # Extract data from video
            try:
                # Extract video title
                video_title = driver.find_element(By.XPATH, "//div[@role='dialog']//h2[contains(@class, 'x1lliihq')]").text.strip()
                data['video_title'] = video_title
                logging.info(f"Extracted video title: {data['video_title']}")
            except (NoSuchElementException, TimeoutException):
                data['video_title'] = "Not found"
                logging.warning("Video title not found")
                
            # Extract video likes using full XPath
            likes_text = get_video_stats(driver)
            data['likes'] = likes_text['likes']
            data['comments'] = likes_text['comments']
            

        else:
            logging.info("Not a video page, trying to extract data from post")
            # Random scroll in popup
            try:
                dialog = driver.find_element(By.XPATH, "//div[@role='dialog']")
                driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight / 2;", dialog)
                time.sleep(random.uniform(0.5, 1.5))
            except:
                pass

            # Extract data (no retries)
            try:
                soup = BeautifulSoup(driver.page_source, 'html.parser')
                dialog_soup = soup.find('div', {'role': 'dialog'})

                if not dialog_soup:
                    logging.warning("Dialog element not found in BeautifulSoup.")
                    data['error_message'] = "Dialog not found in HTML"
                    return data

                # Username/Page name
                try:
                    user_xpath = "//div[@role='dialog']//span[contains(text(), 'Bài viết của')]"
                    user_element = wait.until(EC.visibility_of_element_located((By.XPATH, user_xpath)))
                    user_text = user_element.text.strip()
                    data['user_name'] = user_text.replace("Bài viết của ", "") if user_text.startswith("Bài viết của ") else user_text
                    data['user_name'] = data['user_name'] or "Unknown"
                    logging.info(f"Extracted username: {data['user_name']}")
                except (NoSuchElementException, TimeoutException):
                    data['user_name'] = "Not found"
                    logging.warning("Username not found")

                # Comments
                try:
                    comments_xpath = "//div[@role='dialog']//span[contains(text(), 'bình luận') or contains(text(), 'comment')]"
                    comments_element = wait.until(EC.visibility_of_element_located((By.XPATH, comments_xpath)))
                    comments_text = comments_element.text.strip()
                    # Extract only the number part by removing "lượt bình luận" or "comment" if present
                    data['comments'] = comments_text.split('bình luận')[0].split('comment')[0].strip()
                    logging.info(f"Extracted comments: {data['comments']}")
                except (NoSuchElementException, TimeoutException):
                    data['comments'] = "0"
                    logging.info("No comments found, set to 0")

                # Shares
                try:
                    shares_xpath = "//div[@role='dialog']//span[contains(text(), 'lượt chia sẻ') or contains(text(), 'share')]"
                    shares_element = wait.until(EC.visibility_of_element_located((By.XPATH, shares_xpath)))
                    shares_text = shares_element.text.strip()
                    # Extract only the number part by removing "lượt chia sẻ" or "share" if present
                    data['shares'] = shares_text.split('lượt chia sẻ')[0].split('share')[0].strip()
                    logging.info(f"Extracted shares: {data['shares']}")
                except (NoSuchElementException, TimeoutException):
                    data['shares'] = "0"
                    logging.info("No shares found, set to 0")

                # Likes
                try:
                    # Strategy 1: BeautifulSoup with flexible class matching
                    likes_span = dialog_soup.find('span', class_=lambda x: x and 'x1e558r4' in x)
                    if likes_span:
                        data['likes'] = likes_span.text.strip()
                        logging.info(f"Extracted likes via BeautifulSoup: {data['likes']}")
                    else:
                        # Strategy 2: XPath near 'Tất cả cảm xúc:'
                        likes_xpath = "//div[@role='dialog']//div[contains(text(), 'Tất cả cảm xúc:')]/following-sibling::span//span[contains(@class, 'x1e558r4')]"
                        likes_element = wait.until(EC.visibility_of_element_located((By.XPATH, likes_xpath)))
                        data['likes'] = likes_element.text.strip()
                        logging.info(f"Extracted likes via XPath: {data['likes']}")
                except (NoSuchElementException, TimeoutException):
                    # Strategy 3: Aria-label fallback
                    try:
                        aria_xpath = "//div[@role='dialog']//div[contains(@aria-label, 'Thích:') or contains(@aria-label, 'Like:')]"
                        aria_element = wait.until(EC.visibility_of_element_located((By.XPATH, aria_xpath)))
                        aria_label = aria_element.get_attribute('aria-label')
                        match = re.search(r'\d+[.,]?\d*', aria_label)
                        data['likes'] = match.group() if match else "0"
                        logging.info(f"Extracted likes via aria-label: {data['likes']}")
                    except (NoSuchElementException, TimeoutException):
                        data['likes'] = "0"
                        logging.info("No likes found, set to 0")
                except Exception as e:
                    data['likes'] = "0"
                    logging.warning(f"Error extracting likes: {e}")

            except Exception as e:
                data['error_message'] = f"Extraction Error: {type(e).__name__}"
                logging.error(f"Extraction error for URL {url}: {e}")

    except WebDriverException as e:
        data['error_message'] = f"WebDriver Error: {type(e).__name__}"
        logging.error(f"WebDriver error for URL {url}: {e}")
    except Exception as e:
        data['error_message'] = f"General Error: {type(e).__name__}"
        logging.error(f"Unexpected error for URL {url}: {e}")

    return data


def save_to_txt(data_list, filename="facebook_data.txt"):
    """Save data to TXT file with consistent formatting."""
    try:
        with open(filename, 'w', encoding='utf-8') as txtfile:
            for data in data_list:
                user_name = data.get('user_name', 'Unknown')
                likes = data.get('likes', '0')
                comments = data.get('comments', '0')
                shares = data.get('shares', '0')

                # Format comments: Extract number and append "lượt bình luận"
                if comments == "0":
                    comments_formatted = "0 lượt bình luận"
                else:
                    # Strip suffixes and keep only the number
                    comments_number = re.sub(r'\D', '', comments.replace(',', ''))  # Remove non-digits
                    comments_formatted = f"{comments_number} lượt bình luận"

                # Format shares: Extract number and append "lượt chia sẻ"
                if shares == "0":
                    shares_formatted = "0 lượt chia sẻ"
                else:
                    # Strip suffixes and keep only the number
                    shares_number = re.sub(r'\D', '', shares.replace(',', ''))  # Remove non-digits
                    shares_formatted = f"{shares_number} lượt chia sẻ"

                txtfile.write(f"Bài viết của {user_name}\n")
                txtfile.write(f"        ({likes} lượt thích, {comments_formatted}, {shares_formatted})\n\n")
        logging.info(f"Data saved to {filename}")
        print(f"Data saved to {filename}")
    except IOError as e:
        logging.error(f"IO error writing TXT: {e}")
        print(f"Error writing TXT: {e}")
    except Exception as e:
        logging.error(f"Unexpected error writing TXT: {e}")
        print(f"Unexpected error writing TXT: {e}")

def main():
    """Main function to orchestrate the scraping process."""
    driver = None
    try:
        driver = setup_driver()
        urls = read_urls_from_file("links.txt")
        if not urls:
            logging.error("No URLs to process. Exiting.")
            print(f"Error: No URLs to process. Please add URLs to links.txt and try again.")
            return

        scraped_data = []
        for url in urls:
            logging.info(f"Processing URL: {url}")
            print(f"Processing URL: {url}")
            data = extract_data(driver, url)
            scraped_data.append(data)
            print("-" * 30)
            time.sleep(random.uniform(3, 5))

        # Save data
        save_to_txt(scraped_data)

    except Exception as e:
        logging.error(f"Main process error: {e}")
        print(f"Error: {e}")
    finally:
        if driver:
            driver.quit()
            logging.info("WebDriver closed.")
            print("Scraping completed. Check facebook_data.txt for results.")

if __name__ == "__main__":
    main()