#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script untuk mendownload file ebook dari Z-Library
Dengan multi-account rotation dan tracking status di CSV metadata
"""

import pandas as pd
import requests
import os
import time
from datetime import datetime
from zlib_login import ZLibraryLogin
from zlibrary_scraper import ZLibraryScraper
from config import *

class FileDownloader:
    def __init__(self):
        self.login_manager = ZLibraryLogin()
        self.scraper = ZLibraryScraper()
        self.current_account_index = 0
        self.download_count = 0
        self.failure_count = 0
        
    def get_available_session(self):
        """Dapatkan session yang tersedia untuk download"""
        session, account_index = self.login_manager.get_available_session()
        if session:
            self.current_account_index = account_index
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
            session = self.login_manager.login_account(self.current_account_index)
            if session:
                print(f"✓ Switched ke akun: {ZLIBRARY_ACCOUNTS[self.current_account_index]['email']}")
                return session
        
        print("✗ Tidak ada akun yang tersedia")
        return None
    
    def download_file(self, session, book_id, download_url, title, extension):
        """Download file ebook dengan session yang diberikan"""
        if not download_url:
            return False, "NO_DOWNLOAD_URL"
        
        # Determine filename
        filename = f"{book_id}.{extension}"
        filepath = os.path.join(f"{EBOOK_FOLDER}/{FILES_FOLDER}", filename)
        
        # Skip if file already exists
        if os.path.exists(filepath):
            return True, "ALREADY_EXISTS"
        
        try:
            print(f"Downloading: {filename} - {title}")
            
            # Download file
            response = session.get(download_url, timeout=60, stream=True)
            
            if response.status_code == 200:
                # Check if it's actually a file (not HTML error page)
                content_type = response.headers.get('content-type', '')
                if 'text/html' in content_type and len(response.content) < 10000:
                    return False, "HTML_ERROR_PAGE"
                
                # Save file
                with open(filepath, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                
                # Verify file size
                file_size = os.path.getsize(filepath)
                if file_size < 1000:  # File terlalu kecil, kemungkinan error
                    os.remove(filepath)
                    return False, "FILE_TOO_SMALL"
                
                print(f"✓ Downloaded: {filename} ({file_size:,} bytes)")
                return True, "SUCCESS"
                
            else:
                return False, f"HTTP_{response.status_code}"
                
        except Exception as e:
            return False, f"ERROR_{str(e)}"
    
    def download_files_with_rotation(self):
        """Download files dengan account rotation"""
        print("Download File Ebook Z-Library")
        print("="*50)
        
        # Baca metadata CSV
        csv_file = OUTPUT_FILES['csv']
        if not os.path.exists(csv_file):
            print(f"File {csv_file} tidak ditemukan.")
            print("Jalankan 'python zlibrary_scraper.py' terlebih dahulu untuk mengumpulkan metadata.")
            return
        
        df = pd.read_csv(csv_file)
        
        # Filter buku yang belum di-download file
        pending_files = df[df['file_downloaded'] != 'YES']
        
        if len(pending_files) == 0:
            print("Semua file sudah di-download!")
            return
        
        print(f"Total {len(pending_files)} file yang perlu di-download")
        
        # Setup log file
        log_file = OUTPUT_FILES['file_log']
        
        success_count = 0
        failed_count = 0
        
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
                extension = row.get('extension', 'pdf')
                
                # Check if we need to rotate account
                if (self.download_count >= ROTATE_AFTER_DOWNLOADS or 
                    self.failure_count >= ROTATE_AFTER_FAILURES):
                    session = self.rotate_account()
                    if not session:
                        print("Tidak ada akun yang tersedia, berhenti download")
                        break
                
                # Download file
                success, status = self.download_file(session, book_id, download_url, title, extension)
                
                if success:
                    # Update CSV status
                    account_email = ZLIBRARY_ACCOUNTS[self.current_account_index]['email']
                    self.scraper.update_download_status(book_id, 'file', 'YES', account_email)
                    
                    # Increment counters
                    self.download_count += 1
                    self.login_manager.increment_download_count(self.current_account_index)
                    
                    log.write(f"{book_id}.{extension}: SUCCESS - {title} ({account_email})\n")
                    success_count += 1
                    
                else:
                    # Update CSV status
                    self.scraper.update_download_status(book_id, 'file', 'FAILED')
                    
                    # Increment failure counter
                    self.failure_count += 1
                    
                    log.write(f"{book_id}.{extension}: FAILED ({status}) - {title}\n")
                    failed_count += 1
                
                # Delay between downloads
                time.sleep(DELAY_BETWEEN_REQUESTS)
        
        # Summary
        print(f"\nFile Download Summary:")
        print(f"✓ Success: {success_count}")
        print(f"✗ Failed: {failed_count}")
        print(f"📁 Files disimpan di: {EBOOK_FOLDER}/{FILES_FOLDER}")
        print(f"📝 Log tersimpan di: {log_file}")
        
        # Show account status
        self.login_manager.print_account_status()
        
        # Update CSV dengan status terbaru
        updated_df = pd.read_csv(csv_file)
        file_stats = updated_df['file_downloaded'].value_counts()
        print(f"\nStatus File di CSV:")
        for status, count in file_stats.items():
            print(f"  {status}: {count}")

def main():
    """Fungsi utama"""
    downloader = FileDownloader()
    downloader.download_files_with_rotation()

if __name__ == "__main__":
    main() 