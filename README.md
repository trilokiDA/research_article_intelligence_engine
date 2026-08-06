# Research Article Intelligence Engine

AI-powered platform for collecting, analyzing, and summarizing scientific research articles.

## 🎯 Current Status

**Version:** 1.1 (5-Stage Pipeline)  
**What Works:** PubMed ingestion, GenAI summarization, evaluation pipeline, re-inference workflow  
**Architecture:** Raw → Evaluate → Approved/Re-infer → Re-evaluate → Approved/Rejected

## Features

- 📥 **PubMed Ingestion** - Collect articles from PubMed with topic-based queries
- ⚠️ **Crossref (Disabled)** - Available but commented out (no abstracts returned)
- 🤖 **AI-Powered Analysis** - Automatic summarization using Groq LLMs
- 📊 **Structured Data** - Entity extraction, sentiment analysis, and categorization
- ✅ **Quality Evaluation** - Automated evaluation with factual accuracy checks, hallucination detection, and people-first language validation
- 🔄 **Re-inference Loop** - Failed summaries are re-generated with feedback (max 3 attempts)
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

### 5. Run GenAI Analysis (5-Stage Pipeline)

The GenAI pipeline uses a 5-stage quality-controlled workflow:

**Stage 1:** Data Ingestion → SQLite  
**Stage 2:** GenAI Summarization → `raw/`  
**Stage 3:** Quality Evaluation → `approved/` or `reinfer/`  
**Stage 4:** Re-inference (if needed) → Re-evaluate → `approved/` or `rejected/`  
**Stage 5:** Database Load → `article_analysis` table

#### Stage 2: Generate Summaries

```bash
# Process articles and save to raw/ directory
python backend/scripts/run_summarization.py --limit 10

# Custom configuration
python backend/scripts/run_summarization.py \
    --model llama-3.3-70b-versatile \
    --batch-size 5 \
    --limit 50
```

#### Stage 3: Evaluate Quality

```bash
# Evaluate and route summaries
python scripts/evaluate_summaries.py --source raw --limit 10

# Custom threshold (default: 80%)
python scripts/evaluate_summaries.py --source raw --threshold 85
```

**Evaluation:** Factual accuracy, hallucination detection, people-first language  
**Routing:** Quality ≥80% → `approved/`, <80% → `reinfer/`

#### Stage 4: Re-inference (Optional)

```bash
# Re-infer failed summaries with evaluation feedback
python scripts/reinfer_summaries.py

# Dry run to preview
python scripts/reinfer_summaries.py --dry-run
```

**Re-inference:** Re-run with feedback → Re-evaluate → `approved/` or `rejected/` (max 3 attempts)

#### Stage 5: Load to Database

```bash
# Load all approved summaries to database
python scripts/load_to_database.py

# Load and archive source files
python scripts/load_to_database.py --archive

# Dry run (validate without committing)
python scripts/load_to_database.py --dry-run

# Load specific articles
python scripts/load_to_database.py --article-id PMID001 PMID002
```

**Database Load:** Approved summaries → `article_analysis` table → `loaded/` (archive)

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

### Full Pipeline Orchestrator (Recommended)

The easiest way to run the complete workflow is using the full pipeline orchestrator:

```bash
# Complete 5-stage workflow (one command)
python scripts/full_pipeline.py --topic "Heat-Not-Burn" --max-articles 50 --archive

# Quick test run
python scripts/full_pipeline.py --topic "E-Cigarettes" --limit 10 --dry-run

# Custom stages only
python scripts/full_pipeline.py --stages summarize evaluate load --limit 20

# High quality threshold
python scripts/full_pipeline.py --topic "Nicotine-Pouch" --threshold 90 --max-articles 30
```

### Monthly Research Update (Manual Steps)

For more control, run each stage individually:

```bash
# Step 1: Ingest articles
python ingest_cli.py topic "Heat-Not-Burn" --sources pubmed --max 50

# Step 2: Generate summaries (Stage 2)
python backend/scripts/run_summarization.py --limit 50

# Step 3: Evaluate quality (Stage 3)
python scripts/evaluate_summaries.py --source raw

# Step 4: Re-infer failed summaries (Stage 4)
python scripts/reinfer_summaries.py

# Step 5: Load to database (Stage 5)
python scripts/load_to_database.py --archive

# Step 6: Check results
python ingest_cli.py stats
```

### Historical Backfill

Using full pipeline orchestrator:

```bash
# Single command for complete backfill
python scripts/full_pipeline.py --topic "Heat-Not-Burn" --max-articles 500 --archive
```

