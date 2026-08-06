# Integration Guide - Complete 5-Stage Pipeline

This guide covers the integration of all pipeline stages into a unified workflow.

## Quick Start

### Option 1: Full Pipeline Orchestrator (Recommended)

Run the complete workflow with a single command:

```bash
python scripts/full_pipeline.py --topic "Heat-Not-Burn" --max-articles 50 --archive
```

### Option 2: Manual Stage Execution

Run each stage individually for more control:

```bash
# Stage 1: Ingestion
python ingest_cli.py topic "Heat-Not-Burn" --sources pubmed --max 50

# Stage 2: Summarization
python backend/scripts/run_summarization.py --limit 50

# Stage 3: Evaluation
python scripts/evaluate_summaries.py --source raw

# Stage 4: Re-inference (if needed)
python scripts/reinfer_summaries.py

# Stage 5: Database Load
python scripts/load_to_database.py --archive
```

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                        FULL PIPELINE ORCHESTRATOR                    │
│                      (scripts/full_pipeline.py)                      │
└─────────────────────────────────────────────────────────────────────┘
                                    │
        ┌───────────────────────────┼───────────────────────────┐
        ▼                           ▼                           ▼
┌───────────────┐          ┌────────────────┐          ┌──────────────┐
│   Stage 1     │          │    Stage 2     │          │   Stage 3    │
│  Ingestion    │   ───>   │ Summarization  │   ───>   │  Evaluation  │
│   (PubMed)    │          │   (Groq LLM)   │          │  (Quality)   │
└───────────────┘          └────────────────┘          └──────────────┘
                                                               │
                                                   ┌───────────┴────────────┐
                                                   │                        │
                                                   ▼                        ▼
                                          ┌─────────────┐         ┌─────────────────┐
                                          │   Stage 4   │         │    Stage 5      │
                                          │ Re-inference│ ───>    │  Database Load  │
                                          │ (If needed) │         │   (article_     │
                                          └─────────────┘         │    analysis)    │
                                                                  └─────────────────┘
```

## Integration Points

### Stage 1 → Stage 2: Ingestion to Summarization

**Data Flow:**
- Articles stored in `articles` table
- ArticleAnalysisPipeline queries pending articles (WHERE summary IS NULL)
- Only unprocessed articles enter Stage 2

**Files Involved:**
- `ingest_cli.py` → writes to `articles` table
- `backend/app/genai/repository.py` → reads from `articles` table
- `backend/scripts/run_summarization.py` → orchestrates Stage 2

**Key Function:**
```python
def get_articles_pending_analysis(limit=None):
    """Fetch articles where summary IS NULL"""
```

### Stage 2 → Stage 3: Summarization to Evaluation

**Data Flow:**
- Summaries saved as JSON files in `data/analysis/raw/`
- Evaluator reads JSON files from `raw/`
- Routes to `approved/` or `reinfer/` based on quality score

**Files Involved:**
- `backend/app/genai/pipeline.py` → writes to `raw/`
- `backend/app/genai/file_writer.py` → manages file routing
- `scripts/evaluate_summaries.py` → reads from `raw/`, routes files

**Key Schema:**
```json
{
  "articleID": "PMID12345",
  "title": "...",
  "summary": "...",
  "category": "...",
  "sentiment": "...",
  "entity": [...]
}
```

### Stage 3 → Stage 4: Evaluation to Re-inference

**Data Flow:**
- Low-quality summaries (< threshold) → `reinfer/`
- Re-inference script processes `reinfer/` directory
- Improved summaries re-evaluated → `approved/` or `rejected/`

**Files Involved:**
- `scripts/evaluate_summaries.py` → moves to `reinfer/`
- `scripts/reinfer_summaries.py` → processes `reinfer/`, re-evaluates
- Max 3 attempts before moving to `rejected/`

**Metadata Tracking:**
```json
{
  "_metadata": {
    "attempt": 2,
    "previous_score": 65,
    "feedback": "Improve people-first language"
  }
}
```

### Stage 4 → Stage 5: Re-inference to Database Load

**Data Flow:**
- Approved summaries in `approved/` directory
- Database loader reads JSON files
- Inserts/updates `article_analysis` table
- Archives to `loaded/` (optional)

**Files Involved:**
- `scripts/reinfer_summaries.py` → final routing to `approved/`
- `backend/app/genai/db_loader.py` → AnalysisDatabaseLoader
- `scripts/load_to_database.py` → CLI interface

**Database Schema:**
```sql
INSERT INTO article_analysis (
    article_id, subject, category, summary,
    entities, sentiment, industry_affiliation
) VALUES (?, ?, ?, ?, ?, ?, ?)
ON CONFLICT(article_id) DO UPDATE SET ...
```

## Error Handling

### Retry Mechanisms

**Stage 2 (Summarization):**
- Schema validation errors: 3 retries with feedback
- API rate limits: exponential backoff
- Individual failures don't stop batch

**Stage 3 (Evaluation):**
- LLM errors: continue to next file
- Malformed JSON: skip with error log

**Stage 4 (Re-inference):**
- Max 3 attempts per article
- After 3 failures → move to `rejected/`

**Stage 5 (Database Load):**
- Missing article in `articles` table → error, don't delete file
- Duplicate article_id → UPDATE existing record
- Transaction rollback on error

### Recovery Strategies

**Pipeline Interrupted:**
```bash
# Resume from specific stage
python scripts/full_pipeline.py --stages summarize evaluate load --limit 100
```

**Stage-Specific Failures:**
```bash
# Check failed articles
SELECT * FROM article_analysis WHERE analysis_status = 'failed';

