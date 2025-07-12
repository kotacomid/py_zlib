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
        
    def scrape_gramedia_books(self, max_pages=10, search_query=None):
        """
        Scrape buku dari pencarian Gramedia di Z-Library
        Fokus hanya pada pengumpulan metadata
        Akan scrape dari page 1 sampai max_pages (default 10)
        
        Args:
            max_pages (int): Jumlah halaman maksimal yang akan di-scrape
            search_query (str, optional): Query pencarian tambahan (kosong jika tidak di-set)
        """
        all_books = []
        print("Memulai scraping metadata...")
        print("="*50)
        
        # Gunakan query utama jika tidak ada search_query
        if search_query:
            search_url = f"{SEARCH_URL}?q={search_query}"
            print(f"Menggunakan query: {search_query}")
        else:
            search_url = SEARCH_URL
            print("Menggunakan query utama: gramedia")
            
        for page in range(1, max_pages + 1):
            try:
                # URL dengan parameter halaman dan filter
                url = (
                    f"{self.base_url}{search_url}"
                    f"{'&' if '?' in search_url else '?'}"
                    f"&order={DEFAULT_ORDER}"
                    f"&page={page}"
                )
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
    """Fungsi utama - hanya mengumpulkan metadata"""
    print("Z-Library Metadata Scraper")
    print("="*50)
    
    # Buat instance scraper
    scraper = ZLibraryScraper()
    
    # Scrape metadata sampai halaman 10
    print("Memulai pengumpulan metadata dari Z-Library...")
    print("Scraping akan mengambil sampai 10 halaman")
    print("Menggunakan query utama: gramedia")
    print("Untuk menambah query pencarian, gunakan: scraper.scrape_gramedia_books(max_pages=10, search_query='novel')")
    
    # Scrape dengan query utama saja (tanpa search_query tambahan)
    df = scraper.scrape_gramedia_books(max_pages=10)  # 10 halaman
    
    if df is not None and not df.empty:
        # Tampilkan ringkasan
        scraper.print_summary(df)
        
        # Tampilkan 5 data pertama
        print("\n5 Metadata Buku Pertama:")
        print(df[['title', 'author', 'publisher', 'year', 'rating', 'cover_downloaded', 'file_downloaded']].head())
        
        # Simpan metadata ke berbagai format di folder ebook
        scraper.save_to_csv(df)
        scraper.save_to_excel(df)
        scraper.save_to_json(df)
        
        print(f"\nMetadata scraping selesai! Semua file disimpan di folder '{EBOOK_FOLDER}'")
        print("Langkah selanjutnya:")
        print("1. python download_covers.py - untuk download cover")
        print("2. python download_files.py - untuk download file")
    else:
        print("Tidak ada metadata yang berhasil diambil.")

if __name__ == "__main__":
    main() 