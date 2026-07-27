# ✅ Topic-Based Query System Implemented!

## 🎉 What's Been Added

Your complex PubMed and Google Scholar queries are now **built into the system** as predefined topics!

### New Features

1. **✅ Predefined Topic Queries**
   - Heat-Not-Burn (IQOS, HEETS, THS)
   - E-Cigarettes (vaping, ENDS, e-vapor)
   - Nicotine-Pouch
   - Snus (Swedish snus, smokeless tobacco)

2. **✅ Simple CLI Commands**
   ```bash
   # List topics
   python backend/ingest_cli.py topics
   
   # Search by topic
   python backend/ingest_cli.py topic Heat-Not-Burn --sources pubmed --max 100
   ```

3. **✅ Multi-Source Support**
   - Each topic has PubMed-optimized query
   - Each topic has Google Scholar-optimized query
   - Automatically uses the right query for each source

4. **✅ Easy to Extend**
   - Add new topics by editing `backend/app/config/search_queries.json`
   - No code changes needed

---

## 📂 New Files Created

```
backend/
├── app/
│   └── config/
│       ├── search_queries.json      ✅ Topic definitions
│       └── query_manager.py         ✅ Query loader
└── ingest_cli.py                    ✅ Updated with 'topics' and 'topic' commands
```

---

## 🚀 Quick Examples

### List Available Topics
```bash
python backend/ingest_cli.py topics
```

