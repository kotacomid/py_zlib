#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Book Data Analyzer
Script untuk menganalisis data buku yang telah di-scrape dari Z-Library
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from collections import Counter
import numpy as np
from config import *

class BookAnalyzer:
    def __init__(self, csv_file=None):
        """
        Inisialisasi analyzer dengan file CSV
        """
        if csv_file is None:
            csv_file = OUTPUT_FILES['csv']
            
        try:
            self.df = pd.read_csv(csv_file)
            print(f"Data berhasil dimuat: {len(self.df)} buku")
            print(f"Dari file: {csv_file}")
        except FileNotFoundError:
            print(f"File {csv_file} tidak ditemukan. Jalankan zlibrary_scraper.py terlebih dahulu.")
            self.df = None
    
    def basic_stats(self):
        """
        Statistik dasar data buku
        """
        if self.df is None:
            return
        
        print("\n" + "="*60)
        print("STATISTIK DASAR DATA BUKU")
        print("="*60)
        
        print(f"Total buku: {len(self.df)}")
        print(f"Total halaman yang di-scrape: {self.df['page'].nunique()}")
        print(f"Penerbit unik: {self.df['publisher'].nunique()}")
        print(f"Penulis unik: {self.df['author'].nunique()}")
        print(f"Bahasa unik: {self.df['language'].nunique()}")
        print(f"Tahun terbit range: {self.df['year'].min()} - {self.df['year'].max()}")
        
        # Ekstensi file
        print(f"\nEkstensi file:")
        ext_counts = self.df['extension'].value_counts()
        for ext, count in ext_counts.items():
            print(f"  {ext}: {count} buku")
        
        # Rating
        if 'rating' in self.df.columns:
            ratings = pd.to_numeric(self.df['rating'], errors='coerce')
            valid_ratings = ratings.dropna()
            if len(valid_ratings) > 0:
                print(f"\nRating rata-rata: {valid_ratings.mean():.2f}")
                print(f"Rating tertinggi: {valid_ratings.max():.2f}")
                print(f"Rating terendah: {valid_ratings.min():.2f}")
    
    def top_publishers(self, top_n=10):
        """
        Top N penerbit berdasarkan jumlah buku
        """
        if self.df is None:
            return
        
        print(f"\n" + "="*60)
        print(f"TOP {top_n} PENERBIT")
        print("="*60)
        
        publisher_counts = self.df['publisher'].value_counts().head(top_n)
        
        for i, (publisher, count) in enumerate(publisher_counts.items(), 1):
            print(f"{i:2d}. {publisher:<40} {count:>3d} buku")
    
    def top_authors(self, top_n=10):
        """
        Top N penulis berdasarkan jumlah buku
        """
        if self.df is None:
            return
        
        print(f"\n" + "="*60)
        print(f"TOP {top_n} PENULIS")
        print("="*60)
        
        author_counts = self.df['author'].value_counts().head(top_n)
        
        for i, (author, count) in enumerate(author_counts.items(), 1):
            print(f"{i:2d}. {author:<40} {count:>3d} buku")
    
    def year_analysis(self):
        """
        Analisis berdasarkan tahun terbit
        """
        if self.df is None:
            return
        
        print("\n" + "="*60)
        print("ANALISIS BERDASARKAN TAHUN TERBIT")
        print("="*60)
        
        # Konversi tahun ke numeric
        years = pd.to_numeric(self.df['year'], errors='coerce')
        
        # Filter tahun yang valid (1900-2024)
        valid_years = years[(years >= MIN_YEAR) & (years <= MAX_YEAR)]
        
        if len(valid_years) > 0:
            print(f"Tahun terbit range: {valid_years.min():.0f} - {valid_years.max():.0f}")
            print(f"Tahun rata-rata: {valid_years.mean():.1f}")
            
            # Dekade
            decades = (valid_years // 10) * 10
            decade_counts = decades.value_counts().sort_index()
            
            print("\nDistribusi per dekade:")
            for decade, count in decade_counts.items():
                print(f"  {decade:.0f}s: {count} buku")
        else:
            print("Tidak ada data tahun terbit yang valid")
    
    def file_size_analysis(self):
        """
        Analisis ukuran file
        """
        if self.df is None:
            return
        
        print("\n" + "="*60)
        print("ANALISIS UKURAN FILE")
        print("="*60)
        
        # Ekstrak ukuran file dalam MB
        def extract_size_mb(filesize_str):
            if pd.isna(filesize_str) or filesize_str == "":
                return None
            
            try:
                size_str = str(filesize_str).strip()
                if 'MB' in size_str:
                    return float(size_str.replace('MB', '').strip())
                elif 'KB' in size_str:
                    return float(size_str.replace('KB', '').strip()) / 1024
                elif 'GB' in size_str:
                    return float(size_str.replace('GB', '').strip()) * 1024
                else:
                    return None
            except:
                return None
        
        sizes = self.df['filesize'].apply(extract_size_mb)
        valid_sizes = sizes.dropna()
        
        if len(valid_sizes) > 0:
            print(f"Ukuran file rata-rata: {valid_sizes.mean():.2f} MB")
            print(f"Ukuran file terbesar: {valid_sizes.max():.2f} MB")
            print(f"Ukuran file terkecil: {valid_sizes.min():.2f} MB")
            
            # Kategori ukuran
            small = len(valid_sizes[valid_sizes < FILE_SIZE_CATEGORIES['small']])
            medium = len(valid_sizes[(valid_sizes >= FILE_SIZE_CATEGORIES['small']) & (valid_sizes < FILE_SIZE_CATEGORIES['medium'])])
            large = len(valid_sizes[valid_sizes >= FILE_SIZE_CATEGORIES['large']])
            
            print(f"\nKategori ukuran file:")
            print(f"  Kecil (< {FILE_SIZE_CATEGORIES['small']} MB): {small} buku")
            print(f"  Sedang ({FILE_SIZE_CATEGORIES['small']}-{FILE_SIZE_CATEGORIES['medium']} MB): {medium} buku")
            print(f"  Besar (> {FILE_SIZE_CATEGORIES['large']} MB): {large} buku")
    
    def language_analysis(self):
        """
        Analisis berdasarkan bahasa
        """
        if self.df is None:
            return
        
        print("\n" + "="*60)
        print("ANALISIS BERDASARKAN BAHASA")
        print("="*60)
        
        language_counts = self.df['language'].value_counts()
        
        for language, count in language_counts.items():
            percentage = (count / len(self.df)) * 100
            print(f"{language:<15}: {count:>3d} buku ({percentage:5.1f}%)")
    
    def search_books(self, keyword, field='title'):
        """
        Cari buku berdasarkan keyword
        """
        if self.df is None:
            return
        
        print(f"\n" + "="*60)
        print(f"PENCARIAN BUKU: '{keyword}' di kolom '{field}'")
        print("="*60)
        
        if field not in self.df.columns:
            print(f"Kolom '{field}' tidak ditemukan")
            return
        
        # Case-insensitive search
        mask = self.df[field].str.contains(keyword, case=False, na=False)
        results = self.df[mask]
        
        if len(results) > 0:
            print(f"Ditemukan {len(results)} buku:")
            for _, book in results.iterrows():
                print(f"  - {book['title']} oleh {book['author']} ({book['year']})")
        else:
            print(f"Tidak ada buku yang ditemukan dengan keyword '{keyword}'")
    
    def export_summary(self, filename=None):
        """
        Export ringkasan analisis ke file teks
        """
        if self.df is None:
            return
            
        if filename is None:
            filename = OUTPUT_FILES['summary']
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("RINGKASAN ANALISIS DATA BUKU Z-LIBRARY\n")
            f.write("="*50 + "\n\n")
            
            f.write(f"Total buku: {len(self.df)}\n")
            f.write(f"Penerbit unik: {self.df['publisher'].nunique()}\n")
            f.write(f"Penulis unik: {self.df['author'].nunique()}\n")
            f.write(f"Bahasa unik: {self.df['language'].nunique()}\n\n")
            
            f.write("TOP 10 PENERBIT:\n")
            publisher_counts = self.df['publisher'].value_counts().head(10)
            for publisher, count in publisher_counts.items():
                f.write(f"  {publisher}: {count} buku\n")
            
            f.write("\nTOP 10 PENULIS:\n")
            author_counts = self.df['author'].value_counts().head(10)
            for author, count in author_counts.items():
                f.write(f"  {author}: {count} buku\n")
        
        print(f"Ringkasan analisis disimpan ke {filename}")

def main():
    """
    Fungsi utama
    """
    print("Book Data Analyzer")
    print("="*50)
    
    # Buat instance analyzer
    analyzer = BookAnalyzer()
    
    if analyzer.df is not None:
        # Jalankan berbagai analisis
        analyzer.basic_stats()
        analyzer.top_publishers(10)
        analyzer.top_authors(10)
        analyzer.year_analysis()
        analyzer.file_size_analysis()
        analyzer.language_analysis()
        
        # Contoh pencarian
        analyzer.search_books("Tere Liye", "author")
        analyzer.search_books("Gramedia", "publisher")
        
        # Export ringkasan
        analyzer.export_summary()
        
        print(f"\nAnalisis selesai! File disimpan di folder '{EBOOK_FOLDER}'")
    else:
        print("Tidak dapat memuat data. Pastikan file CSV tersedia.")

if __name__ == "__main__":
    main() 