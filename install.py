#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Installation script for Z-Library Scraper System
Helps users set up the system and configure accounts
"""

import os
import sys
import subprocess
import json
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        print(f"Current version: {sys.version}")
        return False
    print(f"✅ Python version: {sys.version.split()[0]}")
    return True

def install_dependencies():
    """Install required dependencies"""
    print("\n📦 Installing dependencies...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing dependencies: {e}")
        return False

def create_config():
    """Create configuration file with user input"""
    print("\n⚙️  Configuring Z-Library accounts...")
    
    config_template = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Configuration file for Z-Library Scraper System
Contains all settings, URLs, and account configurations
"""

import os
from datetime import datetime

# ============================================================================
# Z-LIBRARY CONFIGURATION
# ============================================================================

# Base URL for Z-Library
BASE_URL = "https://z-library.sk"

# Search URL for Gramedia books
SEARCH_URL = "/s/gramedia"

# Default search parameters
DEFAULT_ORDER = "bestmatch"
DEFAULT_LANGUAGE = "english"  # english, indonesian
DEFAULT_YEAR_FROM = "2025"
DEFAULT_YEAR_TO = ""

# Request settings
REQUEST_TIMEOUT = 30
DELAY_BETWEEN_REQUESTS = 2
RETRY_DELAY = 5
MAX_RETRIES = 3

# Account rotation settings
ROTATE_AFTER_DOWNLOADS = 10
ROTATE_AFTER_FAILURES = 3

# ============================================================================
# Z-LIBRARY ACCOUNTS
# ============================================================================

ZLIBRARY_ACCOUNTS = [
{accounts}
]

# ============================================================================
# FOLDER STRUCTURE
# ============================================================================

# Main folder for all data
EBOOK_FOLDER = "zlib_data"

# Subfolders
COVERS_FOLDER = "covers"
FILES_FOLDER = "files"
LOGS_FOLDER = "logs"
ANALYSIS_FOLDER = "analysis"

# ============================================================================
# OUTPUT FILES
# ============================================================================

OUTPUT_FILES = {{
    "csv": f"{{EBOOK_FOLDER}}/zlib_metadata.csv",
    "json": f"{{EBOOK_FOLDER}}/zlib_metadata.json",
    "excel": f"{{EBOOK_FOLDER}}/zlib_metadata.xlsx",
    "summary": f"{{EBOOK_FOLDER}}/{{ANALYSIS_FOLDER}}/summary.txt",
    "tracking": f"{{EBOOK_FOLDER}}/{{ANALYSIS_FOLDER}}/tracking.txt",
    "cover_log": f"{{EBOOK_FOLDER}}/{{LOGS_FOLDER}}/cover_download.log",
    "file_log": f"{{EBOOK_FOLDER}}/{{LOGS_FOLDER}}/file_download.log",
    "scraper_log": f"{{EBOOK_FOLDER}}/{{LOGS_FOLDER}}/scraper.log"
}}

# ============================================================================
# HTTP HEADERS
# ============================================================================

HEADERS = {{
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9,id;q=0.8',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
    'Cache-Control': 'max-age=0'
}}

# ============================================================================
# SCRAPING SETTINGS
# ============================================================================

# Default scraping parameters
DEFAULT_MAX_PAGES = 10
DEFAULT_SEARCH_QUERY = "gramedia"

# Supported languages for filtering
SUPPORTED_LANGUAGES = ["english", "indonesian"]

# Supported sort orders
SORT_OPTIONS = [
    "bestmatch",
    "title",
    "author", 
    "year",
    "rating",
    "downloads"
]

# ============================================================================
# DOWNLOAD SETTINGS
# ============================================================================

# File size limits (in bytes)
MIN_FILE_SIZE = 1000  # Minimum file size to consider valid
MAX_FILE_SIZE = 500 * 1024 * 1024  # 500MB max

# Cover image settings
COVER_TIMEOUT = 15
COVER_RETRY_COUNT = 3

# File download settings
FILE_TIMEOUT = 60
FILE_CHUNK_SIZE = 8192

# ============================================================================
# FILENAME SETTINGS
# ============================================================================

# Maximum filename length (including extension)
MAX_FILENAME_LENGTH = 160

# Invalid characters for filenames
INVALID_FILENAME_CHARS = '<>:"/\\\\|?*'

# ============================================================================
# WEB INTERFACE SETTINGS (Flask)
# ============================================================================

FLASK_HOST = "127.0.0.1"
FLASK_PORT = 5000
FLASK_DEBUG = True

# ============================================================================
# LOGGING SETTINGS
# ============================================================================

LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def sanitize_filename(filename):
    """Sanitize filename for safe file system usage"""
    # Remove invalid characters
    for char in INVALID_FILENAME_CHARS:
        filename = filename.replace(char, '_')
    
    # Remove extra spaces and dashes
    filename = ' '.join(filename.split())
    filename = filename.replace(' ', '-')
    
    # Limit length
    if len(filename) > MAX_FILENAME_LENGTH:
        filename = filename[:MAX_FILENAME_LENGTH]
    
    return filename

