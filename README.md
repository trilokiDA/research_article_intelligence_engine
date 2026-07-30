# Research Article Intelligence Engine

AI-powered platform for collecting, analyzing, and summarizing scientific research articles.

## 🎯 Current Status

**Version:** 1.0 (Ingestion + GenAI Analysis)  
**What Works:** PubMed ingestion, topic-based queries, file-based GenAI summarization  
**Next Phase:** Evaluation pipeline, revalidation, re-inference capabilities

## Features

- 📥 **PubMed Ingestion** - Collect articles from PubMed with topic-based queries
- ⚠️ **Crossref (Disabled)** - Available but commented out (no abstracts returned)
- 🤖 **AI-Powered Analysis** - Automatic summarization using Groq LLMs (file-based)
- 📊 **Structured Data** - Entity extraction, sentiment analysis, and categorization
- 🔍 **Full-Text Search** - SQLite FTS5 for fast article search
- 🎯 **Smart Filtering** - Skip already-analyzed articles automatically

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

# Edit .env and add your keys:
# - GROQ_API_KEY (for GenAI analysis)
# - NCBI_EMAIL (required for PubMed)
# - NCBI_API_KEY (optional, for faster PubMed access)
```

Get PubMed API key: https://www.ncbi.nlm.nih.gov/account/  
Get Groq API key: https://console.groq.com/keys (free tier available)

### 3. Initialize Database

```bash
python ingest_cli.py init
```

This creates `data/articles.db` with:
- `articles` - Raw article metadata from ingestion
- `article_analysis` - GenAI analysis results
- `articles_fts` - Full-text search index

### 4. Ingest Articles

#### Topic-Based Queries (Recommended)

```bash
# List available topics
python ingest_cli.py topics

# Search using predefined topic queries
python ingest_cli.py topic "Heat-Not-Burn" \
    --sources pubmed \
    --from-date 2024-01-01 \
    --to-date 2024-12-31 \
    --max 50

# Available topics:
# - Heat-Not-Burn (IQOS, HEETS, THS)
# - E-Cigarettes (vaping, ENDS)
# - Nicotine-Pouch
# - Snus
```

#### Custom Queries

```bash
# Search PubMed with custom query
python ingest_cli.py search "tobacco harm reduction" \
    --sources pubmed \
    --from-date 2024-01-01 \
    --to-date 2024-12-31 \
    --max 50
```

### 5. Run GenAI Analysis

The GenAI pipeline analyzes articles and saves results to JSON files (one per article).

```bash
# Check pending articles
python backend/scripts/run_summarization.py --stats-only

# Process 10 articles (dry run)
python backend/scripts/run_summarization.py --limit 10 --dry-run

# Process all pending articles (saves to data/analysis/)
python backend/scripts/run_summarization.py

# Custom configuration
python backend/scripts/run_summarization.py \
    --model llama-3.1-8b-instant \
    --batch-size 5 \
    --limit 50
```

**Output Format:** Each analyzed article produces a JSON file in `data/analysis/` containing:
- Summary (people-first language)
- Entities (topics, products)
- Category (research type)
- Sentiment (THR stance)
- Country, industry affiliation, etc.

**Smart Skip:** Already-analyzed articles (with existing JSON files) are automatically skipped.

### 6. Check Status

```bash
# View database statistics
python ingest_cli.py stats

# View articles pending analysis
python ingest_cli.py pending --limit 10

# View analyzed articles
python view_data.py --stats
python view_data.py --format detailed --limit 10
```

## Usage Examples

### Monthly Research Update

```bash
# Fetch last month's research for all topics
python ingest_cli.py topic "Heat-Not-Burn" \
    --sources pubmed \
    --max 50 \
    --from-date 2024-07-01 \
    --to-date 2024-07-31

python ingest_cli.py topic "E-Cigarettes" \
    --sources pubmed \
    --max 50 \
    --from-date 2024-07-01 \
    --to-date 2024-07-31

