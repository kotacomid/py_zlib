#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Enhanced Z-Library Scraper
Script untuk melakukan parsing data buku dari Z-Library dengan fitur interaktif dan web mode
Fokus pada pengumpulan metadata dengan penghapusan duplikat
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import json
from datetime import datetime
import os
import re
import logging
import threading
from selenium_login import SeleniumZLibraryLogin
from config import *
from bs4.element import Tag

# Optional Flask import for web mode
try:
    from flask import Flask, render_template, request, jsonify, redirect, url_for
    FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False
    print("Flask not available. Web mode disabled.")

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

class EnhancedZLibraryScraper:
    def __init__(self):
        self.base_url = BASE_URL
        self.headers = HEADERS
        self.session = None
        self.login_manager = SeleniumZLibraryLogin()
        self._create_folders()
        self.scraping_status = {
            'is_running': False,
            'current_page': 0,
            'total_pages': 0,
            'books_found': 0,
            'errors': 0
        }
        
    def _create_folders(self):
        """Buat folder struktur yang diperlukan"""
        folders = [
            EBOOK_FOLDER,
            f"{EBOOK_FOLDER}/{COVERS_FOLDER}",
            f"{EBOOK_FOLDER}/{FILES_FOLDER}",
            f"{EBOOK_FOLDER}/{LOGS_FOLDER}",
            f"{EBOOK_FOLDER}/{ANALYSIS_FOLDER}"
        ]
        for folder in folders:
            os.makedirs(folder, exist_ok=True)
    
    def authenticate_session(self, account_index=0):
        """Authenticate session using Selenium login"""
        try:
            self.session = self.login_manager.get_authenticated_session(account_index, headless=True)
            if self.session:
                logger.info(f"✓ Authenticated with account {account_index}")
                return True
            else:
                logger.error(f"✗ Authentication failed for account {account_index}")
                return False
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return False
    
    def scrape_with_filters(self, search_query="gramedia", max_pages=10, 
                           year_from=None, year_to=None, language=None, 
                           sort_by="bestmatch", use_auth=True):
        """
        Scrape buku dengan filter yang dapat dikustomisasi
        """
        all_books = []
        self.scraping_status['is_running'] = True
        self.scraping_status['total_pages'] = max_pages
        self.scraping_status['current_page'] = 0
        self.scraping_status['books_found'] = 0
        self.scraping_status['errors'] = 0
        
        print("Memulai scraping metadata dengan filter...")
        print("="*50)
        print(f"Query: {search_query}")
        print(f"Max pages: {max_pages}")
        print(f"Year range: {year_from} - {year_to}")
        print(f"Language: {language}")
        print(f"Sort by: {sort_by}")
        print(f"Authentication: {'Yes' if use_auth else 'No'}")
        print("="*50)
        
        # Authenticate if needed
        if use_auth:
            if not self.authenticate_session():
                print("✗ Authentication failed, continuing without auth")
                self.session = requests.Session()
                self.session.headers.update(self.headers)
        else:
            self.session = requests.Session()
            self.session.headers.update(self.headers)
        
        # Build search URL with filters
        search_url = f"{SEARCH_URL}?q={search_query}"
        if year_from:
            search_url += f"&yearFrom={year_from}"
        if year_to:
            search_url += f"&yearTo={year_to}"
        if language:
            search_url += f"&language={language}"
        if sort_by:
            search_url += f"&order={sort_by}"
        
        for page in range(1, max_pages + 1):
            try:
                self.scraping_status['current_page'] = page
                
                # URL dengan parameter halaman
                url = f"{self.base_url}{search_url}&page={page}"
                print(f"Mengambil halaman {page}...")
                
                response = self.session.get(url, timeout=REQUEST_TIMEOUT)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.content, 'lxml')
                book_cards = soup.find_all("z-bookcard")
                
                if not book_cards:
                    print(f"Tidak ada data buku di halaman {page}")
                    continue
                
                print(f"Menemukan {len(book_cards)} buku di halaman {page}")
                
                for card in book_cards:
                    book_info = self._extract_book_info(card, page)
                    all_books.append(book_info)
                    self.scraping_status['books_found'] += 1
                
                time.sleep(DELAY_BETWEEN_REQUESTS)
                
            except requests.exceptions.RequestException as e:
                print(f"Error saat mengambil halaman {page}: {e}")
                self.scraping_status['errors'] += 1
                time.sleep(RETRY_DELAY)
            except Exception as e:
                print(f"Error tidak terduga di halaman {page}: {e}")
                self.scraping_status['errors'] += 1
                time.sleep(RETRY_DELAY)
        
        self.scraping_status['is_running'] = False
        print(f"\nScraping selesai! Total {len(all_books)} buku dari {max_pages} halaman")
        
        # Remove duplicates and save
        df = pd.DataFrame(all_books)
        df = self.remove_duplicates(df)
        self.save_metadata(df)
        
        return df
    
    def remove_duplicates(self, df):
        """Remove duplicate books based on title and author"""
        print("Menghapus data duplikat...")
        initial_count = len(df)
        
        # Create a unique identifier combining title and author
        df['unique_id'] = df['title'].str.lower().str.strip() + '|' + df['author'].str.lower().str.strip()
        
        # Remove duplicates based on unique_id
        df = df.drop_duplicates(subset=['unique_id'], keep='first')
        
        # Remove the temporary column
        df = df.drop('unique_id', axis=1)
        
        final_count = len(df)
        removed_count = initial_count - final_count
        
        print(f"Duplikat dihapus: {removed_count} buku")
        print(f"Sisa buku unik: {final_count}")
        
        return df
    
    def _extract_book_info(self, card, page):
        """
        Ekstrak informasi buku dari z-bookcard dengan tracking fields
        """
        return {
            "page": page,
            "id": card.get("id", ""),
            "isbn": card.get("isbn", ""),
            "title": self._get_text_content(card, "title"),
            "author": self._get_text_content(card, "author"),
            "publisher": card.get("publisher", ""),
            "language": card.get("language", ""),
            "year": card.get("year", ""),
            "extension": card.get("extension", ""),
            "filesize": card.get("filesize", ""),
            "rating": card.get("rating", ""),
            "quality": card.get("quality", ""),
            "cover_url": self._get_cover_url(card),
            "download_url": self._get_download_url(card),
            "book_url": self._get_book_url(card),
            "scraped_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "cover_downloaded": "NO",
            "file_downloaded": "NO",
            "download_status": "PENDING",
            "download_account": "",
            "cover_path": "",
            "file_path": "",
            "download_error": ""
        }
    
    def _get_text_content(self, card, slot_name):
        """Ambil teks dari slot tertentu"""
        element = card.find("div", {"slot": slot_name})
        return element.text.strip() if element else ""
    
    def _get_cover_url(self, card):
        """Ambil URL cover buku dan ubah ke s3proxy.cdn-zlib.sk/covers10000"""
        img = card.find("img")
        url = ""
        if img and img.get("data-src"):
            url = img["data-src"]
        elif img and img.get("src"):
            url = img["src"]
        if url:
            # Ganti domain ke covers10000
            m = re.search(r"/(covers100|covers10000)/(.+)$", url)
            if m:
                return f"https://s3proxy.cdn-zlib.sk/covers10000/{m.group(2)}"
        return ""
    
    def _get_download_url(self, card):
        """Ambil URL download"""
        download_path = card.get("download", "")
        if download_path:
            return f"{self.base_url}{download_path}"
        return ""
    
    def _get_book_url(self, card):
        """Ambil URL detail buku"""
        href = card.get("href", "")
        if href:
            return f"{self.base_url}{href}"
        return ""
    
    def save_metadata(self, df, filename=None):
        """Simpan metadata ke CSV dan JSON"""
        if filename is None:
            csv_filename = OUTPUT_FILES['csv']
            json_filename = OUTPUT_FILES['json']
        else:
            csv_filename = f"{EBOOK_FOLDER}/{filename}.csv"
            json_filename = f"{EBOOK_FOLDER}/{filename}.json"
        
        try:
            # Save to CSV
            df.to_csv(csv_filename, index=False, encoding='utf-8')
            print(f"Metadata disimpan ke {csv_filename}")
            
            # Save to JSON
            df.to_json(json_filename, orient='records', indent=2, force_ascii=False)
            print(f"Metadata disimpan ke {json_filename}")
            
            return True
        except Exception as e:
            print(f"✗ Error menyimpan metadata: {e}")
            return False
    
    def load_existing_metadata(self):
        """Load existing metadata from CSV"""
        csv_file = OUTPUT_FILES['csv']
        if os.path.exists(csv_file):
            try:
                df = pd.read_csv(csv_file)
                print(f"Loaded {len(df)} existing records from {csv_file}")
                return df
            except Exception as e:
                print(f"Error loading existing metadata: {e}")
        return pd.DataFrame()
    
    def merge_with_existing(self, new_df):
        """Merge new data with existing data"""
        existing_df = self.load_existing_metadata()
        if existing_df.empty:
            return new_df
        
        # Combine dataframes
        combined_df = pd.concat([existing_df, new_df], ignore_index=True)
        
        # Remove duplicates
        combined_df = self.remove_duplicates(combined_df)
        
        return combined_df
    
    def print_summary(self, df):
        """Tampilkan ringkasan metadata"""
        print("\n" + "="*50)
        print("RINGKASAN METADATA BUKU Z-LIBRARY")
        print("="*50)
        print(f"Total buku: {len(df)}")
        print(f"Total halaman: {df['page'].nunique()}")
        print(f"Penerbit unik: {df['publisher'].nunique()}")
        print(f"Bahasa unik: {df['language'].nunique()}")
        print(f"Ekstensi file: {df['extension'].value_counts().to_dict()}")
        
        if 'rating' in df.columns and df['rating'].notna().any():
            try:
                ratings = []
                for rating_str in df['rating']:
                    if pd.notna(rating_str) and str(rating_str).strip():
                        try:
                            rating_val = float(str(rating_str))
                            ratings.append(rating_val)
                        except (ValueError, TypeError):
                            continue
                
                if ratings:
                    avg_rating = sum(ratings) / len(ratings)
                    print(f"Rating rata-rata: {avg_rating:.2f}")
            except Exception:
                print("Rating rata-rata: tidak dapat dihitung")
        
        print("\nTop 5 Penerbit:")
        print(df['publisher'].value_counts().head())
        
        print("\nTop 5 Penulis:")
        print(df['author'].value_counts().head())
        
        # Status download tracking
        print(f"\nStatus Download Tracking:")
        print(f"Cover downloaded: {len(df[df['cover_downloaded'] == 'YES'])}/{len(df)}")
        print(f"File downloaded: {len(df[df['file_downloaded'] == 'YES'])}/{len(df)}")
        print(f"Pending downloads: {len(df[df['download_status'] == 'PENDING'])}")
    
    def search_metadata(self, df, keyword, field='title'):
        """Cari metadata buku berdasarkan keyword"""
        if field not in df.columns:
            print(f"Kolom '{field}' tidak ditemukan di DataFrame.")
            return pd.DataFrame()
        mask = df[field].str.contains(keyword, case=False, na=False)
        results = df[mask]
        print(f"Ditemukan {len(results)} hasil untuk '{keyword}' di kolom '{field}'.")
        return results
    
    def update_download_status(self, book_id, status_type, status_value, account_email=""):
        """Update status download untuk buku tertentu"""
        csv_file = OUTPUT_FILES['csv']
        if not os.path.exists(csv_file):
            print(f"File CSV tidak ditemukan: {csv_file}")
            return False
        
        try:
            df = pd.read_csv(csv_file)
            mask = df['id'] == book_id
            
            if status_type == 'cover':
                df.loc[mask, 'cover_downloaded'] = status_value
                if status_value == 'YES':
                    df.loc[mask, 'cover_path'] = f"{COVERS_FOLDER}/{book_id}.jpg"
            elif status_type == 'file':
                df.loc[mask, 'file_downloaded'] = status_value
                if status_value == 'YES':
                    df.loc[mask, 'file_path'] = f"{FILES_FOLDER}/{book_id}.{df.loc[mask, 'extension'].iloc[0]}"
            
            df.loc[mask, 'download_account'] = account_email
            df.to_csv(csv_file, index=False, encoding='utf-8')
            return True
            
        except Exception as e:
            print(f"Error updating status: {e}")
            return False

