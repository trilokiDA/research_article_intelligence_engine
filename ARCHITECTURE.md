# System Architecture

**Project:** Research Article Intelligence Engine  
**Version:** 1.0  
**Last Updated:** 2026-07-30

---

## Overview

The system implements a **two-stage pipeline** architecture:

```
┌─────────────────────────────────────────────────────────────────┐
│                     STAGE 1: DATA INGESTION                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  PubMed API  →  Connectors  →  Normalizer  →  SQLite Database  │
│  (Crossref)                                                      │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────┐
│                     STAGE 2: GENAI ANALYSIS                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  SQLite  →  Repository  →  Groq LLM  →  JSON Files              │
│                              (Summarizer)                         │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

### Design Principles

1. **Separation of Concerns** - Ingestion and analysis are independent
2. **Data Integrity** - Raw data preserved; analysis stored separately
3. **Idempotency** - Re-running operations is safe
4. **File-Based Output** - Analysis results in JSON for easy validation
5. **Smart Filtering** - Skip already-processed articles

---

## System Components

### 1. Data Ingestion Layer

#### Purpose
Fetch research articles from external sources and store in normalized format.

#### Components

**PubMed Connector** (`backend/app/ingestion/pubmed_connector.py`)
- E-utilities API integration (Entrez)
- Features:
  - Search with complex queries
  - Date range filtering
  - Batch fetching (200 articles/request)
  - Rate limiting (3-10 req/sec)
  - PMID, DOI, title, abstract extraction
  - Author affiliations parsing
  - MeSH terms and keywords
  - Country extraction from affiliations

**Crossref Connector** (`backend/app/ingestion/crossref_connector.py`)
- REST API integration
- **Status:** Disabled (no abstracts available)
- Features:
  - Search by query
  - Fetch by DOI
  - Metadata extraction (title, authors, journal)
  - Date normalization
- **Why Disabled:** Returns no abstracts, making GenAI analysis impossible

**Data Normalizer** (`backend/app/ingestion/normalizer.py`)
- Unified schema across sources
- Author format standardization
- Date normalization (YYYY-MM-DD)
- Text cleaning and validation
- Field mapping

**Orchestrator** (`backend/app/ingestion/orchestrator.py`)
- Multi-source coordination
- Duplicate detection (by article_id)
- Batch storage
- Error handling
- Statistics tracking

**Topic Query Manager** (`backend/app/config/query_manager.py`)
- Loads predefined topic queries from JSON
- Manages query templates for:
  - Heat-Not-Burn (IQOS, HEETS, THS)
  - E-Cigarettes (vaping, ENDS)
  - Nicotine-Pouch
  - Snus
- Source-specific query formatting

#### Data Flow

```
User Command
    ↓
CLI (ingest_cli.py)
    ↓
Query Manager (get topic query) OR Custom Query
    ↓
Orchestrator
    ↓
├─→ PubMed Connector → Fetch articles → Normalize
├─→ (Crossref Connector - disabled)
│
├─→ Check for duplicates
├─→ Store in articles table
└─→ Return statistics
```

---

### 2. GenAI Analysis Layer

#### Purpose
Process articles through LLM for structured analysis and summarization.

#### Components

**Repository** (`backend/app/genai/repository.py`)
- Database access layer
- Functions:
  - `get_articles_pending_analysis()` - Fetch articles without JSON files
  - `get_articles_for_batch()` - Batch processing support
  - `get_analysis_stats()` - Statistics
- File-based skip logic: Checks for existing JSON files in `data/analysis/`

**Summarizer** (`backend/app/genai/summarizer.py`)
- Groq LLM integration via LangChain
- Features:
  - Structured output with Pydantic validation
  - Automatic schema validation and retry
  - Multiple model support
  - Error handling with retries
- Models:
  - `llama-3.3-70b-versatile` (recommended)
  - `llama-3.1-8b-instant` (fast)
  - `mixtral-8x7b-32768` (alternative)

**Pipeline** (`backend/app/genai/pipeline.py`)
- Batch orchestration
- Progress tracking (tqdm)
- Rate limiting between batches
- File-based output (JSON)
- Comprehensive error handling
- Statistics reporting

**Schemas** (`backend/app/genai/schemas.py`)
- Pydantic models for validation:
  - `Response` - Main analysis schema (11 fields)
  - Entity, Category, Subject, Sentiment enums
  - Industry affiliation detection
- Ensures structured, consistent output

**Prompts** (`backend/app/genai/prompts.py`)
- LLM prompt templates:
  - `summarization_prompt` - Main analysis
  - `revalidate_prompt` - Schema validation retry
  - `summary_evaluation_prompt` - Fact checking (planned)
  - `reinfer_prompt` - Iterative improvement (planned)
- People-first language enforcement
- Structured output instructions

**File Writer** (`backend/app/genai/file_writer.py`)
- Writes analysis results to JSON files
- File naming: `{article_id}.json`
- Directory management
- Atomic writes

#### Data Flow

```
User Command
    ↓
