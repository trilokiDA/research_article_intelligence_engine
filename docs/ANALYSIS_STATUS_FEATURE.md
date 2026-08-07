# Analysis Status Feature

## Overview
This feature adds an `analysis_status` field to the `articles` table to track which articles have been analyzed and loaded into the `article_analysis` table.

## Motivation
Previously, identifying unanalyzed articles required expensive LEFT JOIN queries against the `article_analysis` table. With the new `analysis_status` field, we can quickly filter articles by their analysis state using an indexed column.

## Implementation

### 1. Database Schema Changes

#### New Column
- **Table**: `articles`
- **Column**: `analysis_status TEXT DEFAULT 'pending'`
- **Index**: `idx_articles_analysis_status`

#### Possible Values
- `pending` - Article not yet analyzed (default)
- `analyzed` - Article successfully analyzed and loaded to `article_analysis`
- `failed` - Analysis attempted but failed
- `skipped` - Article intentionally not analyzed (reserved for future use)

### 2. Migration
The migration automatically:
1. Adds `analysis_status` column to existing databases
2. Creates index on the new column
3. Updates existing records: marks articles with analysis records as `'analyzed'`

**Location**: `backend/app/db/database.py::migrate_db()`

### 3. Automatic Status Updates

#### When Loading Analyzed Articles (`db_loader.py`)
```python
# After inserting/updating article_analysis record
UPDATE articles
SET analysis_status = 'analyzed',
    updated_at = CURRENT_TIMESTAMP
WHERE id = ?
```

#### When Saving Analysis (`repository.py::save_analysis()`)
```python
# After saving to article_analysis
UPDATE articles
SET analysis_status = 'analyzed',
    updated_at = CURRENT_TIMESTAMP
WHERE article_id = ?
```

#### When Marking as Failed (`repository.py::mark_analysis_failed()`)
```python
UPDATE articles
SET analysis_status = 'failed',
    updated_at = CURRENT_TIMESTAMP
WHERE article_id = ?
```

### 4. Query Optimization

#### Before (Expensive LEFT JOIN)
```sql
SELECT a.*
FROM articles a
LEFT JOIN article_analysis aa ON a.article_id = aa.article_id
WHERE
    aa.article_id IS NULL
    OR aa.summary IS NULL
    OR aa.summary = ''
    OR aa.analysis_status IN ('pending', 'failed')
```

#### After (Indexed Query)
```sql
SELECT *
FROM articles
WHERE analysis_status IN ('pending', 'failed')
```

**Performance**: O(n) → O(log n) with index lookup

## Usage

### Get Pending Articles
```python
from backend.app.genai.repository import ArticleRepository

# Get articles that need analysis
pending_articles = ArticleRepository.get_articles_pending_analysis(limit=10)

# Count pending articles
pending_count = ArticleRepository.count_articles_pending_analysis()
```

### Check Statistics
```python
from backend.app.db.database import get_stats

stats = get_stats()
print(stats['by_analysis_status'])
# Output: {'pending': 150, 'analyzed': 50, 'failed': 5}
```

### Run Status Report
```bash
python scripts/check_analysis_status.py
```

## Benefits

1. **Performance**: Faster queries using indexed lookups instead of LEFT JOINs
2. **Clarity**: Clear separation of ingestion status vs. analysis status
3. **Retry Logic**: Easy to identify and re-process failed analyses
4. **Pipeline Visibility**: Track article progress through the full pipeline
5. **Atomic Updates**: Status updated in same transaction as analysis load
6. **Scalability**: Indexed queries scale better as dataset grows

## Modified Files

1. `backend/app/db/database.py`
   - Added `analysis_status` column to schema
   - Added index creation
   - Added migration logic
   - Updated statistics function

2. `backend/app/genai/db_loader.py`
   - Updates `articles.analysis_status` when loading to `article_analysis`

3. `backend/app/genai/repository.py`
   - `get_articles_pending_analysis()` - Uses `analysis_status` filter
   - `count_articles_pending_analysis()` - Uses `analysis_status` filter
   - `save_analysis()` - Updates `articles.analysis_status = 'analyzed'`
   - `mark_analysis_failed()` - Updates `articles.analysis_status = 'failed'`

4. `scripts/check_analysis_status.py` (new)
   - Utility script to display analysis status statistics

## Testing

### Run Migration
```bash
python backend/app/db/database.py
```

### Check Status
```bash
python scripts/check_analysis_status.py
```

### Verify Status Updates
1. Run analysis pipeline
2. Observe `analysis_status` changes from `'pending'` to `'analyzed'`
3. Check that failed analyses are marked as `'failed'`

## Future Enhancements

1. **Retry Logic**: Automatically retry failed analyses after a cooldown period
2. **Skipped Status**: Mark certain articles to be skipped based on criteria
3. **Status History**: Track status transitions with timestamps
4. **Dashboard**: Visualize analysis pipeline progress
5. **Alerts**: Notify when failure rate exceeds threshold

## Notes

- Migration is idempotent and safe to run multiple times
- Existing articles without analysis records will default to `'pending'`
- The `updated_at` timestamp is automatically updated when `analysis_status` changes
- Index ensures fast filtering even with millions of articles
