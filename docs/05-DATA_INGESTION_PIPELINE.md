# Data Ingestion Pipeline
## Multi-Source Scientific Literature Ingestion

**Version:** 2.0  
**Date:** 2026-07-23  
**Pipeline Type:** Data Engineer → GenAI Analysis

---

## Overview

The system uses a **two-stage pipeline**:

1. **Stage 1: Data Ingestion** (Data Engineer) - Collect and normalize articles from external sources
2. **Stage 2: GenAI Analysis** (AI System) - Extract insights using LLMs

This document covers Stage 1 (Ingestion).

---

## Data Sources

### Primary Sources

| Source | Coverage | API/Method | Rate Limits | Data Format |
|--------|----------|------------|-------------|-------------|
| **PubMed** | Biomedical literature (35M+ articles) | E-utilities API | 10 req/sec with API key | XML |
| **Crossref** | DOI metadata (130M+ records) | REST API | 50 req/sec (polite pool) | JSON |
| **Google Scholar** | General academic (>500M articles) | Scraping (no official API) | ~100 req/hour (rotating IPs) | HTML |

### Secondary Sources (Future)
- **PubMed Central (PMC)**: Full-text articles (open access)
- **OpenAlex**: Open scholarly graph (250M+ works)
- **Semantic Scholar**: AI-powered literature search
- **medRxiv/bioRxiv**: Preprint servers

---

## v1.0 Schema (DocumentDB)

### Existing Database Structure

**Collection:** `articles`

#### Columns Added by Data Engineer (Ingestion Metadata)
```
Ingestion Metadata (9 columns):
- _id: str                    # MongoDB ObjectID
- articleID: str              # External ID (PMID, DOI, or generated)
- articleName: str            # Short name/slug
- articleDOI: str             # Digital Object Identifier
- articleSource: str          # Source system (pubmed, crossref, scholar)
- metadataID: str             # Source-specific metadata ID
- URL: str                    # Full-text link
- status: str                 # Ingestion status (pending, processed, failed)
- Type: str                   # Article type (research, review, editorial)

Article Metadata (5 columns):
- articleTitle: str           # Full title
- abstracts: str              # Abstract text
- journal: str                # Journal name
- keywords: list[str]         # Author keywords
- authors: list[dict]         # [{name, affiliation, orcid}, ...]
- articlePublishDate: date    # Publication date
- countryOfStudy: str         # Study location

GenAI Analysis Results (11 columns):
- subject: str                # SubjectEnum value
- scientificCategory: str     # CategoryEnum value
- summary: str                # Plain-language summary
- entitiesSummarized: list[str] # EntityEnum values
- sentimentTowardsTHR: str    # SentimentEnum value
- affiliatedCompany: str      # Industry affiliation
- COI: str                    # Conflict of interest details
- affiliation: str            # Author affiliations (detailed)
- Reference: str              # Citation string

Model Metadata (4 columns):
- modelID: str                # LLM model used (e.g., claude-sonnet-4-6)
- prompt: str                 # Prompt used for analysis
- promptVersion: str          # Version of prompt template
- generatedAt: datetime       # Timestamp of analysis
```

**Total: 29 columns**

---

## v2.0 Schema Mapping (SQLite/PostgreSQL)

### Table 1: `articles` (Core Article Data)

Combines ingestion metadata + article metadata.

