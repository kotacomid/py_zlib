#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Enhanced File Downloader for Z-Library
Script untuk mendownload file ebook dari Z-Library
Dengan multi-account rotation dan tracking status di CSV metadata
"""

import pandas as pd
import requests
import os
import time
import re
from datetime import datetime
import logging
from selenium_login import SeleniumZLibraryLogin
from zlibrary_scraper import EnhancedZLibraryScraper
from config import *

# Setup logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format=LOG_FORMAT,
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class EnhancedFileDownloader:
    def __init__(self):
        self.login_manager = SeleniumZLibraryLogin()
        self.scraper = EnhancedZLibraryScraper()
        self.current_account_index = 0
        self.download_count = 0
        self.failure_count = 0
        self.csv_file = OUTPUT_FILES['csv']
        self.files_dir = f"{EBOOK_FOLDER}/{FILES_FOLDER}"
        
    def sanitize_filename(self, title, author):
        """Create sanitized filename from title and author"""
        # Combine title and author
        filename = f"{title} - {author}"
        
        # Remove invalid characters
        filename = re.sub(r'[<>:"/\\|?*]', '', filename)
        
        # Replace multiple spaces with single space
        filename = re.sub(r'\s+', ' ', filename)
        
        # Trim to max length
        if len(filename) > MAX_FILENAME_LENGTH:
            filename = filename[:MAX_FILENAME_LENGTH].rsplit(' ', 1)[0]
        
        return filename.strip()
    
    def get_available_session(self):
        """Dapatkan session yang tersedia untuk download"""
        # Try current account first
        session = self.login_manager.get_authenticated_session(self.current_account_index, headless=True)
        if session:
            return session
        
        # Try other accounts
        for i in range(len(ZLIBRARY_ACCOUNTS)):
            if i != self.current_account_index:
                session = self.login_manager.get_authenticated_session(i, headless=True)
                if session:
                    self.current_account_index = i
                    return session
        
        return None
    
    def rotate_account(self):
        """Rotate ke akun berikutnya"""
        print(f"Rotating account setelah {self.download_count} downloads, {self.failure_count} failures")
        self.download_count = 0
        self.failure_count = 0
        
        # Coba rotate ke akun berikutnya
        for _ in range(len(ZLIBRARY_ACCOUNTS)):
            self.current_account_index = (self.current_account_index + 1) % len(ZLIBRARY_ACCOUNTS)
            session = self.login_manager.get_authenticated_session(self.current_account_index, headless=True)
            if session:
                account_email = ZLIBRARY_ACCOUNTS[self.current_account_index]['email']
                print(f"✓ Switched ke akun: {account_email}")
                return session
        
        print("✗ Tidak ada akun yang tersedia")
        return None
    
    def download_file(self, session, book_id, download_url, title, author, extension):
        """Download file ebook dengan session yang diberikan"""
        if not download_url:
            return False, "NO_DOWNLOAD_URL"
        
        # Create filename
        base_filename = self.sanitize_filename(title, author)
        filename = f"{base_filename}.{extension}"
        filepath = os.path.join(self.files_dir, filename)
        
        # Skip if file already exists
        if os.path.exists(filepath):
            return True, "ALREADY_EXISTS"
        
        try:
            print(f"Downloading: {filename}")
            
            # Download file
            response = session.get(download_url, timeout=DOWNLOAD_TIMEOUT, stream=True)
            
            if response.status_code == 200:
                # Check if it's actually a file (not HTML error page)
                content_type = response.headers.get('content-type', '')
                content_length = response.headers.get('content-length', 0)
                
                if 'text/html' in content_type and int(content_length) < 10000:
                    return False, "HTML_ERROR_PAGE"
                
                # Ensure directory exists
                os.makedirs(os.path.dirname(filepath), exist_ok=True)
                
                # Save file
                with open(filepath, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                
                # Verify file size
                file_size = os.path.getsize(filepath)
                if file_size < MIN_FILE_SIZE:
                    os.remove(filepath)
                    return False, "FILE_TOO_SMALL"
                
                if file_size > MAX_FILE_SIZE:
                    os.remove(filepath)
                    return False, "FILE_TOO_LARGE"
                
                print(f"✓ Downloaded: {filename} ({file_size:,} bytes)")
                return True, "SUCCESS"
                
            else:
                return False, f"HTTP_{response.status_code}"
                
        except requests.exceptions.Timeout:
            return False, "TIMEOUT"
        except Exception as e:
            return False, f"ERROR_{str(e)}"
    
    def download_files_with_rotation(self, max_retries=3):
        """Download files dengan account rotation"""
        print("Enhanced File Downloader for Z-Library")
        print("="*50)
        
        # Check if CSV exists
        if not os.path.exists(self.csv_file):
            print(f"File {self.csv_file} tidak ditemukan.")
            print("Jalankan 'python zlibrary_scraper.py' terlebih dahulu untuk mengumpulkan metadata.")
            return
        
        df = pd.read_csv(self.csv_file)
        
        # Filter buku yang belum di-download file
        pending_files = df[df['file_downloaded'] != 'YES']
        
        if len(pending_files) == 0:
            print("✓ Semua file sudah di-download!")
            return
        
        print(f"Total {len(pending_files)} file yang perlu di-download")
        
        # Setup log file
        log_file = f"{EBOOK_FOLDER}/{LOGS_FOLDER}/file_download.log"
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        
        success_count = 0
        failed_count = 0
        skipped_count = 0
        
        # Get initial session
        session = self.get_available_session()
        if not session:
            print("Tidak ada akun yang tersedia untuk download")
            return
        
        with open(log_file, "a", encoding="utf-8") as log:
            log.write(f"\n=== FILE DOWNLOAD SESSION {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===\n")
            
            for idx, row in pending_files.iterrows():
                book_id = row.get('id', '')
                download_url = row.get('download_url', '')
                title = row.get('title', 'Unknown')
                author = row.get('author', 'Unknown')
                extension = row.get('extension', 'pdf')
                
                # Check if we need to rotate account
                if (self.download_count >= ROTATION_INTERVAL or 
                    self.failure_count >= MAX_CONSECUTIVE_ERRORS):
                    session = self.rotate_account()
                    if not session:
                        print("Tidak ada akun yang tersedia, berhenti download")
                        break
                
                # Download file with retries
                success = False
                for attempt in range(max_retries):
                    success, status = self.download_file(session, book_id, download_url, title, author, extension)
                    
                    if success:
                        break
                    elif attempt < max_retries - 1:
                        print(f"Retrying download ({attempt + 2}/{max_retries})...")
                        time.sleep(RETRY_DELAY)
                
                if success:
                    # Update CSV status
                    account_email = ZLIBRARY_ACCOUNTS[self.current_account_index]['email']
                    self.update_file_status(book_id, 'YES', account_email)
                    
                    # Increment counters
                    self.download_count += 1
                    
                    log.write(f"{book_id}: SUCCESS - {title} - {author} ({account_email})\n")
                    success_count += 1
                    
                else:
                    # Update CSV status
                    self.update_file_status(book_id, 'FAILED', '', status)
                    
                    # Increment failure counter
                    self.failure_count += 1
                    
                    log.write(f"{book_id}: FAILED ({status}) - {title} - {author}\n")
                    failed_count += 1
                
                # Delay between downloads
                time.sleep(DELAY_BETWEEN_REQUESTS)
        
        # Summary
        print(f"\nFile Download Summary:")
        print(f"✓ Success: {success_count}")
        print(f"✗ Failed: {failed_count}")
        print(f"⏭ Skipped: {skipped_count}")
        print(f"📁 Files disimpan di: {self.files_dir}")
        print(f"📝 Log tersimpan di: {log_file}")
        
        # Show account status
        self.print_account_status()
        
        # Update CSV dengan status terbaru
        self.print_file_stats()
    
    def update_file_status(self, book_id, status, account_email="", error_msg=""):
        """Update file download status in CSV"""
        try:
            df = pd.read_csv(self.csv_file)
            mask = df['id'] == book_id
            
            if mask.any():
                df.loc[mask, 'file_downloaded'] = status
                if account_email:
                    df.loc[mask, 'download_account'] = account_email
                if error_msg:
                    df.loc[mask, 'download_error'] = error_msg
                df.to_csv(self.csv_file, index=False, encoding='utf-8')
                return True
            else:
                logger.warning(f"Book ID {book_id} not found in CSV")
                return False
                
        except Exception as e:
            logger.error(f"Error updating file status: {e}")
            return False
    
    def print_account_status(self):
        """Print account status"""
        print(f"\nAccount Status:")
        for i, account in enumerate(ZLIBRARY_ACCOUNTS):
            status = "✓" if account['daily_downloads'] < account['max_daily_downloads'] else "✗"
            print(f"{status} {account['email']} - {account['daily_downloads']}/{account['max_daily_downloads']} downloads")
    
    def print_file_stats(self):
        """Print file download statistics"""
        try:
            df = pd.read_csv(self.csv_file)
            file_stats = df['file_downloaded'].value_counts()
            
            print(f"\nStatus File di CSV:")
            for status, count in file_stats.items():
                print(f"  {status}: {count}")
                
        except Exception as e:
            logger.error(f"Error printing file stats: {e}")
    
    def download_specific_file(self, book_id):
        """Download file for specific book ID"""
        try:
            df = pd.read_csv(self.csv_file)
            book_data = df[df['id'] == book_id]
            
            if book_data.empty:
                print(f"Book ID {book_id} not found")
                return False
            
            row = book_data.iloc[0]
            download_url = row.get('download_url', '')
            title = row.get('title', 'Unknown')
            author = row.get('author', 'Unknown')
            extension = row.get('extension', 'pdf')
            
            if not download_url:
                print(f"No download URL for book: {title} - {author}")
                return False
            
            # Get session
            session = self.get_available_session()
            if not session:
                print("No available account for download")
                return False
            
            # Download file
            success, status = self.download_file(session, book_id, download_url, title, author, extension)
            
            if success:
                account_email = ZLIBRARY_ACCOUNTS[self.current_account_index]['email']
                self.update_file_status(book_id, 'YES', account_email)
                print(f"✓ File downloaded successfully")
                return True
            else:
                self.update_file_status(book_id, 'FAILED', '', status)
                print(f"✗ Failed to download file: {status}")
                return False
                
        except Exception as e:
            print(f"✗ Error downloading file: {e}")
            return False

def main():
    """Main function"""
    import sys
    
    downloader = EnhancedFileDownloader()
    
    if len(sys.argv) > 1:
        if sys.argv[1] == 'specific' and len(sys.argv) > 2:
            # Download specific file
            book_id = sys.argv[2]
            downloader.download_specific_file(book_id)
        elif sys.argv[1] == 'stats':
            # Show statistics only
            downloader.print_file_stats()
        else:
            print("Usage:")
            print("  python download_files.py                    # Download all pending files")
            print("  python download_files.py specific <book_id> # Download specific file")
            print("  python download_files.py stats              # Show statistics only")
    else:
        # Download all pending files
        downloader.download_files_with_rotation()

if __name__ == "__main__":
    main() 