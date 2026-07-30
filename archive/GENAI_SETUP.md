# GenAI Pipeline - Quick Setup Guide

## Overview

The GenAI pipeline is now organized in a proper backend structure under `backend/app/genai/`.

## File Organization

### Before (Root Level - ❌ Removed)
```
❌ schema.py
❌ prompt.py
❌ summarization.py
❌ article_repository.py
❌ summarization_pipeline.py
❌ test_summarization.py
❌ SUMMARIZATION_README.md
```

### After (Organized Structure - ✅ New)
```
✅ backend/app/genai/
   ├── __init__.py           # Module exports
   ├── schemas.py            # Pydantic models (was: schema.py)
   ├── prompts.py            # LLM prompts (was: prompt.py)
   ├── summarizer.py         # Core logic (was: summarization.py)
   ├── repository.py         # Data access (was: article_repository.py)
   └── pipeline.py           # Orchestration (was: summarization_pipeline.py)

✅ backend/scripts/
   └── run_summarization.py  # CLI entry point (new)

✅ tests/
   └── test_genai.py         # Test suite (was: test_summarization.py)

✅ docs/
   ├── GENAI_PIPELINE.md     # Detailed docs (was: SUMMARIZATION_README.md)
   ├── GENAI_SETUP.md        # This file
   └── PROJECT_STRUCTURE.md  # Full project structure
```

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

This installs:
- `langchain-groq` - Groq LLM integration
- `langchain-core` - LangChain framework
- `pydantic` - Schema validation
- `tqdm` - Progress bars

### 2. Configure API Key

Get your Groq API key from: https://console.groq.com/keys

Add to `.env`:
```bash
GROQ_API_KEY=gsk_your_key_here
```

### 3. Run Tests

```bash
python tests/test_genai.py
```

Expected output:
```
================================================================================
GENAI SUMMARIZATION PIPELINE - TEST SUITE
================================================================================
Testing imports...
✓ All imports successful

Testing schema...
✓ Schema validation successful
  - Article ID: TEST001
  - Subject: E-cigarettes
  - Entities: ['electronic cigarettes']

Testing repository...
✓ Pending articles: 0
✓ Total articles: 0
✓ Analyzed: 0

Testing API key...
✓ GROQ_API_KEY found (gsk_abcdef...)

Testing summarizer...
✓ Summarizer initialized
  - Model: llama-3.3-70b-versatile
  - Temperature: 0.0

Testing sample article summarization...
  Sending request to Groq...
✓ Summarization successful!

  Results:
  - Subject: E-cigarettes
  - Category: Clinical Studies
  - Entities: ['electronic cigarettes', 'cardiovascular disease', ...]
  - Sentiment: Positive
  - Summary: This randomized controlled trial examined...

================================================================================
TEST SUMMARY
================================================================================
✓ PASS     Imports
✓ PASS     Schema
✓ PASS     Repository
✓ PASS     API Key
✓ PASS     Summarizer Init
✓ PASS     Sample Article

Total: 6 | Passed: 6 | Failed: 0 | Skipped: 0

✓ All tests passed! Pipeline is ready to use.

Next steps:
  1. Check pending articles: python backend/scripts/run_summarization.py --stats-only
  2. Run pipeline: python backend/scripts/run_summarization.py --limit 10
```

### 4. Check Database

```bash
python backend/scripts/run_summarization.py --stats-only
```

Output:
```
================================================================================
DATABASE STATISTICS
================================================================================
Total articles:       250
Analyzed:             0
Pending:              250

By Status:
  (empty - no analysis yet)

By Category:
  (empty - no analysis yet)

By Sentiment:
  (empty - no analysis yet)
================================================================================
```

### 5. Run Pipeline

**Dry run (test without saving):**
```bash
python backend/scripts/run_summarization.py --limit 5 --dry-run
```

**Process 10 articles:**
```bash
python backend/scripts/run_summarization.py --limit 10
```

**Process all pending:**
```bash
python backend/scripts/run_summarization.py
```

## Import Paths (Updated)

### Old (❌ Don't use)
```python
# These imports will fail now
from schema import Response
from prompt import summarization_prompt
from summarization import ArticleSummarizer
from article_repository import ArticleRepository
from summarization_pipeline import SummarizationPipeline
```

### New (✅ Use these)
```python
# Individual imports
from backend.app.genai.schemas import Response, EntityEnum, CategoryEnum
from backend.app.genai.prompts import summarization_prompt
from backend.app.genai.summarizer import ArticleSummarizer, summarize_article
from backend.app.genai.repository import ArticleRepository
from backend.app.genai.pipeline import SummarizationPipeline

# Or use the module-level exports
from backend.app.genai import (
    ArticleSummarizer,
    summarize_article,
    ArticleRepository,
    SummarizationPipeline
)
```

## CLI Commands

All GenAI commands now use the organized structure:

### Check Statistics
```bash
python backend/scripts/run_summarization.py --stats-only
```

### Process Articles
```bash
# Basic
python backend/scripts/run_summarization.py --limit 10

# With custom settings
python backend/scripts/run_summarization.py \
    --model llama-3.3-70b-versatile \
    --batch-size 10 \
    --delay 1.0 \
    --limit 50

# Dry run
python backend/scripts/run_summarization.py --limit 5 --dry-run
```

### Available Options
```
--limit N              Max articles to process
--model MODEL          Groq model name
--batch-size N         Articles per batch (default: 10)
--delay SECONDS        Delay between batches (default: 1.0)
--dry-run              Process but don't save
--stats-only           Show statistics only
```

## Module Structure

### `backend/app/genai/__init__.py`

Exports main classes for easy importing:

```python
from .summarizer import ArticleSummarizer, summarize_article
from .repository import ArticleRepository
from .pipeline import SummarizationPipeline

__all__ = [
    'ArticleSummarizer',
    'summarize_article',
    'ArticleRepository',
    'SummarizationPipeline',
]
```

### `backend/app/genai/schemas.py`

Pydantic models:
- `Response` - Main article analysis schema
- `EntityEnum` - Topic entities (55 predefined + 'others')
- `CategoryEnum` - Research categories (9 types)
- `SentimentEnum` - THR sentiment (5 levels)
- `SubjectEnum` - Broad subjects (5 areas)

### `backend/app/genai/prompts.py`

Prompt templates:
- `summarization_prompt` - Main analysis prompt
- `revalidate_prompt` - Schema validation retry
- `summary_evaluation_prompt` - Fact checking
- `reinfer_prompt` - Iterative improvement

### `backend/app/genai/summarizer.py`

Core LLM service:
- `ArticleSummarizer` class - Main summarization logic
- `summarize_article()` function - Convenience wrapper

Uses:
- Groq for LLM inference
- LangChain for prompt management
- Pydantic for structured output

### `backend/app/genai/repository.py`

Database operations:
- `get_articles_pending_analysis()` - Fetch WHERE summary IS NULL
- `count_articles_pending_analysis()` - Count pending
- `save_analysis()` - Store results
- `mark_analysis_failed()` - Track failures
- `get_analysis_stats()` - Statistics

### `backend/app/genai/pipeline.py`

Batch processing orchestrator:
- `SummarizationPipeline` class
- Batch processing with progress bars
- Rate limiting
- Error handling and recovery
- Statistics reporting

## Testing

### Run All Tests
```bash
python tests/test_genai.py
```

### Test Individual Components

**Test imports:**
```python
from backend.app.genai import ArticleSummarizer, ArticleRepository
print("Imports successful!")
```

**Test repository:**
```python
from backend.app.genai import ArticleRepository

repo = ArticleRepository()
pending = repo.count_articles_pending_analysis()
print(f"Pending: {pending}")
```

**Test summarizer:**
```python
from backend.app.genai import summarize_article

result = summarize_article(
    doc_id="TEST001",
    title="Your title",
    journal="Your journal",
    date="2024-01-15",
    abstract="Your abstract"
)
print(result.summary)
```

## Troubleshooting

### Import Errors

**Error:** `ModuleNotFoundError: No module named 'schema'`

**Solution:** Update imports to use new paths:
```python
# Old
from schema import Response

# New
from backend.app.genai.schemas import Response
```

### Missing Dependencies

**Error:** `ModuleNotFoundError: No module named 'langchain_groq'`

**Solution:** Install requirements:
```bash
pip install -r requirements.txt
```

### API Key Not Found

**Error:** `GROQ_API_KEY environment variable not set`

**Solution:** Add to `.env`:
```bash
GROQ_API_KEY=gsk_your_key_here
```

### Database Errors

**Error:** `sqlite3.OperationalError: no such table: article_analysis`

**Solution:** Initialize database:
```bash
python ingest_cli.py init
```

## Documentation

- **[GENAI_PIPELINE.md](GENAI_PIPELINE.md)** - Detailed pipeline documentation
- **[PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)** - Full project structure
- **[README.md](../README.md)** - Main project README

## Next Steps

After setup:

1. **Ingest articles:**
   ```bash
   python ingest_cli.py search "tobacco" --sources pubmed --max 50
   ```

2. **Run GenAI analysis:**
   ```bash
   python backend/scripts/run_summarization.py --limit 10
   ```

3. **View results:**
   ```bash
   python view_data.py --limit 5 --format detailed
   ```

4. **Build dashboards** or **export data** using the analyzed results

## Benefits of New Structure

✅ **Organized** - Clear module boundaries  
✅ **Maintainable** - Easy to find and update code  
✅ **Testable** - Isolated components  
✅ **Scalable** - Easy to add new features  
✅ **Professional** - Follows Python best practices  
✅ **Documented** - Clear documentation and examples
