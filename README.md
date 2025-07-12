# Z-Library Scraper System

A comprehensive scraping and download system for Z-Library with interactive and web interfaces, multi-account support, and automatic file management.

## Features

- **Multi-level Scraping**: Advanced filtering by year, language, sort order
- **Interactive Mode**: Command-line interface with menus
- **Web Interface**: Flask-based web dashboard
- **Multi-Account Support**: Automatic account rotation for downloads
- **Duplicate Removal**: Automatic detection and removal of duplicate books
- **File Management**: Organized file structure with proper naming
- **Status Tracking**: Real-time tracking of download progress
- **Cover Downloads**: Automatic cover image downloads
- **Data Export**: Multiple formats (CSV, JSON, Excel)

## System Architecture

```
zlib_scraper/
├── config.py              # Configuration and settings
├── selenium_login.py      # Selenium-based login system
├── zlibrary_scraper.py    # Main scraping engine
├── download_covers.py     # Cover download manager
├── download_files.py      # File download with rotation
├── web_interface.py       # Flask web interface
├── run_all.py            # Complete workflow runner
├── analyze_books.py      # Data analysis tools
├── requirements.txt      # Python dependencies
└── zlib_data/           # Output directory
    ├── covers/          # Downloaded cover images
    ├── files/           # Downloaded ebook files
    ├── logs/            # System logs
    ├── analysis/        # Analysis reports
    └── zlib_metadata.csv # Main metadata file
```

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd zlib_scraper
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Install Chrome WebDriver** (for Selenium):
   ```bash
   # On Ubuntu/Debian
   sudo apt-get install chromium-chromedriver
   
   # On macOS
   brew install chromedriver
   
   # On Windows
   # Download from https://chromedriver.chromium.org/
   ```

4. **Configure accounts**:
   Edit `config.py` and add your Z-Library accounts:
   ```python
   ZLIBRARY_ACCOUNTS = [
       {
           "email": "your_email@example.com",
           "password": "your_password",
           "max_daily_downloads": 10,
           "daily_downloads": 0,
           "last_reset": "2024-01-01"
       }
   ]
   ```

## Usage

### Quick Start

Run the complete workflow:
```bash
python run_all.py
```

### Interactive Mode

#### 1. Login Management
```bash
python selenium_login.py
```
- Login with specific account
- Auto-login with available account
- Load existing session
- Test current session
- Reset daily download counts

#### 2. Metadata Scraping
```bash
python zlibrary_scraper.py
```
- Quick scrape with default settings
- Advanced scrape with filters
- Load existing metadata
- Remove duplicates
- Search in existing data

#### 3. Download Covers
```bash
python download_covers.py
```
Downloads cover images for all books in metadata

#### 4. Download Files
```bash
python download_files.py
```
Downloads ebook files with automatic account rotation

### Web Interface

Start the web interface:
```bash
python web_interface.py
```

Access at: http://127.0.0.1:5000

**Features**:
- Dashboard with real-time statistics
- Interactive scraping configuration
- Data viewing and searching
- Account management
- Download controls

## Configuration

### Main Settings (`config.py`)

```python
# Z-Library Configuration
BASE_URL = "https://z-library.sk"
SEARCH_URL = "/s/gramedia"

# Default Parameters
DEFAULT_ORDER = "bestmatch"
DEFAULT_LANGUAGE = "english"
DEFAULT_YEAR_FROM = "2025"

# Request Settings
REQUEST_TIMEOUT = 30
DELAY_BETWEEN_REQUESTS = 2
ROTATE_AFTER_DOWNLOADS = 10

# File Settings
MAX_FILENAME_LENGTH = 160
MIN_FILE_SIZE = 1000
```

### Supported Languages
- `english`
- `indonesian`

### Sort Options
- `bestmatch`
- `title`
- `author`
- `year`
- `rating`
- `downloads`

## File Structure

### Output Files
- `zlib_metadata.csv` - Main metadata file
- `zlib_metadata.json` - JSON format
- `zlib_metadata.xlsx` - Excel format
- `summary.txt` - Analysis summary
- `tracking.txt` - Download tracking

### File Naming Convention
Files are named using the pattern: `Title - Author.ext`
- Maximum 160 characters
- Invalid characters replaced with underscores
- Same naming for both covers and files

### Folder Structure
```
zlib_data/
├── covers/           # Cover images (.jpg)
├── files/           # Ebook files (.pdf, .epub, .djvu)
├── logs/            # System logs
│   ├── cover_download.log
│   ├── file_download.log
│   └── scraper.log
└── analysis/        # Analysis reports
```

## Advanced Usage

### Custom Scraping Parameters

```python
from zlibrary_scraper import ZLibraryScraper

scraper = ZLibraryScraper()

# Advanced scraping with filters
df = scraper.scrape_gramedia_books(
    max_pages=20,
    search_query="novel",
    year_from="2020",
    year_to="2024",
    language="english",
    sort_order="year"
)
```

### Account Management

```python
from selenium_login import SeleniumZLibraryLogin

login_manager = SeleniumZLibraryLogin()

# Get available account
account_index, account = login_manager.get_available_account()

# Login with specific account
session = login_manager.get_authenticated_session(account_index, headless=True)
```

### Data Analysis

```python
import pandas as pd
from config import OUTPUT_FILES

# Load metadata
df = pd.read_csv(OUTPUT_FILES['csv'])

# Filter by language
english_books = df[df['language'] == 'english']

# Filter by year
recent_books = df[df['year'] >= '2020']

# Search by title
search_results = df[df['title'].str.contains('python', case=False)]
```

## Troubleshooting

### Common Issues

1. **ChromeDriver not found**:
   ```bash
   # Install ChromeDriver
   pip install webdriver-manager
   ```

2. **Login failures**:
   - Check account credentials in `config.py`
   - Verify Z-Library is accessible
   - Try different accounts

3. **Download limits**:
   - Each account has 10 downloads per day
   - System automatically rotates accounts
   - Reset daily counts if needed

4. **File permission errors**:
   - Ensure write permissions to output directory
   - Close any open files before running

### Logs

Check log files in `zlib_data/logs/`:
- `cover_download.log` - Cover download status
- `file_download.log` - File download status
- `scraper.log` - Scraping operations

## Security Notes

- Store account credentials securely
- Don't commit `config.py` with real credentials
- Use environment variables for production
- Respect Z-Library's terms of service

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is for educational purposes only. Please respect the terms of service of Z-Library and other websites.

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review log files
3. Create an issue with detailed information

---

**Note**: This tool is designed for educational and research purposes. Please ensure compliance with all applicable laws and terms of service.