```sql
CREATE TABLE articles (
    -- Primary keys
    id TEXT PRIMARY KEY,                    -- UUID (replaces _id)
    article_id TEXT UNIQUE NOT NULL,        -- Maps to: articleID
    
    -- Ingestion metadata
    source TEXT NOT NULL,                   -- Maps to: articleSource (pubmed, crossref, scholar)
    source_metadata_id TEXT,                -- Maps to: metadataID
    doi TEXT,                               -- Maps to: articleDOI
    url TEXT,                               -- Maps to: URL
    ingestion_status TEXT DEFAULT 'pending', -- Maps to: status
    article_type TEXT,                      -- Maps to: Type (research, review, editorial)
    
    -- Article metadata
    title TEXT NOT NULL,                    -- Maps to: articleTitle
    abstract TEXT,                          -- Maps to: abstracts
    journal TEXT,                           -- Maps to: journal
    keywords JSON,                          -- Maps to: keywords (stored as JSON array)
    authors JSON,                           -- Maps to: authors (stored as JSON array)
    publication_date TEXT,                  -- Maps to: articlePublishDate
    country TEXT,                           -- Maps to: countryOfStudy
    
    -- Additional fields (new in v2.0)
    full_text TEXT,                         -- Full article text (if available)
    figures JSON,                           -- Extracted figures/tables
    references JSON,                        -- Cited references
    
    -- Timestamps
    ingested_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_articles_source ON articles(source);
CREATE INDEX idx_articles_doi ON articles(doi);
CREATE INDEX idx_articles_date ON articles(publication_date);
CREATE INDEX idx_articles_status ON articles(ingestion_status);
```

### Table 2: `article_analysis` (GenAI Results)

Stores LLM analysis results (one-to-one with articles).

```sql
CREATE TABLE article_analysis (
    id TEXT PRIMARY KEY,
    article_id TEXT UNIQUE NOT NULL,        -- Foreign key to articles.id
    
    -- Analysis results (maps to GenAI columns)
    subject TEXT,                           -- Maps to: subject
    category TEXT,                          -- Maps to: scientificCategory
    summary TEXT,                           -- Maps to: summary
    entities JSON,                          -- Maps to: entitiesSummarized
    sentiment TEXT,                         -- Maps to: sentimentTowardsTHR
    industry_affiliation TEXT,              -- Maps to: affiliatedCompany
    coi_details TEXT,                       -- Maps to: COI
    author_affiliations JSON,               -- Maps to: affiliation (parsed)
    citation_string TEXT,                   -- Maps to: Reference
    
    -- Confidence scores (new in v2.0)
    confidence_scores JSON,
    
    -- Model metadata
    model_id TEXT,                          -- Maps to: modelID
    prompt_used TEXT,                       -- Maps to: prompt
    prompt_version TEXT,                    -- Maps to: promptVersion
    analyzed_at DATETIME,                   -- Maps to: generatedAt
    
    -- Status
    analysis_status TEXT DEFAULT 'pending',  -- pending, completed, failed
    fact_check_status TEXT,                  -- passed, failed, not_run
    
    FOREIGN KEY (article_id) REFERENCES articles(id) ON DELETE CASCADE
);

CREATE INDEX idx_analysis_status ON article_analysis(analysis_status);
CREATE INDEX idx_analysis_sentiment ON article_analysis(sentiment);
```

### Column Mapping Summary

| DocumentDB Column | v2.0 Table | v2.0 Column | Notes |
|-------------------|------------|-------------|-------|
| `_id` | `articles` | `id` | MongoDB ObjectID → UUID |
| `articleID` | `articles` | `article_id` | Preserved as external ID |
| `articleName` | - | - | Removed (generated from title) |
| `articleDOI` | `articles` | `doi` | Renamed |
| `articleSource` | `articles` | `source` | Renamed |
| `metadataID` | `articles` | `source_metadata_id` | Renamed |
| `articleTitle` | `articles` | `title` | Renamed |
| `abstracts` | `articles` | `abstract` | Singular form |
| `journal` | `articles` | `journal` | Same |
| `keywords` | `articles` | `keywords` | JSON array |
| `authors` | `articles` | `authors` | JSON array |
| `articlePublishDate` | `articles` | `publication_date` | Renamed |
| `countryOfStudy` | `articles` | `country` | Renamed |
| `URL` | `articles` | `url` | Lowercase |
| `status` | `articles` | `ingestion_status` | Clarified |
| `Type` | `articles` | `article_type` | Lowercase |
| `subject` | `article_analysis` | `subject` | Moved to analysis table |
| `scientificCategory` | `article_analysis` | `category` | Renamed + moved |
| `summary` | `article_analysis` | `summary` | Moved |
| `entitiesSummarized` | `article_analysis` | `entities` | Renamed + moved |
| `sentimentTowardsTHR` | `article_analysis` | `sentiment` | Renamed + moved |
| `affiliatedCompany` | `article_analysis` | `industry_affiliation` | Renamed + moved |
| `COI` | `article_analysis` | `coi_details` | Renamed + moved |
| `affiliation` | `article_analysis` | `author_affiliations` | Moved |
| `Reference` | `article_analysis` | `citation_string` | Renamed + moved |
| `modelID` | `article_analysis` | `model_id` | Moved |
| `prompt` | `article_analysis` | `prompt_used` | Renamed + moved |
| `promptVersion` | `article_analysis` | `prompt_version` | Moved |
| `generatedAt` | `article_analysis` | `analyzed_at` | Renamed + moved |