Or manual steps:

```bash
# Fetch historical research
python ingest_cli.py topic "Heat-Not-Burn" --sources pubmed --max 500

# Process through 5-stage pipeline
python backend/scripts/run_summarization.py --batch-size 10
python scripts/evaluate_summaries.py --source raw
python scripts/reinfer_summaries.py
python scripts/load_to_database.py --archive
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

### Full Pipeline Orchestrator

#### `full_pipeline.py`

Run the complete 5-stage workflow with a single command.

```bash
python scripts/full_pipeline.py [OPTIONS]

Required (for ingestion):
  --topic TOPIC             Predefined topic name
  --query QUERY             Custom search query

Options:
  --stages STAGE [STAGE...] Stages to run (default: all)
                           Choices: ingest, summarize, evaluate, reinfer, load
  --max-articles N          Max articles to ingest (default: 100)
  --limit N                 Limit articles per processing stage
  --threshold N             Quality threshold 0-100 (default: 80)
  --from-date DATE          Start date YYYY-MM-DD
  --to-date DATE            End date YYYY-MM-DD
  --archive                 Archive loaded files
  --dry-run                 Validate without making changes
  --quiet                   Suppress verbose output

Examples:
  # Complete workflow
  python scripts/full_pipeline.py --topic "Heat-Not-Burn" --max-articles 50

  # Specific stages only
  python scripts/full_pipeline.py --stages summarize evaluate load --limit 20

  # Dry run
  python scripts/full_pipeline.py --topic "E-Cigarettes" --limit 10 --dry-run

  # High quality bar
  python scripts/full_pipeline.py --query "IQOS heated tobacco" --threshold 90
```

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

### GenAI Analysis Commands (5-Stage Pipeline)

#### Stage 2: `run_summarization.py`

```bash
python backend/scripts/run_summarization.py [OPTIONS]

Options:
  --limit N                 Process max N articles
  --model MODEL             Groq model (default: llama-3.3-70b-versatile)
  --batch-size N            Articles per batch (default: 10)
  --dry-run                 Process but don't save
```

#### Stage 3: `evaluate_summaries.py`

```bash
python scripts/evaluate_summaries.py [OPTIONS]

Options:
  --source SOURCE           'raw' or 'summarized' (default: raw)
  --threshold N             Quality threshold 0-100 (default: 80)
  --limit N                 Process max N files
  --dry-run                 Evaluate but don't save/move files
```

#### Stage 4: `reinfer_summaries.py`

```bash
python scripts/reinfer_summaries.py [OPTIONS]

Options:
  --max-attempts N          Max retry attempts (default: 3)
  --limit N                 Process max N files
  --dry-run                 Process but don't save/move files
```

#### Stage 5: `load_to_database.py`

```bash
python scripts/load_to_database.py [OPTIONS]

Options:
  --article-id ID [ID...]   Load specific article IDs
  --limit N                 Process max N files
  --dry-run                 Validate without committing to database
  --archive                 Move loaded files to archive directory
  --migrate-only            Only migrate database schema
  --stats                   Show database statistics
```

## GenAI Pipeline (5-Stage Architecture)

### How It Works

**Stage 1: Data Ingestion**  
PubMed API → Normalizer → SQLite

**Stage 2: GenAI Summarization**  
Fetch pending articles → Send to Groq LLM → Validate schema → Save to `raw/`

**Stage 3: Quality Evaluation**  
Load from `raw/` → Evaluate (factual accuracy, hallucination, people-first language) → Route: ≥80% → `approved/`, <80% → `reinfer/`

**Stage 4: Re-inference (If Needed)**  
Load from `reinfer/` → Re-run with feedback → Re-evaluate → Route: Pass → `approved/`, Fail (3x) → `rejected/`

**Stage 5: Database Load**  
Load from `approved/` → Transform JSON to SQL → Insert/update `article_analysis` table → Archive to `loaded/`

### File Structure

```
data/analysis/
├── raw/            # Stage 2: Initial GenAI outputs
├── approved/       # Passed quality gate (≥80%)
├── reinfer/        # Failed, awaiting retry (<80%)
├── rejected/       # Failed after max attempts
├── loaded/         # Stage 5: Successfully loaded to DB (archive)
└── summarized/     # Legacy
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

## Integration Testing

Run integration tests to validate the complete pipeline:

```bash
# Run all integration tests
pytest tests/test_integration.py -v

# Run specific test class
pytest tests/test_integration.py::TestFullPipelineIntegration -v

# Run with coverage
pytest tests/test_integration.py --cov=backend/app --cov-report=html
```

