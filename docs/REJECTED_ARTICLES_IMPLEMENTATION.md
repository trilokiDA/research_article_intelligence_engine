# Rejected Articles Implementation

**Date:** 2026-08-27  
**Status:** ✅ Completed

## Overview

This document describes the implementation of rejected article tracking in the `article_analysis` database table. Previously, rejected articles (those that failed quality checks after maximum retry attempts) were only stored as JSON files. Now they are tracked in the database for better analytics and reporting.

## Changes Summary

### 1. Database Schema Enhancement

**Added Column:**
- `rejection_reason` (TEXT) - Stores the reason why an article analysis was rejected

**Updated Status Values:**
- `analysis_status` now supports: `'pending'`, `'completed'`, `'rejected'`, `'failed'`
- Articles table's `analysis_status` can be: `'pending'`, `'analyzed'`, `'rejected'`

**Migration:**
- `backend/app/db/database.py` - Added `rejection_reason` column to table creation and migration
- Migration is backward compatible and safe to run on existing databases

### 2. Database Loader Updates

**Modified Files:**
- `backend/app/genai/db_loader.py`
  - Added `rejected_dir` path configuration
  - Updated `transform_json_to_record()` to handle rejected articles
  - Updated `load_single_file()` to accept `is_rejected` parameter
  - Added new method: `load_rejected_files()` for loading rejected articles
  - Updates articles table status to 'rejected' when loading rejected analyses

**Modified Files:**
- `scripts/load_to_database.py`
  - Added `--source` parameter to choose between 'approved' or 'rejected' directories
  - Supports loading rejected articles via: `python scripts/load_to_database.py --source rejected`

### 3. Streamlit Dashboard Enhancements

**Modified Files:**
- `streamlit_app.py`

**Dashboard Updates:**
- Added "Rejected" metric card showing count of rejected articles
- Changed "Completion Rate" to "Success Rate" (only counts completed, not rejected)
- Added "Analysis Status" bar chart with color coding:
  - Green (✅) for completed
  - Red (❌) for rejected
  - Yellow (🟡) for pending
- Added "Rejection Reasons" pie chart showing distribution of why articles were rejected

**Article Browser Updates:**
- Added "Analysis Status" filter dropdown with options:
  - All
  - completed
  - rejected
  - pending
  - Not Analyzed
- Display rejected articles with ❌ icon
- Show number of attempts for articles with > 1 attempt
- Display rejection reason as a warning banner for rejected articles
- Updated query to include `rejection_reason` field

### 4. Migration Script

**New File:**
- `scripts/migrate_rejected_articles.py`

**Purpose:** One-time migration script to load existing rejected articles from `data/analysis/rejected/*.json` into the database.

**Usage:**
```bash
# Preview what will be loaded (no changes)
python scripts/migrate_rejected_articles.py --dry-run

# Load all rejected files
python scripts/migrate_rejected_articles.py

# Load and archive source files
python scripts/migrate_rejected_articles.py --archive
```

**Features:**
- Validates all rejected JSON files before loading
- Shows before/after database statistics
- Optionally archives loaded files to `data/analysis/loaded/`
- Reports errors with detailed messages

## Migration Results

**Executed:** 2026-08-27

**Results:**
- ✅ Schema migration successful - added `rejection_reason` column
- ✅ 5 rejected articles migrated to database
- ✅ All rejection reasons captured: "Failed quality check after 3 attempts"
- ✅ All articles show 3 attempts (max retry count)

**Before Migration:**
- Total articles: 154
- Analyzed: 64
- Rejected in DB: 0

**After Migration:**
- Total articles: 154
- Analyzed: 69
- Rejected in DB: 5

## Benefits

### 1. Complete Audit Trail
- All articles (approved and rejected) are tracked in the database
- Maintains full history of analysis attempts and failures

### 2. Better Analytics
- Dashboard shows rejection rate and patterns
- Can analyze which types of articles fail most often
- Track rejection reasons to identify systematic issues

### 3. Query Efficiency
- No need to scan file system for rejected articles
- Can query rejection reasons, attempt counts, and patterns via SQL
- Easier to generate reports and analytics

### 4. Data Integrity
- Single source of truth in the database
- Consistent data model across approved and rejected articles

### 5. Operational Insights
- Identify candidates for reprocessing when prompts improve
- Track success rates by journal, category, or time period
- Monitor quality trends over time

## Database Schema

### article_analysis Table (Updated)

```sql
CREATE TABLE article_analysis (
    id TEXT PRIMARY KEY,
    article_id TEXT UNIQUE NOT NULL,
    subject TEXT,
    category TEXT,
    summary TEXT,
    entities TEXT,
    sentiment TEXT,
    industry_affiliation TEXT,
    coi_details TEXT,
    author_affiliations TEXT,
    citation_string TEXT,
    confidence_scores TEXT,
    fact_check_results TEXT,
    model_id TEXT,
    prompt_used TEXT,
    prompt_version TEXT,
    analyzed_at DATETIME,
    analysis_status TEXT DEFAULT 'pending',  -- Can be: pending, completed, rejected, failed
    fact_check_status TEXT,
    evaluation_score REAL,
    evaluation_metadata TEXT,
    stage TEXT,
    attempt INTEGER DEFAULT 1,
    loaded_at DATETIME,
    rejection_reason TEXT,  -- NEW: Reason for rejection
    FOREIGN KEY (article_id) REFERENCES articles(id) ON DELETE CASCADE
);
```

### Query Examples