# Analyze all pending articles
python backend/scripts/run_summarization.py

# Check results
python ingest_cli.py stats
```

### Historical Backfill

```bash
# Fetch all 2024 research for specific topic
python ingest_cli.py topic "Heat-Not-Burn" \
    --sources pubmed \
    --max 500 \
    --from-date 2024-01-01 \
    --to-date 2024-12-31

# Analyze in batches
python backend/scripts/run_summarization.py --batch-size 10
```

### Specific Research Areas

```bash
# IQOS research
python ingest_cli.py search "IQOS OR heated tobacco products" \
    --sources pubmed \
    --max 50

# Youth vaping studies
python ingest_cli.py search "e-cigarettes AND adolescents" \
    --sources pubmed \
    --max 100
```

## CLI Commands

### Ingestion Commands

#### `init`
Initialize database (create tables and indexes).

```bash
python ingest_cli.py init
```

#### `topics`
List available predefined topic queries.

```bash
python ingest_cli.py topics
```

#### `topic`
Search using predefined topic query.

```bash
python ingest_cli.py topic <TOPIC_NAME> [OPTIONS]

Options:
  --sources SOURCES     Sources to search (currently: pubmed)
  --max MAX             Maximum results (default: 100)
  --from-date DATE      Start date (YYYY-MM-DD)
  --to-date DATE        End date (YYYY-MM-DD)
```

#### `search`
Search with custom query.

```bash
python ingest_cli.py search "query" [OPTIONS]

Options:
  --sources SOURCES     Sources to search (currently: pubmed)
  --max MAX             Maximum results (default: 100)
  --from-date DATE      Start date (YYYY-MM-DD)
  --to-date DATE        End date (YYYY-MM-DD)
```

#### `stats`
Show database statistics.

```bash
python ingest_cli.py stats
```

#### `pending`
Show articles pending GenAI analysis.

```bash
python ingest_cli.py pending [--limit LIMIT]
```

### GenAI Analysis Commands

#### `run_summarization.py`
Process articles through GenAI pipeline.

```bash
python backend/scripts/run_summarization.py [OPTIONS]

Options:
  --stats-only              Show statistics only
  --limit N                 Process max N articles
  --dry-run                 Process but don't save
  --model MODEL             Groq model (default: llama-3.3-70b-versatile)
  --batch-size N            Articles per batch (default: 10)
  --output-format FORMAT    'files' (default) or 'database'
  --analysis-dir DIR        Output directory (default: data/analysis/)
```

## GenAI Pipeline

### How It Works

1. **Fetch** - Get articles where analysis JSON doesn't exist
2. **Process** - Send to Groq LLM with structured output
3. **Validate** - Pydantic validates against schema
4. **Save** - Write JSON file to `data/analysis/{article_id}.json`
5. **Skip** - Already-analyzed articles are automatically skipped

### Output Schema

Each article produces a JSON file:

```json
{
  "articleID": "PMID12345678",
  "title": "Original article title",
  "journal": "Journal name",
  "date": "2024-01-15",
  "abstract": "Original abstract text",
  "entity": ["electronic cigarettes", "harm reduction"],
  "subject": "E-cigarettes",
  "summary": "People-first language summary...",
  "category": "Clinical Studies",
  "country": "United States",
  "sentiment": "Positive",
  "industry_affiliation": "n/a"
}
```

### Available Models

- `llama-3.3-70b-versatile` - **Recommended** (best quality)
- `llama-3.1-8b-instant` - Fast (lower quality)
- `mixtral-8x7b-32768` - Alternative

See detailed documentation: [docs/GENAI_PIPELINE.md](docs/GENAI_PIPELINE.md)

## Data Sources

### PubMed ✅
- **Coverage:** 35M+ biomedical articles
- **Rate Limit:** 3 req/sec (10 req/sec with API key)
- **API Key:** Get from https://www.ncbi.nlm.nih.gov/account/
- **Cost:** FREE
- **Status:** Active

### Crossref ⚠️
- **Coverage:** 130M+ scholarly articles
- **Rate Limit:** 50 req/sec (polite pool with email)
- **Cost:** FREE
- **Status:** **Disabled** (returns no abstracts, making analysis impossible)
- **Note:** Code available but commented out in codebase

### Google Scholar ❌
- **Status:** Not implemented
- **Note:** Planned for future version

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
    ingested_at DATETIME,
    updated_at DATETIME
);
```

