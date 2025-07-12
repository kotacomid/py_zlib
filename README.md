# Enhanced Z-Library Scraper

A comprehensive scraping system for Z-Library with metadata collection, cover downloads, and file downloads with multi-account rotation.

## Features

- **Multi-Mode Operation**: Interactive, Web, and Automatic modes
- **Metadata Scraping**: Collect book metadata with filtering options
- **Cover Downloads**: Download book covers with status tracking
- **File Downloads**: Download ebooks with account rotation
- **Duplicate Removal**: Automatic removal of duplicate entries
- **Progress Tracking**: Real-time progress monitoring
- **Error Handling**: Robust error handling and retry mechanisms
- **Web Interface**: Flask-based web interface for easy control

## Installation

1. **Clone the repository**:
```bash
git clone <repository-url>
cd zlibrary-scraper
```

2. **Install dependencies**:
```bash
pip install -r requirements.txt
```

3. **Configure accounts**:
Edit `config.py` and add your Z-Library accounts:
```python
ZLIBRARY_ACCOUNTS = [
    {
        'email': 'your_email1@example.com',
        'password': 'your_password1',
        'max_daily_downloads': 10,
        'daily_downloads': 0,
        'last_reset': datetime.now().strftime('%Y-%m-%d')
    },
    # Add more accounts as needed
]
```

## Usage

### Quick Start

Run the complete process with default settings:
```bash
python run_all.py
```

### Interactive Mode

Run with interactive menu:
```bash
python run_all.py interactive
```

### Web Interface

Start the web interface:
```bash
python run_all.py web
```
Then open http://localhost:5000 in your browser.

### Individual Components

#### Metadata Scraping
```bash
# Default scraping
python zlibrary_scraper.py auto

# Interactive mode
python zlibrary_scraper.py interactive

# Web mode
python zlibrary_scraper.py web
```

#### Cover Downloads
```bash
# Download all pending covers
python download_covers.py

# Download specific cover
python download_covers.py specific <book_id>

# Show statistics
python download_covers.py stats
```

#### File Downloads
```bash
# Download all pending files
python download_files.py

# Download specific file
python download_files.py specific <book_id>

# Show statistics
python download_files.py stats
```

### Custom Parameters

Run with custom search parameters:
```bash
python run_all.py custom "novel" 15 2020
```

## Configuration

### Main Configuration (`config.py`)

Key settings you can modify:

- **Base URLs**: Z-Library domain and search paths
- **Account Settings**: Email, password, daily limits
- **Scraping Settings**: Max pages, delays, timeouts
- **Download Settings**: File size limits, rotation intervals
- **File Naming**: Max filename length, separators

### Folder Structure

```
ebooks/
├── covers/          # Downloaded book covers
├── files/           # Downloaded ebook files
├── logs/            # Log files
├── analysis/        # Analysis reports
├── zlib_metadata.csv    # Main metadata file
├── zlib_metadata.json   # JSON format metadata
└── zlib_metadata.xlsx   # Excel format metadata
```

## Features in Detail

### Metadata Scraping

- **Multi-level filtering**: Year range, language, sort options
- **Duplicate removal**: Automatic removal based on title and author
- **Status tracking**: Track download progress for each book
- **Multiple formats**: Save to CSV, JSON, and Excel

### Cover Downloads

- **Smart naming**: Use title and author for filenames
- **Status tracking**: Update CSV with download status
- **Retry mechanism**: Automatic retry on failures
- **File validation**: Check file size and format

### File Downloads

- **Account rotation**: Rotate between multiple accounts
- **Rate limiting**: Respect daily download limits
- **Error handling**: Handle timeouts and failures
- **Progress tracking**: Real-time download progress

### Web Interface

- **Real-time status**: Live progress updates
- **Easy configuration**: Web-based parameter setting
- **Statistics display**: Visual progress and statistics
- **Responsive design**: Works on desktop and mobile

## File Naming Convention

Files are named using the pattern: `Title - Author.ext`

- **Covers**: `Title - Author.jpg` (or .png, .webp)
- **Files**: `Title - Author.pdf` (or .epub, .mobi, etc.)
- **Max length**: 160 characters (configurable)
- **Invalid characters**: Automatically removed

## Account Management

### Adding Accounts

1. Edit `config.py`
2. Add account details to `ZLIBRARY_ACCOUNTS`
3. Set appropriate daily limits

### Account Rotation

- **Automatic rotation**: Every 10 downloads (configurable)
- **Failure handling**: Switch accounts on consecutive failures
- **Limit tracking**: Respect daily download limits
- **Status monitoring**: Track account usage

## Error Handling

### Common Issues

1. **Authentication failures**: Check account credentials
2. **Rate limiting**: Wait or use different accounts
3. **Network timeouts**: Automatic retry with delays
4. **File size issues**: Check MIN_FILE_SIZE and MAX_FILE_SIZE

### Logging

All operations are logged to:
- Console output
- Log files in `ebooks/logs/`
- CSV status tracking

## Advanced Usage

### Custom Scraping Filters

```python
from zlibrary_scraper import EnhancedZLibraryScraper

scraper = EnhancedZLibraryScraper()
df = scraper.scrape_with_filters(
    search_query="gramedia",
    max_pages=10,
    year_from="2020",
    year_to="2025",
    language="english",
    sort_by="year",
    use_auth=True
)
```

### Batch Processing

```bash
# Scrape multiple queries
python run_all.py custom "gramedia" 10 2025
python run_all.py custom "novel" 5 2024
python run_all.py custom "fiction" 8 2023
```

### Monitoring Progress

Check progress in real-time:
```bash
# View current status
python download_files.py stats
python download_covers.py stats
```

## Troubleshooting

### Common Problems

1. **"No accounts available"**
   - Check account configuration in `config.py`
   - Verify account credentials
   - Check daily download limits

2. **"Authentication failed"**
   - Verify Z-Library credentials
   - Check if accounts are still active
   - Try different accounts

3. **"File not found"**
   - Run metadata scraping first
   - Check if CSV file exists
   - Verify file paths

4. **"Download timeout"**
   - Increase timeout values in config
   - Check network connection
   - Try different accounts

### Debug Mode

Enable debug logging by changing `LOG_LEVEL` in `config.py`:
```python
LOG_LEVEL = 'DEBUG'
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is for educational purposes only. Please respect Z-Library's terms of service and use responsibly.

## Disclaimer

This tool is provided as-is for educational purposes. Users are responsible for complying with all applicable laws and terms of service. The authors are not responsible for any misuse of this software.