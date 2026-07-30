# Topic-Based Query System

## Overview

The system now supports **predefined topic queries** for common research areas. Instead of manually crafting complex PubMed/Scholar queries, you can use simple topic names.

## ✅ What's New

1. **4 Predefined Topics** with expertly crafted queries
2. **Multi-Source Support** (PubMed + Google Scholar specific queries)
3. **Simple CLI Interface** - Just use topic names
4. **Easy to Extend** - Add new topics via JSON config

---

## 📋 Available Topics

### 1. Heat-Not-Burn
**Products:** IQOS, HEETS, THS, HNB, electrically heated cigarettes

**PubMed Query:**
```
(((eclipse OR accord OR "Heatstick" OR "revo") AND cigarette AND heat* NOT (resin OR column)) OR 
"tobacco heating"[Title/Abstract] OR "heated cigarette*"[Title/Abstract] OR 
"IQOS"[Title/Abstract] OR "HEETS"[Title/Abstract] OR "heatsticks*"[Title/Abstract] OR 
("heat-not-burn"[Title/Abstract] AND "tobacco"[Title/Abstract]) OR 
("HNB"[Title/Abstract] AND "tobacco"[Title/Abstract]) OR 
("THS"[Title/Abstract] AND "tobacco"[Title/Abstract]) ...
```

**Google Scholar Query:**
```
("heated cigarette*") OR ("tobacco heating") OR ("heated tobacco") OR 
("tobacco heating system") OR ("heat-not-burn" "tobacco") OR ("IQOS") OR 
("HEETS") OR ("heatsticks") OR ("heat not burn" "tobacco") OR 
("THS" "tobacco") OR ("HNB" "tobacco")
```

---

### 2. E-Cigarettes
**Products:** Electronic cigarettes, vaping, ENDS, e-vapor

**PubMed Query:**
```
(("electronic cigarettes*"[Title/Abstract]) OR ("e-cigarettes*"[Title/Abstract]) OR 
("electroniccigarettes*"[Title/Abstract]) OR ("EVALI"[Title/Abstract]) OR 
("e vapor*"[Title/Abstract]) OR ("evapour*"[Title/Abstract]) OR 
("ENDS"[Title/Abstract] AND "electronic delivery"[Title/Abstract]) OR 
"electronic delivery nicotine"[Title/Abstract] OR 
("VNP"[Title/Abstract] AND "vaporized nicotine products*"[Title/Abstract]))
```

**Google Scholar Query:**
```
("electronic cigarettes") OR ("e-cigarettes") OR ("vaping") OR ("e-vapor")
```

---

### 3. Nicotine-Pouch
**Products:** Nicotine pouches

**PubMed Query:**
```
"Nicotine pouch*"[Title/Abstract]
```

**Google Scholar Query:**
```
"nicotine pouches" OR "nicotine pouch"
```

---

### 4. Snus
**Products:** Swedish snus, smokeless tobacco

**PubMed Query:**
```
"snus"[Title/Abstract] OR "Swedish snus"[Title/Abstract] OR 
"smokeless tobacco"[Title/Abstract]
```

**Google Scholar Query:**
```
("snus" AND "tobacco") OR ("Swedish snus" AND "tobacco") OR 
("smokeless" AND "tobacco")
```

---

## 🚀 Usage

### List Available Topics
```bash
python backend/ingest_cli.py topics
```

**Output:**
```
======================================================================
[CONFIG] AVAILABLE TOPIC QUERIES
======================================================================

Heat-Not-Burn
  Description: Heated tobacco products (IQOS, HEETS, THS)
  Sources:
    - pubmed: (((eclipse OR accord OR "Heatstick"...
    - google_scholar: ("heated cigarette*") OR...

E-Cigarettes
  Description: Electronic cigarettes, vaping, ENDS
  ...
```

---

### Search Using Topic

