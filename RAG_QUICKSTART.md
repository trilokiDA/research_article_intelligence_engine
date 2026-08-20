# RAG Quick Start Guide

AI-powered Q&A system over your research article corpus using Retrieval-Augmented Generation.

## What is RAG?

RAG enables natural language queries over your research articles:
- **"What are the cardiovascular effects of e-cigarettes?"**
- **"Show studies on youth vaping behavior"**
- **"Compare heated tobacco vs nicotine pouches"**

The system:
1. **Retrieves** relevant articles using semantic search (embeddings)
2. **Augments** the query with retrieved context
3. **Generates** an answer citing specific article IDs

---

## Setup (One-Time)

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

This installs:
- `chromadb` - Vector database (local, SQLite-backed)
- `sentence-transformers` - Embedding model (runs locally)
- Existing Groq LLM integration (already configured)

### 2. Build RAG Index

Index your analyzed articles from the database:

```bash
python scripts/build_rag_index.py
```

**What it does:**
- Reads from `articles` and `article_analysis` tables (database = source of truth)
- Generates embeddings for summaries + abstracts
- Stores vectors in ChromaDB

**Output:**
```
RAG Index Builder - Stage 6
============================================================
Loading embedding model: all-MiniLM-L6-v2...
✓ Model loaded
✓ Created new collection: research_articles

Loading articles from database (status=completed)...
Loaded 19 articles from database
Indexing 19 articles...
✓ Indexed batch 1: 19 articles
============================================================
Indexing Complete
============================================================
  Total Articles: 19
  Indexed: 19
  Skipped: 0
  Errors: 0

Collection now contains 19 documents
Location: data/chroma
```

**Index Location:** `data/chroma/` (persistent storage)

**Options:**
```bash
# Index only specific status
python scripts/build_rag_index.py --status completed

# Custom database path
python scripts/build_rag_index.py --db-path /path/to/articles.db

# Check stats without indexing
python scripts/build_rag_index.py --stats
```

---

## Usage

### Option 1: Streamlit App (Recommended)

Launch the updated Streamlit app with RAG chat:

```bash
streamlit run streamlit_app_with_rag.py
```

**Features:**
- 💬 **Chat sidebar** - Ask questions in natural language
- 🔍 **Advanced filters** - Filter by category, sentiment
- 📚 **Source citations** - Every answer cites article IDs
- 📝 **Chat history** - View previous Q&A sessions
- 💡 **Example questions** - Quick-start templates

**UI Elements:**
- Sidebar: RAG chat interface (always visible)
- Main area: Dashboard and Article Browser (unchanged)

### Option 2: Python API

```python
from backend.app.rag import RAGQueryService

# Initialize service
service = RAGQueryService()

# Ask a question
result = service.query(
    question="What are the cardiovascular risks of vaping?",
    n_results=5  # Number of articles to retrieve
)

# Print answer
print(result['answer'])

# Print sources
for source in result['sources']:
    print(f"  - {source['article_id']}: {source['title']}")
```

### Option 3: CLI (Quick Test)

```bash
python backend/app/rag/query_service.py "What are the cardiovascular effects of e-cigarettes?"
```

---

## How It Works

### Architecture

```
User Question
    ↓
1. Embedding Generation (sentence-transformers)
    ↓
2. Semantic Search (ChromaDB)
    ↓
3. Retrieve Top-K Articles (default: 5)
    ↓
4. Format Context (summaries + abstracts)
    ↓
5. LLM Generation (Groq: llama-3.3-70b)
    ↓
Answer + Source Citations
```

### Pipeline Integration

RAG is **Stage 6** of your pipeline:

```
Stage 1: Ingestion (PubMed → SQLite)
Stage 2: Summarization (Groq LLM)
Stage 3: Evaluation (Quality scoring)
Stage 4: Re-inference (Feedback loop)
Stage 5: Database Load (Approved summaries)
Stage 6: RAG Indexing ← NEW
    ↓
Stage 7: Query Interface (Streamlit/API)
```