---

## Data Ingestion Architecture

### High-Level Flow

```
External Sources → Scrapers/APIs → Raw Data → Normalizer → SQLite → GenAI Analysis
    │                   │              │           │           │           │
    ├─ PubMed          │              │           │           │           └─ Enriched Results
    ├─ Crossref        │              │           │           │
    └─ Google Scholar  │              │           │           └─ articles + article_analysis tables
                       │              │           │
                       │              │           └─ Unified schema
                       │              │
                       │              └─ Source-specific formats (XML, JSON, HTML)
                       │
                       └─ Rate-limited, error-handled fetchers
```

---

## Ingestion Pipeline Components

### Component 1: Source Connectors

#### PubMed Connector
**File:** `backend/app/ingestion/pubmed.py`

```python
from Bio import Entrez
from typing import List, Dict, Optional
from datetime import datetime
import time

Entrez.email = "your-email@example.com"  # Required by NCBI
Entrez.api_key = "YOUR_NCBI_API_KEY"     # For 10 req/sec (vs 3 req/sec without)

class PubMedConnector:
    """Fetch articles from PubMed E-utilities API"""
    
    def __init__(self, api_key: Optional[str] = None):
        if api_key:
            Entrez.api_key = api_key
        self.rate_limit_delay = 0.1  # 10 req/sec with API key
    
    def search_articles(
        self,
        query: str,
        max_results: int = 100,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[str]:
        """
        Search PubMed and return list of PMIDs.
        
        Example query: "tobacco harm reduction[Title/Abstract]"
        Date format: "2024/01/01"
        """
        search_params = {
            'db': 'pubmed',
            'term': query,
            'retmax': max_results,
            'sort': 'pub_date',
            'retmode': 'json'
        }
        
        if start_date and end_date:
            search_params['mindate'] = start_date
            search_params['maxdate'] = end_date
            search_params['datetype'] = 'pdat'  # Publication date
        
        handle = Entrez.esearch(**search_params)
        results = Entrez.read(handle)
        handle.close()
        
        pmids = results['IdList']
        return pmids
    
    def fetch_article_details(self, pmids: List[str]) -> List[Dict]:
        """
        Fetch full article details for list of PMIDs.
        Returns normalized article data.
        """
        articles = []
        
        # Batch fetch (up to 200 PMIDs per request)
        batch_size = 200
        for i in range(0, len(pmids), batch_size):
            batch = pmids[i:i + batch_size]
            
            handle = Entrez.efetch(
                db='pubmed',
                id=','.join(batch),
                retmode='xml'
            )
            records = Entrez.read(handle)
            handle.close()
            
            for record in records['PubmedArticle']:
                article = self._parse_pubmed_record(record)
                articles.append(article)
            
            time.sleep(self.rate_limit_delay)
        
        return articles
    
    def _parse_pubmed_record(self, record: Dict) -> Dict:
        """Parse PubMed XML record to normalized format"""
        medline = record.get('MedlineCitation', {})
        article = medline.get('Article', {})
        
        # Extract authors
        authors = []
        for author in article.get('AuthorList', []):
            authors.append({
                'name': f"{author.get('LastName', '')} {author.get('ForeName', '')}".strip(),
                'affiliation': author.get('AffiliationInfo', [{}])[0].get('Affiliation', ''),
                'orcid': None  # PubMed doesn't consistently provide ORCID
            })
        
        # Extract abstract
        abstract_list = article.get('Abstract', {}).get('AbstractText', [])
        abstract = ' '.join([str(a) for a in abstract_list])
        
        # Extract keywords
        keywords = [kw for kw in medline.get('KeywordList', [[]])[0]]
        
        return {
            'article_id': f"PMID{medline['PMID']}",
            'source': 'pubmed',
            'source_metadata_id': str(medline['PMID']),
            'doi': article.get('ELocationID', [{}])[0].get('#text', '') if article.get('ELocationID') else '',
            'title': article.get('ArticleTitle', ''),
            'abstract': abstract,
            'journal': article.get('Journal', {}).get('Title', ''),
            'authors': authors,
            'keywords': keywords,
            'publication_date': self._parse_pubmed_date(article.get('ArticleDate', [])),
            'url': f"https://pubmed.ncbi.nlm.nih.gov/{medline['PMID']}/",
            'article_type': article.get('PublicationTypeList', [{}])[0].get('#text', 'research'),
            'country': self._extract_country(authors)
        }
    
    def _parse_pubmed_date(self, date_list: List) -> str:
        """Parse PubMed date to ISO format"""
        if not date_list:
            return ''
        date = date_list[0]
        return f"{date.get('Year', '')}-{date.get('Month', '01')}-{date.get('Day', '01')}"
    
    def _extract_country(self, authors: List[Dict]) -> str:
        """Extract country from first author affiliation"""
        if not authors or not authors[0].get('affiliation'):
            return 'n/a'
        
        # Simple heuristic: last word in affiliation is often country
        affiliation = authors[0]['affiliation']
        words = affiliation.split(',')
        return words[-1].strip() if words else 'n/a'
```

