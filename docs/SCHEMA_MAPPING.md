# Complete Schema Mapping: v1.0 DocumentDB → v2.0 SQLite/PostgreSQL

**Version:** 2.0  
**Date:** 2026-07-23  
**Purpose:** Reference guide for data migration and API compatibility

---

## Overview

This document maps every field from the v1.0 DocumentDB schema to the v2.0 SQL schema, showing exactly where each piece of data lives in the new system.

---

## v1.0 DocumentDB Schema (29 Columns)

### Collection: `articles`

**Field Ownership:**
- **Data Engineer Fields (14):** Added during ingestion from PubMed/Crossref/Scholar
- **GenAI Fields (11):** Added by LLM analysis
- **System Fields (4):** Metadata about the analysis process

```javascript
{
  // Data Engineer Fields (Ingestion)
  _id: ObjectId,                      // MongoDB ID
  articleID: "PMID12345",             // External ID (PMID, DOI, or generated)
  articleName: "short-slug",          // Short name/slug
  articleDOI: "10.1234/example",      // Digital Object Identifier
  articleSource: "pubmed",            // Source system (pubmed, crossref, scholar)
  metadataID: "12345",                // Source-specific metadata ID
  articleTitle: "Full article title", // Title
  abstracts: "Abstract text...",      // Abstract
  journal: "Tobacco Control",         // Journal name
  keywords: ["vaping", "youth"],      // Author keywords
  authors: [{name, affiliation, orcid}], // Author list
  articlePublishDate: "2024-01-15",   // Publication date
  countryOfStudy: "United States",    // Study location
  URL: "https://pubmed.ncbi...",      // Full-text link
  
  // GenAI Analysis Fields
  subject: "E-cigarettes",            // SubjectEnum
  scientificCategory: "Clinical Studies", // CategoryEnum
  summary: "Plain-language summary...", // Leadership summary
  entitiesSummarized: ["youth", "vaping"], // List of EntityEnum
  sentimentTowardsTHR: "Neutral",     // SentimentEnum
  affiliatedCompany: "PMI",           // Industry affiliation
  COI: "Author X is funded by...",    // Conflict of interest details
  affiliation: "University of...",    // Author affiliations
  Reference: "Smith et al. 2024",     // Citation string
  
  // System Metadata Fields
  modelID: "claude-sonnet-4-6",       // LLM model used
  prompt: "You are an expert...",     // Prompt used
  promptVersion: "1.0",               // Version of prompt template
  generatedAt: ISODate("2024-01-15"), // Analysis timestamp
  
  // Additional Fields
  status: "processed",                // Ingestion status
  Type: "research"                    // Article type
}
```

---

## v2.0 SQL Schema (Two Tables)

### Design Philosophy
1. **Separation of Concerns:** Ingestion data vs. analysis data in separate tables
2. **Normalization:** No duplicate data, clear foreign keys
3. **Clarity:** Renamed fields for consistency (e.g., `abstracts` → `abstract`)
4. **Extensibility:** Easy to add new fields without schema bloat

---

### Table 1: `articles` (Core Article Data)

**Purpose:** Store raw article metadata from ingestion (Data Engineer stage)

```sql
CREATE TABLE articles (
    -- Primary keys
    id TEXT PRIMARY KEY,                    -- UUID (replaces DocumentDB _id)
    article_id TEXT UNIQUE NOT NULL,        -- External ID (PMID, DOI, etc.)
    
    -- Ingestion metadata (Data Engineer fields)
    source TEXT NOT NULL,                   -- 'pubmed', 'crossref', 'google_scholar'
    source_metadata_id TEXT,                -- Source-specific ID (e.g., PMID number)
    doi TEXT,                               -- Digital Object Identifier
    url TEXT,                               -- Full-text link
    ingestion_status TEXT DEFAULT 'pending', -- 'pending', 'processed', 'failed'
    article_type TEXT,                      -- 'research', 'review', 'editorial'
    
    -- Article metadata
    title TEXT NOT NULL,                    -- Article title
    abstract TEXT,                          -- Abstract text
    journal TEXT,                           -- Journal name
    keywords JSON,                          -- Author keywords (JSON array)
    authors JSON,                           -- Author list (JSON array of objects)
    publication_date TEXT,                  -- ISO format: YYYY-MM-DD
    country TEXT,                           -- Study location
    
    -- New in v2.0 (future expansion)
    full_text TEXT,                         -- Full article text (if available)
    figures JSON,                           -- Extracted figures/tables
    references JSON,                        -- Cited references
    
    -- Timestamps
    ingested_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX idx_articles_source ON articles(source);
CREATE INDEX idx_articles_doi ON articles(doi);
CREATE INDEX idx_articles_date ON articles(publication_date);
CREATE INDEX idx_articles_status ON articles(ingestion_status);

-- Full-text search (SQLite FTS5)
CREATE VIRTUAL TABLE articles_fts USING fts5(
    title, abstract, content='articles', content_rowid='rowid'
);
```