**Get all rejected articles with reasons:**
```sql
SELECT 
    a.article_id,
    a.title,
    aa.rejection_reason,
    aa.attempt,
    aa.analyzed_at
FROM articles a
JOIN article_analysis aa ON a.id = aa.article_id
WHERE aa.analysis_status = 'rejected'
ORDER BY aa.analyzed_at DESC;
```

**Calculate success rate:**
```sql
SELECT 
    COUNT(CASE WHEN analysis_status = 'completed' THEN 1 END) as completed,
    COUNT(CASE WHEN analysis_status = 'rejected' THEN 1 END) as rejected,
    COUNT(*) as total,
    ROUND(COUNT(CASE WHEN analysis_status = 'completed' THEN 1 END) * 100.0 / COUNT(*), 2) as success_rate
FROM article_analysis;
```

**Group rejection reasons:**
```sql
SELECT 
    rejection_reason,
    COUNT(*) as count,
    AVG(attempt) as avg_attempts
FROM article_analysis
WHERE analysis_status = 'rejected'
GROUP BY rejection_reason
ORDER BY count DESC;
```

## Usage Guide

### Loading New Rejected Articles

When the pipeline produces new rejected articles in `data/analysis/rejected/`, load them with:

```bash
# Load from rejected directory
python scripts/load_to_database.py --source rejected

# Or use the dedicated migration script
python scripts/migrate_rejected_articles.py
```

### Viewing Rejected Articles

**In Streamlit Dashboard:**
1. Navigate to "Dashboard" page
2. View "Rejected" metric card for count
3. Check "Analysis Status" chart for distribution
4. Review "Rejection Reasons" pie chart for patterns

**In Article Browser:**
1. Navigate to "Article Browser" page
2. Set "Analysis Status" filter to "rejected"
3. Click on articles to see:
   - ❌ Rejected status indicator
   - Number of attempts
   - Rejection reason in warning banner
   - All other article metadata

### Monitoring Rejection Patterns

**Common Queries:**

1. **Rejection rate by journal:**
```python
import sqlite3
import pandas as pd

conn = sqlite3.connect('data/articles.db')
df = pd.read_sql_query("""
    SELECT 
        a.journal,
        COUNT(CASE WHEN aa.analysis_status = 'rejected' THEN 1 END) as rejected,
        COUNT(aa.id) as total,
        ROUND(COUNT(CASE WHEN aa.analysis_status = 'rejected' THEN 1 END) * 100.0 / COUNT(aa.id), 2) as rejection_rate
    FROM articles a
    JOIN article_analysis aa ON a.id = aa.article_id
    GROUP BY a.journal
    HAVING total > 5
    ORDER BY rejection_rate DESC
""", conn)
print(df)
```

2. **Timeline of rejections:**
```python
df = pd.read_sql_query("""
    SELECT 
        DATE(analyzed_at) as date,
        COUNT(*) as rejected_count
    FROM article_analysis
    WHERE analysis_status = 'rejected'
    GROUP BY DATE(analyzed_at)
    ORDER BY date DESC
""", conn)
```

## Next Steps

### Potential Enhancements

1. **Reprocessing Rejected Articles**
   - Add script to retry rejected articles with improved prompts
   - Track reprocessing attempts separately

2. **Enhanced Rejection Taxonomy**
   - Categorize rejection reasons (quality, formatting, extraction_error, etc.)
   - Add severity levels (minor, major, critical)

3. **Automated Alerts**
   - Alert when rejection rate exceeds threshold
   - Notify when new rejection reasons appear

4. **Quality Improvement Workflow**
   - Identify common failure patterns
   - Suggest prompt improvements based on rejection reasons
   - A/B test different prompts on rejected articles

## Testing

### Validation Steps

✅ Schema migration completes without errors  
✅ Existing data is preserved  
✅ Rejected articles load successfully  
✅ Dashboard displays rejection metrics correctly  
✅ Article browser shows rejected articles with proper indicators  
✅ Rejection reasons display in UI  
✅ Attempt counts are accurate  
✅ Queries return expected results  

### Test Commands

```bash
# Test schema migration
python backend/app/db/database.py

# Test rejected article loading (dry-run)
python scripts/migrate_rejected_articles.py --dry-run

# Test actual loading
python scripts/migrate_rejected_articles.py

# Verify data
python -c "import sqlite3; conn = sqlite3.connect('data/articles.db'); 
cursor = conn.cursor(); 
cursor.execute('SELECT COUNT(*) FROM article_analysis WHERE analysis_status = \"rejected\"'); 
print('Rejected count:', cursor.fetchone()[0])"
```

## Files Modified

### Backend
- ✅ `backend/app/db/database.py` - Schema and migration
- ✅ `backend/app/genai/db_loader.py` - Loader logic

### Scripts  
- ✅ `scripts/load_to_database.py` - CLI updates
- ✅ `scripts/migrate_rejected_articles.py` - New migration script

### Frontend
- ✅ `streamlit_app.py` - Dashboard and browser updates

### Documentation
- ✅ `docs/REJECTED_ARTICLES_IMPLEMENTATION.md` - This document

## Conclusion

The rejected articles tracking feature is now fully implemented and operational. All historical rejected articles have been migrated to the database, and the Streamlit dashboard provides comprehensive visibility into rejection patterns. This enhancement improves data integrity, enables better analytics, and supports continuous improvement of the analysis pipeline.

For questions or issues, refer to the main project documentation or check the troubleshooting section in `docs/TROUBLESHOOTING.md`.