#### Crossref Connector
**File:** `backend/app/ingestion/crossref.py`

```python
import requests
from typing import List, Dict, Optional
import time

class CrossrefConnector:
    """Fetch articles from Crossref REST API"""
    
    BASE_URL = "https://api.crossref.org/works"
    
    def __init__(self, email: str):
        self.email = email  # For polite pool (faster rate limits)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': f'TobaccoResearchPlatform/2.0 (mailto:{email})'
        })
        self.rate_limit_delay = 0.02  # 50 req/sec in polite pool
    
    def search_articles(
        self,
        query: str,
        max_results: int = 100,
        filter_params: Optional[Dict] = None
    ) -> List[Dict]:
        """
        Search Crossref and return article metadata.
        
        Example query: "tobacco harm reduction"
        Filter params: {'from-pub-date': '2024-01-01', 'until-pub-date': '2024-12-31'}
        """
        articles = []
        rows_per_page = 100
        offset = 0
        
        while len(articles) < max_results:
            params = {
                'query': query,
                'rows': min(rows_per_page, max_results - len(articles)),
                'offset': offset,
                'mailto': self.email
            }
            
            if filter_params:
                params['filter'] = ','.join(f"{k}:{v}" for k, v in filter_params.items())
            
            response = self.session.get(self.BASE_URL, params=params)
            response.raise_for_status()
            
            data = response.json()
            items = data['message']['items']
            
            if not items:
                break
            
            for item in items:
                article = self._parse_crossref_item(item)
                articles.append(article)
            
            offset += len(items)
            time.sleep(self.rate_limit_delay)
        
        return articles[:max_results]
    
    def fetch_by_doi(self, doi: str) -> Dict:
        """Fetch single article by DOI"""
        response = self.session.get(f"{self.BASE_URL}/{doi}")
        response.raise_for_status()
        
        item = response.json()['message']
        return self._parse_crossref_item(item)
    
    def _parse_crossref_item(self, item: Dict) -> Dict:
        """Parse Crossref JSON to normalized format"""
        # Extract authors
        authors = []
        for author in item.get('author', []):
            authors.append({
                'name': f"{author.get('family', '')} {author.get('given', '')}".strip(),
                'affiliation': ', '.join([aff.get('name', '') for aff in author.get('affiliation', [])]),
                'orcid': author.get('ORCID', '').replace('http://orcid.org/', '')
            })
        
        # Extract publication date
        pub_date = item.get('published-print', item.get('published-online', {}))
        date_parts = pub_date.get('date-parts', [[]])[0]
        publication_date = '-'.join([str(d).zfill(2) for d in date_parts]) if date_parts else ''
        
        return {
            'article_id': item.get('DOI', ''),
            'source': 'crossref',
            'source_metadata_id': item.get('DOI', ''),
            'doi': item.get('DOI', ''),
            'title': item.get('title', [''])[0],
            'abstract': item.get('abstract', ''),  # Often empty in Crossref
            'journal': item.get('container-title', [''])[0],
            'authors': authors,
            'keywords': item.get('subject', []),
            'publication_date': publication_date,
            'url': item.get('URL', ''),
            'article_type': item.get('type', 'journal-article'),
            'country': 'n/a'  # Crossref doesn't provide this
        }
```

