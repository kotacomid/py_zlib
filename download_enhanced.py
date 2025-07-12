#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Enhanced Download Manager using Official Z-Library Package
Provides better reliability and features for downloading books and covers
"""

import asyncio
import aiohttp
import pandas as pd
import os
import time
from datetime import datetime
from typing import List, Dict, Optional
from zlibrary import ZLibrary
from config import *

class EnhancedDownloadManager:
    def __init__(self):
        self.zlib = ZLibrary()
        self._create_folders()
        self.download_stats = {
            'books_success': 0,
            'books_failed': 0,
            'covers_success': 0,
            'covers_failed': 0
        }
        
    def _create_folders(self):
        """Create necessary folders"""
        folders = [
            EBOOK_FOLDER,
            f"{EBOOK_FOLDER}/{COVERS_FOLDER}",
            f"{EBOOK_FOLDER}/{FILES_FOLDER}",
            f"{EBOOK_FOLDER}/{LOGS_FOLDER}"
        ]
        for folder in folders:
            os.makedirs(folder, exist_ok=True)
    
    async def download_book_async(self, book_id: str, download_url: str, 
                                 title: str, author: str, extension: str) -> bool:
        """
        Download a book asynchronously using the zlibrary package
        
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
                self.download_stats['books_success'] += 1
                return True
            else:
                print(f"✗ Failed to download: {filename}")
                self.download_stats['books_failed'] += 1
                return False
                
        except Exception as e:
            print(f"✗ Error downloading {book_id}: {e}")
            self.download_stats['books_failed'] += 1
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
                self.download_stats['covers_failed'] += 1
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
                        self.download_stats['covers_success'] += 1
                        return True
                    else:
                        print(f"✗ Failed to download cover: {filename} ({response.status})")
                        self.download_stats['covers_failed'] += 1
                        return False
                        
        except Exception as e:
            print(f"✗ Error downloading cover for {title}: {e}")
            self.download_stats['covers_failed'] += 1
            return False
    
    async def download_books_batch_async(self, books_df: pd.DataFrame, 
                                        max_concurrent: int = 5) -> pd.DataFrame:
        """
        Download multiple books asynchronously with concurrency control
        
        Args:
            books_df: DataFrame with book information
            max_concurrent: Maximum concurrent downloads
        """
        print(f"Starting enhanced batch download of {len(books_df)} books")
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
        
        # Update CSV with download status
        self._update_download_status(books_df, 'file', success_count > 0)
        
        return books_df
    
    async def download_covers_batch_async(self, books_df: pd.DataFrame,
                                         max_concurrent: int = 10) -> pd.DataFrame:
        """
        Download multiple covers asynchronously
        
        Args:
            books_df: DataFrame with book information
            max_concurrent: Maximum concurrent downloads
        """
        print(f"Starting enhanced batch cover download of {len(books_df)} books")
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
        
        # Update CSV with download status
        self._update_download_status(books_df, 'cover', success_count > 0)
        
        return books_df
    
    def _update_download_status(self, df: pd.DataFrame, download_type: str, success: bool):
        """Update download status in CSV file"""
        csv_file = OUTPUT_FILES['csv']
        if os.path.exists(csv_file):
            try:
                # Read current CSV
                current_df = pd.read_csv(csv_file)
                
                # Update status based on download type
                if download_type == 'file':
                    if success:
                        current_df['file_downloaded'] = 'YES'
                        current_df['download_status'] = 'SUCCESS'
                    else:
                        current_df['download_status'] = 'FAILED'
                elif download_type == 'cover':
                    if success:
                        current_df['cover_downloaded'] = 'YES'
                
                # Save updated CSV
                current_df.to_csv(csv_file, index=False, encoding='utf-8')
                print(f"✓ Updated {download_type} download status in CSV")
                
            except Exception as e:
                print(f"✗ Error updating CSV status: {e}")
    
    def print_download_stats(self):
        """Print download statistics"""
        print("\n" + "="*50)
        print("ENHANCED DOWNLOAD STATISTICS")
        print("="*50)
        print(f"Books downloaded successfully: {self.download_stats['books_success']}")
        print(f"Books failed: {self.download_stats['books_failed']}")
        print(f"Covers downloaded successfully: {self.download_stats['covers_success']}")
        print(f"Covers failed: {self.download_stats['covers_failed']}")
        
        total_books = self.download_stats['books_success'] + self.download_stats['books_failed']
        total_covers = self.download_stats['covers_success'] + self.download_stats['covers_failed']
        
        if total_books > 0:
            book_success_rate = (self.download_stats['books_success'] / total_books) * 100
            print(f"Book success rate: {book_success_rate:.1f}%")
        
        if total_covers > 0:
            cover_success_rate = (self.download_stats['covers_success'] / total_covers) * 100
            print(f"Cover success rate: {cover_success_rate:.1f}%")
    
    def reset_stats(self):
        """Reset download statistics"""
        self.download_stats = {
            'books_success': 0,
            'books_failed': 0,
            'covers_success': 0,
            'covers_failed': 0
        }
        print("✓ Download statistics reset")

