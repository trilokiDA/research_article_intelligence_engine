# API Reference

**Version:** 1.0  
**Last Updated:** 2026-07-30

This document provides complete reference for CLI commands and Python API.

---

## CLI Commands

### Ingestion CLI (`ingest_cli.py`)

#### `init`
Initialize database with tables and indexes.

```bash
python ingest_cli.py init
```

**Output:**
- Creates `data/articles.db`
- Creates tables: `articles`, `article_analysis`, `articles_fts`
- Creates indexes for performance

---

#### `topics`
List all available predefined topic queries.

```bash
python ingest_cli.py topics
```

**Output:**
```
======================================================================
[CONFIG] AVAILABLE TOPIC QUERIES
======================================================================

Heat-Not-Burn
  Description: Heated tobacco products (IQOS, HEETS, THS)
  Sources:
    - pubmed: (((eclipse OR accord OR "Heatstick"...
    
E-Cigarettes
  Description: Electronic cigarettes, vaping, ENDS
  ...
```

---

#### `topic`
Search using predefined topic query.

```bash
python ingest_cli.py topic <TOPIC_NAME> [OPTIONS]
```

**Arguments:**
- `TOPIC_NAME` - Name of predefined topic (case-sensitive)
  - Available: `Heat-Not-Burn`, `E-Cigarettes`, `Nicotine-Pouch`, `Snus`

**Options:**
- `--sources SOURCES` - Comma-separated list of sources (default: `pubmed`)
  - Currently available: `pubmed`
  - Disabled: `crossref` (no abstracts)
- `--max MAX` - Maximum results per source (default: `100`)
- `--from-date DATE` - Start date in YYYY-MM-DD format
- `--to-date DATE` - End date in YYYY-MM-DD format

**Examples:**
```bash
# Fetch Heat-Not-Burn research from 2024
python ingest_cli.py topic "Heat-Not-Burn" \
    --sources pubmed \
    --max 100 \
    --from-date 2024-01-01 \
    --to-date 2024-12-31

# Fetch recent E-Cigarettes research (no date filter)
python ingest_cli.py topic "E-Cigarettes" \
    --sources pubmed \
    --max 50
```

---

#### `search`
Search with custom query string.

```bash
python ingest_cli.py search "query" [OPTIONS]
```

**Arguments:**
- `query` - Search query string (PubMed syntax)

**Options:**
- Same as `topic` command

**Examples:**
```bash
# Simple query
python ingest_cli.py search "IQOS" \
    --sources pubmed \
    --max 50

# Complex query with Boolean operators
python ingest_cli.py search "electronic cigarettes AND adolescents" \
    --sources pubmed \
    --max 100 \
    --from-date 2024-01-01
```

**PubMed Query Syntax:**
- `AND` - Both terms required
- `OR` - Either term required
- `NOT` - Exclude term
- `"phrase"` - Exact phrase
- `*` - Wildcard (e.g., `cigarette*`)
- `[Title/Abstract]` - Field-specific search

---

#### `stats`
Show database statistics.

```bash
python ingest_cli.py stats
```

**Output:**
```
============================================================
[STATS] DATABASE STATISTICS
============================================================
Total articles: 150
Analyzed: 50
Pending analysis: 100

By source:
  pubmed: 150

By category (analyzed only):
  Clinical Studies: 25
  Epidemiology: 15
  Behavior Studies: 10
============================================================
```

---

#### `pending`
List articles pending GenAI analysis.

```bash
python ingest_cli.py pending [OPTIONS]
```

**Options:**
- `--limit LIMIT` - Maximum number of articles to show (default: all)

**Output:**
```
============================================================
[PENDING] ARTICLES PENDING ANALYSIS: 10
============================================================

PMID12345678
  Title: Electronic cigarette use among adolescents
  Journal: Journal of Public Health
  Date: 2024-05-15
  
PMID87654321
  Title: Heated tobacco products: A systematic review
  ...
```

---

### GenAI CLI (`backend/scripts/run_summarization.py`)

#### Basic Usage

```bash
python backend/scripts/run_summarization.py [OPTIONS]
```

#### Options

**Analysis Control:**
- `--stats-only` - Show statistics only, don't process articles
- `--limit N` - Process maximum N articles (default: all pending)
- `--dry-run` - Process but don't save results (testing)

**Model Configuration:**
- `--model MODEL` - Groq model to use (default: `llama-3.3-70b-versatile`)
  - Options: `llama-3.3-70b-versatile`, `llama-3.1-8b-instant`, `mixtral-8x7b-32768`

**Batch Configuration:**
- `--batch-size N` - Articles per batch (default: `10`)
- `--delay SECONDS` - Delay between batches in seconds (default: `1.0`)

**Output Configuration:**
- `--output-format FORMAT` - Output format (default: `files`)
  - `files` - Save to JSON files in `data/analysis/`
  - `database` - Save directly to database (legacy)