#### Google Scholar Connector
**File:** `backend/app/ingestion/google_scholar.py`

```python
from scholarly import scholarly
from typing import List, Dict
import time
import random

class GoogleScholarConnector:
    """
    Fetch articles from Google Scholar (via scholarly library).
    
    WARNING: Google Scholar has no official API. Use sparingly.
    Rate limits: ~100 requests/hour per IP.
    Consider using proxy rotation or ScraperAPI.
    """
    
    def __init__(self, use_proxy: bool = False):
        if use_proxy:
            # Configure proxy (optional, requires additional setup)
            pass
        self.rate_limit_delay = 30  # 30 seconds between requests
    
    def search_articles(
        self,
        query: str,
        max_results: int = 50,
        year_low: Optional[int] = None,
        year_high: Optional[int] = None
    ) -> List[Dict]:
        """
        Search Google Scholar and return article metadata.
        
        Note: Google Scholar blocks aggressive scraping.
        Use PubMed/Crossref when possible.
        """
        articles = []
        
        # Build search query
        search_query = scholarly.search_pubs(query, year_low=year_low, year_high=year_high)
        
        for _ in range(max_results):
            try:
                result = next(search_query)
                article = self._parse_scholar_result(result)
                articles.append(article)
                
                # Random delay to avoid detection
                time.sleep(self.rate_limit_delay + random.uniform(0, 10))
                
            except StopIteration:
                break
            except Exception as e:
                print(f"Error fetching from Scholar: {e}")
                time.sleep(60)  # Back off on error
        
        return articles
    
    def _parse_scholar_result(self, result: Dict) -> Dict:
        """Parse Google Scholar result to normalized format"""
        bib = result.get('bib', {})
        
        # Extract authors
        authors = []
        for author in bib.get('author', []):
            authors.append({
                'name': author,
                'affiliation': '',  # Not available in Scholar
                'orcid': None
            })
        
        return {
            'article_id': result.get('url_scholarbib', '').split('=')[-1],  # Extract ID from URL
            'source': 'google_scholar',
            'source_metadata_id': result.get('url_scholarbib', '').split('=')[-1],
            'doi': None,  # Often not available
            'title': bib.get('title', ''),
            'abstract': bib.get('abstract', ''),
            'journal': bib.get('venue', ''),
            'authors': authors,
            'keywords': [],
            'publication_date': str(bib.get('pub_year', '')),
            'url': result.get('pub_url', ''),
            'article_type': 'research',
            'country': 'n/a'
        }
```

---

### Component 2: Data Normalizer

**File:** `backend/app/ingestion/normalizer.py`

