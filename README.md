# Tobacco Research Platform - Backend

Data ingestion pipeline for collecting scientific articles from PubMed, Crossref, and Google Scholar.

## Quick Start

### 1. Install Dependencies

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (Linux/Mac)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit .env and add your API keys:
# - ANTHROPIC_API_KEY (for GenAI analysis)
# - NCBI_API_KEY (optional, for faster PubMed access)
# - CROSSREF_EMAIL (for polite pool)
```

### 3. Initialize Database

```bash
python ingest_cli.py init
```

This creates `data/articles.db` with the following tables:
- `articles` - Raw article metadata from ingestion
- `article_analysis` - GenAI analysis results
- `articles_fts` - Full-text search index

### 4. Ingest Articles

```bash
# Search PubMed for articles
python ingest_cli.py search "tobacco harm reduction" \
    --sources pubmed \
    --max 50 \
    --from-date 2024-01-01 \
    --to-date 2024-12-31

# Search both PubMed and Crossref
python ingest_cli.py search "electronic cigarettes youth" \
    --sources pubmed crossref \
    --max 100
```

### 5. Check Status

```bash
# View database statistics
python ingest_cli.py stats

# View articles pending GenAI analysis
python ingest_cli.py pending --limit 10
```

## Usage Examples

### Ingest Recent Articles

```bash
# Last 6 months of tobacco harm reduction research
python ingest_cli.py search "tobacco harm reduction" \
    --sources pubmed crossref \
    --max 200 \
    --from-date 2024-01-01 \
    --to-date 2024-06-30
```

### Specific Topics

```bash
# IQOS research
python ingest_cli.py search "IQOS OR heated tobacco products" \
    --sources pubmed \
    --max 50

# Youth vaping studies
python ingest_cli.py search "e-cigarettes AND adolescents" \
    --sources pubmed crossref \
    --max 100
```

### Check Database

```bash
# Statistics
python ingest_cli.py stats

# Output:
# 📊 DATABASE STATISTICS
# ==========================================
# Total articles: 150
# Analyzed: 0
# Pending analysis: 150
#
# By source:
#   pubmed: 100
#   crossref: 50
```

## CLI Commands

### `init`
Initialize database (create tables and indexes).

```bash
python ingest_cli.py init
```

### `search`
Search and ingest articles from external sources.

```bash
python ingest_cli.py search "query" [OPTIONS]

Options:
  --sources SOURCES     Sources to search (pubmed, crossref, google_scholar)
  --max MAX             Maximum results per source (default: 100)
  --from-date DATE      Start date (YYYY-MM-DD)
  --to-date DATE        End date (YYYY-MM-DD)
```

### `stats`
Show database statistics.

```bash
python ingest_cli.py stats
```

### `pending`
Show articles pending GenAI analysis.

```bash
python ingest_cli.py pending [--limit LIMIT]
```

## Data Sources

### PubMed
- **Coverage:** 35M+ biomedical articles
- **Rate Limit:** 3 req/sec (10 req/sec with API key)
- **API Key:** Get from https://www.ncbi.nlm.nih.gov/account/
- **Cost:** FREE

### Crossref
- **Coverage:** 130M+ scholarly articles
- **Rate Limit:** 50 req/sec (polite pool with email)
- **Email:** Set CROSSREF_EMAIL in .env
- **Cost:** FREE

### Google Scholar (Coming Soon)
- **Coverage:** 500M+ articles
- **Rate Limit:** ~100 req/hour (use cautiously)
- **Note:** No official API, uses scraping
- **Cost:** FREE

## Database Schema

### `articles` table
Stores raw article metadata from ingestion.

```sql
CREATE TABLE articles (
    id TEXT PRIMARY KEY,
    article_id TEXT UNIQUE NOT NULL,  -- External ID (PMID, DOI)
    source TEXT NOT NULL,              -- pubmed, crossref, scholar
    title TEXT NOT NULL,
    abstract TEXT,
    journal TEXT,
    authors TEXT,                      -- JSON array
    keywords TEXT,                     -- JSON array
    publication_date TEXT,             -- YYYY-MM-DD
    country TEXT,
    doi TEXT,
    url TEXT,
    ingestion_status TEXT,             -- pending, processed, failed
    ...
);
```

### `article_analysis` table
Stores GenAI analysis results (populated by separate analysis pipeline).

```sql
CREATE TABLE article_analysis (
    id TEXT PRIMARY KEY,
    article_id TEXT UNIQUE NOT NULL,
    subject TEXT,                      -- SubjectEnum
    category TEXT,                     -- CategoryEnum
    summary TEXT,                      -- Plain-language summary
    entities TEXT,                     -- JSON array of EntityEnum
    sentiment TEXT,                    -- SentimentEnum
    industry_affiliation TEXT,
    ...
    FOREIGN KEY (article_id) REFERENCES articles(id)
);
```

## Python API

You can also use the ingestion components programmatically:

```python
from app.ingestion.orchestrator import IngestionOrchestrator

# Initialize
orchestrator = IngestionOrchestrator()

# Ingest articles
results = orchestrator.ingest_from_query(
    query="tobacco harm reduction",
    sources=['pubmed', 'crossref'],
    max_per_source=100,
    date_range={'from': '2024-01-01', 'to': '2024-12-31'}
)

print(f"Stored: {results['total']} articles")
print(f"Duplicates: {results['duplicates']}")

# Get pending articles
pending = orchestrator.get_pending_articles(limit=50)
for article in pending:
    print(f"{article['article_id']}: {article['title']}")
```

## Troubleshooting

### "No module named Bio"
```bash
pip install biopython
```

### "Database is locked"
SQLite only allows one writer at a time. If you see this error:
1. Close any other connections to the database
2. Or upgrade to PostgreSQL for production

### "PubMed API key not working"
1. Verify key at https://www.ncbi.nlm.nih.gov/account/
2. Set NCBI_API_KEY in .env
3. Restart the script

### "Rate limit exceeded"
- PubMed: Get API key for 10 req/sec
- Crossref: Set email in User-Agent for polite pool
- Scholar: Reduce frequency or use proxy rotation

## Next Steps

1. **Migrate existing data:** See `docs/05-DATA_INGESTION_PIPELINE.md` for DocumentDB migration script
2. **Run GenAI analysis:** See `docs/MIGRATION_GUIDE.md` for analysis pipeline
3. **Build frontend:** See `docs/QUICK_START.md` for full setup

## Directory Structure

```
backend/
├── app/
│   ├── db/
│   │   └── database.py           # Database connection
│   ├── ingestion/
│   │   ├── pubmed_connector.py   # PubMed API
│   │   ├── crossref_connector.py # Crossref API
│   │   ├── normalizer.py         # Data normalization
│   │   └── orchestrator.py       # Multi-source coordination
│   └── schemas/
│       └── schema.py              # Pydantic models (from v1.0)
├── ingest_cli.py                 # Command-line interface
├── requirements.txt
└── .env.example
```

## Contributing

See `docs/04-IMPLEMENTATION_ROADMAP.md` for the full project roadmap.