def main():
    """Main function for enhanced download manager"""
    print("Enhanced Download Manager using Official Z-Library Package")
    print("="*50)
    
    # Create download manager instance
    download_manager = EnhancedDownloadManager()
    
    while True:
        print("\n" + "="*50)
        print("ENHANCED DOWNLOAD MANAGER MENU")
        print("="*50)
        print("Options:")
        print("1. Download books (batch)")
        print("2. Download covers (batch)")
        print("3. Download both books and covers")
        print("4. Show download statistics")
        print("5. Reset statistics")
        print("6. Exit")
        
        try:
            choice = input("\nEnter your choice (1-6): ").strip()
            
            if choice == "1":
                # Download books
                csv_file = OUTPUT_FILES['csv']
                if os.path.exists(csv_file):
                    df = pd.read_csv(csv_file)
                    print(f"Loaded {len(df)} books from {csv_file}")
                    
                    max_concurrent = input("Max concurrent downloads (default 5): ").strip()
                    max_concurrent = int(max_concurrent) if max_concurrent.isdigit() else 5
                    
                    confirm = input(f"Download books with {max_concurrent} concurrent downloads? (y/n): ").strip().lower()
                    if confirm in ['y', 'yes']:
                        # Run async download
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        
                        try:
                            updated_df = loop.run_until_complete(
                                download_manager.download_books_batch_async(df, max_concurrent)
                            )
                            print("✓ Batch book download completed")
                        finally:
                            loop.close()
                else:
                    print(f"✗ No metadata found at {csv_file}")
                    
            elif choice == "2":
                # Download covers
                csv_file = OUTPUT_FILES['csv']
                if os.path.exists(csv_file):
                    df = pd.read_csv(csv_file)
                    print(f"Loaded {len(df)} books from {csv_file}")
                    
                    max_concurrent = input("Max concurrent downloads (default 10): ").strip()
                    max_concurrent = int(max_concurrent) if max_concurrent.isdigit() else 10
                    
                    confirm = input(f"Download covers with {max_concurrent} concurrent downloads? (y/n): ").strip().lower()
                    if confirm in ['y', 'yes']:
                        # Run async download
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        
                        try:
                            updated_df = loop.run_until_complete(
                                download_manager.download_covers_batch_async(df, max_concurrent)
                            )
                            print("✓ Batch cover download completed")
                        finally:
                            loop.close()
                else:
                    print(f"✗ No metadata found at {csv_file}")
                    
            elif choice == "3":
                # Download both
                csv_file = OUTPUT_FILES['csv']
                if os.path.exists(csv_file):
                    df = pd.read_csv(csv_file)
                    print(f"Loaded {len(df)} books from {csv_file}")
                    
                    book_concurrent = input("Max concurrent book downloads (default 5): ").strip()
                    book_concurrent = int(book_concurrent) if book_concurrent.isdigit() else 5
                    
                    cover_concurrent = input("Max concurrent cover downloads (default 10): ").strip()
                    cover_concurrent = int(cover_concurrent) if cover_concurrent.isdigit() else 10
                    
                    confirm = input(f"Download both books and covers? (y/n): ").strip().lower()
                    if confirm in ['y', 'yes']:
                        # Run async downloads
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        
                        try:
                            # Download covers first (faster)
                            print("\n1. Downloading covers...")
                            updated_df = loop.run_until_complete(
                                download_manager.download_covers_batch_async(df, cover_concurrent)
                            )
                            
                            # Then download books
                            print("\n2. Downloading books...")
                            updated_df = loop.run_until_complete(
                                download_manager.download_books_batch_async(updated_df, book_concurrent)
                            )
                            
                            print("✓ Both downloads completed")
                        finally:
                            loop.close()
                else:
                    print(f"✗ No metadata found at {csv_file}")
                    
            elif choice == "4":
                # Show statistics
                download_manager.print_download_stats()
                
            elif choice == "5":
                # Reset statistics
                download_manager.reset_stats()
                
            elif choice == "6":
                # Exit
                print("Goodbye!")
                break
                
            else:
                print("Invalid choice! Please enter 1-6.")
                
        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    main()