```python
from typing import Dict
import uuid
from datetime import datetime

class DataNormalizer:
    """Normalize articles from different sources to unified schema"""
    
    def normalize(self, raw_article: Dict) -> Dict:
        """
        Convert raw article data to v2.0 schema.
        Handles missing fields, validates data.
        """
        return {
            # Generate UUID if not present
            'id': str(uuid.uuid4()),
            'article_id': raw_article.get('article_id', f"UNKNOWN-{uuid.uuid4().hex[:8]}"),
            
            # Ingestion metadata
            'source': raw_article.get('source', 'unknown'),
            'source_metadata_id': raw_article.get('source_metadata_id', ''),
            'doi': raw_article.get('doi', ''),
            'url': raw_article.get('url', ''),
            'ingestion_status': 'pending',  # Will be updated after GenAI analysis
            'article_type': raw_article.get('article_type', 'research'),
            
            # Article metadata
            'title': raw_article.get('title', '').strip(),
            'abstract': raw_article.get('abstract', '').strip(),
            'journal': raw_article.get('journal', ''),
            'keywords': raw_article.get('keywords', []),
            'authors': self._normalize_authors(raw_article.get('authors', [])),
            'publication_date': self._normalize_date(raw_article.get('publication_date', '')),
            'country': raw_article.get('country', 'n/a'),
            
            # Timestamps
            'ingested_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat()
        }
    
    def _normalize_authors(self, authors: list) -> list:
        """Ensure consistent author format"""
        normalized = []
        for author in authors:
            if isinstance(author, str):
                # Convert string to dict
                normalized.append({'name': author, 'affiliation': '', 'orcid': None})
            else:
                normalized.append({
                    'name': author.get('name', ''),
                    'affiliation': author.get('affiliation', ''),
                    'orcid': author.get('orcid', None)
                })
        return normalized
    
    def _normalize_date(self, date_str: str) -> str:
        """Convert various date formats to ISO (YYYY-MM-DD)"""
        if not date_str:
            return ''
        
        # Already in ISO format
        if len(date_str) == 10 and date_str[4] == '-':
            return date_str
        
        # Try common formats
        for fmt in ['%Y/%m/%d', '%Y-%m', '%Y']:
            try:
                dt = datetime.strptime(date_str, fmt)
                return dt.strftime('%Y-%m-%d')
            except:
                continue
        
        return date_str  # Return as-is if can't parse
```

---

### Component 3: Ingestion Orchestrator

**File:** `backend/app/ingestion/orchestrator.py`

