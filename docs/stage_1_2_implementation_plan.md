# Stage 1 & 2 Implementation Plan
## File-based GenAI Pipeline with Quality Control

**Date:** 2026-07-28  
**Status:** Implementation Ready

---

## Current System Analysis

### Existing Components ✅

#### 1. **Database Layer** (`backend/app/db/database.py`)
- ✅ SQLite database at `data/articles.db`
- ✅ `articles` table with all metadata
- ✅ `article_analysis` table for results
- ✅ Proper indexes on key columns
- ✅ Context manager for connections

#### 2. **Repository Layer** (`backend/app/genai/repository.py`)
- ✅ `get_articles_pending_analysis()` - Stage 1 functionality EXISTS
- ✅ `count_articles_pending_analysis()` - Counting logic EXISTS
- ✅ `save_analysis()` - Saves to database directly
- ✅ `mark_analysis_failed()` - Error handling
- ✅ `get_analysis_stats()` - Statistics

**Current Query Logic:**
```sql
SELECT a.* FROM articles a
LEFT JOIN article_analysis aa ON a.article_id = aa.article_id
WHERE aa.article_id IS NULL
   OR aa.summary IS NULL
   OR aa.summary = ''
   OR aa.analysis_status IN ('pending', 'failed')
```
✅ **Already implements Stage 1 requirement!**

#### 3. **Summarization Layer** (`backend/app/genai/summarizer.py`)
- ✅ `ArticleSummarizer` class using Groq LLM
- ✅ Structured output with Pydantic schemas
- ✅ Retry logic for validation errors (max 3 attempts)
- ✅ LangChain integration

#### 4. **Pipeline Orchestrator** (`backend/app/genai/pipeline.py`)
- ✅ `SummarizationPipeline` class
- ✅ Batch processing with configurable batch size
- ✅ Progress tracking with tqdm
- ✅ Rate limiting between batches
- ✅ Statistics reporting
- ❌ **Currently saves directly to database** (needs modification)

#### 5. **Schemas** (`backend/app/genai/schemas.py`)
- ✅ `Response` - Complete Pydantic model for article analysis
- ✅ Enums for entity, category, sentiment, subject
- ✅ Validation logic

#### 6. **CLI Script** (`backend/scripts/run_summarization.py`)
- ✅ Command-line interface with argparse
- ✅ Options for limit, model, batch-size, dry-run
- ✅ Statistics-only mode

---

## What Needs to be Modified ❗

### 1. **Pipeline Class** (`backend/app/genai/pipeline.py`)

**Current Behavior:**
```python
# Lines 158-168
if result:
    stats['successful'] += 1
    if not dry_run:
        saved = self.repo.save_analysis(...)  # ❌ Saves to DB directly
```

**Required Changes:**
- ❌ Remove direct `save_analysis()` call in processing loop
- ✅ Add JSON file writing to `data/analysis/raw/{article_id}.json`
- ✅ Keep metadata (processing time, tokens, cost) in JSON
- ✅ Add stage tracking ("raw", "evaluated", "approved", etc.)

**New Method Needed:**
```python
def save_raw_json(self, article_id: str, result: Response, metadata: Dict) -> bool:
    """Save raw GenAI output to JSON file."""
```

### 2. **Database Schema** (Optional but Recommended)

**Add column to articles table:**
```sql
ALTER TABLE articles ADD COLUMN summary_status TEXT DEFAULT NULL;
CREATE INDEX idx_articles_summary_status ON articles(summary_status);
```

**Possible values:**
- `NULL` = Not yet processed
- `'processing'` = Currently being processed  
- `'completed'` = Analysis loaded to database
- `'failed'` = Needs manual review

**Update Repository Methods:**
```python
def get_articles_pending_analysis():
    # Add: WHERE a.summary_status IS NULL
```

---

## What Needs to be Added Fresh 🆕

### 1. **Directory Structure**

Create folders under `data/`:
```
data/
├── articles.db                  # Existing
└── analysis/                    # NEW
    ├── raw/                     # Stage 2 output
    ├── evaluated/               # Stage 3 (future)
    ├── approved/                # Stage 3 (future)
    ├── reinfer/                 # Stage 3 (future)
    ├── rejected/                # Stage 3 (future)
    └── manifest.json            # Tracking file (future)
```

### 2. **File Writer Module** (`backend/app/genai/file_writer.py`) 🆕

```python
"""
File-based output writer for GenAI pipeline.
Saves article analysis to JSON files.
"""

class AnalysisFileWriter:
    """Handles writing analysis results to JSON files."""
    
    def __init__(self, base_dir: str = "data/analysis"):
        self.base_dir = Path(base_dir)
        self.raw_dir = self.base_dir / "raw"
        # Create directories
        
    def save_raw_analysis(
        self, 
        article_id: str,
        response: Response,
        metadata: Dict[str, Any]
    ) -> Path:
        """Save raw GenAI output to JSON."""
        
    def load_raw_analysis(self, article_id: str) -> Dict:
        """Load raw analysis from JSON."""
        
    def get_processing_stats(self) -> Dict:
        """Get statistics from JSON files."""
```