CLI (run_summarization.py)
    ↓
Pipeline
    ↓
Repository (get pending articles - no JSON file exists)
    ↓
For each article:
    ↓
    Summarizer (Groq LLM)
    ↓
    Pydantic Validation
    ↓
    File Writer → data/analysis/{article_id}.json
    ↓
Repository (mark as analyzed)
    ↓
Statistics Report
```

---

### 3. Database Layer

#### Technology
- **SQLite 3** with FTS5 extension
- Location: `data/articles.db`
- Advantages:
  - Zero configuration
  - Single file
  - Full SQL support
  - Built-in full-text search
- Limitations:
  - Single writer at a time
  - Recommended limit: ~1M rows

#### Schema

**articles** (Raw metadata from ingestion)
```sql
CREATE TABLE articles (
    id TEXT PRIMARY KEY,                -- UUID
    article_id TEXT UNIQUE NOT NULL,    -- PMID or DOI
    source TEXT NOT NULL,                -- pubmed, crossref, scholar
    source_metadata_id TEXT,             -- Source-specific ID
    doi TEXT,
    url TEXT,
    ingestion_status TEXT,               -- pending, processed, failed
    article_type TEXT,                   -- research, review, etc.
    title TEXT NOT NULL,
    abstract TEXT,
    journal TEXT,
    keywords TEXT,                       -- JSON array
    authors TEXT,                        -- JSON array [{name, affiliation}]
    publication_date TEXT,               -- YYYY-MM-DD
    country TEXT,
    ingested_at DATETIME,
    updated_at DATETIME
);
```

**article_analysis** (GenAI results - minimal, JSON files are source of truth)
```sql
CREATE TABLE article_analysis (
    id TEXT PRIMARY KEY,
    article_id TEXT UNIQUE NOT NULL,
    analysis_status TEXT,                -- pending, completed, failed
    analyzed_at DATETIME,
    error_message TEXT,
    FOREIGN KEY (article_id) REFERENCES articles(id) ON DELETE CASCADE
);
```

**articles_fts** (Full-text search index)
```sql
CREATE VIRTUAL TABLE articles_fts USING fts5(
    article_id,
    title,
    abstract,
    content=articles
);
```

#### Indexes
- `idx_articles_source` on articles(source)
- `idx_articles_date` on articles(publication_date)
- `idx_articles_status` on articles(ingestion_status)
- `idx_analysis_status` on article_analysis(analysis_status)

---

### 4. File System Organization

```
radar/
├── backend/
│   ├── app/
│   │   ├── db/
│   │   │   └── database.py              # Database connection & schema
│   │   │
│   │   ├── ingestion/
│   │   │   ├── __init__.py
│   │   │   ├── pubmed_connector.py      # PubMed API client
│   │   │   ├── crossref_connector.py    # Crossref API (disabled)
│   │   │   ├── normalizer.py            # Data normalization
│   │   │   └── orchestrator.py          # Multi-source coordinator
│   │   │
│   │   ├── genai/
│   │   │   ├── __init__.py
│   │   │   ├── pipeline.py              # Batch orchestration
│   │   │   ├── summarizer.py            # Groq LLM integration
│   │   │   ├── repository.py            # Database access
│   │   │   ├── schemas.py               # Pydantic models
│   │   │   ├── prompts.py               # LLM prompts
│   │   │   ├── file_writer.py           # JSON file writer
│   │   │   └── config.py                # Configuration
│   │   │
│   │   └── config/
│   │       ├── query_manager.py         # Topic query loader
│   │       └── search_queries.json      # Predefined queries
│   │
│   ├── scripts/
│   │   └── run_summarization.py         # GenAI CLI
│   │
│   ├── ingest_cli.py                    # Ingestion CLI
│   ├── requirements.txt                 # Python dependencies
│   └── .env.example                     # Environment template
│
├── data/
│   ├── articles.db                      # SQLite database
│   └── analysis/                        # GenAI output (JSON files)
│       ├── PMID12345678.json
│       ├── PMID12345679.json
│       └── ...
│
├── docs/
│   ├── GENAI_PIPELINE.md               # GenAI implementation
│   └── SCHEMA_MAPPING.md               # Database schema
│
├── archive/                            # Historical docs
│
├── README.md                           # Main documentation
├── ARCHITECTURE.md                     # This file
├── DEVELOPMENT.md                      # Setup & development
└── ROADMAP.md                          # Future plans
```

---

## Technology Stack

### Core
- **Python:** 3.11+
- **Database:** SQLite 3 with FTS5
- **Package Manager:** pip + venv

### Data Ingestion
- **biopython:** PubMed API (Entrez E-utilities)
- **requests:** HTTP client for Crossref
- **python-dotenv:** Environment configuration

### GenAI Analysis
- **langchain-groq:** Groq LLM integration
- **langchain-core:** LangChain framework
- **pydantic:** Schema validation and structured output
- **groq:** Groq API client

### Utilities
- **tqdm:** Progress bars
- **numpy:** Array operations (biopython dependency)
- **uuid:** Unique identifiers

### Configuration
- **Environment Variables:** `.env` file
  - `NCBI_EMAIL` - Required for PubMed
  - `NCBI_API_KEY` - Optional, for faster rate limits
  - `GROQ_API_KEY` - Required for GenAI
  - `CROSSREF_EMAIL` - Optional (connector disabled)

---

## Design Decisions & Rationale

### 1. Why Two-Stage Pipeline?
**Decision:** Separate ingestion from analysis  
**Rationale:**
- Can re-analyze articles without re-ingesting
- Different data sources for each stage
- Clear separation of concerns
- Independent scalability

### 2. Why SQLite (not PostgreSQL)?
**Decision:** Start with SQLite  
**Rationale:**
- Zero configuration
- Perfect for <100K articles
- Easy local development
- Simple backup (single file)
- Migration path exists when needed

### 3. Why File-Based GenAI Output?
**Decision:** Save analysis to JSON files, not database  
**Rationale:**
- Easy to review and validate
- Can be versioned (Git LFS)
- Re-processable without database changes
- Simple skip logic (file exists = processed)
- Inspection without SQL queries

### 4. Why Disable Crossref?
**Decision:** Comment out Crossref connector  
**Rationale:**
- API returns no abstracts
- GenAI analysis requires abstracts
- Code preserved for future use
- Focus on PubMed (better quality)

### 5. Why Topic-Based Queries?
**Decision:** Predefined queries in JSON config  
**Rationale:**
- Complex queries are hard to remember
- Consistency across team members
- Expert-crafted search terms
- Easy to add new topics
- Reproducible research

### 6. Why Groq (not Claude/OpenAI)?
**Decision:** Use Groq for LLM inference  
**Rationale:**
- Fast inference (< 3s per article)
- Free tier available
- Good quality with llama-3.3-70b
- Cost-effective for large batches
- Note: Can add Claude/OpenAI later

---

## Data Flow Diagrams

### Ingestion Flow

```
┌──────────────────┐
│   User/Cron      │
└────────┬─────────┘
         │
         ▼
