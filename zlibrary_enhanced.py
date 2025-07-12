#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Enhanced Z-Library Scraper using Official Package
Uses the zlibrary package for better reliability and features
"""

import asyncio
import aiohttp
import pandas as pd
import os
import time
import json
from datetime import datetime
from typing import List, Dict, Optional
from zlibrary import ZLibrary
from config import *

class EnhancedZLibraryScraper:
    def __init__(self):
        self.zlib = ZLibrary()
        self._create_folders()
        self.session = None
        
    def _create_folders(self):
        """Create necessary folders"""
        folders = [
            EBOOK_FOLDER,
            f"{EBOOK_FOLDER}/{COVERS_FOLDER}",
            f"{EBOOK_FOLDER}/{FILES_FOLDER}",
            f"{EBOOK_FOLDER}/{LOGS_FOLDER}",
            f"{EBOOK_FOLDER}/{ANALYSIS_FOLDER}"
        ]
        for folder in folders:
            os.makedirs(folder, exist_ok=True)
    
    async def search_books_async(self, query: str, max_pages: int = 10, 
                                filters: Optional[Dict] = None) -> List[Dict]:
        """
        Search books asynchronously using the zlibrary package
        
        Args:
            query: Search query
            max_pages: Maximum pages to search
            filters: Additional filters (year, language, etc.)
        """
        all_books = []
        
        try:
            print(f"Searching for: {query}")
            print(f"Max pages: {max_pages}")
            if filters:
                print(f"Filters: {filters}")
            
            # Use the zlibrary package to search
            books = await self.zlib.search(query, max_pages=max_pages)
            
            for book in books:
                book_info = self._extract_book_info(book)
                all_books.append(book_info)
                
            print(f"Found {len(all_books)} books")
            
        except Exception as e:
            print(f"Error during search: {e}")
            
        return all_books
    
    def _extract_book_info(self, book) -> Dict:
        """Extract book information from zlibrary package response"""
        return {
            "id": getattr(book, 'id', ''),
            "isbn": getattr(book, 'isbn', ''),
            "title": getattr(book, 'title', ''),
            "author": getattr(book, 'author', ''),
            "publisher": getattr(book, 'publisher', ''),
            "language": getattr(book, 'language', ''),
            "year": getattr(book, 'year', ''),
            "extension": getattr(book, 'extension', ''),
            "filesize": getattr(book, 'filesize', ''),
            "rating": getattr(book, 'rating', ''),
            "quality": getattr(book, 'quality', ''),
            "cover_url": getattr(book, 'cover_url', ''),
            "download_url": getattr(book, 'download_url', ''),
            "book_url": getattr(book, 'book_url', ''),
            "scraped_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "cover_downloaded": "NO",
            "file_downloaded": "NO",
            "download_status": "PENDING",
            "download_account": ""
        }
    
    async def download_book_async(self, book_id: str, download_url: str, 
                                 title: str, author: str, extension: str) -> bool:
        """
        Download a book asynchronously
        
        Args:
            book_id: Book ID
            download_url: Download URL
            title: Book title
            author: Book author
            extension: File extension
        """
        try:
            # Generate file path
            from config import get_file_path
            filepath = get_file_path(title, author, extension, "files")
            filename = os.path.basename(filepath)
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            # Skip if file already exists
            if os.path.exists(filepath):
                print(f"✓ File already exists: {filename}")
                return True
            
            print(f"Downloading: {filename}")
            
            # Use zlibrary package to download
            success = await self.zlib.download(book_id, filepath)
            
            if success:
                print(f"✓ Downloaded: {filename}")
                return True
            else:
                print(f"✗ Failed to download: {filename}")
                return False
                
        except Exception as e:
            print(f"✗ Error downloading {book_id}: {e}")
            return False
    
    async def download_cover_async(self, cover_url: str, title: str, 
                                  author: str) -> bool:
        """
        Download cover image asynchronously
        
        Args:
            cover_url: Cover URL
            title: Book title
            author: Book author
        """
        try:
            # Generate file path
            from config import get_file_path
            filepath = get_file_path(title, author, "jpg", "covers")
            filename = os.path.basename(filepath)
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            # Skip if file already exists
            if os.path.exists(filepath):
                print(f"✓ Cover already exists: {filename}")
                return True
            
            if not cover_url:
                print(f"✗ No cover URL for: {title}")
                return False
            
            print(f"Downloading cover: {filename}")
            
            # Download cover using aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get(cover_url, timeout=COVER_TIMEOUT) as response:
                    if response.status == 200:
                        content = await response.read()
                        with open(filepath, 'wb') as f:
                            f.write(content)
                        print(f"✓ Downloaded cover: {filename}")
                        return True
                    else:
                        print(f"✗ Failed to download cover: {filename} ({response.status})")
                        return False
                        
        except Exception as e:
            print(f"✗ Error downloading cover for {title}: {e}")
            return False
    
    def scrape_gramedia_books(self, max_pages: int = 10, search_query: str = "gramedia",
                             year_from: Optional[str] = None, year_to: Optional[str] = None,
                             language: Optional[str] = None, sort_order: Optional[str] = None) -> pd.DataFrame:
        """
        Scrape books using the enhanced zlibrary package
        
        Args:
            max_pages: Maximum pages to scrape
            search_query: Search query
            year_from: Year from filter
            year_to: Year to filter
            language: Language filter
            sort_order: Sort order
        """
        print("Enhanced Z-Library Scraper using Official Package")
        print("="*50)
        
        # Build search query with filters
        query = search_query
        if year_from:
            query += f" year:{year_from}"
        if year_to:
            query += f" year:{year_to}"
        if language:
            query += f" language:{language}"
        
        print(f"Search query: {query}")
        print(f"Max pages: {max_pages}")
        
        # Run async search
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            books = loop.run_until_complete(
                self.search_books_async(query, max_pages)
            )
            
            if books:
                df = pd.DataFrame(books)
                print(f"✓ Scraped {len(df)} books successfully")
                return df
            else:
                print("✗ No books found")
                return pd.DataFrame()
                
        except Exception as e:
            print(f"✗ Error during scraping: {e}")
            return pd.DataFrame()
        finally:
            loop.close()
    
    async def download_books_batch_async(self, books_df: pd.DataFrame, 
                                        max_concurrent: int = 5) -> pd.DataFrame:
        """
        Download multiple books asynchronously with concurrency control
        
        Args:
            books_df: DataFrame with book information
            max_concurrent: Maximum concurrent downloads
        """
        print(f"Starting batch download of {len(books_df)} books")
        print(f"Max concurrent downloads: {max_concurrent}")
        
        # Filter books that need downloading
        pending_books = books_df[books_df['file_downloaded'] != 'YES']
        
        if len(pending_books) == 0:
            print("No books to download")
            return books_df
        
        print(f"Books to download: {len(pending_books)}")
        
        # Create semaphore for concurrency control
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def download_with_semaphore(book):
            async with semaphore:
                return await self.download_book_async(
                    book['id'],
                    book['download_url'],
                    book['title'],
                    book['author'],
                    book['extension']
                )
        
        # Download books concurrently
        tasks = []
        for _, book in pending_books.iterrows():
            task = download_with_semaphore(book)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Update DataFrame with results
        success_count = sum(1 for r in results if r is True)
        print(f"✓ Successfully downloaded {success_count}/{len(pending_books)} books")
        
        return books_df
    
    async def download_covers_batch_async(self, books_df: pd.DataFrame,
                                         max_concurrent: int = 10) -> pd.DataFrame:
        """
        Download multiple covers asynchronously
        
        Args:
            books_df: DataFrame with book information
            max_concurrent: Maximum concurrent downloads
        """
        print(f"Starting batch cover download of {len(books_df)} books")
        print(f"Max concurrent downloads: {max_concurrent}")
        
        # Filter books that need cover downloading
        pending_covers = books_df[books_df['cover_downloaded'] != 'YES']
        
        if len(pending_covers) == 0:
            print("No covers to download")
            return books_df
        
        print(f"Covers to download: {len(pending_covers)}")
        
        # Create semaphore for concurrency control
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def download_cover_with_semaphore(book):
            async with semaphore:
                return await self.download_cover_async(
                    book['cover_url'],
                    book['title'],
                    book['author']
                )
        
        # Download covers concurrently
        tasks = []
        for _, book in pending_covers.iterrows():
            task = download_cover_with_semaphore(book)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Update DataFrame with results
        success_count = sum(1 for r in results if r is True)
        print(f"✓ Successfully downloaded {success_count}/{len(pending_covers)} covers")
        
        return books_df
    
    def save_to_csv(self, df: pd.DataFrame, filename: Optional[str] = None):
        """Save DataFrame to CSV"""
        if filename is None:
            filename = OUTPUT_FILES['csv']
        
        try:
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            df.to_csv(filename, index=False, encoding='utf-8')
            print(f"✓ Metadata saved to {filename}")
        except Exception as e:
            print(f"✗ Error saving CSV: {e}")
    
    def save_to_json(self, df: pd.DataFrame, filename: Optional[str] = None):
        """Save DataFrame to JSON"""
        if filename is None:
            filename = OUTPUT_FILES['json']
        
        try:
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            df.to_json(filename, orient='records', indent=2, force_ascii=False)
            print(f"✓ Metadata saved to {filename}")
        except Exception as e:
            print(f"✗ Error saving JSON: {e}")
    
    def save_to_excel(self, df: pd.DataFrame, filename: Optional[str] = None):
        """Save DataFrame to Excel"""
        if filename is None:
            filename = OUTPUT_FILES['excel']
        
        try:
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            df.to_excel(filename, index=False)
            print(f"✓ Metadata saved to {filename}")
        except Exception as e:
            print(f"✗ Error saving Excel: {e}")
    
    def remove_duplicates(self, df: pd.DataFrame) -> pd.DataFrame:
        """Remove duplicate books based on title and author"""
        print("Checking for duplicates...")
        initial_count = len(df)
        
        # Remove duplicates based on title and author
        df_clean = df.drop_duplicates(subset=['title', 'author'], keep='first')
        
        removed_count = initial_count - len(df_clean)
        print(f"Removed {removed_count} duplicate entries")
        print(f"Remaining: {len(df_clean)} unique books")
        
        return df_clean
    
    def print_summary(self, df: pd.DataFrame):
        """Print summary of scraped data"""
        print("\n" + "="*50)
        print("ENHANCED Z-LIBRARY SCRAPER SUMMARY")
        print("="*50)
        print(f"Total books: {len(df)}")
        print(f"Unique authors: {df['author'].nunique()}")
        print(f"Unique publishers: {df['publisher'].nunique()}")
        print(f"Languages: {df['language'].value_counts().to_dict()}")
        print(f"File extensions: {df['extension'].value_counts().to_dict()}")
        
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
                    print(f"Average rating: {avg_rating:.2f}")
            except Exception:
                print("Average rating: cannot calculate")
        
        print("\nTop 5 Publishers:")
        print(df['publisher'].value_counts().head())
        
        print("\nTop 5 Authors:")
        print(df['author'].value_counts().head())
        
        print(f"\nDownload Status:")
        print(f"Cover downloaded: {len(df[df['cover_downloaded'] == 'YES'])}/{len(df)}")
        print(f"File downloaded: {len(df[df['file_downloaded'] == 'YES'])}/{len(df)}")
        print(f"Pending downloads: {len(df[df['download_status'] == 'PENDING'])}")

def main():
    """Main function for enhanced scraper"""
    print("Enhanced Z-Library Scraper using Official Package")
    print("="*50)
    
    # Create scraper instance
    scraper = EnhancedZLibraryScraper()
    
    while True:
        print("\n" + "="*50)
        print("ENHANCED Z-LIBRARY SCRAPER MENU")
        print("="*50)
        print("Options:")
        print("1. Quick scrape (default settings)")
        print("2. Advanced scrape with filters")
        print("3. Batch download books")
        print("4. Batch download covers")
        print("5. Load existing metadata")
        print("6. Remove duplicates from existing data")
        print("7. Show summary of existing data")
        print("8. Exit")
        
        try:
            choice = input("\nEnter your choice (1-8): ").strip()
            
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
                # Batch download books
                csv_file = OUTPUT_FILES['csv']
                if os.path.exists(csv_file):
                    df = pd.read_csv(csv_file)
                    print(f"Loaded {len(df)} books from {csv_file}")
                    
                    max_concurrent = input("Max concurrent downloads (default 5): ").strip()
                    max_concurrent = int(max_concurrent) if max_concurrent.isdigit() else 5
                    
                    confirm = input(f"Download {len(df)} books with {max_concurrent} concurrent downloads? (y/n): ").strip().lower()
                    if confirm in ['y', 'yes']:
                        # Run async download
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        
                        try:
                            updated_df = loop.run_until_complete(
                                scraper.download_books_batch_async(df, max_concurrent)
                            )
                            scraper.save_to_csv(updated_df)
                            print("✓ Batch download completed")
                        finally:
                            loop.close()
                else:
                    print(f"✗ No metadata found at {csv_file}")
                    
            elif choice == "4":
                # Batch download covers
                csv_file = OUTPUT_FILES['csv']
                if os.path.exists(csv_file):
                    df = pd.read_csv(csv_file)
                    print(f"Loaded {len(df)} books from {csv_file}")
                    
                    max_concurrent = input("Max concurrent downloads (default 10): ").strip()
                    max_concurrent = int(max_concurrent) if max_concurrent.isdigit() else 10
                    
                    confirm = input(f"Download covers for {len(df)} books with {max_concurrent} concurrent downloads? (y/n): ").strip().lower()
                    if confirm in ['y', 'yes']:
                        # Run async download
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        
                        try:
                            updated_df = loop.run_until_complete(
                                scraper.download_covers_batch_async(df, max_concurrent)
                            )
                            scraper.save_to_csv(updated_df)
                            print("✓ Batch cover download completed")
                        finally:
                            loop.close()
                else:
                    print(f"✗ No metadata found at {csv_file}")
                    
            elif choice == "5":
                # Load existing metadata
                csv_file = OUTPUT_FILES['csv']
                if os.path.exists(csv_file):
                    df = pd.read_csv(csv_file)
                    print(f"✓ Loaded {len(df)} records from {csv_file}")
                    scraper.print_summary(df)
                else:
                    print(f"✗ No existing metadata found at {csv_file}")
                    
            elif choice == "6":
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
                    
            elif choice == "7":
                # Show summary of existing data
                csv_file = OUTPUT_FILES['csv']
                if os.path.exists(csv_file):
                    df = pd.read_csv(csv_file)
                    scraper.print_summary(df)
                else:
                    print(f"✗ No existing metadata found at {csv_file}")
                    
            elif choice == "8":
                # Exit
                print("Goodbye!")
                break
                
            else:
                print("Invalid choice! Please enter 1-8.")
                
        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    main()