#### Example 1: Fetch Heat-Not-Burn articles from PubMed
```bash
python backend/ingest_cli.py topic Heat-Not-Burn \
    --sources pubmed \
    --max 100 \
    --from-date 2024-01-01 \
    --to-date 2024-12-31
```

#### Example 2: Fetch E-Cigarettes from both PubMed and Crossref
```bash
python backend/ingest_cli.py topic E-Cigarettes \
    --sources pubmed crossref \
    --max 200
```

#### Example 3: Fetch Snus research (last 6 months)
```bash
python backend/ingest_cli.py topic Snus \
    --sources pubmed \
    --max 50 \
    --from-date 2024-06-01 \
    --to-date 2024-12-31
```

#### Example 4: All topics, recent research
```bash
# Run multiple topic searches
for topic in "Heat-Not-Burn" "E-Cigarettes" "Nicotine-Pouch" "Snus"; do
    python backend/ingest_cli.py topic "$topic" \
        --sources pubmed \
        --max 50 \
        --from-date 2024-01-01
done
```

---

## 🔧 How It Works

### 1. Configuration File
Queries are stored in `backend/app/config/search_queries.json`:

```json
{
  "queries": [
    {
      "name": "Heat-Not-Burn",
      "description": "Heated tobacco products (IQOS, HEETS, THS)",
      "sources": {
        "pubmed": {
          "query": "(((...complex query...)))"
        },
        "google_scholar": {
          "query": "(((...complex query...)))",
          "exclude_patents": true
        }
      }
    }
  ]
}
```

### 2. Query Manager
`backend/app/config/query_manager.py` loads and manages queries:

```python
from app.config.query_manager import QueryManager

manager = QueryManager()

# List topics
topics = manager.list_topics()  # ['Heat-Not-Burn', 'E-Cigarettes', ...]

# Get query for specific topic + source
query = manager.get_query('E-Cigarettes', 'pubmed')

# Get all queries for a topic
all_queries = manager.get_all_queries_for_topic('Snus')
```

### 3. CLI Integration
New commands in `ingest_cli.py`:

- `topics` - List available topics
- `topic <name>` - Search using predefined topic query

---

## ➕ Adding New Topics

### Step 1: Edit Configuration
Open `backend/app/config/search_queries.json` and add:

```json
{
  "name": "Your-Topic-Name",
  "description": "Brief description of topic",
  "sources": {
    "pubmed": {
      "query": "your[Title/Abstract] AND complex[Title/Abstract] AND query"
    },
    "google_scholar": {
      "query": "\"your topic\" OR (\"alternative terms\")",
      "exclude_patents": true
    }
  }
}
```

### Step 2: Test
```bash
# List topics (should see your new one)
python backend/ingest_cli.py topics

# Try searching
python backend/ingest_cli.py topic Your-Topic-Name --sources pubmed --max 10
```

---

## 📊 Comparison: Custom vs Topic Queries

### Custom Query (Manual)
```bash
# You write the complex query yourself
python backend/ingest_cli.py search \
    '((("electronic cigarettes*"[Title/Abstract]) OR ("e-cigarettes*"[Title/Abstract]) OR ("EVALI"[Title/Abstract])))' \
    --sources pubmed \
    --max 100
```

**Pros:** Full control  
**Cons:** Complex, error-prone, hard to remember

---

### Topic Query (Predefined)
```bash
# Just use the topic name
python backend/ingest_cli.py topic E-Cigarettes \
    --sources pubmed \
    --max 100
```

**Pros:** Simple, consistent, expert-crafted  
**Cons:** Limited to predefined topics (but easy to add new ones!)

---

## 🎯 Use Cases