┌──────────────────────────────┐
│  CLI: ingest_cli.py          │
│  Command: topic/search       │
└────────┬─────────────────────┘
         │
         ▼
┌──────────────────────────────┐
│  Query Manager               │
│  (get predefined query)      │
└────────┬─────────────────────┘
         │
         ▼
┌──────────────────────────────┐
│  Orchestrator                │
│  - Multi-source coordination │
│  - Duplicate detection       │
└────────┬─────────────────────┘
         │
         ├─────────────────────────┐
         ▼                         ▼
┌────────────────┐      ┌────────────────┐
│ PubMed API     │      │ (Crossref -    │
│ - Search       │      │  disabled)     │
│ - Fetch        │      └────────────────┘
│ - Parse        │
└────────┬───────┘
         │
         ▼
┌──────────────────────────────┐
│  Normalizer                  │
│  - Unified schema            │
│  - Date format               │
│  - Author format             │
└────────┬─────────────────────┘
         │
         ▼
┌──────────────────────────────┐
│  SQLite: articles table      │
│  - Insert if not exists      │
│  - Return statistics         │
└──────────────────────────────┘
```

### GenAI Analysis Flow

```
┌──────────────────┐
│   User/Cron      │
└────────┬─────────┘
         │
         ▼
┌──────────────────────────────┐
│  CLI: run_summarization.py   │
│  Options: limit, model, etc. │
└────────┬─────────────────────┘
         │
         ▼
