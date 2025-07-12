#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Installation script for Enhanced Z-Library Scraper
"""

import os
import sys
import subprocess
import shutil

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 7):
        print("✗ Python 3.7 or higher is required")
        return False
    print(f"✓ Python {sys.version_info.major}.{sys.version_info.minor} detected")
    return True

def install_dependencies():
    """Install required dependencies"""
    print("Installing dependencies...")
    
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✓ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to install dependencies: {e}")
        return False

def create_folders():
    """Create necessary folders"""
    folders = [
        "ebooks",
        "ebooks/covers",
        "ebooks/files", 
        "ebooks/logs",
        "ebooks/analysis",
        "templates"
    ]
    
    for folder in folders:
        if not os.path.exists(folder):
            os.makedirs(folder, exist_ok=True)
            print(f"✓ Created folder: {folder}")
        else:
            print(f"✓ Folder exists: {folder}")

def check_config():
    """Check if config.py is properly configured"""
    try:
        from config import ZLIBRARY_ACCOUNTS
        
        if not ZLIBRARY_ACCOUNTS or ZLIBRARY_ACCOUNTS[0]['email'] == 'your_email1@example.com':
            print("⚠️  Please configure your Z-Library accounts in config.py")
            print("   Edit config.py and add your account details")
            return False
        else:
            print(f"✓ {len(ZLIBRARY_ACCOUNTS)} account(s) configured")
            return True
    except ImportError:
        print("✗ config.py not found")
        return False

def test_imports():
    """Test if all modules can be imported"""
    modules = [
        'requests',
        'pandas', 
        'bs4',
        'selenium',
        'lxml'
    ]
    
    print("Testing imports...")
    for module in modules:
        try:
            __import__(module)
            print(f"✓ {module}")
        except ImportError:
            print(f"✗ {module} - not installed")
            return False
    
    return True

def main():
    """Main installation function"""
    print("="*50)
    print("Enhanced Z-Library Scraper - Installation")
    print("="*50)
    
    # Check Python version
    if not check_python_version():
        return False
    
    # Install dependencies
    if not install_dependencies():
        return False
    
    # Create folders
    create_folders()
    
    # Test imports
    if not test_imports():
        print("✗ Some dependencies are missing")
        return False
    
    # Check config
    check_config()
    
    print("\n" + "="*50)
    print("Installation completed!")
    print("="*50)
    print("\nNext steps:")
    print("1. Edit config.py and add your Z-Library accounts")
    print("2. Run: python run_all.py")
    print("3. Or try interactive mode: python run_all.py interactive")
    print("4. Or web interface: python run_all.py web")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)