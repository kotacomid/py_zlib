#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Flask Web Interface for Z-Library Scraper System
Provides web-based control for scraping, downloading, and monitoring
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
import pandas as pd
import os
import json
from datetime import datetime
from zlibrary_scraper import ZLibraryScraper
from selenium_login import SeleniumZLibraryLogin
from download_covers import download_covers_with_tracking
from download_files import FileDownloader
from config import *

app = Flask(__name__)
app.secret_key = 'zlib_scraper_secret_key_2024'

# Global instances
scraper = ZLibraryScraper()
login_manager = SeleniumZLibraryLogin()
file_downloader = FileDownloader()

@app.route('/')
def index():
    """Main dashboard"""
    # Get current status
    csv_file = OUTPUT_FILES['csv']
    metadata_exists = os.path.exists(csv_file)
    
    if metadata_exists:
        df = pd.read_csv(csv_file)
        total_books = len(df)
        covers_downloaded = len(df[df['cover_downloaded'] == 'YES'])
        files_downloaded = len(df[df['file_downloaded'] == 'YES'])
        pending_downloads = len(df[df['download_status'] == 'PENDING'])
    else:
        total_books = covers_downloaded = files_downloaded = pending_downloads = 0
    
    # Account status
    account_status = []
    for i, account in enumerate(ZLIBRARY_ACCOUNTS):
        status = "Available" if account['daily_downloads'] < account['max_daily_downloads'] else "Limit Reached"
        account_status.append({
            'email': account['email'],
            'downloads': f"{account['daily_downloads']}/{account['max_daily_downloads']}",
            'status': status
        })
    
    return render_template('index.html', 
                         total_books=total_books,
                         covers_downloaded=covers_downloaded,
                         files_downloaded=files_downloaded,
                         pending_downloads=pending_downloads,
                         account_status=account_status,
                         metadata_exists=metadata_exists)

@app.route('/scrape', methods=['GET', 'POST'])
def scrape():
    """Scraping interface"""
    if request.method == 'POST':
        try:
            # Get form data
            max_pages = int(request.form.get('max_pages', 10))
            search_query = request.form.get('search_query', 'gramedia')
            year_from = request.form.get('year_from', '')
            year_to = request.form.get('year_to', '')
            language = request.form.get('language', '')
            sort_order = request.form.get('sort_order', 'bestmatch')
            
            # Clean empty values
            year_from = year_from if year_from else None
            year_to = year_to if year_to else None
            language = language if language else None
            sort_order = sort_order if sort_order else None
            
            # Start scraping
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
                
                flash(f'Successfully scraped {len(df)} books!', 'success')
            else:
                flash('No books found with the given criteria.', 'warning')
                
        except Exception as e:
            flash(f'Error during scraping: {str(e)}', 'error')
    
    return render_template('scrape.html', 
                         supported_languages=SUPPORTED_LANGUAGES,
                         sort_options=SORT_OPTIONS)

@app.route('/download_covers')
def download_covers():
    """Download covers endpoint"""
    try:
        download_covers_with_tracking()
        flash('Cover download completed!', 'success')
    except Exception as e:
        flash(f'Error downloading covers: {str(e)}', 'error')
    
    return redirect(url_for('index'))