┌──────────────────────────────┐
│  Pipeline                    │
│  - Batch orchestration       │
│  - Progress tracking         │
└────────┬─────────────────────┘
         │
         ▼
┌──────────────────────────────┐
│  Repository                  │
│  - Query pending articles    │
│  - Check for existing JSON   │
└────────┬─────────────────────┘
         │
         ▼
┌──────────────────────────────┐
│  For each article:           │
│                              │
│  ┌────────────────────┐      │
│  │ Summarizer         │      │
│  │ - Format prompt    │      │
│  │ - Call Groq LLM    │      │
│  │ - Parse response   │      │
│  └────────┬───────────┘      │
│           │                  │
│           ▼                  │
│  ┌────────────────────┐      │
│  │ Pydantic Validator │      │
│  │ - Check schema     │      │
│  │ - Retry if invalid │      │
│  └────────┬───────────┘      │
│           │                  │
│           ▼                  │
│  ┌────────────────────┐      │
│  │ File Writer        │      │
│  │ - Save to JSON     │      │
│  └────────────────────┘      │
└──────────────────────────────┘
         │
         ▼
┌──────────────────────────────┐
│  data/analysis/              │
│  {article_id}.json           │
└──────────────────────────────┘
```

---

## Performance Characteristics

### Ingestion
- **PubMed Rate:** 3 req/sec (default), 10 req/sec (with API key)
- **Batch Size:** 200 articles per request
- **Throughput:** ~600-2000 articles/minute
- **Bottleneck:** API rate limits

### GenAI Analysis
- **Model Speed:**
  - llama-3.3-70b: ~3-5 seconds per article
  - llama-3.1-8b: ~1-2 seconds per article
- **Batch Processing:** 10 articles per batch (configurable)
- **Throughput:** ~120-600 articles/hour (depending on model)
- **Bottleneck:** LLM inference time

### Database
- **SQLite Performance:**
  - Inserts: ~10K per second (batch)
  - Queries: <1ms for indexed lookups
  - Full-text search: <100ms for most queries
- **Capacity:** Tested up to 100K articles
- **Bottleneck:** Single writer (consider PostgreSQL for concurrent writes)

---

## Security Considerations

### API Keys
- Stored in `.env` (not committed to Git)
- Required:
  - `GROQ_API_KEY` - For GenAI analysis
  - `NCBI_EMAIL` - For PubMed access
- Optional:
  - `NCBI_API_KEY` - For faster PubMed access

### Data Privacy
- No personal data collected
- Research articles are public domain
- Metadata stored locally
- No external tracking

### Rate Limiting
- PubMed: Respects rate limits (3-10 req/sec)
- Groq: Free tier has generous limits
- Delays between batches to avoid throttling

---

## Error Handling

### Ingestion
- API failures: Retry with exponential backoff
- Invalid data: Skip and log error
- Duplicates: Detect by article_id, skip silently
- Database errors: Log and continue

### GenAI Analysis
- LLM failures: Retry up to 3 times
- Schema validation errors: Auto-retry with feedback
- File write errors: Log and mark as failed
- Batch errors: Continue with next article

---

## Monitoring & Logging

### Current (Basic)
- Console output with progress bars (tqdm)
- Statistics printed after each run
- Error messages to stderr

### Planned (v1.1)
- Structured logging (JSON)
- Log files in `logs/`
- Error tracking
- Performance metrics

---

## Scalability Considerations

### Current Limits
- **SQLite:** ~1M articles (single writer)
- **File System:** ~1M JSON files per directory (consider subdirectories)
- **LLM API:** Groq free tier limits

### Upgrade Path
1. **PostgreSQL:** For >100K articles or concurrent writes
2. **Redis:** For caching and job queues
3. **Celery:** For distributed task processing
4. **Object Storage:** For large JSON file collections (S3/MinIO)

---

## Testing Strategy

### Unit Tests (Planned)
- Database operations
- Data normalization
- Schema validation
- File operations

### Integration Tests (Planned)
- PubMed API connector
- GenAI pipeline end-to-end
- CLI commands

### Manual Testing (Current)
- Ingest 5-10 articles
- Run analysis
- Check JSON output
- Verify database state

---

## Future Architecture (v2.0)

See [ROADMAP.md](ROADMAP.md) for detailed future plans including:
- Vector embeddings (ChromaDB/Qdrant)
- RAG Q&A system
- Citation network graph (Neo4j)
- FastAPI REST API
- React frontend
- Real-time monitoring

---

**Last Updated:** 2026-07-30  
**Version:** 1.0  
**Status:** Current Production Architecture
