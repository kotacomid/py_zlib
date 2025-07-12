#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Z-Library Scraper
Script untuk melakukan parsing data buku dari Z-Library dan mengubahnya menjadi tabel
Fokus hanya pada pengumpulan metadata
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import json
from datetime import datetime
import os
import re
from config import *
from bs4.element import Tag

class ZLibraryScraper:
    def __init__(self):
        self.base_url = BASE_URL
        self.headers = HEADERS
        self._create_folders()
        
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
        
    def scrape_gramedia_books(self, max_pages=10, search_query=None, year_from=None, year_to=None, 
                             language=None, sort_order=None):
        """
        Scrape buku dari pencarian Gramedia di Z-Library dengan filter lanjutan
        Fokus hanya pada pengumpulan metadata
        Akan scrape dari page 1 sampai max_pages (default 10)
        
        Args:
            max_pages (int): Jumlah halaman maksimal yang akan di-scrape
            search_query (str, optional): Query pencarian tambahan
            year_from (str, optional): Tahun mulai filter
            year_to (str, optional): Tahun akhir filter
            language (str, optional): Filter bahasa (english/indonesian)
            sort_order (str, optional): Urutan sorting
        """
        all_books = []
        print("Memulai scraping metadata...")
        print("="*50)
        
        # Build search URL with parameters
        search_url = SEARCH_URL
        params = []
        
        if search_query:
            params.append(f"q={search_query}")
            print(f"Query: {search_query}")
        
        if year_from:
            params.append(f"yearFrom={year_from}")
            print(f"Year from: {year_from}")
            
        if year_to:
            params.append(f"yearTo={year_to}")
            print(f"Year to: {year_to}")
            
        if language and language in SUPPORTED_LANGUAGES:
            params.append(f"language={language}")
            print(f"Language: {language}")
            
        if sort_order and sort_order in SORT_OPTIONS:
            params.append(f"order={sort_order}")
            print(f"Sort order: {sort_order}")
        else:
            params.append(f"order={DEFAULT_ORDER}")
            print(f"Sort order: {DEFAULT_ORDER} (default)")
        
        # Build final URL
        if params:
            search_url += "?" + "&".join(params)
        
        print(f"Search URL: {search_url}")
        print("="*50)
            
        for page in range(1, max_pages + 1):
            try:
                # URL dengan parameter halaman
                url = f"{self.base_url}{search_url}&page={page}"
                print(f"Mengambil halaman {page}...")
                
                response = requests.get(url, headers=self.headers, timeout=REQUEST_TIMEOUT)
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
                    
                time.sleep(DELAY_BETWEEN_REQUESTS)
                
            except requests.exceptions.RequestException as e:
                print(f"Error saat mengambil halaman {page}: {e}")
                time.sleep(RETRY_DELAY)
            except Exception as e:
                print(f"Error tidak terduga di halaman {page}: {e}")
                time.sleep(RETRY_DELAY)
                
        print(f"\nScraping selesai! Total {len(all_books)} buku dari {max_pages} halaman")
        return pd.DataFrame(all_books)
    
    def _extract_book_info(self, card, page):
        """
        Ekstrak informasi buku dari z-bookcard
        Termasuk tracking fields untuk download status
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
            "cover_downloaded": "NO",  # Tracking field
            "file_downloaded": "NO",   # Tracking field
            "download_status": "PENDING",  # PENDING, SUCCESS, FAILED
            "download_account": ""     # Akun yang digunakan untuk download
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
            # Ambil path setelah /covers100/ atau /covers10000/
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
    
    def save_to_csv(self, df, filename=None):
        """Simpan DataFrame ke CSV"""
        if filename is None:
            filename = OUTPUT_FILES['csv']
        
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            df.to_csv(filename, index=False, encoding='utf-8')
            print(f"Metadata disimpan ke {filename}")
        except PermissionError:
            print(f"✗ Error: Tidak dapat menyimpan ke {filename} (Permission denied)")
            print("  Pastikan file tidak sedang dibuka di aplikasi lain")
            # Try alternative filename
            alt_filename = f"{EBOOK_FOLDER}/zlibrary_gramedia_books_new.csv"
            try:
                df.to_csv(alt_filename, index=False, encoding='utf-8')
                print(f"Metadata disimpan ke {alt_filename}")
            except Exception as e:
                print(f"✗ Error menyimpan ke file alternatif: {e}")
        except Exception as e:
            print(f"✗ Error menyimpan CSV: {e}")
    
    def save_to_excel(self, df, filename=None):
        """Simpan DataFrame ke Excel"""
        if filename is None:
            filename = OUTPUT_FILES['excel']
        df.to_excel(filename, index=False)
        print(f"Metadata disimpan ke {filename}")
    
    def save_to_json(self, df, filename=None):
        """Simpan DataFrame ke JSON"""
        if filename is None:
            filename = OUTPUT_FILES['json']
        df.to_json(filename, orient='records', indent=2, force_ascii=False)
        print(f"Metadata disimpan ke {filename}")
    
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
            # Calculate rating average safely
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
        """Cari metadata buku berdasarkan keyword di kolom tertentu (default: title)"""
        if field not in df.columns:
            print(f"Kolom '{field}' tidak ditemukan di DataFrame.")
            return pd.DataFrame()
        mask = df[field].str.contains(keyword, case=False, na=False)
        results = df[mask]
        print(f"Ditemukan {len(results)} hasil untuk '{keyword}' di kolom '{field}'.")
        return results

    def remove_duplicates(self, df):
        """Remove duplicate books based on title and author"""
        print("Checking for duplicates...")
        initial_count = len(df)
        
        # Remove duplicates based on title and author
        df_clean = df.drop_duplicates(subset=['title', 'author'], keep='first')
        
        removed_count = initial_count - len(df_clean)
        print(f"Removed {removed_count} duplicate entries")
        print(f"Remaining: {len(df_clean)} unique books")
        
        return df_clean
    
    def update_download_status(self, book_id, status_type, status_value, account_email=""):
        """Update status download untuk buku tertentu"""
        csv_file = OUTPUT_FILES['csv']
        if not os.path.exists(csv_file):
            print(f"File CSV tidak ditemukan: {csv_file}")
            return False
        
        try:
            df = pd.read_csv(csv_file)
            
            # Update status berdasarkan book_id
            mask = df['id'] == book_id
            if mask.any():
                if status_type == 'cover':
                    df.loc[mask, 'cover_downloaded'] = status_value
                elif status_type == 'file':
                    df.loc[mask, 'file_downloaded'] = status_value
                    df.loc[mask, 'download_status'] = status_value
                    if account_email:
                        df.loc[mask, 'download_account'] = account_email
                
                # Save updated CSV
                df.to_csv(csv_file, index=False, encoding='utf-8')
                print(f"✓ Updated {status_type} status untuk book ID {book_id}: {status_value}")
                return True
            else:
                print(f"✗ Book ID {book_id} tidak ditemukan")
                return False
                
        except Exception as e:
            print(f"✗ Error updating status: {e}")
            return False

def main():
    """Interactive Z-Library Metadata Scraper"""
    print("Z-Library Metadata Scraper - Interactive Mode")
    print("="*50)
    
    # Create scraper instance
    scraper = ZLibraryScraper()
    
    while True:
        print("\n" + "="*50)
        print("Z-LIBRARY SCRAPER MENU")
        print("="*50)
        print("Options:")
        print("1. Quick scrape (default settings)")
        print("2. Advanced scrape with filters")
        print("3. Load existing metadata")
        print("4. Remove duplicates from existing data")
        print("5. Search in existing metadata")
        print("6. Show summary of existing data")
        print("7. Exit")
        
        try:
            choice = input("\nEnter your choice (1-7): ").strip()
            
            if choice == "1":
                # Quick scrape with default settings
                print("\nQuick scrape with default settings:")
                print("- Query: gramedia")
                print("- Pages: 10")
                print("- Language: All")
                print("- Sort: Best match")
                
                confirm = input("Continue? (y/n): ").strip().lower()
                if confirm in ['y', 'yes']:
                    df = scraper.scrape_gramedia_books(max_pages=10)
                    if df is not None and not df.empty:
                        # Remove duplicates
                        df = scraper.remove_duplicates(df)
                        
                        # Save data
                        scraper.save_to_csv(df)
                        scraper.save_to_excel(df)
                        scraper.save_to_json(df)
                        
                        # Show summary
                        scraper.print_summary(df)
                        
            elif choice == "2":
                # Advanced scrape with filters
                print("\nAdvanced scrape with filters:")
                
                # Get parameters
                max_pages = input("Max pages (default 10): ").strip()
                max_pages = int(max_pages) if max_pages.isdigit() else 10
                
                search_query = input("Search query (default: gramedia): ").strip()
                search_query = search_query if search_query else "gramedia"
                
                year_from = input("Year from (optional): ").strip()
                year_from = year_from if year_from else None
                
                year_to = input("Year to (optional): ").strip()
                year_to = year_to if year_to else None
                
                print(f"\nAvailable languages: {', '.join(SUPPORTED_LANGUAGES)}")
                language = input("Language (optional): ").strip()
                language = language if language in SUPPORTED_LANGUAGES else None
                
                print(f"\nAvailable sort options: {', '.join(SORT_OPTIONS)}")
                sort_order = input("Sort order (optional): ").strip()
                sort_order = sort_order if sort_order in SORT_OPTIONS else None
                
                confirm = input("\nStart scraping with these settings? (y/n): ").strip().lower()
                if confirm in ['y', 'yes']:
                    df = scraper.scrape_gramedia_books(
                        max_pages=max_pages,
                        search_query=search_query,
                        year_from=year_from,
                        year_to=year_to,
                        language=language,
                        sort_order=sort_order
                    )
                    
                    if df is not None and not df.empty:
                        # Remove duplicates
                        df = scraper.remove_duplicates(df)
                        
                        # Save data
                        scraper.save_to_csv(df)
                        scraper.save_to_excel(df)
                        scraper.save_to_json(df)
                        
                        # Show summary
                        scraper.print_summary(df)
                        
            elif choice == "3":
                # Load existing metadata
                csv_file = OUTPUT_FILES['csv']
                if os.path.exists(csv_file):
                    df = pd.read_csv(csv_file)
                    print(f"✓ Loaded {len(df)} records from {csv_file}")
                    scraper.print_summary(df)
                else:
                    print(f"✗ No existing metadata found at {csv_file}")
                    
            elif choice == "4":
                # Remove duplicates from existing data
                csv_file = OUTPUT_FILES['csv']
                if os.path.exists(csv_file):
                    df = pd.read_csv(csv_file)
                    print(f"Loaded {len(df)} records")
                    
                    df_clean = scraper.remove_duplicates(df)
                    
                    # Save cleaned data
                    scraper.save_to_csv(df_clean)
                    scraper.save_to_excel(df_clean)
                    scraper.save_to_json(df_clean)
                    
                    print("✓ Duplicates removed and data saved!")
                else:
                    print(f"✗ No existing metadata found at {csv_file}")
                    
            elif choice == "5":
                # Search in existing metadata
                csv_file = OUTPUT_FILES['csv']
                if os.path.exists(csv_file):
                    df = pd.read_csv(csv_file)
                    print(f"Loaded {len(df)} records")
                    
                    keyword = input("Enter search keyword: ").strip()
                    if keyword:
                        field = input("Search in field (title/author/publisher, default: title): ").strip()
                        field = field if field in df.columns else 'title'
                        
                        results = scraper.search_metadata(df, keyword, field)
                        if not results.empty:
                            print("\nSearch results:")
                            print(results[['title', 'author', 'publisher', 'year']].head(10))
                else:
                    print(f"✗ No existing metadata found at {csv_file}")
                    
            elif choice == "6":
                # Show summary of existing data
                csv_file = OUTPUT_FILES['csv']
                if os.path.exists(csv_file):
                    df = pd.read_csv(csv_file)
                    scraper.print_summary(df)
                else:
                    print(f"✗ No existing metadata found at {csv_file}")
                    
            elif choice == "7":
                # Exit
                print("Goodbye!")
                break
                
            else:
                print("Invalid choice! Please enter 1-7.")
                
        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    main() 