**JSON Field Formats:**

```json
// keywords
["vaping", "e-cigarettes", "youth"]

// authors
[
  {
    "name": "John Smith",
    "affiliation": "University of California",
    "orcid": "0000-0001-2345-6789"
  },
  {
    "name": "Jane Doe",
    "affiliation": "Harvard Medical School",
    "orcid": null
  }
]
```

---

### Table 2: `article_analysis` (GenAI Results)

**Purpose:** Store LLM analysis results (GenAI stage)

```sql
CREATE TABLE article_analysis (
    id TEXT PRIMARY KEY,                    -- UUID
    article_id TEXT UNIQUE NOT NULL,        -- Foreign key to articles.id
    
    -- Analysis results (GenAI fields from v1.0)
    subject TEXT,                           -- SubjectEnum value
    category TEXT,                          -- CategoryEnum value
    summary TEXT,                           -- Plain-language summary
    entities JSON,                          -- EntityEnum values (JSON array)
    sentiment TEXT,                         -- SentimentEnum value
    industry_affiliation TEXT,              -- Industry affiliation (e.g., "PMI")
    coi_details TEXT,                       -- Conflict of interest details
    author_affiliations JSON,               -- Parsed affiliation data
    citation_string TEXT,                   -- Citation string
    
    -- New in v2.0
    confidence_scores JSON,                 -- Per-field confidence scores
    fact_check_results JSON,                -- Fact-checking results
    
    -- Model metadata
    model_id TEXT,                          -- LLM model (e.g., "claude-sonnet-4-6")
    prompt_used TEXT,                       -- Prompt template used
    prompt_version TEXT,                    -- Version of prompt
    analyzed_at DATETIME,                   -- Timestamp of analysis
    
    -- Status tracking
    analysis_status TEXT DEFAULT 'pending', -- 'pending', 'completed', 'failed'
    fact_check_status TEXT,                 -- 'passed', 'failed', 'not_run'
    
    FOREIGN KEY (article_id) REFERENCES articles(id) ON DELETE CASCADE
);

-- Indexes
CREATE INDEX idx_analysis_status ON article_analysis(analysis_status);
CREATE INDEX idx_analysis_sentiment ON article_analysis(sentiment);
CREATE INDEX idx_analysis_category ON article_analysis(category);
```

**JSON Field Formats:**

```json
// entities
["youth", "vaping", "e-cigarettes", "public health"]

// confidence_scores
{
  "subject": 0.95,
  "category": 0.88,
  "sentiment": 0.72,
  "entities": 0.91,
  "summary": 0.85
}

// fact_check_results
{
  "claims": [
    {
      "claim": "E-cigarettes contain nicotine.",
      "label": "Supported",
      "explanation": "Explicitly stated in abstract."
    }
  ],
  "overall_status": "passed"
}

// author_affiliations (parsed)
[
  {
    "author": "John Smith",
    "institution": "University of California",
    "department": "School of Public Health",
    "country": "United States"
  }
]
```

---

## Complete Field Mapping Table

