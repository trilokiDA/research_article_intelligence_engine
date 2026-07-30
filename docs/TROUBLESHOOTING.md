# Troubleshooting Guide

**Last Updated:** 2026-07-30

Common issues and solutions for the Research Article Intelligence Engine.

---

## Installation Issues

### "No module named 'Bio'"

**Problem:** Biopython not installed

**Symptoms:**
```
ModuleNotFoundError: No module named 'Bio'
```

**Solution:**
```bash
# Activate virtual environment first
cd backend
source venv/bin/activate  # Linux/Mac
# OR
venv\Scripts\activate     # Windows

# Install biopython
pip install biopython

# Or install all dependencies
pip install -r requirements.txt
```

---

### "No module named 'app'"

**Problem:** Running command from wrong directory or virtual environment not activated

**Symptoms:**
```
ModuleNotFoundError: No module named 'app'
```

**Solution:**
```bash
# Make sure you're in the backend directory
cd backend

# Activate virtual environment
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Run command
python ingest_cli.py stats
```

---

### "pip: command not found"

**Problem:** Python or pip not in PATH

**Solution:**

**Windows:**
```powershell
# Add Python to PATH during installation
# Or use py launcher:
py -m pip install -r requirements.txt
```

**Linux/Mac:**
```bash
# Install pip
python3 -m ensurepip

# Or use python3 explicitly
python3 -m pip install -r requirements.txt
```

---

## Environment Configuration Issues

### "NCBI_EMAIL not found in environment"

**Problem:** `.env` file missing or not configured

**Symptoms:**
```
Error: NCBI_EMAIL not found in environment
```

**Solution:**
```bash
# Check if .env exists
ls .env

# If not, copy from example
cp .env.example .env

# Edit .env and add your email
nano .env  # or vim, code, notepad++, etc.

# Add:
NCBI_EMAIL=your-email@example.com
```

---

### "GROQ_API_KEY not found"

**Problem:** Groq API key not configured

**Symptoms:**
```
Error: GROQ_API_KEY not found in environment
```

**Solution:**
```bash
# Get API key from https://console.groq.com/keys

# Add to .env file
echo "GROQ_API_KEY=your-key-here" >> .env

# Or edit manually
nano .env
```

---

## Database Issues

### "Database is locked"

**Problem:** Another process is using the database (SQLite allows only one writer)

**Symptoms:**
```
sqlite3.OperationalError: database is locked
```

**Solutions:**

**1. Close Other Connections:**
```bash
# Check for other Python processes
ps aux | grep python

# Kill if necessary
kill <process_id>

# Close DB Browser or other tools
```

**2. Wait and Retry:**
```bash
# SQLite usually releases lock quickly
# Wait 5 seconds and try again
```

**3. Check for Stale Lock:**
```bash
# Remove database lock file (only if sure no other process)
rm data/articles.db-journal
rm data/articles.db-wal
```

**4. Upgrade to PostgreSQL** (for production with concurrent writes)

---

### "No such table: articles"

**Problem:** Database not initialized

**Symptoms:**
```
sqlite3.OperationalError: no such table: articles
```

**Solution:**
```bash
# Initialize database
python ingest_cli.py init

# Verify tables exist
sqlite3 data/articles.db ".tables"
# Should show: articles  article_analysis  articles_fts
```

---

### "Unable to open database file"

**Problem:** Database file path is invalid or permissions issue

**Solutions:**

**1. Create data directory:**
```bash
mkdir -p data
```

**2. Check permissions:**
```bash
ls -la data/
# Should be writable by current user

# Fix permissions if needed
chmod 755 data
chmod 644 data/articles.db  # if exists
```

**3. Check path in .env:**
```env
DATABASE_URL=sqlite:///./data/articles.db
# Note the three slashes for relative path
```

---

## PubMed API Issues

### "PubMed API rate limit exceeded"

**Problem:** Making too many requests too quickly

**Symptoms:**
```
Error: HTTP 429 - Too Many Requests
```

**Solutions:**

**1. Get API Key** (recommended - increases limit from 3 to 10 req/sec):
```bash
# Get from: https://www.ncbi.nlm.nih.gov/account/
# Add to .env:
NCBI_API_KEY=your-api-key-here
```

**2. Reduce Request Rate:**
```bash
# Fetch fewer articles at once
python ingest_cli.py search "query" --max 50  # instead of --max 500

# Add delays between requests (handled automatically by connector)
```

**3. Check Current Usage:**
- NCBI monitors usage per IP address
- Wait 1 hour if hitting limits
- Consider using different query times

---

### "PubMed API returned no results"

**Problem:** Query too specific or no articles match

**Solutions:**

**1. Simplify Query:**
```bash
# Too specific:
python ingest_cli.py search "IQOS AND adolescents AND Finland"

# Better:
python ingest_cli.py search "IQOS"
```