### Monthly Update Workflow
```bash
# Fetch last month's research for all topics
python backend/ingest_cli.py topic Heat-Not-Burn --sources pubmed --max 50 --from-date 2024-11-01 --to-date 2024-11-30
python backend/ingest_cli.py topic E-Cigarettes --sources pubmed --max 50 --from-date 2024-11-01 --to-date 2024-11-30
python backend/ingest_cli.py topic Nicotine-Pouch --sources pubmed --max 50 --from-date 2024-11-01 --to-date 2024-11-30
python backend/ingest_cli.py topic Snus --sources pubmed --max 50 --from-date 2024-11-01 --to-date 2024-11-30

# Check stats
python backend/ingest_cli.py stats
```

### Historical Backfill
```bash
# Fetch all 2024 research for a specific topic
python backend/ingest_cli.py topic Heat-Not-Burn \
    --sources pubmed crossref \
    --max 500 \
    --from-date 2024-01-01 \
    --to-date 2024-12-31
```

### Targeted Deep Dive
```bash
# Focus on specific topic with multiple sources
python backend/ingest_cli.py topic IQOS \
    --sources pubmed crossref google_scholar \
    --max 200
```

---

## 🔍 Query Quality Tips

### For PubMed
- Use `[Title/Abstract]` for field-specific searches
- Use `*` for wildcards (e.g., `cigarette*` matches cigarettes, cigarette)
- Use `OR` for synonyms, `AND` for required terms
- Use `NOT` to exclude terms
- Enclose phrases in quotes: `"electronic cigarette"`

### For Google Scholar
- Use quotes for exact phrases: `"heat-not-burn"`
- Use `OR` for alternatives: `"vaping" OR "e-cigarettes"`
- Use `AND` to combine concepts: `"snus" AND "tobacco"`
- Add `-patent` to exclude patents (optional in config)

---

## 📈 Benefits

### 1. Consistency
All researchers use the same proven queries for each topic.

### 2. Expertise
Queries crafted by domain experts, covering all relevant terms.

### 3. Maintainability
Update queries in one place (`search_queries.json`), affects all searches.

### 4. Simplicity
```bash
# Instead of this:
python backend/ingest_cli.py search '((("electronic cigarettes*"[Title/Abstract]) OR ("e-cigarettes*"[Title/Abstract]) OR ("electroniccigarettes*"[Title/Abstract]) OR ("EVALI"[Title/Abstract]) OR ("e vapor*"[Title/Abstract]) OR ("evapour*"[Title/Abstract]) OR ("ENDS"[Title/Abstract] AND "electronic delivery"[Title/Abstract]) OR "electronic delivery nicotine"[Title/Abstract] OR ("VNP"[Title/Abstract] AND "vaporized nicotine products*"[Title/Abstract])))' --sources pubmed --max 100

# Just do this:
python backend/ingest_cli.py topic E-Cigarettes --sources pubmed --max 100
```

### 5. Collaboration
Share topic names instead of long query strings. New team members can start immediately.

---

## 🛠️ Python API

You can also use topics programmatically:

```python
from app.config.query_manager import QueryManager
from app.ingestion.orchestrator import IngestionOrchestrator

# Initialize
manager = QueryManager()
orchestrator = IngestionOrchestrator()

# Get query for a topic
query = manager.get_query('E-Cigarettes', 'pubmed')

# Run ingestion
results = orchestrator.ingest_from_query(
    query=query,
    sources=['pubmed'],
    max_per_source=100,
    date_range={'from': '2024-01-01', 'to': '2024-12-31'}
)

print(f"Ingested: {results['total']} articles")
```

---

## 📝 Summary

**What You Get:**
✅ 4 expertly-crafted topic queries (Heat-Not-Burn, E-Cigarettes, Nicotine-Pouch, Snus)  
✅ Simple CLI: `python backend/ingest_cli.py topic <name>`  
✅ Multi-source support (PubMed + Google Scholar)  
✅ Easy to add new topics (JSON config)  
✅ Consistent, reproducible searches  

**Commands:**
- `topics` - List available topics
- `topic <name> --sources pubmed --max 100` - Search by topic
- `search "query"` - Custom query (still available)

**Next:** Add your own topics by editing `backend/app/config/search_queries.json`!