| v1.0 DocumentDB Field | v2.0 Table | v2.0 Field | Data Type Change | Notes |
|-----------------------|------------|------------|------------------|-------|
| `_id` | `articles` | `id` | ObjectId → TEXT (UUID) | MongoDB ID replaced with UUID |
| `articleID` | `articles` | `article_id` | - | Preserved as external identifier |
| `articleName` | - | - | Removed | Generated from title on demand |
| `articleDOI` | `articles` | `doi` | - | Renamed for consistency |
| `articleSource` | `articles` | `source` | - | Renamed, enum values lowercase |
| `metadataID` | `articles` | `source_metadata_id` | - | Renamed for clarity |
| `articleTitle` | `articles` | `title` | - | Renamed (singular) |
| `abstracts` | `articles` | `abstract` | - | Renamed (singular form) |
| `journal` | `articles` | `journal` | - | No change |
| `keywords` | `articles` | `keywords` | Array → JSON | Stored as JSON array |
| `authors` | `articles` | `authors` | Array → JSON | Stored as JSON array of objects |
| `articlePublishDate` | `articles` | `publication_date` | - | Renamed, ISO format enforced |
| `countryOfStudy` | `articles` | `country` | - | Renamed for brevity |
| `URL` | `articles` | `url` | - | Lowercase |
| `status` | `articles` | `ingestion_status` | - | Renamed for clarity |
| `Type` | `articles` | `article_type` | - | Lowercase for consistency |
| `subject` | `article_analysis` | `subject` | - | Moved to analysis table |
| `scientificCategory` | `article_analysis` | `category` | - | Renamed + moved to analysis table |
| `summary` | `article_analysis` | `summary` | - | Moved to analysis table |
| `entitiesSummarized` | `article_analysis` | `entities` | Array → JSON | Renamed + stored as JSON |
| `sentimentTowardsTHR` | `article_analysis` | `sentiment` | - | Renamed + moved |
| `affiliatedCompany` | `article_analysis` | `industry_affiliation` | - | Renamed + moved |
| `COI` | `article_analysis` | `coi_details` | - | Renamed + moved |
| `affiliation` | `article_analysis` | `author_affiliations` | String → JSON | Parsed into structured JSON |
| `Reference` | `article_analysis` | `citation_string` | - | Renamed + moved |
| `modelID` | `article_analysis` | `model_id` | - | Moved to analysis table |
| `prompt` | `article_analysis` | `prompt_used` | - | Renamed + moved |
| `promptVersion` | `article_analysis` | `prompt_version` | - | Moved to analysis table |
| `generatedAt` | `article_analysis` | `analyzed_at` | ISODate → TEXT | Renamed + moved |
| - | `articles` | `full_text` | - | **NEW:** Future full-text storage |
| - | `articles` | `figures` | - | **NEW:** Extracted figures |
| - | `articles` | `references` | - | **NEW:** Citation list |
| - | `articles` | `ingested_at` | - | **NEW:** Ingestion timestamp |
| - | `articles` | `updated_at` | - | **NEW:** Last update timestamp |
| - | `article_analysis` | `confidence_scores` | - | **NEW:** Per-field confidence |
| - | `article_analysis` | `fact_check_results` | - | **NEW:** Fact-check details |
| - | `article_analysis` | `analysis_status` | - | **NEW:** Analysis status tracking |
| - | `article_analysis` | `fact_check_status` | - | **NEW:** Fact-check status |

**Summary:**
- **29 v1.0 fields** → **36 v2.0 fields** (7 new fields added)
- **1 table** → **2 tables** (better normalization)
- **3 fields removed** (articleName - generated on demand)

---

## SQL Queries for Common Operations

### Retrieve Full Article with Analysis (Join)
```sql
SELECT 
    a.*,
    aa.subject,
    aa.category,
    aa.summary,
    aa.entities,
    aa.sentiment,
    aa.industry_affiliation
FROM articles a
LEFT JOIN article_analysis aa ON a.id = aa.article_id
WHERE a.article_id = 'PMID12345';
```

### Get All Articles Pending Analysis
```sql
SELECT a.id, a.article_id, a.title, a.abstract
FROM articles a
LEFT JOIN article_analysis aa ON a.id = aa.article_id
WHERE aa.id IS NULL
  AND a.ingestion_status = 'processed'
ORDER BY a.publication_date DESC;
```

### Filter by Sentiment and Entity
```sql
SELECT a.title, a.journal, aa.sentiment, aa.entities
FROM articles a
JOIN article_analysis aa ON a.id = aa.article_id
WHERE aa.sentiment = 'Positive'
  AND JSON_EXTRACT(aa.entities, '$') LIKE '%youth%'
ORDER BY a.publication_date DESC;
```

### Full-Text Search
```sql
-- SQLite FTS5
SELECT a.article_id, a.title, a.journal
FROM articles_fts fts
JOIN articles a ON fts.rowid = a.rowid
WHERE articles_fts MATCH 'tobacco harm reduction'
ORDER BY rank;

-- PostgreSQL
SELECT article_id, title, journal
FROM articles
WHERE to_tsvector('english', title || ' ' || abstract) @@ to_tsquery('tobacco & harm & reduction')
ORDER BY ts_rank(to_tsvector('english', title || ' ' || abstract), to_tsquery('tobacco & harm & reduction')) DESC;
```

---

## API Response Format (v1.0 Compatible)

To maintain backward compatibility, the API can return v1.0 format:

### GET /api/v1/articles/{article_id}

