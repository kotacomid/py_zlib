#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Example usage of Enhanced Z-Library Scraper
"""

from zlibrary_scraper import EnhancedZLibraryScraper
from download_covers import CoverDownloader
from download_files import EnhancedFileDownloader
import pandas as pd

def example_metadata_scraping():
    """Example of metadata scraping with different filters"""
    print("Example: Metadata Scraping")
    print("="*40)
    
    scraper = EnhancedZLibraryScraper()
    
    # Example 1: Basic scraping
    print("\n1. Basic scraping (10 pages, 2025 books)")
    df1 = scraper.scrape_with_filters(
        search_query="gramedia",
        max_pages=10,
        year_from="2025",
        sort_by="bestmatch"
    )
    print(f"   Found {len(df1)} books")
    
    # Example 2: English books only
    print("\n2. English books only (5 pages)")
    df2 = scraper.scrape_with_filters(
        search_query="gramedia",
        max_pages=5,
        language="english",
        sort_by="year"
    )
    print(f"   Found {len(df2)} books")
    
    # Example 3: Indonesian books with year range
    print("\n3. Indonesian books 2020-2025 (8 pages)")
    df3 = scraper.scrape_with_filters(
        search_query="gramedia",
        max_pages=8,
        year_from="2020",
        year_to="2025",
        language="indonesian",
        sort_by="rating"
    )
    print(f"   Found {len(df3)} books")
    
    return df1, df2, df3

def example_cover_download():
    """Example of cover downloading"""
    print("\nExample: Cover Download")
    print("="*40)
    
    downloader = CoverDownloader()
    
    # Download all pending covers
    print("\nDownloading all pending covers...")
    downloader.download_covers_with_tracking()
    
    # Show statistics
    print("\nCover download statistics:")
    downloader.print_cover_stats()

def example_file_download():
    """Example of file downloading"""
    print("\nExample: File Download")
    print("="*40)
    
    downloader = EnhancedFileDownloader()
    
    # Download all pending files
    print("\nDownloading all pending files...")
    downloader.download_files_with_rotation()
    
    # Show statistics
    print("\nFile download statistics:")
    downloader.print_file_stats()

def example_data_analysis():
    """Example of data analysis"""
    print("\nExample: Data Analysis")
    print("="*40)
    
    # Load metadata
    csv_file = "ebooks/zlib_metadata.csv"
    try:
        df = pd.read_csv(csv_file)
        
        print(f"Total books: {len(df)}")
        print(f"Unique authors: {df['author'].nunique()}")
        print(f"Unique publishers: {df['publisher'].nunique()}")
        print(f"Languages: {df['language'].value_counts().to_dict()}")
        print(f"File extensions: {df['extension'].value_counts().to_dict()}")
        
        # Download status
        print(f"\nDownload Status:")
        print(f"Covers downloaded: {len(df[df['cover_downloaded'] == 'YES'])}")
        print(f"Files downloaded: {len(df[df['file_downloaded'] == 'YES'])}")
        print(f"Pending: {len(df[df['download_status'] == 'PENDING'])}")
        
        # Top authors
        print(f"\nTop 5 Authors:")
        print(df['author'].value_counts().head())
        
        # Top publishers
        print(f"\nTop 5 Publishers:")
        print(df['publisher'].value_counts().head())
        
    except FileNotFoundError:
        print("No metadata file found. Run scraping first.")

def example_search():
    """Example of searching metadata"""
    print("\nExample: Metadata Search")
    print("="*40)
    
    scraper = EnhancedZLibraryScraper()
    df = scraper.load_existing_metadata()
    
    if df.empty:
        print("No metadata available. Run scraping first.")
        return
    
    # Search by title
    print("\n1. Search books with 'novel' in title:")
    results = scraper.search_metadata(df, 'novel', 'title')
    if not results.empty:
        print(results[['title', 'author', 'year']].head())
    
    # Search by author
    print("\n2. Search books by author 'gramedia':")
    results = scraper.search_metadata(df, 'gramedia', 'author')
    if not results.empty:
        print(results[['title', 'author', 'year']].head())
    
    # Search by publisher
    print("\n3. Search books by publisher 'gramedia':")
    results = scraper.search_metadata(df, 'gramedia', 'publisher')
    if not results.empty:
        print(results[['title', 'author', 'publisher']].head())

def main():
    """Main example function"""
    print("Enhanced Z-Library Scraper - Examples")
    print("="*50)
    
    # Check if config is set up
    try:
        from config import ZLIBRARY_ACCOUNTS
        if ZLIBRARY_ACCOUNTS[0]['email'] == 'your_email1@example.com':
            print("⚠️  Please configure your Z-Library accounts in config.py first")
            print("   Edit config.py and add your account details")
            return
    except ImportError:
        print("✗ config.py not found")
        return
    
    # Run examples
    try:
        # Metadata scraping examples
        example_metadata_scraping()
        
        # Cover download example
        example_cover_download()
        
        # File download example
        example_file_download()
        
        # Data analysis example
        example_data_analysis()
        
        # Search example
        example_search()
        
    except Exception as e:
        print(f"Error running examples: {e}")
        print("Make sure all dependencies are installed and config is set up correctly")

if __name__ == "__main__":
    main()