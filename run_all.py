#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Enhanced Z-Library Complete Scraper
Script untuk menjalankan seluruh proses scraping dan download secara otomatis
Dengan progress tracking dan error handling yang lebih baik
"""

import os
import sys
import time
import logging
from datetime import datetime
from config import *
from zlibrary_scraper import EnhancedZLibraryScraper, InteractiveScraper, FLASK_AVAILABLE
from download_covers import CoverDownloader
from download_files import EnhancedFileDownloader

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

class CompleteZLibraryScraper:
    def __init__(self):
        self.scraper = EnhancedZLibraryScraper()
        self.cover_downloader = CoverDownloader()
        self.file_downloader = EnhancedFileDownloader()
        self.start_time = None
        self.stats = {
            'scraping': {'started': False, 'completed': False, 'books_found': 0},
            'covers': {'started': False, 'completed': False, 'downloaded': 0, 'failed': 0},
            'files': {'started': False, 'completed': False, 'downloaded': 0, 'failed': 0}
        }
    
    def print_banner(self):
        """Print welcome banner"""
        print("="*60)
        print("🚀 ENHANCED Z-LIBRARY COMPLETE SCRAPER")
        print("="*60)
        print("This script will:")
        print("1. Scrape metadata from Z-Library")
        print("2. Download book covers")
        print("3. Download book files with account rotation")
        print("="*60)
    
    def check_prerequisites(self):
        """Check if all prerequisites are met"""
        print("Checking prerequisites...")
        
        # Check if config is properly set
        if not ZLIBRARY_ACCOUNTS or ZLIBRARY_ACCOUNTS[0]['email'] == 'your_email1@example.com':
            print("✗ Please configure your Z-Library accounts in config.py")
            return False
        
        # Check if required folders exist
        required_folders = [
            EBOOK_FOLDER,
            f"{EBOOK_FOLDER}/{COVERS_FOLDER}",
            f"{EBOOK_FOLDER}/{FILES_FOLDER}",
            f"{EBOOK_FOLDER}/{LOGS_FOLDER}"
        ]
        
        for folder in required_folders:
            if not os.path.exists(folder):
                os.makedirs(folder, exist_ok=True)
                print(f"✓ Created folder: {folder}")
        
        print("✓ Prerequisites check completed")
        return True
    
    def run_metadata_scraping(self, search_query="gramedia", max_pages=10, 
                             year_from="2025", language=None, sort_by="bestmatch"):
        """Run metadata scraping phase"""
        print("\n" + "="*50)
        print("📚 PHASE 1: METADATA SCRAPING")
        print("="*50)
        
        self.stats['scraping']['started'] = True
        
        try:
            df = self.scraper.scrape_with_filters(
                search_query=search_query,
                max_pages=max_pages,
                year_from=year_from,
                language=language,
                sort_by=sort_by,
                use_auth=True
            )
            
            if df is not None and not df.empty:
                self.stats['scraping']['books_found'] = len(df)
                self.stats['scraping']['completed'] = True
                print(f"✓ Metadata scraping completed: {len(df)} books found")
                return True
            else:
                print("✗ No metadata found")
                return False
                
        except Exception as e:
            logger.error(f"Error during metadata scraping: {e}")
            print(f"✗ Error during metadata scraping: {e}")
            return False
    
    def run_cover_download(self):
        """Run cover download phase"""
        print("\n" + "="*50)
        print("🖼️  PHASE 2: COVER DOWNLOAD")
        print("="*50)
        
        self.stats['covers']['started'] = True
        
        try:
            # Check if metadata exists
            csv_file = OUTPUT_FILES['csv']
            if not os.path.exists(csv_file):
                print("✗ No metadata file found. Run metadata scraping first.")
                return False
            
            # Run cover download
            self.cover_downloader.download_covers_with_tracking()
            
            # Update stats
            df = self.cover_downloader.scraper.load_existing_metadata()
            if not df.empty:
                covers_downloaded = len(df[df['cover_downloaded'] == 'YES'])
                covers_failed = len(df[df['cover_downloaded'].isin(['FAILED', 'ERROR', 'TIMEOUT'])])
                
                self.stats['covers']['downloaded'] = covers_downloaded
                self.stats['covers']['failed'] = covers_failed
                self.stats['covers']['completed'] = True
            
            print(f"✓ Cover download completed")
            return True
            
        except Exception as e:
            logger.error(f"Error during cover download: {e}")
            print(f"✗ Error during cover download: {e}")
            return False
    
    def run_file_download(self):
        """Run file download phase"""
        print("\n" + "="*50)
        print("📖 PHASE 3: FILE DOWNLOAD")
        print("="*50)
        
        self.stats['files']['started'] = True
        
        try:
            # Check if metadata exists
            csv_file = OUTPUT_FILES['csv']
            if not os.path.exists(csv_file):
                print("✗ No metadata file found. Run metadata scraping first.")
                return False
            
            # Run file download
            self.file_downloader.download_files_with_rotation()
            
            # Update stats
            df = self.file_downloader.scraper.load_existing_metadata()
            if not df.empty:
                files_downloaded = len(df[df['file_downloaded'] == 'YES'])
                files_failed = len(df[df['file_downloaded'] == 'FAILED'])
                
                self.stats['files']['downloaded'] = files_downloaded
                self.stats['files']['failed'] = files_failed
                self.stats['files']['completed'] = True
            
            print(f"✓ File download completed")
            return True
            
        except Exception as e:
            logger.error(f"Error during file download: {e}")
            print(f"✗ Error during file download: {e}")
            return False
    
    def print_final_stats(self):
        """Print final statistics"""
        print("\n" + "="*60)
        print("📊 FINAL STATISTICS")
        print("="*60)
        
        if self.start_time:
            duration = time.time() - self.start_time
            print(f"⏱️  Total Duration: {duration:.2f} seconds ({duration/60:.2f} minutes)")
        
        print(f"\n📚 Metadata Scraping:")
        print(f"   Status: {'✓ Completed' if self.stats['scraping']['completed'] else '✗ Failed'}")
        print(f"   Books Found: {self.stats['scraping']['books_found']}")
        
        print(f"\n🖼️  Cover Download:")
        print(f"   Status: {'✓ Completed' if self.stats['covers']['completed'] else '✗ Failed'}")
        print(f"   Downloaded: {self.stats['covers']['downloaded']}")
        print(f"   Failed: {self.stats['covers']['failed']}")
        
        print(f"\n📖 File Download:")
        print(f"   Status: {'✓ Completed' if self.stats['files']['completed'] else '✗ Failed'}")
        print(f"   Downloaded: {self.stats['files']['downloaded']}")
        print(f"   Failed: {self.stats['files']['failed']}")
        
        # Load final metadata for summary
        try:
            df = self.scraper.load_existing_metadata()
            if not df.empty:
                print(f"\n📈 Overall Summary:")
                print(f"   Total Books: {len(df)}")
                print(f"   Covers Downloaded: {len(df[df['cover_downloaded'] == 'YES'])}")
                print(f"   Files Downloaded: {len(df[df['file_downloaded'] == 'YES'])}")
                print(f"   Pending Downloads: {len(df[df['download_status'] == 'PENDING'])}")
        except Exception as e:
            logger.error(f"Error loading final metadata: {e}")
        
        print(f"\n📁 Files Location:")
        print(f"   Metadata: {OUTPUT_FILES['csv']}")
        print(f"   Covers: {EBOOK_FOLDER}/{COVERS_FOLDER}")
        print(f"   Files: {EBOOK_FOLDER}/{FILES_FOLDER}")
        print(f"   Logs: {EBOOK_FOLDER}/{LOGS_FOLDER}")
    
    def run_complete_process(self, search_query="gramedia", max_pages=10, 
                           year_from="2025", language=None, sort_by="bestmatch"):
        """Run the complete scraping and downloading process"""
        self.start_time = time.time()
        
        # Print banner
        self.print_banner()
        
        # Check prerequisites
        if not self.check_prerequisites():
            return False
        
        # Phase 1: Metadata Scraping
        if not self.run_metadata_scraping(search_query, max_pages, year_from, language, sort_by):
            print("✗ Metadata scraping failed. Stopping process.")
            return False
        
        # Phase 2: Cover Download
        if not self.run_cover_download():
            print("⚠️  Cover download failed, but continuing with file download...")
        
        # Phase 3: File Download
        if not self.run_file_download():
            print("⚠️  File download failed.")
        
        # Print final statistics
        self.print_final_stats()
        
        return True
    
    def run_interactive_mode(self):
        """Run interactive mode"""
        print("Starting interactive mode...")
        interactive = InteractiveScraper()
        interactive.show_menu()
    
    def run_web_mode(self):
        """Run web interface mode"""
        if not FLASK_AVAILABLE:
            print("✗ Flask not available. Install Flask to use web mode.")
            return
        
        print("Starting web interface...")
        from zlibrary_scraper import run_web_mode
        run_web_mode()

def main():
    """Main function"""
    import sys
    
    scraper = CompleteZLibraryScraper()
    
    if len(sys.argv) > 1:
        mode = sys.argv[1].lower()
        
        if mode == 'interactive':
            scraper.run_interactive_mode()
        elif mode == 'web':
            scraper.run_web_mode()
        elif mode == 'scrape-only':
            # Only run metadata scraping
            scraper.run_metadata_scraping()
        elif mode == 'covers-only':
            # Only run cover download
            scraper.run_cover_download()
        elif mode == 'files-only':
            # Only run file download
            scraper.run_file_download()
        elif mode == 'custom':
            # Custom parameters
            if len(sys.argv) < 3:
                print("Usage: python run_all.py custom <search_query> [max_pages] [year_from]")
                return
            
            search_query = sys.argv[2]
            max_pages = int(sys.argv[3]) if len(sys.argv) > 3 else 10
            year_from = sys.argv[4] if len(sys.argv) > 4 else "2025"
            
            scraper.run_complete_process(search_query, max_pages, year_from)
        else:
            print("Invalid mode. Available modes:")
            print("  python run_all.py                    # Run complete process with defaults")
            print("  python run_all.py interactive        # Interactive mode")
            print("  python run_all.py web                # Web interface mode")
            print("  python run_all.py scrape-only        # Only metadata scraping")
            print("  python run_all.py covers-only        # Only cover download")
            print("  python run_all.py files-only         # Only file download")
            print("  python run_all.py custom <query>     # Custom parameters")
    else:
        # Run complete process with default settings
        scraper.run_complete_process()

if __name__ == "__main__":
    main() 