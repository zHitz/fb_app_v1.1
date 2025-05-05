# Facebook Post Scraper

A desktop application built with Python and pywebview that allows users to scrape Facebook post engagement metrics (likes, comments, shares) in a modern, user-friendly interface.

## 🚀 Features

- **Modern UI with Dark Mode**
  - Clean, responsive interface
  - Dark/light mode toggle
  - Real-time feedback
  - Loading indicators

- **Multi-URL Processing**
  - Process multiple Facebook post URLs at once
  - Each URL on a new line
  - Progress tracking
  - Error handling per URL

- **Data Display**
  - User-friendly result cards
  - Engagement metrics (likes, comments, shares)
  - Timestamp of scraping
  - Copyable summary line
  - Error messages for failed attempts

- **Technical Features**
  - Built with pywebview for native desktop experience
  - Selenium for robust web scraping
  - BeautifulSoup for HTML parsing
  - Anti-detection measures
  - Comprehensive error handling
  - Logging system

## 🛠️ Installation

1. **Clone the repository**
   ```bash
   git clone [repository-url]
   cd fb_app
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Ensure Chrome is installed**
   - The application uses Chrome for web scraping
   - Make sure Chrome is installed on your system

## 💻 Usage

1. **Start the application**
   ```bash
   python app.py
   ```

2. **Using the application**
   - Paste one or more Facebook post URLs in the text area
   - Each URL should be on a new line
   - Click "Scrape Posts" to start processing
   - Results will appear in cards below
   - Use the copy button to copy engagement metrics

3. **Dark Mode**
   - Click the moon/sun icon in the top right to toggle dark mode
   - Your preference will be saved for future sessions

## 📁 Project Structure

```
fb_app/
├── app.py              # Main application and API
├── index.html          # Frontend interface
├── facebook_scrapper.py # Scraping logic
├── requirements.txt    # Dependencies
└── README.md          # Documentation
```

## 🔧 How It Works

1. **Frontend (index.html)**
   - Modern UI built with Tailwind CSS
   - Handles user input and display
   - Communicates with Python backend via pywebview API

2. **Backend (app.py)**
   - Manages the desktop window
   - Provides API for frontend
   - Handles resource management
   - Coordinates scraping operations

3. **Scraper (facebook_scrapper.py)**
   - Uses Selenium for web automation
   - Implements anti-detection measures
   - Extracts engagement metrics
   - Handles errors and timeouts

## ⚠️ Important Notes

- This tool is for educational purposes only
- Respect Facebook's terms of service
- Use responsibly and avoid excessive scraping
- Some posts may be inaccessible due to privacy settings

## 🐛 Troubleshooting

1. **Chrome not found**
   - Ensure Chrome is installed
   - Check Chrome version compatibility

2. **Scraping errors**
   - Check internet connection
   - Verify URL validity
   - Ensure you're logged into Facebook in Chrome

3. **Application not starting**
   - Verify all dependencies are installed
   - Check Python version (3.7+ required)
   - Ensure required permissions

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request. 