```python
from app.ingestion.pubmed import PubMedConnector
from app.ingestion.crossref import CrossrefConnector
from app.ingestion.google_scholar import GoogleScholarConnector
from app.ingestion.normalizer import DataNormalizer
from app.db.sqlite import get_db
import sqlite3
from typing import List, Dict

class IngestionOrchestrator:
    """Coordinate multi-source ingestion"""
    
    def __init__(self):
        self.pubmed = PubMedConnector()
        self.crossref = CrossrefConnector(email="your-email@example.com")
        self.scholar = GoogleScholarConnector()
        self.normalizer = DataNormalizer()
    
    def ingest_from_query(
        self,
        query: str,
        sources: List[str] = ['pubmed', 'crossref'],
        max_per_source: int = 100
    ) -> Dict:
        """
        Ingest articles from multiple sources based on query.
        Returns summary of ingestion.
        """
        results = {
            'total': 0,
            'by_source': {},
            'errors': []
        }
        
        db = get_db()
        
        for source in sources:
            try:
                if source == 'pubmed':
                    raw_articles = self._fetch_from_pubmed(query, max_per_source)
                elif source == 'crossref':
                    raw_articles = self._fetch_from_crossref(query, max_per_source)
                elif source == 'google_scholar':
                    raw_articles = self._fetch_from_scholar(query, max_per_source)
                else:
                    continue
                
                # Normalize and store
                stored = 0
                for raw in raw_articles:
                    normalized = self.normalizer.normalize(raw)
                    if self._store_article(db, normalized):
                        stored += 1
                
                results['by_source'][source] = stored
                results['total'] += stored
                
            except Exception as e:
                results['errors'].append(f"{source}: {str(e)}")
        
        return results
    
    def _fetch_from_pubmed(self, query: str, max_results: int) -> List[Dict]:
        """Fetch from PubMed"""
        pmids = self.pubmed.search_articles(query, max_results=max_results)
        return self.pubmed.fetch_article_details(pmids)
    
    def _fetch_from_crossref(self, query: str, max_results: int) -> List[Dict]:
        """Fetch from Crossref"""
        return self.crossref.search_articles(query, max_results=max_results)
    
    def _fetch_from_scholar(self, query: str, max_results: int) -> List[Dict]:
        """Fetch from Google Scholar"""
        return self.scholar.search_articles(query, max_results=max_results)
    
    def _store_article(self, db: sqlite3.Connection, article: Dict) -> bool:
        """Store article in database (skip if duplicate)"""
        cursor = db.cursor()
        
        # Check for duplicate
        cursor.execute(
            "SELECT id FROM articles WHERE article_id = ?",
            (article['article_id'],)
        )
        if cursor.fetchone():
            return False  # Already exists
        
        # Insert
        cursor.execute("""
            INSERT INTO articles (
                id, article_id, source, source_metadata_id, doi, url,
                ingestion_status, article_type, title, abstract, journal,
                keywords, authors, publication_date, country, ingested_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            article['id'], article['article_id'], article['source'],
            article['source_metadata_id'], article['doi'], article['url'],
            article['ingestion_status'], article['article_type'],
            article['title'], article['abstract'], article['journal'],
            json.dumps(article['keywords']), json.dumps(article['authors']),
            article['publication_date'], article['country'],
            article['ingested_at'], article['updated_at']
        ))
        
        db.commit()
        return True
```

---

## Migration Script: DocumentDB → SQLite

**File:** `backend/scripts/migrate_documentdb_to_sqlite.py`

