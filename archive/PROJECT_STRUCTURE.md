# Project Structure

## Overview

```
radar/
├── backend/
│   ├── app/
│   │   ├── config/           # Configuration and query management
│   │   ├── db/              # Database connections and schema
│   │   ├── genai/           # 🆕 AI/ML pipeline for article analysis
│   │   ├── ingestion/       # Data collection from external sources
│   │   └── schemas/         # Pydantic models (if any)
│   └── scripts/             # CLI tools and utilities
├── data/                     # SQLite database and artifacts
├── docs/                     # 🆕 Documentation
├── tests/                    # 🆕 Test suites
├── .env                      # Environment variables (gitignored)
├── .env.example             # Template for environment setup
├── requirements.txt         # Python dependencies
└── README.md               # Main documentation
```

## Backend Structure

### `backend/app/`

Core application modules:

#### `config/`
- `query_manager.py` - Search query templates and management

#### `db/`
- `database.py` - SQLite connection, schema initialization, statistics

#### `genai/` 🆕
AI-powered article analysis pipeline:

```
genai/
├── __init__.py           # Module exports
├── schemas.py            # Pydantic models (Response, Enums)
├── prompts.py            # LLM prompt templates
├── summarizer.py         # Core summarization logic (Groq + LangChain)
├── repository.py         # Database operations for analysis
└── pipeline.py           # Orchestration and batch processing
```

**Key Classes:**
- `ArticleSummarizer` - LLM service for article summarization
- `ArticleRepository` - Data access layer for articles and analysis
- `SummarizationPipeline` - Batch processing orchestrator

**Key Functions:**
- `summarize_article()` - Convenience function for single article
- `get_articles_pending_analysis()` - Query articles where summary IS NULL
- `save_analysis()` - Store results in article_analysis table

#### `ingestion/`
Data collection from external APIs:

- `pubmed_connector.py` - PubMed/NCBI API integration
- `crossref_connector.py` - Crossref API integration
- `normalizer.py` - Data normalization and cleaning

#### `schemas/`
Pydantic models for API validation (if used)

### `backend/scripts/`

CLI tools:

- `run_summarization.py` - 🆕 Main entry point for GenAI pipeline

## Root Level

### Configuration Files

- **`.env`** - Environment variables (API keys, database URL)
  - `GROQ_API_KEY` - For GenAI analysis
  - `NCBI_API_KEY` - For PubMed (optional)
  - `CROSSREF_EMAIL` - For Crossref polite pool
  - `DATABASE_URL` - SQLite database path

- **`.env.example`** - Template for environment setup

- **`requirements.txt`** - Python dependencies
  - Data ingestion: `biopython`, `requests`, `python-dotenv`
  - GenAI: `langchain-groq`, `langchain-core`, `pydantic`, `tqdm`

### CLI Scripts (Root Level)

- `ingest_cli.py` - Data ingestion CLI
- `view_data.py` - View and export articles

### Data Directory

```
data/
└── articles.db          # SQLite database
    ├── articles         # Ingested article metadata
    ├── article_analysis # GenAI analysis results
    └── articles_fts     # Full-text search index
```

### Documentation 🆕

```
docs/
├── PROJECT_STRUCTURE.md  # This file
└── GENAI_PIPELINE.md    # Detailed GenAI documentation
```

### Tests 🆕

```
tests/
└── test_genai.py        # GenAI pipeline test suite
```

## Data Flow

### 1. Ingestion Flow

```
External API (PubMed/Crossref)
         ↓
   Connector (fetch)
         ↓
   Normalizer (clean)
         ↓
   Database (articles table)
```

### 2. GenAI Flow

```
articles table (WHERE summary IS NULL)
         ↓
   ArticleRepository (fetch pending)
         ↓
   ArticleSummarizer (Groq LLM)
         ↓
   Schema Validation (Pydantic)
         ↓
   Database (article_analysis table)
```

## Database Schema

### `articles` Table

```sql
CREATE TABLE articles (
    id TEXT PRIMARY KEY,
    article_id TEXT UNIQUE NOT NULL,  -- PMID or DOI
    source TEXT NOT NULL,              -- pubmed, crossref
    title TEXT NOT NULL,
    abstract TEXT,
    journal TEXT,
    publication_date TEXT,
    authors TEXT,                      -- JSON array
    keywords TEXT,                     -- JSON array
    doi TEXT,
    url TEXT,
    ingestion_status TEXT,
    ingested_at DATETIME,
    updated_at DATETIME
)
```

