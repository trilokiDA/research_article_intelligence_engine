# Running Streamlit with RAG

## Quick Start

```bash
# Activate virtual environment
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac

# Run the app
streamlit run streamlit_app_with_rag.py
```

## Expected Warnings (Safe to Ignore)

You may see warnings like:
```
ModuleNotFoundError: No module named 'torchvision'
```

**These are safe to ignore.** They occur because:
- `sentence-transformers` imports the `transformers` library
- `transformers` has optional vision models that need `torchvision`
- Streamlit's file watcher tries to inspect all modules
- **We don't use those vision models** - only text embeddings

The warnings don't affect functionality.

## Suppressing Warnings

The `.streamlit/config.toml` file suppresses most warnings:

```toml
[logger]
level = "error"

[server]
fileWatcherType = "none"
```

## First-Time Setup Checklist

Before running the app:

1. **Build RAG index** (required once):
   ```bash
   python scripts/build_rag_index.py
   ```

2. **Verify environment** (.env file):
   ```bash
   GROQ_API_KEY=your-key-here
   NCBI_EMAIL=your@email.com
   ```

3. **Check database**:
   ```bash
   python ingest_cli.py stats
   ```

## Troubleshooting

### "RAG index not built"
**Fix:**
```bash
python scripts/build_rag_index.py
```

### "No module named 'chromadb'"
**Fix:**
```bash
pip install chromadb sentence-transformers
```

### "GROQ_API_KEY not found"
**Fix:** Add to `.env` file:
```
GROQ_API_KEY=your-key-here
```

### Port already in use
**Fix:** Use a different port:
```bash
streamlit run streamlit_app_with_rag.py --server.port 8502
```

## Features Available

Once running, you'll have:

✅ **Dashboard** - Statistics and charts  
✅ **Article Browser** - Search and filter articles  
✅ **RAG Chat** (Sidebar) - Ask questions about your corpus  
✅ **Source Citations** - Every answer cites article IDs  
✅ **Chat History** - Review previous Q&A sessions  

## Production Deployment

For production, use:

```bash
# Install production server
pip install gunicorn streamlit-server-state

# Run with gunicorn
gunicorn -w 4 -b 0.0.0.0:8501 streamlit_app_with_rag:main
```

Or deploy to:
- **Streamlit Cloud** (free tier available)
- **Docker** (Dockerfile provided in docs/)
- **AWS/GCP/Azure** (standard Python app)

## Performance Notes

- **First query**: ~5-10 seconds (loads embedding model)
- **Subsequent queries**: ~3-5 seconds (Groq LLM generation)
- **Embedding**: <100ms (runs locally)
- **ChromaDB retrieval**: <50ms

## Alternative: Run without RAG

If you don't need RAG, use the original app:

```bash
streamlit run streamlit_app.py
```

(No RAG index required)
