#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Configuration file for Z-Library Scraper System
"""

import os
from datetime import datetime

# Base URLs
BASE_URL = "https://z-library.sk"
SEARCH_URL = "/s/gramedia"

# Request settings
REQUEST_TIMEOUT = 30
DELAY_BETWEEN_REQUESTS = 2
RETRY_DELAY = 5
MAX_RETRIES = 3

# Headers for requests
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
}

# Default search parameters
DEFAULT_ORDER = "bestmatch"
DEFAULT_LANGUAGE = "english"
DEFAULT_YEAR_FROM = "2020"
DEFAULT_YEAR_TO = "2025"

# Folder structure
EBOOK_FOLDER = "ebooks"
COVERS_FOLDER = "covers"
FILES_FOLDER = "files"
LOGS_FOLDER = "logs"
ANALYSIS_FOLDER = "analysis"

# Output files
OUTPUT_FILES = {
    'csv': f"{EBOOK_FOLDER}/zlib_metadata.csv",
    'json': f"{EBOOK_FOLDER}/zlib_metadata.json",
    'excel': f"{EBOOK_FOLDER}/zlib_metadata.xlsx"
}

# Z-Library accounts for rotation
ZLIBRARY_ACCOUNTS = [
    {
        'email': 'your_email1@example.com',
        'password': 'your_password1',
        'max_daily_downloads': 10,
        'daily_downloads': 0,
        'last_reset': datetime.now().strftime('%Y-%m-%d')
    },
    {
        'email': 'your_email2@example.com',
        'password': 'your_password2',
        'max_daily_downloads': 10,
        'daily_downloads': 0,
        'last_reset': datetime.now().strftime('%Y-%m-%d')
    }
]

# Scraping settings
MAX_PAGES_PER_SEARCH = 10
MAX_BOOKS_PER_PAGE = 50
MAX_TOTAL_BOOKS = 500

# Download settings
DOWNLOAD_TIMEOUT = 300  # 5 minutes
COVER_DOWNLOAD_TIMEOUT = 60
ROTATION_INTERVAL = 10  # Rotate account every 10 downloads
MAX_CONCURRENT_DOWNLOADS = 3

# File naming settings
MAX_FILENAME_LENGTH = 160
FILENAME_SEPARATOR = " - "

# Supported languages
SUPPORTED_LANGUAGES = ['english', 'indonesian']

# Sort options
SORT_OPTIONS = [
    'bestmatch',
    'title',
    'author', 
    'year',
    'rating',
    'downloads',
    'date'
]

# Web interface settings
FLASK_HOST = '0.0.0.0'
FLASK_PORT = 5000
FLASK_DEBUG = True

# Logging settings
LOG_LEVEL = 'INFO'
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOG_FILE = f"{EBOOK_FOLDER}/{LOGS_FOLDER}/scraper.log"

# Database settings (for future use)
DATABASE_URL = 'sqlite:///zlibrary.db'

# Cache settings
CACHE_ENABLED = True
CACHE_TIMEOUT = 3600  # 1 hour

# Error handling
MAX_CONSECUTIVE_ERRORS = 5
ERROR_COOLDOWN = 300  # 5 minutes

# Validation settings
MIN_FILE_SIZE = 1000  # 1KB
MAX_FILE_SIZE = 500 * 1024 * 1024  # 500MB
VALID_EXTENSIONS = ['pdf', 'epub', 'mobi', 'azw3', 'txt', 'doc', 'docx']

# Rate limiting
RATE_LIMIT_REQUESTS = 100
RATE_LIMIT_WINDOW = 3600  # 1 hour

# Backup settings
BACKUP_ENABLED = True
BACKUP_INTERVAL = 24  # hours
MAX_BACKUP_FILES = 10