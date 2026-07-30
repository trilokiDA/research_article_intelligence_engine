# Development Guide

**Project:** Research Article Intelligence Engine  
**Version:** 1.0  
**Last Updated:** 2026-07-30

---

## Prerequisites

Before you begin, ensure you have:

- **Python 3.11 or higher** - [Download Python](https://www.python.org/downloads/)
- **Git** - [Download Git](https://git-scm.com/downloads/)
- **Text editor or IDE** - VS Code, PyCharm, etc.
- **API Keys:**
  - PubMed/NCBI email (required) - Free
  - NCBI API key (optional, recommended) - [Get key](https://www.ncbi.nlm.nih.gov/account/)
  - Groq API key (required for GenAI) - [Get key](https://console.groq.com/keys)

---

## Installation

### 1. Clone Repository

```bash
git clone <repository-url>
cd radar
```

### 2. Create Virtual Environment

```bash
# Navigate to backend
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows (PowerShell):
venv\Scripts\Activate.ps1

# Windows (Command Prompt):
venv\Scripts\activate.bat

# Linux/Mac:
source venv/bin/activate
```

You should see `(venv)` in your terminal prompt.

### 3. Install Dependencies

```bash
# Install all required packages
pip install -r requirements.txt
```

**Packages installed:**
- `biopython` - PubMed API access
- `requests` - HTTP client
- `python-dotenv` - Environment variables
- `langchain-groq` - Groq LLM integration
- `pydantic` - Data validation
- `tqdm` - Progress bars
- `numpy` - Array operations

### 4. Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your favorite editor
nano .env  # or vim, code, notepad, etc.
```

**Required configuration:**

```env
# PubMed Configuration (Required)
NCBI_EMAIL=your-email@example.com
NCBI_API_KEY=your-ncbi-api-key-here  # Optional but recommended

# Groq Configuration (Required for GenAI)
GROQ_API_KEY=your-groq-api-key-here

# Crossref Configuration (Optional - connector disabled)
CROSSREF_EMAIL=your-email@example.com

# Database Configuration (Default is fine)
DATABASE_URL=sqlite:///./data/articles.db
```

**Getting API Keys:**

- **NCBI API Key** (recommended for faster rate limits):
  1. Create account at https://www.ncbi.nlm.nih.gov/account/
  2. Go to Settings → API Key Management
  3. Create new API key
  4. Copy key to `.env` file

- **Groq API Key** (required for GenAI):
  1. Sign up at https://console.groq.com/
  2. Go to API Keys section
  3. Create new API key
  4. Copy key to `.env` file
  5. Free tier available with generous limits

### 5. Initialize Database

```bash
python ingest_cli.py init
```

**Expected output:**
```
============================================================
[OK] Database initialized at: data/articles.db
============================================================
Tables created:
  - articles
  - article_analysis
  - articles_fts (full-text search)
============================================================
```

### 6. Verify Installation

```bash
# Test PubMed connection (fetch 5 articles)
python ingest_cli.py search "tobacco harm reduction" --sources pubmed --max 5

# Check database
python ingest_cli.py stats

# Expected output:
# Total articles: 5
# Pending analysis: 5
```

---

## Running the System

### Data Ingestion

#### List Available Topics

```bash
python ingest_cli.py topics
```

#### Ingest Using Topics (Recommended)

```bash
# Fetch Heat-Not-Burn research
python ingest_cli.py topic "Heat-Not-Burn" \
    --sources pubmed \
    --max 50 \
    --from-date 2024-01-01 \
    --to-date 2024-12-31

# Fetch E-Cigarettes research
python ingest_cli.py topic "E-Cigarettes" \
    --sources pubmed \
    --max 50 \
    --from-date 2024-01-01 \
    --to-date 2024-12-31
```

#### Ingest Using Custom Queries

```bash
# Simple query
python ingest_cli.py search "IQOS" \
    --sources pubmed \
    --max 50

# Complex query with date range
python ingest_cli.py search "electronic cigarettes AND youth" \
    --sources pubmed \
    --max 100 \
    --from-date 2024-01-01 \
    --to-date 2024-12-31
```

#### Check Ingestion Status

```bash
# Database statistics
python ingest_cli.py stats

# List pending articles
python ingest_cli.py pending --limit 10
```

### GenAI Analysis

#### Check Pending Articles

```bash
python backend/scripts/run_summarization.py --stats-only
```

#### Run Analysis (Dry Run)

```bash
# Process 10 articles without saving
python backend/scripts/run_summarization.py --limit 10 --dry-run
```

#### Run Analysis (Production)

```bash
# Process all pending articles
python backend/scripts/run_summarization.py

# Process limited number
python backend/scripts/run_summarization.py --limit 50

# Use faster model
python backend/scripts/run_summarization.py \
    --model llama-3.1-8b-instant \
    --limit 20
```

#### Custom Batch Configuration

```bash
# Smaller batches with longer delay (rate limiting)
python backend/scripts/run_summarization.py \
    --batch-size 5 \
    --delay 2.0 \
    --limit 100
```

### View Results

#### View Database

```bash
# Statistics
python view_data.py --stats

# Detailed view (first 10 articles)
python view_data.py --format detailed --limit 10

# View specific source
python view_data.py --source pubmed --limit 20
```

#### View JSON Files

```bash
# List analysis files
ls data/analysis/

# View specific analysis
cat data/analysis/PMID12345678.json

# Pretty print with Python
python -m json.tool data/analysis/PMID12345678.json
```

---

## Development Workflow

### Daily Workflow

1. **Activate virtual environment**
   ```bash
   cd backend
   source venv/bin/activate  # or venv\Scripts\activate on Windows
   ```

2. **Pull latest changes**
   ```bash
   git pull origin main
   ```

3. **Install any new dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run your work**
   ```bash
   # Ingestion
   python ingest_cli.py topic "E-Cigarettes" --max 10
   
   # Analysis
   python backend/scripts/run_summarization.py --limit 10
   ```

5. **Check results**
   ```bash
   python ingest_cli.py stats
   python view_data.py --stats
   ```

### Adding New Topics

1. **Edit topic configuration**
   ```bash
   nano backend/app/config/search_queries.json
   ```

2. **Add new topic entry**
   ```json
   {
     "name": "Your-Topic-Name",
     "description": "Brief description",
     "sources": {
       "pubmed": {
         "query": "your complex query here"
       }
     }
   }
   ```

3. **Test new topic**
   ```bash
   python ingest_cli.py topics  # Should show your new topic
   python ingest_cli.py topic "Your-Topic-Name" --max 5
   ```

### Modifying GenAI Prompts

1. **Edit prompts**
   ```bash
   nano backend/app/genai/prompts.py
   ```

2. **Test with dry run**
   ```bash
   python backend/scripts/run_summarization.py --limit 5 --dry-run
   ```

3. **Review output** in console

4. **Run for real**
   ```bash
   python backend/scripts/run_summarization.py --limit 10
   ```

---

## Testing

### Manual Testing

#### Test Ingestion

```bash
# Test PubMed connector
python -c "from app.ingestion.pubmed_connector import PubMedConnector; \
           c = PubMedConnector(); \
           results = c.search('tobacco', max_results=5); \
           print(f'Found {len(results)} articles')"

# Test database
python -c "from app.db.database import get_db; \
           with get_db() as db: \
               cursor = db.execute('SELECT COUNT(*) FROM articles'); \
               print(f'Total articles: {cursor.fetchone()[0]}')"
```

#### Test GenAI

```bash
# Test with single article (dry run)
python backend/scripts/run_summarization.py --limit 1 --dry-run
```

### Unit Tests (Planned)

```bash
# When implemented:
pytest tests/
pytest tests/test_ingestion.py
pytest tests/test_genai.py
```

---

## Troubleshooting

### Common Issues

#### "No module named 'Bio'"

**Problem:** Biopython not installed  
**Solution:**
```bash
# Make sure virtual environment is activated
source venv/bin/activate  # or venv\Scripts\activate
pip install biopython
```

#### "Database is locked"

**Problem:** SQLite only allows one writer at a time  
**Solution:**
- Close any other Python processes accessing the database
- Close any database browser tools (DB Browser for SQLite, etc.)
- Wait a moment and try again
- For production, consider PostgreSQL

#### "PubMed API rate limit exceeded"

**Problem:** Making too many requests too quickly  
**Solution:**
- Get NCBI API key for higher rate limits (10 req/sec vs 3 req/sec)
- Add delays: `--batch-size 5` with smaller batches
- Reduce `--max` to fetch fewer articles per run

#### "GROQ_API_KEY not found"

**Problem:** API key not configured  
**Solution:**
```bash
# Make sure .env file exists
ls .env

# Check if key is set
cat .env | grep GROQ

# Add key to .env
echo "GROQ_API_KEY=your-key-here" >> .env
```

#### "ModuleNotFoundError" or import errors

**Problem:** Virtual environment not activated  
**Solution:**
```bash
# Activate virtual environment first
cd backend
source venv/bin/activate  # or venv\Scripts\activate

# Then run your command
python ingest_cli.py stats
```

#### Unicode/Emoji errors on Windows

**Problem:** Windows console doesn't support emoji  
**Solution:** Already fixed! Code uses `[OK]`, `[STATS]` prefixes instead of emoji.

#### "No articles need processing"

**Problem:** All articles already analyzed  
**Solution:**
```bash
# Ingest new articles first
python ingest_cli.py topic "E-Cigarettes" --max 10

# Then analyze
python backend/scripts/run_summarization.py
```

#### Schema validation errors

**Problem:** LLM output doesn't match expected schema  
**Solution:**
- Pipeline auto-retries 3 times
- Check error message for details
- May need to adjust prompt or schema
- Try different model: `--model llama-3.1-8b-instant`

### Getting Help

1. **Check documentation:**
   - README.md - Quick start
   - ARCHITECTURE.md - System design
   - docs/GENAI_PIPELINE.md - GenAI details

2. **Check logs:**
   - Console output shows errors
   - Check data/analysis/ for failed analyses

3. **Verify configuration:**
   ```bash
   # Check .env file
   cat .env
   
   # Test database
   python ingest_cli.py stats
   
   # Test API keys
   python -c "import os; from dotenv import load_dotenv; load_dotenv(); \
              print('GROQ_API_KEY:', 'SET' if os.getenv('GROQ_API_KEY') else 'NOT SET')"
   ```

---

## Directory Structure

```
radar/
├── backend/
│   ├── app/                      # Application code
│   │   ├── db/                   # Database layer
│   │   ├── ingestion/            # Data ingestion
│   │   ├── genai/                # GenAI analysis
│   │   └── config/               # Configuration
│   ├── scripts/                  # CLI scripts
│   ├── ingest_cli.py             # Main CLI
│   ├── requirements.txt          # Dependencies
│   └── .env                      # Configuration (create from .env.example)
│
├── data/
│   ├── articles.db               # SQLite database (created by init)
│   └── analysis/                 # GenAI output (JSON files)
│
├── docs/                         # Documentation
├── archive/                      # Historical docs
│
└── [README.md, ARCHITECTURE.md, etc.]
```

---

## Best Practices

### Virtual Environment

- **Always activate** before running commands
- **Use separate environments** for different Python projects
- **Don't commit** venv/ to Git (already in .gitignore)

### Environment Variables

- **Never commit** .env to Git (already in .gitignore)
- **Use .env.example** as template for team members
- **Rotate API keys** if accidentally exposed

### Database

- **Backup regularly** - `cp data/articles.db data/articles.db.backup`
- **Don't edit directly** - use CLI or Python API
- **Monitor size** - SQLite works well up to ~1M articles

### GenAI Analysis

- **Start small** - Test with `--limit 10 --dry-run` first
- **Monitor costs** - Groq free tier is generous but has limits
- **Review output** - Check JSON files for quality
- **Version prompts** - Keep track of prompt changes in Git

### Code Changes

- **Test locally** first
- **Use small commits** with clear messages
- **Update documentation** when changing behavior
- **Don't break existing** - maintain backwards compatibility

---

## Next Steps

### After Setup

1. **Ingest some articles:**
   ```bash
   python ingest_cli.py topic "Heat-Not-Burn" --max 20
   ```

2. **Run GenAI analysis:**
   ```bash
   python backend/scripts/run_summarization.py
   ```

3. **View results:**
   ```bash
   python view_data.py --format detailed --limit 5
   ```

4. **Read documentation:**
   - ARCHITECTURE.md - Understand system design
   - docs/GENAI_PIPELINE.md - GenAI details
   - ROADMAP.md - Future plans

### For Contributors

1. **Review architecture:** Read ARCHITECTURE.md
2. **Check roadmap:** See ROADMAP.md for planned features
3. **Set up pre-commit hooks** (when available)
4. **Run tests** (when implemented)

---

## Performance Tips

### Faster Ingestion

- Get NCBI API key (3x faster: 10 req/sec vs 3 req/sec)
- Use topic queries (pre-optimized)
- Batch operations with `--max 100` or higher

### Faster GenAI Analysis

- Use faster model: `--model llama-3.1-8b-instant`
- Increase batch size: `--batch-size 20`
- Reduce delay: `--delay 0.5`
- Note: May hit rate limits with aggressive settings

### Database Performance

- Regular VACUUM: `sqlite3 data/articles.db "VACUUM;"`
- Monitor size: `ls -lh data/articles.db`
- Consider PostgreSQL for >100K articles

---

## Environment Variables Reference

```env
# Required for PubMed
NCBI_EMAIL=your-email@example.com

# Optional but recommended for PubMed (10 req/sec vs 3 req/sec)
NCBI_API_KEY=your-ncbi-api-key-here

# Required for GenAI analysis
GROQ_API_KEY=your-groq-api-key-here

# Optional - Crossref connector disabled
CROSSREF_EMAIL=your-email@example.com

# Database (default is fine)
DATABASE_URL=sqlite:///./data/articles.db
```

---

**Happy developing! 🚀**

For more information, see:
- [README.md](README.md) - Project overview
- [ARCHITECTURE.md](ARCHITECTURE.md) - System design
- [ROADMAP.md](ROADMAP.md) - Future plans
- [docs/GENAI_PIPELINE.md](docs/GENAI_PIPELINE.md) - GenAI details