**2. Check Date Range:**
```bash
# If date range is empty, no results
python ingest_cli.py search "IQOS" --from-date 2020-01-01  # remove --to-date
```

**3. Use Topic Queries:**
```bash
# Pre-optimized queries
python ingest_cli.py topic "Heat-Not-Burn" --max 100
```

---

### "Invalid PubMed query syntax"

**Problem:** Query has syntax errors

**Common Mistakes:**
```bash
# Wrong: Unmatched quotes
"electronic cigarettes

# Wrong: Invalid field
electronic cigarettes[BadField]

# Wrong: Invalid Boolean
electronic cigarettes && adolescents
```

**Correct Syntax:**
```bash
# Correct: Matched quotes
"electronic cigarettes"

# Correct: Valid field
"electronic cigarettes"[Title/Abstract]

# Correct: Boolean AND
electronic cigarettes AND adolescents
```

---

## GenAI Analysis Issues

### "No articles need processing"

**Problem:** All articles already analyzed

**Symptoms:**
```
No pending articles found.
```

**Solutions:**

**1. Ingest New Articles:**
```bash
python ingest_cli.py topic "E-Cigarettes" --max 20
python backend/scripts/run_summarization.py
```

**2. Check Existing JSON Files:**
```bash
# Count analysis files
ls data/analysis/ | wc -l

# Check specific article
ls data/analysis/PMID*.json
```

**3. Re-analyze by Deleting JSON** (if needed):
```bash
# Delete specific analysis
rm data/analysis/PMID12345678.json

# Or delete all (careful!)
rm data/analysis/*.json
```

---

### "Schema validation error after 3 retries"

**Problem:** LLM output doesn't match expected schema

**Symptoms:**
```
Error: Failed to validate schema after 3 attempts
Expected field 'summary' but got...
```

**Solutions:**

**1. Check Groq API Status:**
- Visit https://status.groq.com/
- API may be having issues

**2. Try Different Model:**
```bash
# If 70b is failing, try 8b
python backend/scripts/run_summarization.py \
    --model llama-3.1-8b-instant \
    --limit 10
```

**3. Check Article Quality:**
```bash
# Some articles may have bad abstracts
# Check the failed article in database:
sqlite3 data/articles.db
SELECT article_id, title, abstract FROM articles WHERE article_id = 'PMID...';
```

**4. Update Prompts** (if consistent failures):
- Edit `backend/app/genai/prompts.py`
- Test with `--dry-run` first

---

### "Groq API timeout"

**Problem:** API request taking too long

**Symptoms:**
```
Error: Request timeout after 60 seconds
```

**Solutions:**

**1. Retry:**
```bash
# Often transient, just retry
python backend/scripts/run_summarization.py --limit 10
```

**2. Use Faster Model:**
```bash
python backend/scripts/run_summarization.py \
    --model llama-3.1-8b-instant
```

**3. Check API Status:**
- https://status.groq.com/

---

### "File write error: Permission denied"

**Problem:** Cannot write to analysis directory

**Symptoms:**
```
PermissionError: [Errno 13] Permission denied: 'data/analysis/PMID...'
```

**Solutions:**

**1. Check Permissions:**
```bash
ls -la data/
mkdir -p data/analysis
chmod 755 data/analysis
```

**2. Check Disk Space:**
```bash
df -h  # Linux/Mac
# Make sure data/ partition has space
```

**3. Check Path:**
```bash
# Ensure analysis directory exists
mkdir -p data/analysis
```

---

## Performance Issues

### "Ingestion is very slow"

**Problem:** Not using API key or hitting rate limits

**Solutions:**

**1. Get NCBI API Key:**
```bash
# Increases rate from 3 to 10 req/sec (3x speedup)
# Add to .env:
NCBI_API_KEY=your-key-here
```

**2. Use Batch Fetching:**
```bash
# Already optimized (200 articles per request)
# But can increase --max for larger batches
python ingest_cli.py search "query" --max 500
```

---

### "GenAI analysis is very slow"

**Problem:** Using slow model or small batch size

**Solutions:**

**1. Use Faster Model:**
```bash
# 8b is 2-3x faster than 70b
python backend/scripts/run_summarization.py \
    --model llama-3.1-8b-instant \
    --limit 100
```

**2. Increase Batch Size:**
```bash
python backend/scripts/run_summarization.py \
    --batch-size 20 \
    --delay 0.5
```

**3. Reduce Delay:**
```bash
# Only if not hitting rate limits
python backend/scripts/run_summarization.py --delay 0.5
```

---

### "Database queries are slow"

**Problem:** Large database without indexes or needs VACUUM

**Solutions:**