**Response (v1.0 format):**
```json
{
  "articleID": "PMID12345",
  "title": "Effects of E-Cigarettes on Youth",
  "journal": "Tobacco Control",
  "date": "2024-01-15",
  "abstract": "This study examines...",
  "entity": ["youth", "vaping", "e-cigarettes"],
  "subject": "E-cigarettes",
  "summary": "This research found that...",
  "category": "Epidemiology",
  "country": "United States",
  "sentiment": "Neutral",
  "industry_affiliation": "n/a"
}
```

**Backend Code (Pydantic model conversion):**
```python
from app.schemas.schema import Response, EntityEnum, SubjectEnum, CategoryEnum, SentimentEnum

def to_v1_response(article: Article, analysis: ArticleAnalysis) -> Response:
    """Convert v2.0 SQL objects to v1.0 Pydantic Response"""
    return Response(
        articleID=article.article_id,
        title=article.title,
        journal=article.journal or '',
        date=article.publication_date or '',
        abstract=article.abstract or '',
        entity=[EntityEnum(e) for e in json.loads(analysis.entities)],
        subject=SubjectEnum(analysis.subject),
        summary=analysis.summary or '',
        category=CategoryEnum(analysis.category),
        country=article.country or 'n/a',
        sentiment=SentimentEnum(analysis.sentiment),
        industry_affiliation=analysis.industry_affiliation or 'n/a'
    )
```

---

## Migration Script Example

**Minimal Migration (DocumentDB → SQLite):**

```python
from pymongo import MongoClient
import sqlite3
import json
from datetime import datetime

# Connect
mongo = MongoClient("mongodb://localhost:27017")
mongo_db = mongo["tobacco_research"]
articles_collection = mongo_db["articles"]

sqlite_conn = sqlite3.connect("articles.db")

# Migrate
for doc in articles_collection.find():
    # Insert into articles table
    sqlite_conn.execute("""
        INSERT INTO articles (
            id, article_id, source, source_metadata_id, doi, url,
            ingestion_status, article_type, title, abstract, journal,
            keywords, authors, publication_date, country
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        str(doc['_id']),
        doc.get('articleID', ''),
        doc.get('articleSource', 'unknown'),
        doc.get('metadataID', ''),
        doc.get('articleDOI', ''),
        doc.get('URL', ''),
        doc.get('status', 'processed'),
        doc.get('Type', 'research'),
        doc.get('articleTitle', ''),
        doc.get('abstracts', ''),
        doc.get('journal', ''),
        json.dumps(doc.get('keywords', [])),
        json.dumps(doc.get('authors', [])),
        doc.get('articlePublishDate', ''),
        doc.get('countryOfStudy', 'n/a')
    ))
    
    # Insert into article_analysis table (if analyzed)
    if doc.get('summary'):
        sqlite_conn.execute("""
            INSERT INTO article_analysis (
                id, article_id, subject, category, summary, entities,
                sentiment, industry_affiliation, coi_details,
                citation_string, model_id, prompt_version, analyzed_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            str(doc['_id']) + '_analysis',
            str(doc['_id']),
            doc.get('subject', ''),
            doc.get('scientificCategory', ''),
            doc.get('summary', ''),
            json.dumps(doc.get('entitiesSummarized', [])),
            doc.get('sentimentTowardsTHR', ''),
            doc.get('affiliatedCompany', 'n/a'),
            doc.get('COI', ''),
            doc.get('Reference', ''),
            doc.get('modelID', ''),
            doc.get('promptVersion', ''),
            doc.get('generatedAt', datetime.utcnow()).isoformat()
        ))

sqlite_conn.commit()
print("Migration complete!")
```

---

## Key Takeaways

1. **Two-Table Design:** Clean separation between ingestion (Data Engineer) and analysis (GenAI)
2. **JSON Storage:** Complex arrays stored as JSON for flexibility
3. **Backward Compatible:** Can recreate v1.0 Response format from SQL data
4. **Future-Proof:** New fields added without breaking existing schema
5. **Database Agnostic:** Works with SQLite (dev) and PostgreSQL (prod) via SQLAlchemy

---

## Next Steps

1. **Run Migration:** Use `scripts/migrate_documentdb_to_sqlite.py`
2. **Verify Data:** Check row counts and sample queries
3. **Test API:** Ensure v1.0 endpoints return same data
4. **Build New Features:** Start using v2.0 schema for advanced features

See:
- `05-DATA_INGESTION_PIPELINE.md` - Full migration script
- `MIGRATION_GUIDE.md` - Code-level migration guide
- `03-TECHNICAL_REQUIREMENTS.md` - Database architecture details