- `--analysis-dir DIR` - Output directory for JSON files (default: `data/analysis/`)

#### Examples

```bash
# Show statistics
python backend/scripts/run_summarization.py --stats-only

# Test with 5 articles (dry run)
python backend/scripts/run_summarization.py --limit 5 --dry-run

# Process all pending articles
python backend/scripts/run_summarization.py

# Use fast model for large batch
python backend/scripts/run_summarization.py \
    --model llama-3.1-8b-instant \
    --batch-size 20 \
    --limit 100

# Custom configuration
python backend/scripts/run_summarization.py \
    --model llama-3.3-70b-versatile \
    --batch-size 5 \
    --delay 2.0 \
    --limit 50 \
    --output-format files
```

#### Output

**Progress Display:**
```
Processing articles: 45%|████▌     | 45/100 [02:15<02:45, 0.33article/s]
```

**Statistics:**
```
================================================================================
SUMMARIZATION COMPLETE
================================================================================
Successfully processed: 95/100 articles
Failed: 5 articles
Time taken: 8m 23s

Failed articles:
  - PMID999999: Schema validation error after 3 retries
  - PMID888888: API timeout
  ...
================================================================================
```

---

### View Data CLI (`view_data.py`)

```bash
python view_data.py [OPTIONS]
```

#### Options

- `--stats` - Show statistics only
- `--format FORMAT` - Output format: `summary`, `detailed`, `json`
- `--limit N` - Maximum articles to show
- `--source SOURCE` - Filter by source (e.g., `pubmed`)
- `--analyzed` - Show only analyzed articles
- `--pending` - Show only pending articles

#### Examples

```bash
# Show statistics
python view_data.py --stats

# Show detailed view of first 10 articles
python view_data.py --format detailed --limit 10

# Show only analyzed articles
python view_data.py --analyzed --limit 20

# Show pending articles from PubMed
python view_data.py --pending --source pubmed
```

---

## Python API

### Ingestion Module

#### PubMedConnector

```python
from app.ingestion.pubmed_connector import PubMedConnector

# Initialize
connector = PubMedConnector()

# Search articles
results = connector.search(
    query="tobacco harm reduction",
    max_results=100,
    date_range={
        'from': '2024-01-01',
        'to': '2024-12-31'
    }
)

# Fetch article details
article = connector.fetch(pmid="12345678")
```

#### QueryManager

```python
from app.config.query_manager import QueryManager

# Initialize
manager = QueryManager()

# List available topics
topics = manager.list_topics()
# Returns: ['Heat-Not-Burn', 'E-Cigarettes', 'Nicotine-Pouch', 'Snus']

# Get query for specific topic
query = manager.get_query('E-Cigarettes', 'pubmed')
# Returns: "((\"electronic cigarettes*\"[Title/Abstract]) OR ...)"

# Get all queries for a topic
all_queries = manager.get_all_queries_for_topic('Heat-Not-Burn')
# Returns: {'pubmed': '...', 'google_scholar': '...'}
```

#### IngestionOrchestrator

```python
from app.ingestion.orchestrator import IngestionOrchestrator

# Initialize
orchestrator = IngestionOrchestrator()

# Ingest articles
results = orchestrator.ingest_from_query(
    query="tobacco harm reduction",
    sources=['pubmed'],
    max_per_source=100,
    date_range={'from': '2024-01-01', 'to': '2024-12-31'}
)

# Returns:
# {
#     'total': 100,
#     'duplicates': 5,
#     'by_source': {'pubmed': 95}
# }

# Get pending articles
pending = orchestrator.get_pending_articles(limit=50)
for article in pending:
    print(f"{article['article_id']}: {article['title']}")
```

---

### GenAI Module

#### ArticleSummarizer

```python
from app.genai.summarizer import ArticleSummarizer

# Initialize
summarizer = ArticleSummarizer(model="llama-3.3-70b-versatile")

# Summarize single article
result = summarizer.summarize_article(
    doc_id="PMID12345678",
    title="Article title here",
    journal="Journal name",
    date="2024-01-15",
    abstract="Article abstract text..."
)

# Returns Response object with:
# - articleID
# - title, journal, date, abstract
# - entity (list)
# - subject
# - summary
# - category
# - country
# - sentiment
# - industry_affiliation
```

#### SummarizationPipeline

```python
from app.genai.pipeline import SummarizationPipeline

# Initialize
pipeline = SummarizationPipeline(
    model="llama-3.3-70b-versatile",
    batch_size=10,
    output_format="files",
    analysis_dir="data/analysis/"
)

# Run pipeline
stats = pipeline.run(
    limit=100,
    dry_run=False
)

# Returns:
# {
#     'total': 100,
#     'successful': 95,
#     'failed': 5,
#     'skipped': 0,
#     'time_taken': 502.3
# }
```

