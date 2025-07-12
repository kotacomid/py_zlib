#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script to debug URL construction and requests
"""

import requests
from config import *

def test_url_construction():
    """Test URL construction"""
    print("Testing URL construction...")
    
    # Test basic URL
    search_query = "gramedia"
    year_from = "2025"
    sort_by = "bestmatch"
    
    # Build search URL with filters
    search_url = f"{SEARCH_URL}?q={search_query}"
    if year_from:
        search_url += f"&yearFrom={year_from}"
    if sort_by:
        search_url += f"&order={sort_by}"
    
    print(f"Search URL: {search_url}")
    
    # Test full URL
    url = f"{BASE_URL}{search_url}&page=1"
    print(f"Full URL: {url}")
    
    # Test request
    print("\nTesting request...")
    session = requests.Session()
    session.headers.update(HEADERS)
    
    try:
        print(f"Making request to: {url}")
        response = session.get(url, timeout=30)
        print(f"Response status: {response.status_code}")
        print(f"Response length: {len(response.content)}")
        
        if response.status_code == 200:
            print("✓ Request successful!")
            # Check if page contains book data
            if "z-bookcard" in response.text:
                print("✓ Found z-bookcard elements!")
            else:
                print("✗ No z-bookcard elements found")
                print("Page might be different or blocked")
        else:
            print(f"✗ Request failed with status {response.status_code}")
            
    except Exception as e:
        print(f"✗ Error making request: {e}")

def test_authenticated_request():
    """Test authenticated request"""
    print("\n" + "="*50)
    print("Testing authenticated request...")
    
    try:
        from selenium_login import SeleniumZLibraryLogin
        
        login_manager = SeleniumZLibraryLogin()
        session = login_manager.get_authenticated_session(0, headless=True)
        
        if session:
            print("✓ Authentication successful!")
            
            # Test the same URL with authenticated session
            search_query = "gramedia"
            year_from = "2025"
            sort_by = "bestmatch"
            
            search_url = f"{SEARCH_URL}?q={search_query}"
            if year_from:
                search_url += f"&yearFrom={year_from}"
            if sort_by:
                search_url += f"&order={sort_by}"
            
            url = f"{BASE_URL}{search_url}&page=1"
            print(f"Testing authenticated URL: {url}")
            
            response = session.get(url, timeout=30)
            print(f"Response status: {response.status_code}")
            print(f"Response length: {len(response.content)}")
            
            if response.status_code == 200:
                print("✓ Authenticated request successful!")
                if "z-bookcard" in response.text:
                    print("✓ Found z-bookcard elements!")
                else:
                    print("✗ No z-bookcard elements found")
            else:
                print(f"✗ Authenticated request failed with status {response.status_code}")
        else:
            print("✗ Authentication failed")
            
    except Exception as e:
        print(f"✗ Error in authenticated test: {e}")

if __name__ == "__main__":
    test_url_construction()
    test_authenticated_request()