# Retry failed summaries
python backend/scripts/run_summarization.py --retry-failed

# Re-evaluate specific directory
python scripts/evaluate_summaries.py --source reinfer
```

**File System Issues:**
```bash
# Check directory structure
ls -R data/analysis/

# Find orphaned files
find data/analysis/ -name "*.json" -type f

# Verify file counts
echo "Raw: $(ls data/analysis/raw/*.json 2>/dev/null | wc -l)"
echo "Approved: $(ls data/analysis/approved/*.json 2>/dev/null | wc -l)"
echo "Reinfer: $(ls data/analysis/reinfer/*.json 2>/dev/null | wc -l)"
```

## Integration Testing

### Running Tests

```bash
# Full integration test suite
pytest tests/test_integration.py -v

# Specific test class
pytest tests/test_integration.py::TestFullPipelineIntegration -v

# Test coverage
pytest tests/test_integration.py --cov=backend/app --cov-report=html
```

### Test Categories

**1. Stage-to-Stage Integration:**
- `test_stage_1_to_2_ingestion_to_summarization`
- `test_stage_2_to_3_summarization_to_evaluation`
- `test_stage_3_to_4_evaluation_to_reinference`
- `test_stage_4_to_5_reinference_to_database_load`

**2. End-to-End Workflows:**
- `test_end_to_end_happy_path` - Complete success flow
- `test_end_to_end_with_reinference` - Quality improvement loop

**3. Error Handling:**
- `test_missing_article_in_database`
- `test_malformed_json_file`
- `test_max_reinference_attempts`

**4. Data Integrity:**
- `test_article_id_consistency`
- `test_no_data_loss_on_error`

### Test Fixtures

```python
@pytest.fixture
def test_dirs(tmp_path):
    """Create temporary directory structure"""

@pytest.fixture
def test_db(tmp_path):
    """Create temporary test database"""

@pytest.fixture
def sample_article():
    """Sample article data for testing"""
```

## Monitoring and Observability

### Pipeline Statistics

```bash
# Get real-time statistics
python scripts/full_pipeline.py --topic "Heat-Not-Burn" --max-articles 50

