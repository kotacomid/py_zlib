#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Debug script to analyze current Z-Library page structure
"""

import requests
from bs4 import BeautifulSoup
from config import *

def analyze_page_structure():
    """Analyze the current page structure"""
    print("Analyzing Z-Library page structure...")
    
    # Test URL
    url = "https://z-library.sk/s/gramedia?q=gramedia&yearFrom=2025&order=bestmatch&page=1"
    
    session = requests.Session()
    session.headers.update(HEADERS)
    
    try:
        response = session.get(url, timeout=30)
        print(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'lxml')
            
            # Save the page for analysis
            with open("debug_page.html", "w", encoding="utf-8") as f:
                f.write(response.text)
            print("✓ Page saved to debug_page.html")
            
            # Look for common book-related elements
            print("\nSearching for book-related elements...")
            
            # Check for z-bookcard (old structure)
            z_bookcards = soup.find_all("z-bookcard")
            print(f"z-bookcard elements: {len(z_bookcards)}")
            
            # Check for div elements that might contain books
            divs = soup.find_all("div")
            print(f"Total div elements: {len(divs)}")
            
            # Look for elements with book-related classes
            book_classes = []
            for div in divs:
                if div.get('class'):
                    classes = ' '.join(div.get('class'))
                    if any(keyword in classes.lower() for keyword in ['book', 'card', 'item', 'result']):
                        book_classes.append(classes)
            
            print(f"Book-related classes found: {set(book_classes)}")
            
            # Look for elements with book-related IDs
            book_ids = []
            for element in soup.find_all():
                if element.get('id'):
                    if any(keyword in element.get('id').lower() for keyword in ['book', 'card', 'item', 'result']):
                        book_ids.append(element.get('id'))
            
            print(f"Book-related IDs found: {set(book_ids)}")
            
            # Look for links that might be book links
            book_links = []
            for link in soup.find_all('a', href=True):
                href = link.get('href')
                if href and any(keyword in href.lower() for keyword in ['/book/', '/item/', '/result/']):
                    book_links.append(href)
            
            print(f"Book-related links found: {len(book_links)}")
            if book_links:
                print("Sample links:", book_links[:5])
            
            # Look for images (book covers)
            images = soup.find_all('img')
            print(f"Total images: {len(images)}")
            
            cover_images = []
            for img in images:
                src = img.get('src', '') or img.get('data-src', '')
                if src and any(keyword in src.lower() for keyword in ['cover', 'book', 'image']):
                    cover_images.append(src)
            
            print(f"Cover-related images: {len(cover_images)}")
            if cover_images:
                print("Sample covers:", cover_images[:3])
            
            # Look for text content that might be book titles
            title_elements = []
            for element in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'span', 'div']):
                text = element.get_text().strip()
                if text and len(text) > 10 and len(text) < 200:
                    if any(keyword in text.lower() for keyword in ['book', 'novel', 'story', 'author']):
                        title_elements.append(text[:100])
            
            print(f"Potential title elements: {len(title_elements)}")
            if title_elements:
                print("Sample titles:", title_elements[:3])
            
            # Check if page is blocked or shows different content
            page_text = soup.get_text().lower()
            if 'captcha' in page_text:
                print("⚠️  Page contains CAPTCHA - might be blocked")
            if 'blocked' in page_text:
                print("⚠️  Page shows blocked message")
            if 'maintenance' in page_text:
                print("⚠️  Page shows maintenance message")
            if 'error' in page_text:
                print("⚠️  Page shows error message")
            
            # Look for any JavaScript that might load content dynamically
            scripts = soup.find_all('script')
            print(f"Script elements: {len(scripts)}")
            
            # Check for any data attributes that might contain book info
            data_attrs = []
            for element in soup.find_all():
                for attr in element.attrs:
                    if attr.startswith('data-'):
                        data_attrs.append(attr)
            
            print(f"Data attributes found: {set(data_attrs)}")
            
        else:
            print(f"✗ Request failed with status {response.status_code}")
            
    except Exception as e:
        print(f"✗ Error analyzing page: {e}")

if __name__ == "__main__":
    analyze_page_structure()