class InteractiveScraper:
    """Interactive mode for the scraper"""
    
    def __init__(self):
        self.scraper = EnhancedZLibraryScraper()
    
    def show_menu(self):
        """Show interactive menu"""
        while True:
            print("\n" + "="*50)
            print("Z-LIBRARY SCRAPER - INTERACTIVE MODE")
            print("="*50)
            print("1. Scrape dengan filter kustom")
            print("2. Scrape dengan preset")
            print("3. Lihat metadata yang ada")
            print("4. Cari buku")
            print("5. Ringkasan metadata")
            print("6. Keluar")
            print("="*50)
            
            choice = input("Pilih menu (1-6): ").strip()
            
            if choice == '1':
                self.custom_scrape()
            elif choice == '2':
                self.preset_scrape()
            elif choice == '3':
                self.view_metadata()
            elif choice == '4':
                self.search_books()
            elif choice == '5':
                self.show_summary()
            elif choice == '6':
                print("Keluar dari interactive mode...")
                break
            else:
                print("Pilihan tidak valid!")
    
    def custom_scrape(self):
        """Custom scraping with user input"""
        print("\n--- CUSTOM SCRAPING ---")
        
        search_query = input("Query pencarian (default: gramedia): ").strip() or "gramedia"
        max_pages = int(input("Max halaman (default: 10): ").strip() or "10")
        year_from = input("Tahun dari (kosong untuk semua): ").strip() or None
        year_to = input("Tahun sampai (kosong untuk semua): ").strip() or None
        
        print("\nPilihan bahasa:")
        for i, lang in enumerate(SUPPORTED_LANGUAGES, 1):
            print(f"{i}. {lang}")
        lang_choice = input("Pilih bahasa (kosong untuk semua): ").strip()
        language = SUPPORTED_LANGUAGES[int(lang_choice)-1] if lang_choice.isdigit() and 1 <= int(lang_choice) <= len(SUPPORTED_LANGUAGES) else None
        
        print("\nPilihan sorting:")
        for i, sort in enumerate(SORT_OPTIONS, 1):
            print(f"{i}. {sort}")
        sort_choice = input("Pilih sorting (default: bestmatch): ").strip()
        sort_by = SORT_OPTIONS[int(sort_choice)-1] if sort_choice.isdigit() and 1 <= int(sort_choice) <= len(SORT_OPTIONS) else "bestmatch"
        
        use_auth = input("Gunakan authentication? (y/n, default: n): ").strip().lower() == 'y'
        
        print(f"\nMemulai scraping dengan parameter:")
        print(f"Query: {search_query}")
        print(f"Max pages: {max_pages}")
        print(f"Year: {year_from} - {year_to}")
        print(f"Language: {language}")
        print(f"Sort: {sort_by}")
        print(f"Auth: {use_auth}")
        
        confirm = input("\nLanjutkan? (y/n): ").strip().lower()
        if confirm == 'y':
            df = self.scraper.scrape_with_filters(
                search_query=search_query,
                max_pages=max_pages,
                year_from=year_from,
                year_to=year_to,
                language=language,
                sort_by=sort_by,
                use_auth=use_auth
            )
            self.scraper.print_summary(df)
    
    def preset_scrape(self):
        """Preset scraping options"""
        print("\n--- PRESET SCRAPING ---")
        print("1. Gramedia 2025 (10 halaman)")
        print("2. Gramedia English (5 halaman)")
        print("3. Gramedia Indonesian (5 halaman)")
        print("4. Gramedia 2020-2025 (15 halaman)")
        
        choice = input("Pilih preset (1-4): ").strip()
        
        if choice == '1':
            df = self.scraper.scrape_with_filters(
                search_query="gramedia",
                max_pages=10,
                year_from="2025",
                sort_by="bestmatch",
                use_auth=False
            )
        elif choice == '2':
            df = self.scraper.scrape_with_filters(
                search_query="gramedia",
                max_pages=5,
                language="english",
                sort_by="bestmatch",
                use_auth=False
            )
        elif choice == '3':
            df = self.scraper.scrape_with_filters(
                search_query="gramedia",
                max_pages=5,
                language="indonesian",
                sort_by="bestmatch",
                use_auth=False
            )
        elif choice == '4':
            df = self.scraper.scrape_with_filters(
                search_query="gramedia",
                max_pages=15,
                year_from="2020",
                year_to="2025",
                sort_by="year",
                use_auth=False
            )
        else:
            print("Pilihan tidak valid!")
            return
        
        self.scraper.print_summary(df)
    
    def view_metadata(self):
        """View existing metadata"""
        df = self.scraper.load_existing_metadata()
        if df.empty:
            print("Tidak ada metadata yang tersedia.")
            return
        
        print(f"\nMetadata yang tersedia: {len(df)} buku")
        print(df.head(10).to_string())
    
    def search_books(self):
        """Search books in metadata"""
        df = self.scraper.load_existing_metadata()
        if df.empty:
            print("Tidak ada metadata yang tersedia.")
            return
        
        keyword = input("Masukkan keyword pencarian: ").strip()
        field = input("Cari di kolom (title/author/publisher, default: title): ").strip() or "title"
        
        results = self.scraper.search_metadata(df, keyword, field)
        if not results.empty:
            print(results.head(10).to_string())
    
    def show_summary(self):
        """Show metadata summary"""
        df = self.scraper.load_existing_metadata()
        if df.empty:
            print("Tidak ada metadata yang tersedia.")
            return
        
        self.scraper.print_summary(df)