# Output includes:
#   - Ingested count
#   - Summarized count
#   - Evaluation pass/fail rates
#   - Re-inference success rate
#   - Database load success
```

### Directory Monitoring

```bash
# File counts by stage
echo "=== Pipeline Status ==="
echo "Raw (Stage 2):       $(ls data/analysis/raw/*.json 2>/dev/null | wc -l)"
echo "Approved (Stage 3):  $(ls data/analysis/approved/*.json 2>/dev/null | wc -l)"
echo "Reinfer (Stage 4):   $(ls data/analysis/reinfer/*.json 2>/dev/null | wc -l)"
echo "Rejected (Stage 4):  $(ls data/analysis/rejected/*.json 2>/dev/null | wc -l)"
echo "Loaded (Stage 5):    $(ls data/analysis/loaded/*.json 2>/dev/null | wc -l)"
```

### Database Queries

```sql
-- Pipeline progress
SELECT 
    COUNT(*) as total_articles,
    SUM(CASE WHEN summary IS NOT NULL THEN 1 ELSE 0 END) as analyzed,
    SUM(CASE WHEN summary IS NULL THEN 1 ELSE 0 END) as pending
FROM articles a
LEFT JOIN article_analysis aa ON a.article_id = aa.article_id;

-- Quality distribution
SELECT 
    category,
    sentiment,
    COUNT(*) as count
FROM article_analysis
GROUP BY category, sentiment
ORDER BY count DESC;

-- Recent processing
SELECT 
    article_id,
    analysis_status,
    analyzed_at
FROM article_analysis
ORDER BY analyzed_at DESC
LIMIT 20;
```

## Performance Optimization

### Batch Processing

```bash
# Large datasets (>1000 articles)
python scripts/full_pipeline.py \
    --topic "Heat-Not-Burn" \
    --max-articles 1000 \
    --limit 100 \
    --archive

# Breaks into batches of 100
# Reduces memory usage
# Allows progress tracking
```

### Parallel Processing

Current implementation is sequential. For production scale:

```python
# Future: Parallel summarization (Stage 2)
from concurrent.futures import ThreadPoolExecutor

# Process 5 articles simultaneously
with ThreadPoolExecutor(max_workers=5) as executor:
    results = executor.map(summarize_article, articles)
```

### Caching Strategy

```python
# File-based caching (current)
- Raw summaries cached in files
- Evaluation results cached with metadata
- Database serves as final cache

# Future: Redis caching
- Cache pending articles list
- Cache evaluation scores
- Distributed processing support
```

## Best Practices

### Development Workflow

1. **Start Small:**
   ```bash
   python scripts/full_pipeline.py --limit 10 --dry-run
   ```

2. **Test Each Stage:**
   ```bash
   pytest tests/test_integration.py::TestFullPipelineIntegration -v
   ```

3. **Manual Verification:**
   ```bash
   # Check file routing
   ls -lh data/analysis/{raw,approved,reinfer,rejected}/
   
   # Verify database
   python view_data.py --stats
   ```

### Production Workflow

1. **Use Orchestrator:**
   ```bash
   python scripts/full_pipeline.py \
       --topic "Heat-Not-Burn" \
       --max-articles 500 \
       --threshold 85 \
       --archive
   ```

2. **Monitor Logs:**
   ```bash
   # Redirect to log file
   python scripts/full_pipeline.py ... 2>&1 | tee pipeline.log
   ```

3. **Scheduled Runs:**
   ```bash
   # Cron job (daily at 2 AM)
   0 2 * * * cd /path/to/radar && \
       /path/to/venv/bin/python scripts/full_pipeline.py \
       --topic "Heat-Not-Burn" --max-articles 50 --archive \
       >> logs/pipeline_$(date +\%Y\%m\%d).log 2>&1
   ```

4. **Health Checks:**
   ```bash
   # Alert on failures
   if [ -z "$(ls data/analysis/approved/*.json 2>/dev/null)" ]; then
       echo "WARNING: No approved summaries" | mail -s "Pipeline Alert" admin@example.com
   fi
   ```

## Troubleshooting

### Common Issues

**Issue: "No articles need processing"**
```bash
# Solution: Run ingestion first
python ingest_cli.py topic "Heat-Not-Burn" --max 50
python scripts/full_pipeline.py --stages summarize evaluate load
```

**Issue: "All summaries fail evaluation"**
```bash
# Check threshold
python scripts/full_pipeline.py --threshold 70  # Lower threshold

# Or improve prompt
vim backend/app/genai/prompts.py  # Edit summarization_prompt
```

**Issue: "Database load fails"**
```bash
# Verify article exists
SELECT article_id FROM articles WHERE article_id = 'PMID...';