### 3. **Enhanced Metadata Tracking** 🆕

Add to `pipeline.py`:
```python
def process_article(self, article: Dict[str, Any]) -> Dict[str, Any]:
    """
    Returns:
        {
            'result': Response object,
            'metadata': {
                'processing_time_ms': int,
                'tokens_used': int,
                'cost': float,
                'attempt': int,
                'model': str,
                'prompt_version': str
            }
        }
    """
```

### 4. **Configuration Module** (`backend/app/genai/config.py`) 🆕

```python
"""Configuration for GenAI pipeline."""

class PipelineConfig:
    # File paths
    BASE_DIR = Path("data/analysis")
    RAW_DIR = BASE_DIR / "raw"
    
    # Processing settings
    MAX_RETRIES = 3
    BATCH_SIZE = 10
    DELAY_BETWEEN_BATCHES = 1.0
    
    # Future: Evaluation settings
    PASSING_SCORE_THRESHOLD = 80
    MAX_REINFER_ATTEMPTS = 3
    
    # Model settings
    DEFAULT_MODEL = "llama-3.3-70b-versatile"
    PROMPT_VERSION = "v1"
```

---

## Implementation Steps (Stage 1 & 2 Only)

### Step 1: Create Directory Structure ✅
```bash
mkdir -p data/analysis/{raw,evaluated,approved,reinfer,rejected}
```

### Step 2: Create `file_writer.py` Module 🆕
- Implement `AnalysisFileWriter` class
- Methods for save/load JSON files
- Proper error handling

### Step 3: Create `config.py` Module 🆕
- Centralized configuration
- Easy to modify for future stages

### Step 4: Modify `pipeline.py` ✏️
**Changes needed:**
1. Import `AnalysisFileWriter`
2. Initialize writer in `__init__`
3. Modify `process_article()` to track metadata:
   - Start time, end time → processing_time_ms
   - Model tokens (if available from Groq response)
   - Cost calculation
4. Modify `run()` method:
   - Replace `self.repo.save_analysis()` with `self.writer.save_raw_analysis()`
   - Keep dry-run functionality
5. Add new method `save_raw_json()`

### Step 5: Modify `repository.py` ✏️ (Optional)
- Update queries to use `summary_status` column
- Add method to update `summary_status`

### Step 6: Update CLI Script ✏️
- Add `--output-format` option: `json` (new) or `database` (old)
- Add `--analysis-dir` option for custom output directory

### Step 7: Test with Small Batch ✅
```bash
python backend/scripts/run_summarization.py \
  --limit 10 \
  --output-format json \
  --dry-run
```

---

## File Format Specification

### Raw Analysis File (`raw/PMID001.json`)

```json
{
  "article_id": "PMID001",
  "stage": "raw",
  "attempt": 1,
  "processed_at": "2026-07-28T10:30:00Z",
  "model": "llama-3.3-70b-versatile",
  "prompt_version": "v1",
  
  "source_data": {
    "title": "Article Title",
    "journal": "Journal Name",
    "publication_date": "2024-01-15",
    "abstract": "Original abstract text...",
    "doi": "10.1234/example",
    "source": "pubmed"
  },
  
  "analysis": {
    "articleID": "PMID001",
    "title": "Article Title",
    "journal": "Journal Name",
    "date": "2024-01-15",
    "abstract": "Original abstract text...",
    "entity": ["electronic cigarettes", "harm reduction"],
    "subject": "E-cigarettes",
    "summary": "AI-generated summary with people-first language...",
    "category": "Clinical Studies",
    "country": "United States",
    "sentiment": "Positive",
    "industry_affiliation": "n/a"
  },
  
  "metadata": {
    "processing_time_ms": 3450,
    "tokens_used": 1250,
    "cost_usd": 0.0015,
    "model_id": "llama-3.3-70b-versatile",
    "prompt_version": "v1",
    "success": true,
    "error": null
  }
}
```

---

## Modified Pipeline Flow (Stage 1 & 2)

```
┌─────────────────────────────────────────────────────────────┐
│ STAGE 1: FETCH PENDING                                      │
└─────────────────────────────────────────────────────────────┘
                            ↓
        SELECT * FROM articles a
        LEFT JOIN article_analysis aa ON a.article_id = aa.article_id
        WHERE aa.article_id IS NULL
           OR aa.summary IS NULL
           OR aa.analysis_status IN ('pending', 'failed')
                            ↓
                    [N pending articles]

┌─────────────────────────────────────────────────────────────┐
│ STAGE 2: GENAI SUMMARIZATION                                │
└─────────────────────────────────────────────────────────────┘
                            ↓
            For each article (in batches):
              1. Run GenAI summarization
              2. Track metadata (time, tokens, cost)
              3. Save to: data/analysis/raw/{article_id}.json
                            ↓
            ✅ Files created: PMID001.json, PMID002.json, ...

┌─────────────────────────────────────────────────────────────┐
│ FUTURE: STAGE 3 (Evaluation) - Not implemented yet          │
│ FUTURE: STAGE 4 (Load to DB) - Not implemented yet          │
└─────────────────────────────────────────────────────────────┘
```

---

## Code Changes Summary

