#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Selenium Login for Z-Library with Cookie Transfer to Requests
Uses Selenium to login and transfers cookies to requests.Session for fast scraping
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import requests
import json
from config import *

class SeleniumZLibraryLogin:
    def __init__(self):
        self.driver = None
        self.session = None
        self.current_account_index = 0
        
    def setup_driver(self, headless=False):
        """Setup Chrome driver with options"""
        chrome_options = Options()
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        if headless:
            chrome_options.add_argument("--headless")
            
        self.driver = webdriver.Chrome(options=chrome_options)
        # Remove webdriver property
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
    def login_with_selenium(self, account_index=0):
        """Login using Selenium and return success status"""
        if account_index >= len(ZLIBRARY_ACCOUNTS):
            print(f"Account index {account_index} tidak valid")
            return False
            
        account = ZLIBRARY_ACCOUNTS[account_index]
        print(f"Attempting Selenium login with: {account['email']}")
        
        try:
            # Navigate to login page
            login_url = f"{BASE_URL}/login"
            self.driver.get(login_url)
            time.sleep(2)
            
            # Wait for page to load
            wait = WebDriverWait(self.driver, 10)
            
            # Fill email
            email_input = wait.until(EC.presence_of_element_located((By.NAME, "email")))
            email_input.clear()
            email_input.send_keys(account['email'])
            
            # Fill password
            password_input = self.driver.find_element(By.NAME, "password")
            password_input.clear()
            password_input.send_keys(account['password'])
            
            # Submit form
            password_input.send_keys(Keys.RETURN)
            time.sleep(3)
            
            # Check for login success
            success_indicators = [
                'logout' in self.driver.page_source.lower(),
                'my library' in self.driver.page_source.lower(),
                'welcome' in self.driver.page_source.lower(),
                'dashboard' in self.driver.page_source.lower()
            ]
            
            if any(success_indicators):
                print(f"✓ Selenium login successful: {account['email']}")
                self.current_account_index = account_index
                return True
            else:
                print(f"✗ Selenium login failed - no success indicators found")
                return False
                
        except Exception as e:
            print(f"✗ Selenium login error: {e}")
            return False
    
    def transfer_cookies_to_requests(self):
        """Transfer cookies from Selenium to requests.Session"""
        if not self.driver:
            print("✗ No Selenium driver available")
            return None
            
        try:
            # Create new requests session
            session = requests.Session()
            
            # Set headers to mimic browser
            session.headers.update({
                'User-Agent': self.driver.execute_script("return navigator.userAgent;"),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            })
            
            # Transfer cookies
            for cookie in self.driver.get_cookies():
                session.cookies.set(
                    cookie['name'], 
                    cookie['value'], 
                    domain=cookie.get('domain', 'z-library.sk')
                )
            
            print("✓ Cookies transferred to requests session")
            self.session = session
            return session
            
        except Exception as e:
            print(f"✗ Error transferring cookies: {e}")
            return None
    
    def test_authenticated_session(self):
        """Test if the requests session is properly authenticated"""
        if not self.session:
            print("✗ No requests session available")
            return False
            
        try:
            # Test with a page that requires login
            test_url = f"{BASE_URL}/"
            response = self.session.get(test_url, timeout=30)
            
            success_indicators = [
                'logout' in response.text.lower(),
                'my library' in response.text.lower(),
                'welcome' in response.text.lower()
            ]
            
            if any(success_indicators):
                print("✓ Requests session is authenticated!")
                return True
            else:
                print("✗ Requests session is NOT authenticated")
                return False
                
        except Exception as e:
            print(f"✗ Error testing session: {e}")
            return False
    
    def get_authenticated_session(self, account_index=0, headless=True):
        """Complete login process and return authenticated requests session"""
        try:
            # Setup driver
            self.setup_driver(headless=headless)
            
            # Login with Selenium
            if not self.login_with_selenium(account_index):
                return None
            
            # Transfer cookies to requests
            session = self.transfer_cookies_to_requests()
            if not session:
                return None
            
            # Test authentication
            if not self.test_authenticated_session():
                return None
            
            return session
            
        except Exception as e:
            print(f"✗ Error in authentication process: {e}")
            return None
        finally:
            # Close browser
            if self.driver:
                self.driver.quit()
    
    def save_session_cookies(self, filename="authenticated_cookies.json"):
        """Save session cookies to file for later use"""
        if not self.session:
            print("✗ No session available to save")
            return False
            
        try:
            cookies_data = []
            for cookie in self.session.cookies:
                cookies_data.append({
                    'name': cookie.name,
                    'value': cookie.value,
                    'domain': cookie.domain,
                    'path': cookie.path
                })
            
            with open(filename, 'w') as f:
                json.dump(cookies_data, f, indent=2)
            
            print(f"✓ Session cookies saved to {filename}")
            return True
            
        except Exception as e:
            print(f"✗ Error saving cookies: {e}")
            return False
    
    def load_session_cookies(self, filename="authenticated_cookies.json"):
        """Load session cookies from file"""
        try:
            with open(filename, 'r') as f:
                cookies_data = json.load(f)
            
            session = requests.Session()
            session.headers.update(HEADERS)
            
            for cookie in cookies_data:
                session.cookies.set(
                    cookie['name'],
                    cookie['value'],
                    domain=cookie['domain'],
                    path=cookie['path']
                )
            
            print(f"✓ Session cookies loaded from {filename}")
            self.session = session
            return session
            
        except Exception as e:
            print(f"✗ Error loading cookies: {e}")
            return None

def main():
    """Test Selenium login with cookie transfer"""
    print("Selenium Z-Library Login with Cookie Transfer")
    print("="*50)
    
    # Show account status
    print("Account Status:")
    for i, account in enumerate(ZLIBRARY_ACCOUNTS):
        status = "✓" if account['daily_downloads'] < account['max_daily_downloads'] else "✗"
        print(f"{status} {account['email']} - {account['daily_downloads']}/{account['max_daily_downloads']} downloads")
    print()
    
    # Create login manager
    login_manager = SeleniumZLibraryLogin()
    
    # Get authenticated session
    print("Starting Selenium login process...")
    session = login_manager.get_authenticated_session(account_index=0, headless=False)
    
    if session:
        print("✓ Successfully obtained authenticated session!")
        
        # Save cookies for later use
        login_manager.save_session_cookies()
        
        # Test the session with a simple request
        print("\nTesting authenticated session...")
        try:
            response = session.get(f"{BASE_URL}/")
            print(f"Response status: {response.status_code}")
            print(f"Page title contains 'Z-Library': {'Z-Library' in response.text}")
            
            # Check if we can access authenticated features
            if 'logout' in response.text.lower():
                print("✓ Session can access authenticated features")
            else:
                print("✗ Session may not be fully authenticated")
                
        except Exception as e:
            print(f"✗ Error testing session: {e}")
    else:
        print("✗ Failed to obtain authenticated session")

if __name__ == "__main__":
    main()