Integration tests cover:
- Stage-to-stage data flow
- End-to-end workflows (happy path and error scenarios)
- Data integrity across pipeline
- Error handling and rollback
- File routing (raw → approved/reinfer/rejected → loaded)

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

### "No files to evaluate"
- Run Stage 2 first: `python backend/scripts/run_summarization.py --limit 10`
- Check raw directory: `ls data/analysis/raw/`

### Import errors after updates
- Ensure all modules use relative imports (v1.1 update)
- Run from project root directory
- Restart Python environment if needed

### Pipeline orchestrator fails
- Check that all stage scripts are present
- Verify database and directory permissions
- Run with --dry-run to validate before execution
- Check logs for specific stage failures

### Integration tests failing
- Ensure pytest is installed: `pip install pytest pytest-cov`
- Check test database path and permissions
- Verify all dependencies are installed
- Run individual test classes to isolate issues

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
│   │   │   ├── pipeline.py           # Summarization pipeline (Stage 2)
│   │   │   ├── summarizer.py         # Groq LLM integration
│   │   │   ├── evaluator.py          # Quality evaluation (Stage 3)
│   │   │   ├── repository.py         # Database access
│   │   │   ├── db_loader.py          # Database loader (Stage 5)
│   │   │   ├── file_writer.py        # File routing (raw/approved/reinfer/rejected)
│   │   │   ├── schemas.py            # Pydantic models
│   │   │   ├── prompts.py            # LLM prompts
│   │   │   └── config.py             # Pipeline configuration
│   │   └── config/
│   │       ├── query_manager.py      # Topic query loader
│   │       └── search_queries.json   # Predefined queries
│   ├── scripts/
│   │   └── run_summarization.py      # Stage 2: Generate summaries
│   ├── ingest_cli.py                 # Ingestion CLI (Stage 1)
│   └── requirements.txt
├── scripts/
│   ├── full_pipeline.py              # Complete workflow orchestrator
│   ├── evaluate_summaries.py         # Stage 3: Quality evaluation
│   ├── reinfer_summaries.py          # Stage 4: Re-inference workflow
│   └── load_to_database.py           # Stage 5: Database load
├── tests/
│   ├── test_integration.py           # Integration tests (full pipeline)
│   ├── test_genai.py                 # GenAI unit tests
│   ├── test_evaluator_quick.py      # Evaluator tests
│   └── test_pubmed.py                # PubMed ingestion tests
├── data/
│   ├── articles.db                   # SQLite database
│   └── analysis/
│       ├── raw/                      # Stage 2 output
│       ├── approved/                 # Passed quality gate
│       ├── reinfer/                  # Awaiting retry
│       ├── rejected/                 # Failed max attempts
│       ├── loaded/                   # Archived after DB load
│       └── summarized/               # Legacy
├── docs/
│   ├── GENAI_PIPELINE.md            # GenAI implementation
│   ├── EVALUATOR_MODULE.md          # Evaluation pipeline
│   ├── STAGE_5_DATABASE_LOAD.md     # Database load documentation
│   ├── MIGRATION_TO_5_STAGE.md      # Migration plan
│   └── SCHEMA_REFERENCE.md          # Database schema
└── README.md                        # This file
```

## Documentation

- **GenAI Pipeline:** [docs/GENAI_PIPELINE.md](docs/GENAI_PIPELINE.md)
- **Evaluation Module:** [docs/EVALUATOR_MODULE.md](docs/EVALUATOR_MODULE.md)
- **Stage 5 Database Load:** [docs/STAGE_5_DATABASE_LOAD.md](docs/STAGE_5_DATABASE_LOAD.md)
- **5-Stage Migration:** [docs/MIGRATION_TO_5_STAGE.md](docs/MIGRATION_TO_5_STAGE.md)
- **Database Schema:** [docs/SCHEMA_REFERENCE.md](docs/SCHEMA_REFERENCE.md)
- **API Reference:** [docs/API_REFERENCE.md](docs/API_REFERENCE.md)
- **Full Project Docs:** [docs/](docs/)

## Roadmap

### Current (v1.1) ✅
- PubMed ingestion with topic queries
- Complete 5-stage quality-controlled pipeline
- GenAI summarization with structured output
- Evaluation with factual accuracy checks
- Re-inference workflow with feedback loop
- Automated quality routing (approved/reinfer/rejected)
- Database load with archiving and idempotency

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
