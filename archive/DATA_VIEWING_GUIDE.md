# Data Viewing Guide

## Quick Reference

### View Statistics
```bash
python view_data.py --stats
```

### View Database Schema
```bash
python view_data.py --schema
```

### View All Available Columns (with sample data)
```bash
python view_data.py --columns
```

---

## Viewing Articles

### Table View (Summary)
View articles in a compact table format showing key columns:

```bash
# View 10 most recent articles
python view_data.py --limit 10

# View 20 most recent articles
python view_data.py --limit 20

# View only PubMed articles
python view_data.py --source pubmed --limit 50

# View only Crossref articles
python view_data.py --source crossref --limit 50
```

**Table columns shown:**
- article_id
- title (truncated to 50 chars)
- journal
- publication_date
- source
- article_type
- country

---

### Detailed View (Full Information)
View complete article details one at a time:

```bash
# View 5 articles with full details
python view_data.py --limit 5 --format detailed

# View PubMed articles with details
python view_data.py --source pubmed --limit 5 --format detailed
```

**Detailed view includes:**
- Article ID, DOI, Source
- Title, Journal, Publication Date
- Full Abstract
- Authors (with affiliations)
- Keywords
- Metadata (URL, ingestion timestamps)

---

### Export to CSV
Export articles to CSV for Excel/Google Sheets:

```bash
# Export all articles
python view_data.py --limit 1000 --format csv

# Export only PubMed articles
python view_data.py --source pubmed --limit 1000 --format csv

# Export only Crossref articles  
python view_data.py --source crossref --limit 1000 --format csv
```

**Output:** `articles_export.csv` in current directory

---

## Database Schema

### Articles Table Columns

| Column | Type | Description |
|--------|------|-------------|
| `id` | TEXT | Internal UUID |
| `article_id` | TEXT | Unique article identifier (PMID or DOI) |
| `source` | TEXT | Source of data (pubmed, crossref, google_scholar) |
| `source_metadata_id` | TEXT | Source-specific ID |
| `doi` | TEXT | Digital Object Identifier |
| `url` | TEXT | Link to article |
| `ingestion_status` | TEXT | Status (pending, completed, failed) |
| `article_type` | TEXT | Type (research, review, editorial, meta-analysis) |
| `title` | TEXT | Article title |
| `abstract` | TEXT | Abstract text |
| `journal` | TEXT | Journal name |
| `keywords` | TEXT | JSON array of keywords |
| `authors` | TEXT | JSON array of author objects |
| `publication_date` | TEXT | Publication date (YYYY-MM-DD) |
| `country` | TEXT | Country (from first author affiliation) |
| `full_text` | TEXT | Full text (if available) |
| `figures` | TEXT | Figure data (if available) |
| `article_references` | TEXT | References (if available) |
| `ingested_at` | DATETIME | When article was ingested |
| `updated_at` | DATETIME | Last update timestamp |

---

## Direct Database Access

### Using SQLite CLI
```bash
# Open database
sqlite3 data/articles.db

# View tables
.tables

# View schema
.schema articles

# Query data
SELECT article_id, title, source, publication_date 
FROM articles 
ORDER BY publication_date DESC 
LIMIT 10;

# Count by source
SELECT source, COUNT(*) as count 
FROM articles 
GROUP BY source;

# Exit
.quit
```

---

## Python Access

### Simple Query Example
```python
import sys
sys.path.insert(0, 'backend')

from app.db.database import get_db

# Query articles
with get_db() as conn:
    cursor = conn.cursor()
    cursor.execute("""
        SELECT article_id, title, journal, publication_date 
        FROM articles 
        WHERE source = 'pubmed'
        ORDER BY publication_date DESC 
        LIMIT 10
    """)
    
    for row in cursor.fetchall():
        article = dict(row)
        print(f"{article['article_id']}: {article['title']}")
```

---

## Common Queries

### Articles by Date Range
```sql
SELECT article_id, title, publication_date 
FROM articles 
WHERE publication_date BETWEEN '2024-06-01' AND '2024-07-31'
ORDER BY publication_date DESC;
```

### Articles by Journal
```sql
SELECT article_id, title, journal 
FROM articles 
WHERE journal LIKE '%tobacco%'
ORDER BY publication_date DESC;
```

### Articles with Specific Keywords
```sql
SELECT article_id, title, keywords 
FROM articles 
WHERE keywords LIKE '%nicotine%'
ORDER BY publication_date DESC;
```

### Articles by Country
```sql
SELECT country, COUNT(*) as count 
FROM articles 
GROUP BY country 
ORDER BY count DESC;
```

---

## Tips

1. **Large Exports**: When exporting all data, increase the limit:
   ```bash
   python view_data.py --limit 10000 --format csv
   ```

2. **Filtering in CSV**: Open `articles_export.csv` in Excel/Google Sheets for advanced filtering and analysis

3. **JSON Fields**: The `keywords` and `authors` columns contain JSON data. Parse them in Python:
   ```python
   import json
   keywords = json.loads(article['keywords'])
   authors = json.loads(article['authors'])
   ```

4. **Database Location**: `data/articles.db`

5. **Backup Database**:
   ```bash
   cp data/articles.db data/articles_backup_$(date +%Y%m%d).db
   ```

---

## Troubleshooting

### No articles found
```bash
# Check database
python view_data.py --stats

# If empty, run ingestion
python backend/ingest_cli.py topic E-Cigarettes --sources pubmed --max 10
```

### CSV not opening properly
- Make sure to use UTF-8 encoding when opening in Excel
- Try Google Sheets for better UTF-8 support

### Want to see raw database
```bash
sqlite3 data/articles.db
.mode column
.headers on
SELECT * FROM articles LIMIT 5;
```