### Data Flow

```
data/articles.db
├── articles table         ← Raw metadata
└── article_analysis table ← GenAI analysis (source of truth)
    ↓
scripts/build_rag_index.py
    ↓
SQL JOIN (articles + article_analysis)
    ↓
Embedding Model (all-MiniLM-L6-v2)
    ↓
data/chroma/
├── chroma.sqlite3  ← Vector index
└── collections/
    └── research_articles/
    ↓
RAGQueryService
    ↓
Streamlit Chat Interface
```

**Why database-first?**
- ✅ Single source of truth (no JSON file dependencies)
- ✅ Consistent with rest of pipeline
- ✅ Easy to filter by status, date, category
- ✅ Automatic updates when analysis completes
- ✅ No file system sync issues

---

## Advanced Features

### Metadata Filtering

Filter retrieved articles by metadata:

```python
result = service.query(
    question="Youth vaping studies",
    n_results=5,
    filters={
        'category': 'Behavior Studies',
        'sentiment': 'Negative',
        'publication_date': '2025-01-01'  # >=
    }
)
```

**Available Filters:**
- `category` - Clinical Studies, Epidemiology, etc.
- `subject` - E-cigarettes, Heated Tobacco Products, etc.
- `sentiment` - Positive, Negative, Neutral, Mixed
- `country` - Study country
- `source` - pubmed, crossref
- `industry_affiliation` - PMI, JTI, BAT, etc.

### Hybrid Search (Coming Soon)

Combine semantic (RAG) + keyword (FTS5) search:

```python
# Semantic: "cardiovascular effects of vaping"
# Keyword: exact phrase match "myocardial infarction"
```

### Rebuild Index

After analyzing new articles:

```bash
# Incremental (add new only)
python scripts/build_rag_index.py

# Full rebuild (delete and recreate)
python scripts/build_rag_index.py --rebuild

# Index articles with different status
python scripts/build_rag_index.py --status approved
```

**When to rebuild:**
- After running the GenAI pipeline (new articles analyzed)
- When changing embedding models
- If index becomes corrupted

### Check Index Stats

```bash
python scripts/build_rag_index.py --stats
```

**Output:**
```
Collection Stats:
  Name: research_articles
  Total Documents: 19
  Sample IDs: PMID41666634, PMID41702869, ...
```

---

## Configuration

### Embedding Model

Default: `all-MiniLM-L6-v2` (384 dimensions, fast, good quality)

**Alternatives:**
- `all-mpnet-base-v2` - Better quality, slower (768 dim)
- `multi-qa-MiniLM-L6-cos-v1` - Optimized for Q&A

Change in `backend/app/rag/query_service.py`:

```python
service = RAGQueryService(
    embedding_model="all-mpnet-base-v2"
)
```

### LLM Model

Default: `llama-3.3-70b-versatile` (Groq)

**Alternatives:**
- `llama-3.1-8b-instant` - Faster, lower cost
- `mixtral-8x7b-32768` - Larger context window

Change in `backend/app/rag/query_service.py`:

```python
service = RAGQueryService(
    llm_model="llama-3.1-8b-instant"
)
```

### Retrieval Settings

- **n_results** - Number of articles to retrieve (default: 5)
- **temperature** - LLM creativity (default: 0.3 for factual)

---

## Troubleshooting

### "RAG service not available"

**Cause:** Index not built

**Fix:**
```bash
python scripts/build_rag_index.py
```

### "Collection 'research_articles' not found"

**Cause:** ChromaDB directory missing or corrupted

**Fix:**
```bash
# Rebuild index
python scripts/build_rag_index.py --rebuild
```

### "No articles to index"

**Cause:** No analyzed articles in `data/analysis/loaded/`

**Fix:** Run the GenAI pipeline first:
```bash
python scripts/full_pipeline.py --topic "Heat-Not-Burn" --max-articles 50
```

