#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Run All Scripts
Script untuk menjalankan scraper dan analyzer secara berurutan
Dengan workflow lengkap: metadata -> cover -> file download
"""

import os
import sys
import subprocess
import time
from config import *

def run_script(script_name, description):
    """
    Jalankan script Python dan tampilkan output
    """
    print(f"\n{'='*60}")
    print(f"MENJALANKAN: {description}")
    print(f"{'='*60}")
    
    try:
        # Jalankan script
        result = subprocess.run([sys.executable, script_name], 
                              capture_output=True, 
                              text=True, 
                              encoding='utf-8')
        
        # Tampilkan output
        if result.stdout:
            print(result.stdout)
        
        if result.stderr:
            print("ERROR:", result.stderr)
        
        if result.returncode == 0:
            print(f"✓ {description} berhasil dijalankan")
            return True
        else:
            print(f"✗ {description} gagal dijalankan")
            return False
            
    except Exception as e:
        print(f"✗ Error menjalankan {script_name}: {e}")
        return False

def check_dependencies():
    """
    Cek apakah semua dependensi terinstall
    """
    print("Memeriksa dependensi...")
    
    required_packages = [
        'requests', 'beautifulsoup4', 'pandas', 'lxml', 'openpyxl'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"✓ {package}")
        except ImportError:
            print(f"✗ {package} - TIDAK TERINSTALL")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\nDependensi yang hilang: {', '.join(missing_packages)}")
        print("Install dengan perintah:")
        print(f"pip install {' '.join(missing_packages)}")
        return False
    
    print("✓ Semua dependensi terinstall")
    return True

def check_accounts():
    """
    Cek konfigurasi akun Z-Library
    """
    print("\nMemeriksa konfigurasi akun...")
    
    if not ZLIBRARY_ACCOUNTS:
        print("✗ Tidak ada akun Z-Library yang dikonfigurasi")
        print("  Edit file config.py dan tambahkan akun di ZLIBRARY_ACCOUNTS")
        return False
    
    print(f"✓ {len(ZLIBRARY_ACCOUNTS)} akun Z-Library dikonfigurasi")
    for i, account in enumerate(ZLIBRARY_ACCOUNTS):
        print(f"  {i+1}. {account['email']} (max: {account['max_daily_downloads']} downloads/hari)")
    
    return True

def main():
    """
    Fungsi utama
    """
    print("Z-Library Scraper & Downloader - Complete Workflow")
    print("="*60)
    print("Workflow yang akan dijalankan:")
    print("1. zlibrary_scraper.py - Scraping metadata dari Z-Library (query: gramedia)")
    print("2. download_covers.py - Download cover buku")
    print("3. download_files.py - Download file ebook (dengan multi-account)")
    print("4. analyze_books.py - Analisis data buku")
    print(f"5. Semua hasil disimpan di folder '{EBOOK_FOLDER}'")
    print("="*60)
    
    # Cek dependensi
    if not check_dependencies():
        print("\nSilakan install dependensi yang hilang terlebih dahulu.")
        return
    
    # Cek akun
    if not check_accounts():
        print("\nSilakan konfigurasi akun Z-Library terlebih dahulu.")
        return
    
    # Cek apakah file script ada
    scripts = [
        ("zlibrary_scraper.py", "Z-Library Metadata Scraper"),
        ("download_covers.py", "Cover Downloader"),
        ("download_files.py", "File Downloader"),
        ("analyze_books.py", "Book Data Analyzer")
    ]
    
    for script_file, description in scripts:
        if not os.path.exists(script_file):
            print(f"✗ File {script_file} tidak ditemukan")
            return
    
    # Jalankan workflow lengkap
    print("\nMemulai workflow lengkap...")
    
    # Step 1: Metadata Scraping
    success = run_script("zlibrary_scraper.py", "Z-Library Metadata Scraper")
    
    if success:
        # Step 2: Cover Download
        print("\nMenunggu 3 detik sebelum download cover...")
        time.sleep(3)
        run_script("download_covers.py", "Cover Downloader")
        
        # Step 3: File Download (dengan konfirmasi)
        print("\n" + "="*60)
        print("DOWNLOAD FILE EBOOK")
        print("="*60)
        print("⚠️  PERINGATAN: Download file akan menggunakan akun Z-Library")
        print("   Pastikan akun sudah dikonfigurasi dengan benar di config.py")
        print("   Setiap akun memiliki limit 10 download per hari")
        print("\nLanjutkan dengan download file? (y/n): ", end="")
        
        try:
            choice = input().strip().lower()
            if choice in ['y', 'yes', 'ya']:
                run_script("download_files.py", "File Downloader")
            else:
                print("Download file dilewati.")
        except KeyboardInterrupt:
            print("\nDownload file dibatalkan.")
        
        # Step 4: Analysis
        print("\nMenunggu 3 detik sebelum analisis...")
        time.sleep(3)
        run_script("analyze_books.py", "Book Data Analyzer")
        
        print("\n" + "="*60)
        print("WORKFLOW SELESAI!")
        print("="*60)
        print(f"File yang dihasilkan di folder '{EBOOK_FOLDER}':")
        
        output_files = [
            OUTPUT_FILES['csv'],
            OUTPUT_FILES['excel'], 
            OUTPUT_FILES['json'],
            OUTPUT_FILES['summary'],
            OUTPUT_FILES['tracking']
        ]
        
        for file in output_files:
            if os.path.exists(file):
                size = os.path.getsize(file)
                filename = os.path.basename(file)
                print(f"✓ {filename} ({size:,} bytes)")
            else:
                filename = os.path.basename(file)
                print(f"✗ {filename} - tidak ditemukan")
        
        # Cek folder covers
        covers_dir = f"{EBOOK_FOLDER}/{COVERS_FOLDER}"
        if os.path.exists(covers_dir):
            cover_count = len([f for f in os.listdir(covers_dir) if f.endswith(('.jpg', '.png', '.jpeg'))])
            print(f"✓ {covers_dir} ({cover_count} cover images)")
        else:
            print(f"✗ {covers_dir} - tidak ditemukan")
            
        # Cek folder files
        files_dir = f"{EBOOK_FOLDER}/{FILES_FOLDER}"
        if os.path.exists(files_dir):
            file_count = len([f for f in os.listdir(files_dir) if f.endswith(('.pdf', '.epub', '.djvu'))])
            print(f"✓ {files_dir} ({file_count} ebook files)")
        else:
            print(f"✗ {files_dir} - tidak ditemukan")
            
        # Cek folder logs
        logs_dir = f"{EBOOK_FOLDER}/{LOGS_FOLDER}"
        if os.path.exists(logs_dir):
            log_files = os.listdir(logs_dir)
            print(f"✓ {logs_dir} ({len(log_files)} log files)")
        else:
            print(f"✗ {logs_dir} - tidak ditemukan")
    
    else:
        print("\nMetadata scraping gagal. Workflow tidak dapat dilanjutkan.")

if __name__ == "__main__":
    main() 