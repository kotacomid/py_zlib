#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script untuk mendownload semua cover dari file CSV hasil scraping Z-Library
Dengan tracking status di CSV metadata
"""

import pandas as pd
from zlibrary_scraper import ZLibraryScraper
import sys
import os
import requests
from datetime import datetime
from config import *

def download_covers_with_tracking():
    """Download covers dengan tracking status di CSV"""
    print("Download Cover Buku Z-Library")
    print("="*50)
    
    # Baca metadata CSV
    csv_file = OUTPUT_FILES['csv']
    if not os.path.exists(csv_file):
        print(f"File {csv_file} tidak ditemukan.")
        print(f"Pastikan file CSV ada di: {csv_file}")
        print("Jalankan 'python zlibrary_scraper.py' terlebih dahulu untuk mengumpulkan metadata.")
        return
    
    df = pd.read_csv(csv_file)
    scraper = ZLibraryScraper()
    
    # Filter buku yang belum di-download cover
    pending_covers = df[df['cover_downloaded'] != 'YES']
    
    if len(pending_covers) == 0:
        print("Semua cover sudah di-download!")
        return
    
    print(f"Total {len(pending_covers)} cover yang perlu di-download")
    
    # Setup log file
    log_file = OUTPUT_FILES['cover_log']
    covers_dir = f"{EBOOK_FOLDER}/{COVERS_FOLDER}"
    
    success_count = 0
    failed_count = 0
    
    with open(log_file, "a", encoding="utf-8") as log:
        log.write(f"\n=== COVER DOWNLOAD SESSION {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===\n")
        
        for idx, row in pending_covers.iterrows():
            book_id = row.get('id', '')
            cover_url = row.get('cover_url', '')
            title = row.get('title', 'Unknown')
            
            if not cover_url:
                log.write(f"{book_id}: NO COVER URL - {title}\n")
                scraper.update_download_status(book_id, 'cover', 'NO_URL')
                failed_count += 1
                continue
            
            # Generate filename based on title and author
            title = row.get('title', 'Unknown')
            author = row.get('author', 'Unknown')
            
            # Use config function to generate proper filename
            from config import get_file_path
            filepath = get_file_path(title, author, "jpg", "covers")
            filename = os.path.basename(filepath)
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            # Skip if file already exists
            if os.path.exists(filepath):
                print(f"✓ Cover sudah ada: {filename}")
                scraper.update_download_status(book_id, 'cover', 'YES')
                success_count += 1
                log.write(f"{filename}: ALREADY EXISTS\n")
                continue
            
            try:
                print(f"Downloading: {filename} - {title}")
                resp = requests.get(cover_url, timeout=COVER_TIMEOUT)
                
                if resp.status_code == 200:
                    with open(filepath, "wb") as f:
                        f.write(resp.content)
                    
                    print(f"✓ Downloaded: {filename}")
                    scraper.update_download_status(book_id, 'cover', 'YES')
                    log.write(f"{filename}: SUCCESS - {title}\n")
                    success_count += 1
                else:
                    print(f"✗ Failed: {filename} ({resp.status_code})")
                    scraper.update_download_status(book_id, 'cover', 'FAILED')
                    log.write(f"{filename}: FAIL ({resp.status_code}) - {title}\n")
                    failed_count += 1
                    
            except Exception as e:
                print(f"✗ Error downloading {filename}: {e}")
                scraper.update_download_status(book_id, 'cover', 'ERROR')
                log.write(f"{filename}: ERROR {e} - {title}\n")
                failed_count += 1
    
    # Summary
    print(f"\nCover Download Summary:")
    print(f"✓ Success: {success_count}")
    print(f"✗ Failed: {failed_count}")
    print(f"📁 Covers disimpan di: {covers_dir}")
    print(f"📝 Log tersimpan di: {log_file}")
    
    # Update CSV dengan status terbaru
    updated_df = pd.read_csv(csv_file)
    cover_stats = updated_df['cover_downloaded'].value_counts()
    print(f"\nStatus Cover di CSV:")
    for status, count in cover_stats.items():
        print(f"  {status}: {count}")

def main():
    """Fungsi utama"""
    download_covers_with_tracking()

if __name__ == "__main__":
    main() 