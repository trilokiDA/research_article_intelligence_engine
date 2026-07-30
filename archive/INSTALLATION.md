# Installation Guide - Data Ingestion Pipeline

## ✅ What We've Built

Complete data ingestion system that:
- Fetches articles from PubMed and Crossref
- Normalizes data from multiple sources
- Stores in SQLite database
- Provides CLI for easy operation

## 🚀 Installation Steps

### Step 1: Install Python Dependencies

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate

# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

**Note:** This will install:
- `biopython` - for PubMed API
- `requests` - for Crossref API
- `fastapi` - for future API development
- `anthropic` - for GenAI analysis (later)

### Step 2: Set Up Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env file and add:
# - Your email for NCBI_EMAIL
# - Your email for CROSSREF_EMAIL
# - (Optional) NCBI_API_KEY from https://www.ncbi.nlm.nih.gov/account/
```

### Step 3: Initialize Database

```bash
python ingest_cli.py init
```

This creates `data/articles.db` with all necessary tables.

### Step 4: Test Ingestion

```bash
# Fetch 10 recent articles about tobacco harm reduction
python ingest_cli.py search "tobacco harm reduction" --sources pubmed --max 10

# Check results
python ingest_cli.py stats
```

## 📊 Usage Examples

### Basic Search
```bash
# Search PubMed
python ingest_cli.py search "electronic cigarettes" --sources pubmed --max 50

# Search both PubMed and Crossref
python ingest_cli.py search "vaping youth" --sources pubmed crossref --max 100
```

### With Date Range
```bash
python ingest_cli.py search "IQOS" \
    --sources pubmed \
    --max 50 \
    --from-date 2024-01-01 \
    --to-date 2024-12-31
```

### Check Status
```bash
# Database statistics
python ingest_cli.py stats

# Pending articles (need GenAI analysis)
python ingest_cli.py pending --limit 20
```

## 🗂️ Files Created

```
backend/
├── app/
│   ├── db/
│   │   └── database.py              ✅ Database connection & schema
│   ├── ingestion/
│   │   ├── pubmed_connector.py      ✅ PubMed E-utilities API
│   │   ├── crossref_connector.py    ✅ Crossref REST API
│   │   ├── normalizer.py            ✅ Data normalization
│   │   └── orchestrator.py          ✅ Multi-source coordination
├── ingest_cli.py                    ✅ Command-line interface
├── requirements.txt                 ✅ Dependencies
├── .env.example                     ✅ Environment template
└── README.md                        ✅ Backend documentation

data/
└── articles.db                      ✅ SQLite database (created on init)
```

## 🧪 Testing

### Test Individual Connectors

```bash
cd backend

# Test PubMed connector
python -m app.ingestion.pubmed_connector

# Test Crossref connector
python -m app.ingestion.crossref_connector

# Test normalizer
python -m app.ingestion.normalizer

# Test orchestrator
python -m app.ingestion.orchestrator
```

### Test Database

```bash
# Initialize and show stats
python -m app.db.database

# Query directly
sqlite3 data/articles.db "SELECT COUNT(*) FROM articles;"
```

## 🔧 Troubleshooting

### "ModuleNotFoundError: No module named 'Bio'"
```bash
pip install biopython
```

### "No such file or directory: '.env'"
```bash
cp .env.example .env
```

### "Database is locked"
Only one process can write to SQLite at a time. Close other connections or upgrade to PostgreSQL.

### "PubMed rate limit exceeded"
Get API key from https://www.ncbi.nlm.nih.gov/account/ and add to .env

## 📈 Next Steps

Now that ingestion is working:

1. **Migrate existing DocumentDB data:**
   ```bash
   python scripts/migrate_documentdb_to_sqlite.py \
       --mongo-uri "mongodb://your-host:27017" \
       --mongo-db "tobacco_research"
   ```

2. **Build GenAI analysis pipeline** (see `docs/MIGRATION_GUIDE.md`)

3. **Set up FastAPI server** for the frontend

4. **Deploy to production** (see `docs/06-OPEN_SOURCE_STACK.md`)

## 🎯 What Works Now

✅ PubMed article fetching  
✅ Crossref article fetching  
✅ Data normalization (unified schema)  
✅ SQLite storage  
✅ Duplicate detection  
✅ CLI interface  
✅ Database statistics  

## 🔜 Coming Next

- [ ] Google Scholar connector
- [ ] GenAI analysis integration (your existing schema.py)
- [ ] FastAPI REST API
- [ ] React frontend
- [ ] Vector embeddings for semantic search

## 📞 Help

- **Ingestion docs:** `backend/README.md`
- **Full project docs:** `docs/00-README.md`
- **Migration guide:** `docs/MIGRATION_GUIDE.md`
- **Tech stack:** `docs/06-OPEN_SOURCE_STACK.md`