@app.route('/download_files')
def download_files():
    """Download files endpoint"""
    try:
        file_downloader.download_files_with_rotation()
        flash('File download completed!', 'success')
    except Exception as e:
        flash(f'Error downloading files: {str(e)}', 'error')
    
    return redirect(url_for('index'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login management"""
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'login':
            account_index = int(request.form.get('account_index', 0))
            headless = request.form.get('headless', 'true') == 'true'
            
            try:
                session = login_manager.get_authenticated_session(account_index, headless=headless)
                if session:
                    login_manager.save_session_cookies()
                    flash(f'Successfully logged in with account {account_index + 1}', 'success')
                else:
                    flash('Login failed. Please check credentials.', 'error')
            except Exception as e:
                flash(f'Login error: {str(e)}', 'error')
                
        elif action == 'load_session':
            try:
                session = login_manager.load_session_cookies()
                if session and login_manager.test_authenticated_session():
                    flash('Session loaded successfully!', 'success')
                else:
                    flash('Failed to load valid session.', 'error')
            except Exception as e:
                flash(f'Session load error: {str(e)}', 'error')
                
        elif action == 'reset_counts':
            login_manager.reset_daily_downloads()
            flash('Daily download counts reset!', 'success')
    
    return render_template('login.html', accounts=ZLIBRARY_ACCOUNTS)

@app.route('/data')
def data():
    """View scraped data"""
    csv_file = OUTPUT_FILES['csv']
    if not os.path.exists(csv_file):
        flash('No metadata found. Please scrape data first.', 'warning')
        return redirect(url_for('index'))
    
    try:
        df = pd.read_csv(csv_file)
        
        # Get pagination parameters
        page = request.args.get('page', 1, type=int)
        per_page = 50
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        
        # Get search parameters
        search = request.args.get('search', '')
        if search:
            mask = df['title'].str.contains(search, case=False, na=False) | \
                   df['author'].str.contains(search, case=False, na=False)
            df = df[mask]
        
        total_pages = (len(df) + per_page - 1) // per_page
        df_page = df.iloc[start_idx:end_idx]
        
        return render_template('data.html', 
                             books=df_page.to_dict('records'),
                             page=page,
                             total_pages=total_pages,
                             search=search,
                             total_books=len(df))
    except Exception as e:
        flash(f'Error loading data: {str(e)}', 'error')
        return redirect(url_for('index'))

@app.route('/api/status')
def api_status():
    """API endpoint for status updates"""
    try:
        csv_file = OUTPUT_FILES['csv']
        if os.path.exists(csv_file):
            df = pd.read_csv(csv_file)
            return jsonify({
                'total_books': len(df),
                'covers_downloaded': len(df[df['cover_downloaded'] == 'YES']),
                'files_downloaded': len(df[df['file_downloaded'] == 'YES']),
                'pending_downloads': len(df[df['download_status'] == 'PENDING'])
            })
        else:
            return jsonify({
                'total_books': 0,
                'covers_downloaded': 0,
                'files_downloaded': 0,
                'pending_downloads': 0
            })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/accounts')
def api_accounts():
    """API endpoint for account status"""
    try:
        accounts = []
        for i, account in enumerate(ZLIBRARY_ACCOUNTS):
            accounts.append({
                'index': i,
                'email': account['email'],
                'downloads': f"{account['daily_downloads']}/{account['max_daily_downloads']}",
                'available': account['daily_downloads'] < account['max_daily_downloads']
            })
        return jsonify(accounts)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Create templates directory if it doesn't exist
    os.makedirs('templates', exist_ok=True)
    
    # Create basic templates
    create_templates()
    
    print(f"Starting Z-Library Scraper Web Interface")
    print(f"Access at: http://{FLASK_HOST}:{FLASK_PORT}")
    app.run(host=FLASK_HOST, port=FLASK_PORT, debug=FLASK_DEBUG)

def create_templates():
    """Create basic HTML templates"""
    
    # Base template
    base_template = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Z-Library Scraper - {% block title %}{% endblock %}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
        <div class="container">
            <a class="navbar-brand" href="{{ url_for('index') }}">
                <i class="fas fa-book"></i> Z-Library Scraper
            </a>
            <div class="navbar-nav">
                <a class="nav-link" href="{{ url_for('index') }}">Dashboard</a>
                <a class="nav-link" href="{{ url_for('scrape') }}">Scrape</a>
                <a class="nav-link" href="{{ url_for('data') }}">Data</a>
                <a class="nav-link" href="{{ url_for('login') }}">Login</a>
            </div>
        </div>
    </nav>

    <div class="container mt-4">
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                {% for category, message in messages %}
                    <div class="alert alert-{{ 'danger' if category == 'error' else category }} alert-dismissible fade show">
                        {{ message }}
                        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                    </div>
                {% endfor %}
            {% endif %}
        {% endwith %}

        {% block content %}{% endblock %}
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    {% block scripts %}{% endblock %}
</body>
</html>'''
    
    # Index template
    index_template = '''{% extends "base.html" %}
{% block title %}Dashboard{% endblock %}

{% block content %}
<div class="row">
    <div class="col-md-12">
        <h1><i class="fas fa-tachometer-alt"></i> Dashboard</h1>
        <hr>
    </div>
</div>

<div class="row mb-4">
    <div class="col-md-3">
        <div class="card bg-primary text-white">
            <div class="card-body">
                <h5 class="card-title"><i class="fas fa-books"></i> Total Books</h5>
                <h2>{{ total_books }}</h2>
            </div>
        </div>
    </div>
    <div class="col-md-3">
        <div class="card bg-success text-white">
            <div class="card-body">
                <h5 class="card-title"><i class="fas fa-image"></i> Covers Downloaded</h5>
                <h2>{{ covers_downloaded }}</h2>
            </div>
        </div>
    </div>
    <div class="col-md-3">
        <div class="card bg-info text-white">
            <div class="card-body">
                <h5 class="card-title"><i class="fas fa-file"></i> Files Downloaded</h5>
                <h2>{{ files_downloaded }}</h2>
            </div>
        </div>
    </div>
    <div class="col-md-3">
        <div class="card bg-warning text-white">
            <div class="card-body">
                <h5 class="card-title"><i class="fas fa-clock"></i> Pending</h5>
                <h2>{{ pending_downloads }}</h2>
            </div>
        </div>
    </div>
</div>

<div class="row">
    <div class="col-md-6">
        <div class="card">
            <div class="card-header">
                <h5><i class="fas fa-cogs"></i> Quick Actions</h5>
            </div>
            <div class="card-body">
                <div class="d-grid gap-2">
                    <a href="{{ url_for('scrape') }}" class="btn btn-primary">
                        <i class="fas fa-search"></i> Scrape Metadata
                    </a>
                    {% if metadata_exists %}
                    <a href="{{ url_for('download_covers') }}" class="btn btn-success">
                        <i class="fas fa-image"></i> Download Covers
                    </a>
                    <a href="{{ url_for('download_files') }}" class="btn btn-info">
                        <i class="fas fa-download"></i> Download Files
                    </a>
                    <a href="{{ url_for('data') }}" class="btn btn-secondary">
                        <i class="fas fa-table"></i> View Data
                    </a>
                    {% endif %}
                </div>
            </div>
        </div>
    </div>
    
    <div class="col-md-6">
        <div class="card">
            <div class="card-header">
                <h5><i class="fas fa-users"></i> Account Status</h5>
            </div>
            <div class="card-body">
                {% for account in account_status %}
                <div class="d-flex justify-content-between align-items-center mb-2">
                    <span>{{ account.email }}</span>
                    <span class="badge bg-{{ 'success' if account.status == 'Available' else 'danger' }}">
                        {{ account.downloads }} downloads
                    </span>
                </div>
                {% endfor %}
            </div>
        </div>
    </div>
</div>
{% endblock %}'''
    
    # Scrape template
    scrape_template = '''{% extends "base.html" %}
{% block title %}Scrape Metadata{% endblock %}

{% block content %}
<div class="row">
    <div class="col-md-12">
        <h1><i class="fas fa-search"></i> Scrape Metadata</h1>
        <hr>
    </div>
</div>

<div class="row">
    <div class="col-md-8">
        <div class="card">
            <div class="card-header">
                <h5>Scraping Configuration</h5>
            </div>
            <div class="card-body">
                <form method="POST">
                    <div class="row">
                        <div class="col-md-6">
                            <div class="mb-3">
                                <label for="max_pages" class="form-label">Max Pages</label>
                                <input type="number" class="form-control" id="max_pages" name="max_pages" value="10" min="1" max="50">
                            </div>
                        </div>
                        <div class="col-md-6">
                            <div class="mb-3">
                                <label for="search_query" class="form-label">Search Query</label>
                                <input type="text" class="form-control" id="search_query" name="search_query" value="gramedia">
                            </div>
                        </div>
                    </div>
                    
                    <div class="row">
                        <div class="col-md-6">
                            <div class="mb-3">
                                <label for="year_from" class="form-label">Year From</label>
                                <input type="number" class="form-control" id="year_from" name="year_from" min="1900" max="2030">
                            </div>
                        </div>
                        <div class="col-md-6">
                            <div class="mb-3">
                                <label for="year_to" class="form-label">Year To</label>
                                <input type="number" class="form-control" id="year_to" name="year_to" min="1900" max="2030">
                            </div>
                        </div>
                    </div>
                    
                    <div class="row">
                        <div class="col-md-6">
                            <div class="mb-3">
                                <label for="language" class="form-label">Language</label>
                                <select class="form-select" id="language" name="language">
                                    <option value="">All Languages</option>
                                    {% for lang in supported_languages %}
                                    <option value="{{ lang }}">{{ lang.title() }}</option>
                                    {% endfor %}
                                </select>
                            </div>
                        </div>
                        <div class="col-md-6">
                            <div class="mb-3">
                                <label for="sort_order" class="form-label">Sort Order</label>
                                <select class="form-select" id="sort_order" name="sort_order">
                                    {% for option in sort_options %}
                                    <option value="{{ option }}" {{ 'selected' if option == 'bestmatch' }}>{{ option.title() }}</option>
                                    {% endfor %}
                                </select>
                            </div>
                        </div>
                    </div>
                    
                    <div class="d-grid">
                        <button type="submit" class="btn btn-primary">
                            <i class="fas fa-search"></i> Start Scraping
                        </button>
                    </div>
                </form>
            </div>
        </div>
    </div>
    
    <div class="col-md-4">
        <div class="card">
            <div class="card-header">
                <h5>Tips</h5>
            </div>
            <div class="card-body">
                <ul class="list-unstyled">
                    <li><i class="fas fa-info-circle text-info"></i> Start with 10 pages for testing</li>
                    <li><i class="fas fa-info-circle text-info"></i> Use "gramedia" as default query</li>
                    <li><i class="fas fa-info-circle text-info"></i> Filter by year for specific periods</li>
                    <li><i class="fas fa-info-circle text-info"></i> Choose language to limit results</li>
                </ul>
            </div>
        </div>
    </div>
</div>
{% endblock %}'''
    
    # Data template
    data_template = '''{% extends "base.html" %}
{% block title %}View Data{% endblock %}

{% block content %}
<div class="row">
    <div class="col-md-12">
        <h1><i class="fas fa-table"></i> Scraped Data</h1>
        <hr>
    </div>
</div>

<div class="row mb-3">
    <div class="col-md-6">
        <form method="GET" class="d-flex">
            <input type="text" class="form-control me-2" name="search" value="{{ search }}" placeholder="Search by title or author...">
            <button type="submit" class="btn btn-primary">Search</button>
        </form>
    </div>
    <div class="col-md-6 text-end">
        <span class="badge bg-secondary">{{ total_books }} total books</span>
    </div>
</div>

<div class="table-responsive">
    <table class="table table-striped">
        <thead>
            <tr>
                <th>Title</th>
                <th>Author</th>
                <th>Publisher</th>
                <th>Year</th>
                <th>Language</th>
                <th>Cover</th>
                <th>File</th>
            </tr>
        </thead>
        <tbody>
            {% for book in books %}
            <tr>
                <td>{{ book.title }}</td>
                <td>{{ book.author }}</td>
                <td>{{ book.publisher }}</td>
                <td>{{ book.year }}</td>
                <td>{{ book.language }}</td>
                <td>
                    <span class="badge bg-{{ 'success' if book.cover_downloaded == 'YES' else 'warning' }}">
                        {{ book.cover_downloaded }}
                    </span>
                </td>
                <td>
                    <span class="badge bg-{{ 'success' if book.file_downloaded == 'YES' else 'warning' }}">
                        {{ book.file_downloaded }}
                    </span>
                </td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
</div>

{% if total_pages > 1 %}
<nav>
    <ul class="pagination justify-content-center">
        {% for p in range(1, total_pages + 1) %}
        <li class="page-item {{ 'active' if p == page else '' }}">
            <a class="page-link" href="{{ url_for('data', page=p, search=search) }}">{{ p }}</a>
        </li>
        {% endfor %}
    </ul>
</nav>
{% endif %}
{% endblock %}'''
    
    # Login template
    login_template = '''{% extends "base.html" %}
{% block title %}Login Management{% endblock %}

{% block content %}
<div class="row">
    <div class="col-md-12">
        <h1><i class="fas fa-sign-in-alt"></i> Login Management</h1>
        <hr>
    </div>
</div>

<div class="row">
    <div class="col-md-6">
        <div class="card">
            <div class="card-header">
                <h5>Manual Login</h5>
            </div>
            <div class="card-body">
                <form method="POST">
                    <input type="hidden" name="action" value="login">
                    <div class="mb-3">
                        <label for="account_index" class="form-label">Select Account</label>
                        <select class="form-select" id="account_index" name="account_index">
                            {% for i, account in enumerate(accounts) %}
                            <option value="{{ i }}">{{ account.email }} ({{ account.daily_downloads }}/{{ account.max_daily_downloads }})</option>
                            {% endfor %}
                        </select>
                    </div>
                    <div class="mb-3">
                        <div class="form-check">
                            <input class="form-check-input" type="checkbox" id="headless" name="headless" value="true" checked>
                            <label class="form-check-label" for="headless">
                                Run in headless mode
                            </label>
                        </div>
                    </div>
                    <button type="submit" class="btn btn-primary">Login</button>
                </form>
            </div>
        </div>
    </div>
    
    <div class="col-md-6">
        <div class="card">
            <div class="card-header">
                <h5>Session Management</h5>
            </div>
            <div class="card-body">
                <form method="POST" class="mb-3">
                    <input type="hidden" name="action" value="load_session">
                    <button type="submit" class="btn btn-success w-100">
                        <i class="fas fa-upload"></i> Load Existing Session
                    </button>
                </form>
                
                <form method="POST">
                    <input type="hidden" name="action" value="reset_counts">
                    <button type="submit" class="btn btn-warning w-100">
                        <i class="fas fa-redo"></i> Reset Daily Download Counts
                    </button>
                </form>
            </div>
        </div>
    </div>
</div>

<div class="row mt-4">
    <div class="col-md-12">
        <div class="card">
            <div class="card-header">
                <h5>Account Status</h5>
            </div>
            <div class="card-body">
                <div class="table-responsive">
                    <table class="table">
                        <thead>
                            <tr>
                                <th>Email</th>
                                <th>Daily Downloads</th>
                                <th>Status</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for account in accounts %}
                            <tr>
                                <td>{{ account.email }}</td>
                                <td>{{ account.daily_downloads }}/{{ account.max_daily_downloads }}</td>
                                <td>
                                    <span class="badge bg-{{ 'success' if account.daily_downloads < account.max_daily_downloads else 'danger' }}">
                                        {{ 'Available' if account.daily_downloads < account.max_daily_downloads else 'Limit Reached' }}
                                    </span>
                                </td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}'''
    
    # Write templates to files
    templates = {
        'base.html': base_template,
        'index.html': index_template,
        'scrape.html': scrape_template,
        'data.html': data_template,
        'login.html': login_template
    }
    
    for filename, content in templates.items():
        with open(f'templates/{filename}', 'w', encoding='utf-8') as f:
            f.write(content)