### "GROQ_API_KEY not found"

**Cause:** Missing API key

**Fix:** Add to `.env`:
```bash
GROQ_API_KEY=your-key-here
```

Get key from: https://console.groq.com/keys

### Slow queries (>10 seconds)

**Potential causes:**
- Large n_results (>10)
- Slow LLM model (switch to `llama-3.1-8b-instant`)
- Cold start (first query loads models)

**Optimization:**
```python
result = service.query(
    question="...",
    n_results=3  # Reduce from 5
)
```

---

## Performance

### Indexing
- **Speed:** ~10 articles/second
- **Storage:** ~1-2 MB per 100 articles (embeddings + metadata)
- **Index Time:** 19 articles in <5 seconds

### Query
- **Embedding:** <100ms (local model)
- **Retrieval:** <50ms (ChromaDB)
- **Generation:** 2-5 seconds (Groq LLM)
- **Total:** ~3-5 seconds end-to-end

### Scalability
- **Tested:** 19 articles (current corpus)
- **Recommended:** Up to 10,000 articles (local ChromaDB)
- **Beyond:** Consider Qdrant Cloud or Pinecone

---

## Example Questions

Try these in the Streamlit chat:

**General:**
- "What are the main health risks of vaping?"
- "Summarize findings on IQOS heated tobacco"
- "Which studies focus on smoking cessation?"

**Comparative:**
- "Compare e-cigarettes vs nicotine pouches"
- "Heated tobacco vs traditional cigarettes"
- "Youth vs adult vaping patterns"

**Specific:**
- "Studies with PMI affiliation"
- "Clinical trials on cardiovascular effects"
- "Negative sentiment studies from 2025"

**Research Gaps:**
- "What's missing from the literature on snus?"
- "Understudied aspects of dual use?"

---

## Next Steps

1. **Build index**: `python scripts/build_rag_index.py`
2. **Launch app**: `streamlit run streamlit_app_with_rag.py`
3. **Ask questions** in the chat sidebar
4. **Add more articles** → Re-run indexing → Ask deeper questions

---

## Architecture Diagram

```
┌──────────────────────────────────────────────────────────┐
│                    RAG SYSTEM ARCHITECTURE                │
└──────────────────────────────────────────────────────────┘

Data Sources:
    PubMed API → Ingestion → SQLite
         ↓
    GenAI Pipeline (Stages 1-5)
         ↓
    data/analysis/loaded/*.json
         ↓
         ↓
Indexing (Stage 6):
    build_rag_index.py
         ↓
    sentence-transformers (all-MiniLM-L6-v2)
         ↓
    ChromaDB (persistent, local)
         ↓
    data/chroma/
         ↓
         ↓
Query Interface:
    User Question
         ↓
    RAGQueryService
         ├─→ Semantic Search (ChromaDB)
         ├─→ Metadata Filtering
         ├─→ Context Assembly
         └─→ LLM Generation (Groq)
              ↓
    Answer + Citations
         ↓
    Streamlit Chat UI
```

---

## Cost Analysis

**Free Tier (Current Setup):**
- Embedding: Free (local `sentence-transformers`)
- Storage: Free (local ChromaDB)
- LLM: Groq free tier (6,000 requests/day)

**Per Query Cost:**
- Embedding: $0 (local)
- ChromaDB: $0 (local)
- Groq LLM: ~$0.0005 (llama-3.3-70b)
- **Total: <$0.001 per query**

**Estimated Monthly:**
- 1,000 queries/month: ~$1
- 10,000 queries/month: ~$10

---

## Credits

- **ChromaDB**: https://www.trychroma.com/
- **Sentence Transformers**: https://www.sbert.net/
- **Groq**: https://groq.com/
- **Streamlit**: https://streamlit.io/

---

**Version:** 1.0  
**Last Updated:** 2026-08-19