# Flask web interface
app = Flask(__name__)
scraper_instance = EnhancedZLibraryScraper()

@app.route('/')
def index():
    """Main page"""
    return render_template('index.html')

@app.route('/scrape', methods=['POST'])
def scrape():
    """API endpoint for scraping"""
    data = request.get_json()
    
    # Start scraping in background thread
    def scrape_background():
        scraper_instance.scrape_with_filters(
            search_query=data.get('query', 'gramedia'),
            max_pages=int(data.get('max_pages', 10)),
            year_from=data.get('year_from'),
            year_to=data.get('year_to'),
            language=data.get('language'),
            sort_by=data.get('sort_by', 'bestmatch'),
            use_auth=data.get('use_auth', False)
        )
    
    thread = threading.Thread(target=scrape_background)
    thread.start()
    
    return jsonify({'status': 'started'})

@app.route('/status')
def status():
    """Get scraping status"""
    return jsonify(scraper_instance.scraping_status)

@app.route('/metadata')
def metadata():
    """Get metadata summary"""
    df = scraper_instance.load_existing_metadata()
    if df.empty:
        return jsonify({'total': 0, 'data': []})
    
    return jsonify({
        'total': len(df),
        'data': df.head(100).to_dict('records')
    })

def run_web_mode():
    """Run web interface"""
    print(f"Starting web interface at http://{FLASK_HOST}:{FLASK_PORT}")
    app.run(host=FLASK_HOST, port=FLASK_PORT, debug=FLASK_DEBUG)

def main():
    """Main function"""
    import sys
    
    if len(sys.argv) > 1:
        mode = sys.argv[1].lower()
        
        if mode == 'interactive':
            interactive = InteractiveScraper()
            interactive.show_menu()
        elif mode == 'web':
            run_web_mode()
        elif mode == 'auto':
            # Automatic scraping with default settings (no authentication needed for metadata)
            scraper = EnhancedZLibraryScraper()
            df = scraper.scrape_with_filters(
                search_query="gramedia",
                max_pages=10,
                year_from="2025",
                sort_by="bestmatch",
                use_auth=False  # No Selenium needed for metadata scraping
            )
            scraper.print_summary(df)
        else:
            print("Mode tidak valid! Gunakan: interactive, web, atau auto")
    else:
        print("Z-Library Scraper")
        print("Usage: python zlibrary_scraper.py [interactive|web|auto]")
        print("\nModes:")
        print("  interactive - Interactive command line mode")
        print("  web        - Web interface mode")
        print("  auto       - Automatic scraping with default settings")

if __name__ == "__main__":
    main() 