```python
from pymongo import MongoClient
import sqlite3
import json
from datetime import datetime

def migrate_documentdb_to_sqlite(
    mongo_uri: str,
    mongo_db: str,
    mongo_collection: str,
    sqlite_path: str
):
    """
    Migrate existing DocumentDB articles to SQLite v2.0 schema.
    """
    # Connect to DocumentDB
    mongo_client = MongoClient(mongo_uri)
    mongo_db = mongo_client[mongo_db]
    articles_collection = mongo_db[mongo_collection]
    
    # Connect to SQLite
    sqlite_conn = sqlite3.connect(sqlite_path)
    sqlite_conn.row_factory = sqlite3.Row
    
    # Initialize v2.0 schema (run schema.sql first)
    
    # Migrate articles
    total = articles_collection.count_documents({})
    migrated = 0
    
    for doc in articles_collection.find():
        try:
            # Map DocumentDB fields to v2.0 schema
            article_data = {
                'id': str(doc.get('_id')),
                'article_id': doc.get('articleID', ''),
                'source': doc.get('articleSource', 'unknown'),
                'source_metadata_id': doc.get('metadataID', ''),
                'doi': doc.get('articleDOI', ''),
                'url': doc.get('URL', ''),
                'ingestion_status': doc.get('status', 'processed'),
                'article_type': doc.get('Type', 'research'),
                'title': doc.get('articleTitle', ''),
                'abstract': doc.get('abstracts', ''),
                'journal': doc.get('journal', ''),
                'keywords': json.dumps(doc.get('keywords', [])),
                'authors': json.dumps(doc.get('authors', [])),
                'publication_date': doc.get('articlePublishDate', ''),
                'country': doc.get('countryOfStudy', 'n/a'),
                'ingested_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat()
            }
            
            # Insert into articles table
            sqlite_conn.execute("""
                INSERT INTO articles (
                    id, article_id, source, source_metadata_id, doi, url,
                    ingestion_status, article_type, title, abstract, journal,
                    keywords, authors, publication_date, country, ingested_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, tuple(article_data.values()))
            
            # Migrate analysis results (if present)
            if doc.get('summary'):
                analysis_data = {
                    'id': str(doc.get('_id')) + '_analysis',
                    'article_id': str(doc.get('_id')),
                    'subject': doc.get('subject', ''),
                    'category': doc.get('scientificCategory', ''),
                    'summary': doc.get('summary', ''),
                    'entities': json.dumps(doc.get('entitiesSummarized', [])),
                    'sentiment': doc.get('sentimentTowardsTHR', ''),
                    'industry_affiliation': doc.get('affiliatedCompany', 'n/a'),
                    'coi_details': doc.get('COI', ''),
                    'author_affiliations': json.dumps(doc.get('affiliation', [])),
                    'citation_string': doc.get('Reference', ''),
                    'confidence_scores': json.dumps({}),  # New field
                    'model_id': doc.get('modelID', ''),
                    'prompt_used': doc.get('prompt', ''),
                    'prompt_version': doc.get('promptVersion', ''),
                    'analyzed_at': doc.get('generatedAt', datetime.utcnow()).isoformat(),
                    'analysis_status': 'completed',
                    'fact_check_status': 'not_run'
                }
                
                sqlite_conn.execute("""
                    INSERT INTO article_analysis (
                        id, article_id, subject, category, summary, entities,
                        sentiment, industry_affiliation, coi_details,
                        author_affiliations, citation_string, confidence_scores,
                        model_id, prompt_used, prompt_version, analyzed_at,
                        analysis_status, fact_check_status
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, tuple(analysis_data.values()))
            
            migrated += 1
            if migrated % 100 == 0:
                print(f"Migrated {migrated}/{total} articles")
                sqlite_conn.commit()
        
        except Exception as e:
            print(f"Error migrating article {doc.get('articleID')}: {e}")
    
    sqlite_conn.commit()
    sqlite_conn.close()
    mongo_client.close()
    
    print(f"\nMigration complete: {migrated}/{total} articles migrated")

if __name__ == "__main__":
    migrate_documentdb_to_sqlite(
        mongo_uri="mongodb://localhost:27017",
        mongo_db="tobacco_research",
        mongo_collection="articles",
        sqlite_path="./articles.db"
    )
```

---

## Ingestion API Endpoints

### Trigger Ingestion
```
POST /api/v1/ingestion/trigger
Request:
{
  "query": "tobacco harm reduction",
  "sources": ["pubmed", "crossref"],
  "max_per_source": 100,
  "date_range": {"from": "2024-01-01", "to": "2024-12-31"}
}

Response:
{
  "job_id": "uuid",
  "status": "processing",
  "estimated_time": "5 minutes"
}
```

### Check Ingestion Status
```
GET /api/v1/ingestion/status/{job_id}

Response:
{
  "job_id": "uuid",
  "status": "completed",
  "results": {
    "total": 150,
    "by_source": {"pubmed": 100, "crossref": 50},
    "errors": []
  }
}
```

---

## Best Practices

### Rate Limiting
1. **PubMed**: Get API key for 10 req/sec (vs 3 without)
2. **Crossref**: Use polite pool (include email in User-Agent)
3. **Google Scholar**: Use sparingly, rotate IPs if possible

### Deduplication
- Check `article_id` (PMID, DOI) before inserting
- Cross-reference DOIs across sources
- Use title fuzzy matching for Scholar results

### Error Handling
- Retry failed requests with exponential backoff
- Log all errors with source and article ID
- Mark articles as `ingestion_status: 'failed'` for manual review

### Scheduling
- Run daily for new articles (PubMed, Crossref)
- Weekly for backfilling (Google Scholar)
- Use Celery Beat for scheduled jobs

---

## Next Steps

After ingestion completes → Trigger GenAI analysis pipeline (see `01-SYSTEM_ARCHITECTURE.md`).