### Files to Modify ✏️
1. `backend/app/genai/pipeline.py` - Main processing loop
2. `backend/app/genai/repository.py` - Add summary_status tracking (optional)
3. `backend/scripts/run_summarization.py` - Add CLI options

### Files to Create 🆕
1. `backend/app/genai/file_writer.py` - JSON file operations
2. `backend/app/genai/config.py` - Configuration constants

### Database Changes (Optional) 🗄️
1. Add `summary_status` column to `articles` table
2. Create index on `summary_status`

---

## Benefits of This Approach

### ✅ Advantages
1. **No Database Changes Required** (for basic implementation)
   - Can use existing query logic
   - `summary_status` column is optional enhancement

2. **Backward Compatible**
   - Existing code continues to work
   - Can run old and new pipelines side-by-side

3. **Easy Testing**
   - Dry-run mode works the same
   - Can inspect JSON files directly
   - No DB clutter during experimentation

4. **Separation of Concerns**
   - Processing layer → JSON files
   - Serving layer → Database (future Stage 4)
   - Evaluation layer → Separate module (future Stage 3)

5. **Traceability**
   - Every article has a JSON file with full metadata
   - Can re-process without re-running GenAI
   - Complete audit trail

### 📊 What We Keep from Current System
- ✅ Repository query logic (`get_articles_pending_analysis`)
- ✅ Summarizer class (no changes needed)
- ✅ Schemas (no changes needed)
- ✅ Batch processing logic
- ✅ Rate limiting
- ✅ Progress tracking
- ✅ Statistics reporting

### 🔄 What Changes
- ❌ No longer saves to `article_analysis` table during processing
- ✅ Saves to `data/analysis/raw/*.json` instead
- ✅ Adds metadata tracking (time, tokens, cost)
- ✅ Prepares for Stage 3 (evaluation)

---

## Testing Plan

### 1. Unit Tests
```python
# test_file_writer.py
def test_save_raw_analysis():
    writer = AnalysisFileWriter()
    result = writer.save_raw_analysis(...)
    assert result.exists()

def test_load_raw_analysis():
    data = writer.load_raw_analysis("PMID001")
    assert data['stage'] == 'raw'
```

### 2. Integration Test
```bash
# Process 10 articles to JSON
python backend/scripts/run_summarization.py \
  --limit 10 \
  --output-format json

# Verify files created
ls -la data/analysis/raw/ | wc -l  # Should show 10 files
```

### 3. Performance Test
```bash
# Process 100 articles, measure time
time python backend/scripts/run_summarization.py \
  --limit 100 \
  --output-format json
```

---

## Next Steps (After Stage 1 & 2)

Once Stage 1 & 2 are complete:

1. **Stage 3: Evaluation Pipeline**
   - Create `evaluator.py` module
   - Implement scoring logic
   - Add reinfer loop
   - Move files: raw → evaluated → approved/rejected

2. **Stage 4: Load to Database**
   - Bulk loader script
   - Read from `approved/*.json`
   - Insert into `article_analysis` table
   - Update `articles.summary_status = 'completed'`

3. **Stage 5: Serving Layer**
   - No changes needed (existing API works)
   - Dashboard queries existing database

---

## Estimated Effort

| Task | Effort | Priority |
|------|--------|----------|
| Create directory structure | 5 min | P0 |
| Create `file_writer.py` | 2 hours | P0 |
| Create `config.py` | 30 min | P0 |
| Modify `pipeline.py` | 3 hours | P0 |
| Modify `repository.py` (optional) | 1 hour | P1 |
| Update CLI script | 1 hour | P0 |
| Unit tests | 2 hours | P1 |
| Integration testing | 1 hour | P0 |
| Documentation | 1 hour | P1 |
| **Total** | **~12 hours** | |

---

## Questions to Resolve

1. **Database Migration**
   - Add `summary_status` column now or later?
   - **Recommendation**: Add it now (5 min effort, big benefit)

2. **Output Directory**
   - Hardcode `data/analysis/` or make configurable?
   - **Recommendation**: Use `config.py` with sensible defaults

3. **Backward Compatibility**
   - Keep old direct-to-DB mode as fallback?
   - **Recommendation**: Yes, use `--output-format` flag

4. **Metadata Tracking**
   - Track token usage from Groq API?
   - Track cost calculation?
   - **Recommendation**: Yes to both (useful for Stage 3)

5. **Error Handling**
   - What happens if JSON write fails?
   - Fallback to database?
   - **Recommendation**: Log error, mark as failed, continue

---

## Success Criteria

Stage 1 & 2 implementation is successful when:

- ✅ Pipeline fetches articles using existing query logic
- ✅ GenAI summarization runs as before
- ✅ Results saved to `data/analysis/raw/{article_id}.json`
- ✅ Each JSON file contains complete analysis + metadata
- ✅ CLI can process 10, 100, 1000+ articles without errors
- ✅ Statistics reported correctly
- ✅ No database writes during processing (unless opted in)
- ✅ Dry-run mode works correctly
- ✅ Backward compatibility maintained
- ✅ Code is well-documented and tested

---

**Ready to implement?** Let me know which components to start with!