### `article_analysis` Table

```sql
CREATE TABLE article_analysis (
    id TEXT PRIMARY KEY,
    article_id TEXT UNIQUE NOT NULL,  -- FK to articles.id
    subject TEXT,                      -- E-cigarettes, HTPs, etc.
    category TEXT,                     -- Clinical Studies, etc.
    summary TEXT,                      -- AI-generated summary
    entities TEXT,                     -- JSON array of topics
    sentiment TEXT,                    -- Positive/Negative/Neutral/Mixed
    industry_affiliation TEXT,
    model_id TEXT,
    prompt_version TEXT,
    analyzed_at DATETIME,
    analysis_status TEXT,              -- completed, pending, failed
    FOREIGN KEY (article_id) REFERENCES articles(id)
)
```

## Key Technologies

### Data Ingestion
- **Biopython** - PubMed API client
- **Requests** - HTTP client for APIs
- **SQLite** - Embedded database with FTS5

### GenAI Pipeline
- **Groq** - Fast LLM inference (llama-3.3-70b)
- **LangChain** - LLM orchestration framework
- **Pydantic** - Data validation and structured output
- **tqdm** - Progress bars

## Entry Points

### For Users

**Data Ingestion:**
```bash
python ingest_cli.py search "query" --sources pubmed --max 100
python ingest_cli.py stats
```

**GenAI Processing:**
```bash
python backend/scripts/run_summarization.py --limit 10
python backend/scripts/run_summarization.py --stats-only
```

**View Data:**
```bash
python view_data.py --limit 10 --format detailed
python view_data.py --stats
```

**Testing:**
```bash
python tests/test_genai.py
```

### For Developers

**Module Imports:**
```python
# GenAI
from backend.app.genai import ArticleSummarizer, ArticleRepository, SummarizationPipeline

# Database
from backend.app.db.database import get_db, init_db

# Ingestion
from backend.app.ingestion.pubmed_connector import PubMedConnector
```

## Configuration Management

### Environment Variables

All configuration via `.env` file:

```bash
# Required for GenAI
GROQ_API_KEY=gsk_...

# Optional for faster PubMed
NCBI_API_KEY=your_key

# Required for Crossref polite pool
CROSSREF_EMAIL=your@email.com

# Database location
DATABASE_URL=sqlite:///./data/articles.db
```

### No environment variable = Feature disabled

- No `GROQ_API_KEY` → GenAI features unavailable
- No `NCBI_API_KEY` → PubMed rate limited to 3 req/sec
- No `CROSSREF_EMAIL` → Crossref rate limited

## Development Workflow

### 1. Setup
```bash
python -m venv .venv
.venv\Scripts\activate  # Windows
pip install -r requirements.txt
cp .env.example .env
# Edit .env with API keys
```

### 2. Initialize
```bash
python ingest_cli.py init
```

### 3. Ingest Data
```bash
python ingest_cli.py search "tobacco" --sources pubmed --max 50
```

### 4. Test GenAI
```bash
python tests/test_genai.py
```

### 5. Run Pipeline
```bash
python backend/scripts/run_summarization.py --limit 10
```

### 6. View Results
```bash
python view_data.py --limit 5 --format detailed
```

## Future Enhancements

Potential additions to the structure:

```
backend/app/
├── api/              # FastAPI endpoints
├── services/         # Business logic layer
├── models/           # SQLAlchemy ORM models (if migrating from raw SQL)
└── tasks/           # Celery background tasks

frontend/             # React/Vue UI
tests/
├── test_ingestion.py
├── test_genai.py
└── test_api.py      # API integration tests

notebooks/           # Jupyter notebooks for analysis
scripts/             # Utility scripts
```

## Notes

- **Single Responsibility** - Each module has a clear purpose
- **Separation of Concerns** - Data access (repository), business logic (pipeline), LLM service (summarizer)
- **Testability** - All components can be tested independently
- **Extensibility** - Easy to add new data sources or analysis features
- **Configuration** - All external dependencies configurable via environment variables
