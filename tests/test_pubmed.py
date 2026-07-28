#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Quick test of PubMed API"""
import sys
import os
from dotenv import load_dotenv

# Clear any existing env vars to force reload from .env
os.environ.pop('NCBI_EMAIL', None)
os.environ.pop('NCBI_API_KEY', None)

# Load .env
load_dotenv(override=True)

# Add backend to path
sys.path.insert(0, 'backend')

from Bio import Entrez

# Get credentials
email = os.getenv('NCBI_EMAIL', 'test@example.com')
api_key = os.getenv('NCBI_API_KEY')

print(f"Email: {email}")
print(f"API Key: {'SET' if api_key else 'NOT SET'}")
print()

# Set Entrez credentials
Entrez.email = email
if api_key:
    Entrez.api_key = api_key

# Test 1: Search without date filter
print("=" * 60)
print("TEST 1: Search for 'nicotine pouch' (no date filter)")
print("=" * 60)
try:
    handle = Entrez.esearch(
        db='pubmed',
        term='nicotine pouch',
        retmax=5
    )
    results = Entrez.read(handle)
    handle.close()

    print(f"Found: {results['Count']} total articles")
    print(f"Returned: {len(results['IdList'])} PMIDs")
    print(f"PMIDs: {results['IdList']}")
except Exception as e:
    print(f"ERROR: {e}")

print()

# Test 2: Search with date filter (last 30 days)
print("=" * 60)
print("TEST 2: Search for 'nicotine' with date filter (last 30 days)")
print("=" * 60)
try:
    handle = Entrez.esearch(
        db='pubmed',
        term='nicotine',
        retmax=5,
        mindate='2024/06/24',
        maxdate='2024/07/24',
        datetype='pdat'
    )
    results = Entrez.read(handle)
    handle.close()

    print(f"Found: {results['Count']} total articles")
    print(f"Returned: {len(results['IdList'])} PMIDs")
    print(f"PMIDs: {results['IdList']}")
except Exception as e:
    print(f"ERROR: {e}")

print()

# Test 3: Today's date filter
from datetime import datetime, timedelta

today = datetime.now()
two_days_ago = today - timedelta(days=2)

print("=" * 60)
print(f"TEST 3: Search with recent dates")
print(f"From: {two_days_ago.strftime('%Y/%m/%d')}")
print(f"To: {today.strftime('%Y/%m/%d')}")
print("=" * 60)
try:
    handle = Entrez.esearch(
        db='pubmed',
        term='nicotine OR tobacco',
        retmax=5,
        mindate=two_days_ago.strftime('%Y/%m/%d'),
        maxdate=today.strftime('%Y/%m/%d'),
        datetype='pdat'
    )
    results = Entrez.read(handle)
    handle.close()

    print(f"Found: {results['Count']} total articles")
    print(f"Returned: {len(results['IdList'])} PMIDs")
    print(f"PMIDs: {results['IdList']}")
except Exception as e:
    print(f"ERROR: {e}")
