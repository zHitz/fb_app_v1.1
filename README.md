# Facebook Post Scraper

A powerful desktop application that allows users to scrape Facebook post engagement metrics (likes, comments, shares) with both a modern GUI interface and command-line functionality.

## 🚀 Features

- **Dual Interface Options**
  - Modern GUI built with pywebview
  - Command-line interface for automation
  - Dark/light mode support
  - Real-time feedback

- **Robust Scraping**
  - Handles both posts and videos
  - Anti-detection measures
  - Automatic retry mechanism
  - Comprehensive error handling

- **Data Export**
  - Multiple export formats (TXT, CSV, JSON)
  - Consistent formatting
  - Timestamp tracking
  - Error logging

- **Technical Features**
  - Selenium WebDriver automation
  - BeautifulSoup HTML parsing
  - Chrome profile management
  - Detailed logging system

## 🛠️ Installation

1. **System Requirements**
   - Python 3.7 or higher
   - Google Chrome browser
   - Facebook account

2. **Install Python**
   ```bash
   # Download from https://www.python.org/downloads/
   # During installation, check "Add Python to PATH"
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Chrome**
   - Create a new Chrome profile for scraping
   - Log into Facebook in this profile
   - Note the profile directory path

## 💻 Usage

### GUI Mode
1. Run the application:
   ```bash
   python app.py
   ```
2. Enter Facebook post URLs
3. Click "Scrape" to start
4. View results in the interface

### Command Line Mode
1. Create a `links.txt` file with URLs
2. Run the scraper:
   ```bash
   python facebook_scrapper.py
   ```
3. Check `facebook_data.txt` for results

## 📁 Project Structure

```
fb_app/
├── app.py              # GUI application
├── facebook_scrapper.py # Core scraping logic
├── index.html          # GUI frontend
├── requirements.txt    # Dependencies
├── README.md          # Documentation
└── huong_dan.txt      # Vietnamese guide
```

## 🔧 Configuration

1. **Chrome Profile**
   ```python
   user_data_dir = "path/to/chrome/user/data"
   profile_directory = "profile_name"
   ```

2. **Scraping Settings**
   - Timeout: 10 seconds
   - Delay between requests: 3-5 seconds
   - Headless mode enabled

## ⚠️ Important Notes

- For educational purposes only
- Respect Facebook's terms of service
- Use responsibly
- Some posts may be inaccessible

## 🐛 Troubleshooting

1. **Chrome Issues**
   - Verify Chrome installation
   - Check profile configuration
   - Ensure Facebook login

2. **Python Issues**
   - Verify Python installation
   - Check dependencies
   - Review scraper.log

3. **Scraping Issues**
   - Check internet connection
   - Verify URL validity
   - Check post accessibility

## 📝 License

This project is licensed under the MIT License.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📧 Support

Email: [16.leminhnguyen@gmail.com] 