#### ArticleRepository

```python
from app.genai.repository import ArticleRepository

# Initialize
repo = ArticleRepository()

# Get pending articles
pending = repo.get_articles_pending_analysis(limit=100)

# Get articles for batch processing
batch = repo.get_articles_for_batch(
    batch_size=10,
    offset=0
)

# Get statistics
stats = repo.get_analysis_stats()
# Returns:
# {
#     'total': 500,
#     'analyzed': 400,
#     'pending': 100,
#     'failed': 0
# }
```

---

### Database Module

#### Database Connection

```python
from app.db.database import get_db

# Use context manager
with get_db() as db:
    cursor = db.execute("SELECT COUNT(*) FROM articles")
    count = cursor.fetchone()[0]
    print(f"Total articles: {count}")
```

#### Initialize Database

```python
from app.db.database import init_db

# Initialize all tables
init_db()
```

---

## JSON Output Format

### GenAI Analysis Output (`data/analysis/{article_id}.json`)

```json
{
  "articleID": "PMID12345678",
  "title": "Electronic cigarette use among adolescents: A cross-sectional study",
  "journal": "Journal of Public Health",
  "date": "2024-05-15",
  "abstract": "Background: E-cigarettes have become increasingly popular...",
  "entity": [
    "electronic cigarettes",
    "youth",
    "prevalence",
    "risk factors"
  ],
  "subject": "E-cigarettes",
  "summary": "This study examined e-cigarette use among adolescents aged 13-17...",
  "category": "Epidemiology",
  "country": "United States",
  "sentiment": "Negative",
  "industry_affiliation": "n/a"
}
```

**Fields:**
- `articleID` - PMID or DOI
- `title` - Original article title
- `journal` - Journal name
- `date` - Publication date (YYYY-MM-DD)
- `abstract` - Original abstract
- `entity` - List of extracted entities (topics, products, etc.)
- `subject` - Broad subject category (E-cigarettes, HTPs, etc.)
- `summary` - Plain-language summary with people-first language
- `category` - Research category (Clinical Studies, Epidemiology, etc.)
- `country` - Study location or first author country
- `sentiment` - THR sentiment (Positive, Negative, Neutral, Mixed, Unclear)
- `industry_affiliation` - Industry affiliation if detected (PMI, JTI, BAT, etc.) or "n/a"

---

## Environment Variables

Required environment variables in `.env` file:

```env
# PubMed Configuration
NCBI_EMAIL=your-email@example.com          # Required
NCBI_API_KEY=your-api-key-here             # Optional (recommended)

# Groq Configuration
GROQ_API_KEY=your-groq-api-key-here        # Required for GenAI

# Crossref Configuration (Optional - connector disabled)
CROSSREF_EMAIL=your-email@example.com

# Database
DATABASE_URL=sqlite:///./data/articles.db  # Default
```

---

## Error Codes & Messages

### Ingestion Errors

| Error | Cause | Solution |
|-------|-------|----------|
| `"No module named 'Bio'"` | Biopython not installed | `pip install biopython` |
| `"PubMed API rate limit exceeded"` | Too many requests | Get NCBI API key or reduce request rate |
| `"Invalid date format"` | Date not in YYYY-MM-DD | Use correct format |
| `"Database is locked"` | Concurrent writes | Close other connections to SQLite |

### GenAI Errors

| Error | Cause | Solution |
|-------|-------|----------|
| `"GROQ_API_KEY not found"` | API key not set | Add key to `.env` file |
| `"Schema validation error"` | LLM output doesn't match schema | Auto-retry 3 times, check prompt |
| `"File write error"` | Permissions or disk space | Check file permissions and disk space |
| `"No articles need processing"` | No pending articles | Run ingestion first |

---

## Performance Characteristics

### Ingestion
- **PubMed Rate:** 3 req/sec (default), 10 req/sec (with API key)
- **Throughput:** ~600-2000 articles/minute
- **Bottleneck:** API rate limits

### GenAI Analysis
- **Model Speed:**
  - `llama-3.3-70b-versatile`: ~3-5 seconds/article
  - `llama-3.1-8b-instant`: ~1-2 seconds/article
- **Throughput:** ~120-600 articles/hour
- **Bottleneck:** LLM inference time

---

## Rate Limits

### PubMed
- **Without API key:** 3 requests/second
- **With API key:** 10 requests/second
- **Recommendation:** Get API key for production use

### Groq
- **Free Tier:** Generous limits (check current limits at console.groq.com)
- **Recommendation:** Monitor usage, add delays if hitting limits

---

**For more information:**
- [README.md](../README.md) - Getting started
- [DEVELOPMENT.md](../DEVELOPMENT.md) - Setup and development
- [ARCHITECTURE.md](../ARCHITECTURE.md) - System design