Output:
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
  Sources:
    - pubmed: (("electronic cigarettes*"[Title/Abstract])...
    - google_scholar: ("electronic cigarettes") OR...

Nicotine-Pouch
  Description: Nicotine pouches and related products
  Sources:
    - pubmed: "Nicotine pouch*"[Title/Abstract]
    - google_scholar: "nicotine pouches" OR "nicotine pouch"

Snus
  Description: Swedish snus and smokeless tobacco
  Sources:
    - pubmed: "snus"[Title/Abstract] OR...
    - google_scholar: ("snus" AND "tobacco") OR...
```

---

### Fetch Articles Using Your Complex Queries

#### Heat-Not-Burn (IQOS, HEETS, THS)
```bash
python backend/ingest_cli.py topic Heat-Not-Burn \
    --sources pubmed \
    --max 100 \
    --from-date 2024-01-01 \
    --to-date 2024-12-31
```

This automatically uses your complex query:
```
(((eclipse OR accord OR "Heatstick" OR "revo") AND cigarette AND heat* NOT (resin OR column)) OR 
"tobacco heating"[Title/Abstract] OR "heated cigarette*"[Title/Abstract] OR 
"IQOS"[Title/Abstract] OR "HEETS"[Title/Abstract] OR ... [full query]
```

#### E-Cigarettes
```bash
python backend/ingest_cli.py topic E-Cigarettes \
    --sources pubmed crossref \
    --max 200
```

#### All Topics (Monthly Update)
```bash
# Fetch recent research for all topics
python backend/ingest_cli.py topic Heat-Not-Burn --sources pubmed --max 50
python backend/ingest_cli.py topic E-Cigarettes --sources pubmed --max 50
python backend/ingest_cli.py topic Nicotine-Pouch --sources pubmed --max 50
python backend/ingest_cli.py topic Snus --sources pubmed --max 50

# Check what was ingested
python backend/ingest_cli.py stats
```

---

## 📊 Comparison

### Before (Manual Query)
```bash
# You had to type/paste the entire complex query
python backend/ingest_cli.py search \
    '((("electronic cigarettes*"[Title/Abstract]) OR ("e-cigarettes*"[Title/Abstract]) OR ("electroniccigarettes*"[Title/Abstract]) OR ("EVALI"[Title/Abstract]) OR ("e vapor*"[Title/Abstract]) OR ("evapour*"[Title/Abstract]) OR ("ENDS"[Title/Abstract] AND "electronic delivery"[Title/Abstract]) OR "electronic delivery nicotine"[Title/Abstract] OR ("VNP"[Title/Abstract] AND "vaporized nicotine products*"[Title/Abstract])))' \
    --sources pubmed \
    --max 100
```

### After (Topic Name)
```bash
# Just use the topic name
python backend/ingest_cli.py topic E-Cigarettes \
    --sources pubmed \
    --max 100
```

**Result:** Same data, 90% less typing! ✅

---

## 🔧 Your Queries Are Preserved

All your complex PubMed and Google Scholar queries are stored in:
**`backend/app/config/search_queries.json`**

### Heat-Not-Burn Query
```json
{
  "name": "Heat-Not-Burn",
  "description": "Heated tobacco products (IQOS, HEETS, THS)",
  "sources": {
    "pubmed": {
      "query": "(((eclipse OR accord OR \"Heatstick\" OR \"revo\") AND cigarette AND heat* NOT (resin OR column)) OR \"tobacco heating\"[Title/Abstract] OR \"heated cigarette*\"[Title/Abstract] OR \"electrically heated cigarette*\"[Title/Abstract] OR \"EHCSS\"[Title/Abstract] OR \"Electrically Heated Cigarette Smoking System*\"[Title/Abstract] OR \"heat* tobacco\"[Title/Abstract] OR \"tobacco heating cigarette*\"[Title/Abstract] OR \"EHCSS-K3\"[Title/Abstract] OR \"EHCSS-K6\"[Title/Abstract] OR \"heated tobacco\"[Title/Abstract] OR \"tobacco heating system\"[Title/Abstract] OR (\"heat-notburn\"[Title/Abstract] AND \"tobacco\"[Title/Abstract]) OR \"IQOS\"[Title/Abstract] OR \"HEETS\"[Title/Abstract] OR \"heatsticks*\"[Title/Abstract] OR (\"heat-not-burn\"[Title/Abstract] AND \"tobacco\"[Title/Abstract]) OR (\"HNB\"[Title/Abstract] AND \"tobacco\"[Title/Abstract]) OR (\"THS\"[Title/Abstract] AND \"tobacco\"[Title/Abstract]) OR (\"Lil\"[Title/Abstract] AND \"tobacco\"[Title/Abstract]) OR (\"TEEPS\"[Title/Abstract] AND \"tobacco\"[Title/Abstract])) OR (\"Modified risk tobacco product*\"[Title/Abstract]) OR (\"non-cigarette combustible*\"[Title/Abstract]) OR (\"non combusted\" AND cigarette[Title/Abstract]) OR (\"Risk continuum\"[Title/Abstract] AND \"tobacco\"[Title/Abstract]) OR (\"non combustible\" AND \"tobacco\"[Title/Abstract])"
    },
    "google_scholar": {
      "query": "(\"heated cigarette*\") OR (\"tobacco heating\") OR (\"heated tobacco\") OR (\"tobacco heating system\") OR (\"heat-not-burn\" \"tobacco\") OR (\"IQOS\") OR (\"HEETS\") OR (\"heatsticks\") OR (\"heat not burn\" \"tobacco\") OR (\"THS\" \"tobacco\") OR (\"HNB\" \"tobacco\")",
      "exclude_patents": true
    }
  }
}
```

---

## ➕ Adding More Topics

### Step 1: Edit Configuration File
Open `backend/app/config/search_queries.json` and add:

```json
{
  "name": "Your-New-Topic",
  "description": "Brief description",
  "sources": {
    "pubmed": {
      "query": "your complex pubmed query here"
    },
    "google_scholar": {
      "query": "your google scholar query",
      "exclude_patents": true
    }
  }
}
```

### Step 2: Test It
```bash
# List topics (should show your new one)
python backend/ingest_cli.py topics

# Use it
python backend/ingest_cli.py topic Your-New-Topic --sources pubmed --max 10
```

---

## 🎯 Use Cases

### 1. Weekly Research Updates
```bash
# Every Monday, fetch last week's research
python backend/ingest_cli.py topic Heat-Not-Burn \
    --sources pubmed \
    --max 20 \
    --from-date 2024-12-16 \
    --to-date 2024-12-22
```

### 2. Comprehensive Topic Review
```bash
# Fetch everything from 2024 for a specific topic
python backend/ingest_cli.py topic E-Cigarettes \
    --sources pubmed crossref \
    --max 500 \
    --from-date 2024-01-01 \
    --to-date 2024-12-31
```

### 3. Automated Monthly Ingestion
Create a script `monthly_update.sh`:
```bash
#!/bin/bash
# Fetch last month's research for all topics

for TOPIC in "Heat-Not-Burn" "E-Cigarettes" "Nicotine-Pouch" "Snus"; do
    echo "Fetching $TOPIC..."
    python backend/ingest_cli.py topic "$TOPIC" \
        --sources pubmed \
        --max 100 \
        --from-date 2024-11-01 \
        --to-date 2024-11-30
done

echo "Done! Checking stats..."
python backend/ingest_cli.py stats
```

---

## 🆘 Troubleshooting

### "Unknown topic: XYZ"
```bash
# List available topics
python backend/ingest_cli.py topics

# Use exact name (case-sensitive)
python backend/ingest_cli.py topic Heat-Not-Burn  # ✅ Correct
python backend/ingest_cli.py topic heat-not-burn  # ✗ Wrong (case matters)
```

### Custom Query Still Works
```bash
# You can still use custom queries
python backend/ingest_cli.py search "your custom query" --sources pubmed --max 50
```

### Modify Existing Queries
Edit `backend/app/config/search_queries.json` and update the query text.

---

## 📖 Documentation

- **Full Guide:** `TOPIC_QUERIES_GUIDE.md` (detailed examples)
- **Backend README:** `backend/README.md`
- **Setup Guide:** `SETUP_COMPLETE.md`

---

## ✅ Summary

**What You Can Do Now:**

✅ Use simple topic names instead of complex queries  
✅ Fetch Heat-Not-Burn research: `python backend/ingest_cli.py topic Heat-Not-Burn`  
✅ Fetch E-Cigarettes research: `python backend/ingest_cli.py topic E-Cigarettes`  
✅ Fetch Nicotine-Pouch research: `python backend/ingest_cli.py topic Nicotine-Pouch`  
✅ Fetch Snus research: `python backend/ingest_cli.py topic Snus`  
✅ Add new topics by editing JSON config  
✅ Run monthly automated updates  
✅ Consistent, reproducible searches  

**Your complex PubMed and Google Scholar queries are now:**
- ✅ Stored in one place (`search_queries.json`)
- ✅ Easy to use (just topic names)
- ✅ Easy to maintain (edit JSON, no code changes)
- ✅ Easy to share (topic names instead of long query strings)

---

## 🎉 Success!

Your topic-based query system is ready to use. No more copy-pasting complex queries! 🚀

**Test it now:**
```bash
python backend/ingest_cli.py topics
python backend/ingest_cli.py topic E-Cigarettes --sources pubmed --max 5
```