def create_folder_structure():
    """Create all necessary folders"""
    folders = [
        EBOOK_FOLDER,
        f"{{EBOOK_FOLDER}}/{{COVERS_FOLDER}}",
        f"{{EBOOK_FOLDER}}/{{FILES_FOLDER}}",
        f"{{EBOOK_FOLDER}}/{{LOGS_FOLDER}}",
        f"{{EBOOK_FOLDER}}/{{ANALYSIS_FOLDER}}"
    ]
    
    for folder in folders:
        os.makedirs(folder, exist_ok=True)
    
    return True

def get_file_path(title, author, extension, folder_type="files"):
    """Generate file path based on title and author"""
    # Create base filename
    base_filename = f"{{title}} - {{author}}"
    base_filename = sanitize_filename(base_filename)
    
    # Add extension
    if not extension.startswith('.'):
        extension = f".{{extension}}"
    
    filename = f"{{base_filename}}{{extension}}"
    
    # Determine folder
    if folder_type == "covers":
        folder = f"{{EBOOK_FOLDER}}/{{COVERS_FOLDER}}"
    else:
        folder = f"{{EBOOK_FOLDER}}/{{FILES_FOLDER}}"
    
    return os.path.join(folder, filename)

# ============================================================================
# INITIALIZATION
# ============================================================================

# Create folder structure on import
create_folder_structure()
'''
    
    accounts = []
    print("Enter your Z-Library account details:")
    print("(Press Enter without email to finish)")
    
    while True:
        email = input("\nEmail: ").strip()
        if not email:
            break
            
        password = input("Password: ").strip()
        if not password:
            print("❌ Password is required")
            continue
            
        max_downloads = input("Max daily downloads (default 10): ").strip()
        max_downloads = int(max_downloads) if max_downloads.isdigit() else 10
        
        account = f'''    {{
        "email": "{email}",
        "password": "{password}",
        "max_daily_downloads": {max_downloads},
        "daily_downloads": 0,
        "last_reset": datetime.now().strftime("%Y-%m-%d")
    }}'''
        
        accounts.append(account)
        
        add_more = input("Add another account? (y/n): ").strip().lower()
        if add_more not in ['y', 'yes']:
            break
    
    if not accounts:
        print("❌ At least one account is required")
        return False
    
    accounts_str = ',\n'.join(accounts)
    config_content = config_template.format(accounts=accounts_str)
    
    try:
        with open('config.py', 'w', encoding='utf-8') as f:
            f.write(config_content)
        print("✅ Configuration file created successfully")
        return True
    except Exception as e:
        print(f"❌ Error creating config file: {e}")
        return False

def create_folders():
    """Create necessary folders"""
    print("\n📁 Creating folder structure...")
    
    folders = [
        "zlib_data",
        "zlib_data/covers",
        "zlib_data/files", 
        "zlib_data/logs",
        "zlib_data/analysis"
    ]
    
    for folder in folders:
        try:
            os.makedirs(folder, exist_ok=True)
            print(f"✅ Created: {folder}")
        except Exception as e:
            print(f"❌ Error creating {folder}: {e}")
            return False
    
    return True

def test_installation():
    """Test if installation is working"""
    print("\n🧪 Testing installation...")
    
    try:
        # Test imports
        import config
        print("✅ Config imported successfully")
        
        from selenium_login import SeleniumZLibraryLogin
        print("✅ Selenium login imported successfully")
        
        from zlibrary_scraper import ZLibraryScraper
        print("✅ Scraper imported successfully")
        
        # Test folder creation
        config.create_folder_structure()
        print("✅ Folder structure created successfully")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Test error: {e}")
        return False

def main():
    """Main installation function"""
    print("🚀 Z-Library Scraper System - Installation")
    print("=" * 50)
    
    # Check Python version
    if not check_python_version():
        return False
    
    # Install dependencies
    if not install_dependencies():
        return False
    
    # Create configuration
    if not create_config():
        return False
    
    # Create folders
    if not create_folders():
        return False
    
    # Test installation
    if not test_installation():
        return False
    
    print("\n" + "=" * 50)
    print("🎉 Installation completed successfully!")
    print("=" * 50)
    print("\nNext steps:")
    print("1. Edit config.py if you need to add more accounts")
    print("2. Run: python selenium_login.py (to test login)")
    print("3. Run: python zlibrary_scraper.py (to start scraping)")
    print("4. Run: python run_all.py (for complete workflow)")
    print("5. Run: python web_interface.py (for web interface)")
    
    print("\n📚 Documentation:")
    print("- README.md - Complete usage guide")
    print("- config.py - Configuration options")
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        if not success:
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n❌ Installation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Installation failed: {e}")
        sys.exit(1)