**1. Rebuild Indexes:**
```bash
sqlite3 data/articles.db "REINDEX;"
```

**2. VACUUM Database:**
```bash
sqlite3 data/articles.db "VACUUM;"
```

**3. Analyze Tables:**
```bash
sqlite3 data/articles.db "ANALYZE;"
```

**4. Consider PostgreSQL** (for >100K articles)

---

## Windows-Specific Issues

### Unicode / Emoji Errors

**Problem:** Windows console doesn't support emoji

**Status:** **Already Fixed** - Code uses `[OK]`, `[STATS]` instead of emoji

**If Still Seeing Errors:**
```powershell
# Use PowerShell instead of CMD
# Or set encoding
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
```

---

### "venv\Scripts\activate: cannot be loaded"

**Problem:** PowerShell execution policy

**Solution:**
```powershell
# Option 1: Use .ps1 script
venv\Scripts\Activate.ps1

# Option 2: Change execution policy
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Option 3: Use Command Prompt instead
venv\Scripts\activate.bat
```

---

### Path Issues

**Problem:** Backslash vs forward slash in paths

**Solutions:**
```python
# Use forward slashes in Python (works on Windows too)
"data/analysis/file.json"

# Or use pathlib
from pathlib import Path
path = Path("data") / "analysis" / "file.json"
```

---

## Debugging Tips

### Enable Verbose Logging

```python
# Add to top of script
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Check Environment

```bash
# Print all environment variables
python -c "import os; from dotenv import load_dotenv; load_dotenv(); \
           print('GROQ_API_KEY:', 'SET' if os.getenv('GROQ_API_KEY') else 'NOT SET'); \
           print('NCBI_EMAIL:', os.getenv('NCBI_EMAIL', 'NOT SET'))"
```

### Test Database Connection

```bash
# Quick test
python -c "from app.db.database import get_db; \
           with get_db() as db: \
               c = db.execute('SELECT COUNT(*) FROM articles'); \
               print('Total articles:', c.fetchone()[0])"
```

### Test API Keys

**PubMed:**
```bash
python -c "from app.ingestion.pubmed_connector import PubMedConnector; \
           c = PubMedConnector(); \
           results = c.search('tobacco', max_results=1); \
           print('PubMed API working' if results else 'PubMed API failed')"
```

**Groq:**
```bash
python -c "from groq import Groq; import os; from dotenv import load_dotenv; \
           load_dotenv(); \
           client = Groq(api_key=os.getenv('GROQ_API_KEY')); \
           print('Groq API key valid' if client else 'Invalid key')"
```

---

## Getting More Help

### Check Documentation
1. **README.md** - Quick start and overview
2. **DEVELOPMENT.md** - Setup and development
3. **ARCHITECTURE.md** - System design
4. **API_REFERENCE.md** - CLI commands and Python API

### Check Logs
```bash
# Console output shows most errors
# For detailed errors, enable DEBUG logging
```

### Check GitHub Issues
- Search existing issues
- Create new issue with:
  - Error message (full traceback)
  - Command that failed
  - Environment (OS, Python version)
  - Steps to reproduce

### Community Support
- Check project discussions
- Ask in community channels (if available)

---

## Prevention Best Practices

### 1. Always Use Virtual Environment
```bash
# Before running ANY command:
source venv/bin/activate  # or venv\Scripts\activate
```

### 2. Keep Dependencies Updated
```bash
pip install --upgrade pip
pip install --upgrade -r requirements.txt
```

### 3. Backup Database Regularly
```bash
# Before major operations:
cp data/articles.db data/articles.db.backup.$(date +%Y%m%d)
```

### 4. Monitor API Usage
- Track how many requests you're making
- Stay well under rate limits
- Use API keys where available

### 5. Validate Configuration
```bash
# Before starting work:
python -c "from dotenv import load_dotenv; import os; load_dotenv(); \
           assert os.getenv('NCBI_EMAIL'), 'NCBI_EMAIL not set'; \
           assert os.getenv('GROQ_API_KEY'), 'GROQ_API_KEY not set'; \
           print('Configuration OK')"
```

### 6. Start Small
```bash
# Test with small limits first:
python ingest_cli.py search "query" --max 5
python backend/scripts/run_summarization.py --limit 5 --dry-run
```

### 7. Check Status Before Operations
```bash
# Before ingesting:
python ingest_cli.py stats

# Before analyzing:
python backend/scripts/run_summarization.py --stats-only
```

---

**Still having issues?**
1. Check if issue is already documented above
2. Search GitHub issues
3. Enable DEBUG logging and check full error
4. Create issue with full details

**For more information:**
- [README.md](../README.md) - Getting started
- [DEVELOPMENT.md](../DEVELOPMENT.md) - Setup guide
- [API_REFERENCE.md](API_REFERENCE.md) - Command reference