# Check schema
python scripts/load_to_database.py --migrate-only
```

**Issue: "Files stuck in reinfer/"**
```bash
# Check attempt count
cat data/analysis/reinfer/*.json | grep '"attempt"'

# Force approval (if quality is acceptable)
mv data/analysis/reinfer/*.json data/analysis/approved/
python scripts/load_to_database.py --archive
```

## File Lifecycle Management

### The Problem

Without cleanup, files accumulate indefinitely:
- `raw/` - Summaries after Stage 2
- `approved/` - After evaluation (stays even after DB load)
- `reinfer/` - Failed summaries
- `rejected/` - Failed after max attempts
- `loaded/` - Archived successful loads

### Solution 1: Automatic Cleanup (Recommended)

Enable automatic cleanup when running the pipeline:

```bash
# Auto-archive files older than 7 days
python scripts/full_pipeline.py \
    --topic "Heat-Not-Burn" \
    --max-articles 50 \
    --archive \
    --auto-cleanup
```

Files older than 7 days in `raw/` and `evaluated/` are automatically moved to:
```
data/analysis/archive/
  ├── raw/20260806/
  └── evaluated/20260806/
```

### Solution 2: Manual Cleanup Tool

Use the dedicated cleanup script for more control:

```bash
# Dry run (see what would be cleaned)
python scripts/cleanup_pipeline.py --dry-run

# Archive files older than 30 days
python scripts/cleanup_pipeline.py --archive --days 30

# Delete files older than 90 days
python scripts/cleanup_pipeline.py --delete --days 90

# Clean specific directory
python scripts/cleanup_pipeline.py --dir raw --archive --days 7

# Aggressive cleanup (delete everything in raw/)
python scripts/cleanup_pipeline.py --aggressive --dir raw
```

### Solution 3: Scheduled Cleanup (Production)

Add to crontab for automated maintenance:

```bash
# Weekly: Archive processed files (every Sunday at 3 AM)
0 3 * * 0 cd /path/to/radar && \
    python scripts/cleanup_pipeline.py --archive --days 7

# Monthly: Delete old archives (1st of month at 4 AM)
0 4 1 * * cd /path/to/radar && \
    python scripts/cleanup_pipeline.py --delete --days 90
```

### Cleanup Strategy by Directory

**raw/** - Archive after 7 days
- Files have been evaluated and routed
- Safe to archive once evaluation complete

**approved/** - Keep until DB load (auto-cleaned by Stage 5 with --archive)
- Should be loaded to DB quickly
- Stage 5 with --archive flag moves to `loaded/`

**reinfer/** - Archive after 30 days
- May need manual review if stuck
- Check before cleanup: `ls -lh data/analysis/reinfer/`

**rejected/** - Archive after 90 days
- Failed max attempts (3x)
- Keep for analysis/debugging
- Eventually can be deleted

**loaded/** - Delete after 180 days
- Successfully loaded to database
- Can be recreated from DB if needed

### Best Practices

1. **Enable --auto-cleanup for daily runs**
   ```bash
   python scripts/full_pipeline.py --auto-cleanup
   ```

2. **Manual review before aggressive cleanup**
   ```bash
   # Check what's in directory first
   ls -lh data/analysis/raw/
   
   # Then clean if safe
   python scripts/cleanup_pipeline.py --dir raw --archive --days 7
   ```

3. **Keep archives for audit trail**
   - Don't delete archives immediately
   - Useful for troubleshooting quality issues
   - Can compare old vs new summaries

4. **Monitor disk usage**
   ```bash
   du -sh data/analysis/*
   ```

5. **Set up alerts**
   ```bash
   # Alert if raw/ exceeds 1000 files
   COUNT=$(ls data/analysis/raw/*.json 2>/dev/null | wc -l)
   if [ $COUNT -gt 1000 ]; then
       echo "WARNING: $COUNT files in raw/ - cleanup needed"
   fi
   ```

## See Also

- [GenAI Pipeline Documentation](GENAI_PIPELINE.md)
- [Evaluation Module](EVALUATOR_MODULE.md)
- [Database Load Documentation](STAGE_5_DATABASE_LOAD.md)
- [README - Quick Start](../README.md)
