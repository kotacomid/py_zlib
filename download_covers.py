#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Enhanced Cover Downloader for Z-Library
Script untuk mendownload semua cover dari file CSV hasil scraping Z-Library
Dengan tracking status di CSV metadata dan file naming yang konsisten
"""

import pandas as pd
import sys
import os
import requests
import re
from datetime import datetime
import logging
from config import *
from zlibrary_scraper import EnhancedZLibraryScraper

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

class CoverDownloader:
    def __init__(self):
        self.scraper = EnhancedZLibraryScraper()
        self.covers_dir = f"{EBOOK_FOLDER}/{COVERS_FOLDER}"
        self.csv_file = OUTPUT_FILES['csv']
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        
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
    
    def get_cover_extension(self, url):
        """Get file extension from cover URL"""
        if not url:
            return '.jpg'
        
        # Try to extract extension from URL
        ext = os.path.splitext(url.split('/')[-1])[1]
        if ext and len(ext) <= 5 and ext.lower() in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
            return ext.lower()
        
        return '.jpg'
    
    def download_covers_with_tracking(self, max_retries=3):
        """Download covers dengan tracking status di CSV"""
        print("Enhanced Cover Downloader for Z-Library")
        print("="*50)
        
        # Check if CSV exists
        if not os.path.exists(self.csv_file):
            print(f"File {self.csv_file} tidak ditemukan.")
            print("Jalankan 'python zlibrary_scraper.py' terlebih dahulu untuk mengumpulkan metadata.")
            return
        
        # Load metadata
        df = pd.read_csv(self.csv_file)
        
        # Filter buku yang belum di-download cover
        pending_covers = df[df['cover_downloaded'] != 'YES']
        
        if len(pending_covers) == 0:
            print("✓ Semua cover sudah di-download!")
            return
        
        print(f"Total {len(pending_covers)} cover yang perlu di-download")
        
        # Setup log file
        log_file = f"{EBOOK_FOLDER}/{LOGS_FOLDER}/cover_download.log"
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        
        success_count = 0
        failed_count = 0
        skipped_count = 0
        
        with open(log_file, "a", encoding="utf-8") as log:
            log.write(f"\n=== COVER DOWNLOAD SESSION {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===\n")
            
            for idx, row in pending_covers.iterrows():
                book_id = row.get('id', '')
                cover_url = row.get('cover_url', '')
                title = row.get('title', 'Unknown')
                author = row.get('author', 'Unknown')
                
                if not cover_url:
                    print(f"✗ No cover URL for: {title} - {author}")
                    self.update_cover_status(book_id, 'NO_URL', '')
                    log.write(f"{book_id}: NO COVER URL - {title} - {author}\n")
                    failed_count += 1
                    continue
                
                # Create filename
                base_filename = self.sanitize_filename(title, author)
                ext = self.get_cover_extension(cover_url)
                filename = f"{base_filename}{ext}"
                filepath = os.path.join(self.covers_dir, filename)
                
                # Skip if file already exists
                if os.path.exists(filepath):
                    print(f"✓ Cover sudah ada: {filename}")
                    self.update_cover_status(book_id, 'YES', filepath)
                    log.write(f"{filename}: ALREADY EXISTS\n")
                    success_count += 1
                    continue
                
                # Download with retries
                success = False
                for attempt in range(max_retries):
                    try:
                        print(f"Downloading ({attempt + 1}/{max_retries}): {filename}")
                        resp = self.session.get(cover_url, timeout=COVER_DOWNLOAD_TIMEOUT)
                        
                        if resp.status_code == 200 and len(resp.content) > 1000:  # Minimum size check
                            # Ensure directory exists
                            os.makedirs(os.path.dirname(filepath), exist_ok=True)
                            
                            with open(filepath, "wb") as f:
                                f.write(resp.content)
                            
                            print(f"✓ Downloaded: {filename}")
                            self.update_cover_status(book_id, 'YES', filepath)
                            log.write(f"{filename}: SUCCESS - {title} - {author}\n")
                            success_count += 1
                            success = True
                            break
                        else:
                            print(f"✗ Failed: {filename} (Status: {resp.status_code}, Size: {len(resp.content)})")
                            
                    except requests.exceptions.Timeout:
                        print(f"✗ Timeout downloading {filename} (attempt {attempt + 1})")
                        if attempt == max_retries - 1:
                            self.update_cover_status(book_id, 'TIMEOUT', '')
                            log.write(f"{filename}: TIMEOUT - {title} - {author}\n")
                            failed_count += 1
                    except Exception as e:
                        print(f"✗ Error downloading {filename}: {e}")
                        if attempt == max_retries - 1:
                            self.update_cover_status(book_id, 'ERROR', str(e))
                            log.write(f"{filename}: ERROR {e} - {title} - {author}\n")
                            failed_count += 1
                
                if not success:
                    print(f"✗ Failed after {max_retries} attempts: {filename}")
        
        # Summary
        print(f"\nCover Download Summary:")
        print(f"✓ Success: {success_count}")
        print(f"✗ Failed: {failed_count}")
        print(f"⏭ Skipped: {skipped_count}")
        print(f"📁 Covers disimpan di: {self.covers_dir}")
        print(f"📝 Log tersimpan di: {log_file}")
        
        # Update CSV dengan status terbaru
        self.print_cover_stats()
    
    def update_cover_status(self, book_id, status, file_path):
        """Update cover download status in CSV"""
        try:
            df = pd.read_csv(self.csv_file)
            mask = df['id'] == book_id
            
            if mask.any():
                df.loc[mask, 'cover_downloaded'] = status
                if file_path:
                    df.loc[mask, 'cover_path'] = file_path
                df.to_csv(self.csv_file, index=False, encoding='utf-8')
                return True
            else:
                logger.warning(f"Book ID {book_id} not found in CSV")
                return False
                
        except Exception as e:
            logger.error(f"Error updating cover status: {e}")
            return False
    
    def print_cover_stats(self):
        """Print cover download statistics"""
        try:
            df = pd.read_csv(self.csv_file)
            cover_stats = df['cover_downloaded'].value_counts()
            
            print(f"\nStatus Cover di CSV:")
            for status, count in cover_stats.items():
                print(f"  {status}: {count}")
                
        except Exception as e:
            logger.error(f"Error printing cover stats: {e}")
    
    def download_specific_cover(self, book_id):
        """Download cover for specific book ID"""
        try:
            df = pd.read_csv(self.csv_file)
            book_data = df[df['id'] == book_id]
            
            if book_data.empty:
                print(f"Book ID {book_id} not found")
                return False
            
            row = book_data.iloc[0]
            cover_url = row.get('cover_url', '')
            title = row.get('title', 'Unknown')
            author = row.get('author', 'Unknown')
            
            if not cover_url:
                print(f"No cover URL for book: {title} - {author}")
                return False
            
            # Create filename
            base_filename = self.sanitize_filename(title, author)
            ext = self.get_cover_extension(cover_url)
            filename = f"{base_filename}{ext}"
            filepath = os.path.join(self.covers_dir, filename)
            
            print(f"Downloading cover for: {title} - {author}")
            resp = self.session.get(cover_url, timeout=COVER_DOWNLOAD_TIMEOUT)
            
            if resp.status_code == 200:
                os.makedirs(os.path.dirname(filepath), exist_ok=True)
                with open(filepath, "wb") as f:
                    f.write(resp.content)
                
                self.update_cover_status(book_id, 'YES', filepath)
                print(f"✓ Cover downloaded: {filename}")
                return True
            else:
                print(f"✗ Failed to download cover (Status: {resp.status_code})")
                return False
                
        except Exception as e:
            print(f"✗ Error downloading cover: {e}")
            return False

def main():
    """Main function"""
    import sys
    
    downloader = CoverDownloader()
    
    if len(sys.argv) > 1:
        if sys.argv[1] == 'specific' and len(sys.argv) > 2:
            # Download specific cover
            book_id = sys.argv[2]
            downloader.download_specific_cover(book_id)
        elif sys.argv[1] == 'stats':
            # Show statistics only
            downloader.print_cover_stats()
        else:
            print("Usage:")
            print("  python download_covers.py                    # Download all pending covers")
            print("  python download_covers.py specific <book_id> # Download specific cover")
            print("  python download_covers.py stats              # Show statistics only")
    else:
        # Download all pending covers
        downloader.download_covers_with_tracking()

if __name__ == "__main__":
    main() 