### `article_analysis` table
Stores GenAI analysis results (populated by GenAI pipeline).

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
    analysis_status TEXT,              -- pending, completed, failed
    analyzed_at DATETIME,
    FOREIGN KEY (article_id) REFERENCES articles(id)
);
```

## Python API

You can also use the components programmatically:

```python
from app.ingestion.orchestrator import IngestionOrchestrator
from app.config.query_manager import QueryManager

# Initialize
orchestrator = IngestionOrchestrator()
query_manager = QueryManager()

# Get predefined topic query
query = query_manager.get_query('E-Cigarettes', 'pubmed')

# Ingest articles
results = orchestrator.ingest_from_query(
    query=query,
    sources=['pubmed'],
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

### "GROQ_API_KEY not found"
1. Get key from https://console.groq.com/keys
2. Add to .env file: `GROQ_API_KEY=your-key-here`
3. Restart the script

### "Rate limit exceeded"
- PubMed: Get API key for 10 req/sec
- Add delays with `--batch-size` and reduce `--max`

### "No articles need processing"
- Run ingestion first: `python ingest_cli.py topic "Heat-Not-Burn" --max 10`
- Check: `python ingest_cli.py stats`

## Project Structure

```
radar/
├── backend/
│   ├── app/
│   │   ├── db/
│   │   │   └── database.py           # Database connection
│   │   ├── ingestion/
│   │   │   ├── pubmed_connector.py   # PubMed API
│   │   │   ├── crossref_connector.py # Crossref (disabled)
│   │   │   ├── normalizer.py         # Data normalization
│   │   │   └── orchestrator.py       # Multi-source coordination
│   │   ├── genai/
│   │   │   ├── pipeline.py           # Analysis orchestration
│   │   │   ├── summarizer.py         # Groq LLM integration
│   │   │   ├── repository.py         # Database access
│   │   │   ├── schemas.py            # Pydantic models
│   │   │   └── prompts.py            # LLM prompts
│   │   └── config/
│   │       ├── query_manager.py      # Topic query loader
│   │       └── search_queries.json   # Predefined queries
│   ├── scripts/
│   │   └── run_summarization.py      # GenAI CLI
│   ├── ingest_cli.py                 # Ingestion CLI
│   └── requirements.txt
├── data/
│   ├── articles.db                   # SQLite database
│   └── analysis/                     # GenAI output (JSON files)
├── docs/
│   ├── GENAI_PIPELINE.md            # GenAI implementation
│   └── SCHEMA_MAPPING.md            # Database schema
└── README.md                        # This file
```

## Documentation

- **GenAI Pipeline:** [docs/GENAI_PIPELINE.md](docs/GENAI_PIPELINE.md)
- **Database Schema:** [docs/SCHEMA_MAPPING.md](docs/SCHEMA_MAPPING.md)
- **Full Project Docs:** [docs/](docs/)

## Roadmap

### Current (v1.0) ✅
- PubMed ingestion with topic queries
- File-based GenAI analysis
- Skip logic for existing summaries
- Structured output validation

### In Progress (v1.1)
- Evaluation pipeline
- Revalidation workflow
- Re-inference capabilities

### Planned (v2.0)
- Advanced RAG Q&A across corpus
- Citation network analysis
- Multi-document synthesis
- Interactive web UI
- Real-time monitoring

See [ROADMAP.md](ROADMAP.md) for detailed future plans.

## Contributing

See documentation in `docs/` for implementation details.

## License

[Your License Here]
