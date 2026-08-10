# Streamlit UI - Quick Start

## Installation

```bash
# Install Streamlit dependencies
pip install streamlit plotly pandas

# Or install all requirements
pip install -r requirements.txt
```

## Running the App

```bash
# From project root
streamlit run streamlit_app.py
```

The app will open automatically in your browser at `http://localhost:8501`

## Features

### Dashboard
- Total articles, analyzed count, pending count
- Completion rate metrics
- Source distribution pie chart
- Recent publications timeline
- Latest articles table

### Article Browser
- Full-text search (uses SQLite FTS5)
- Filter by source (PubMed, Crossref)
- Date range filtering
- Analysis status filtering
- Expandable article cards with:
  - Full abstract
  - AI analysis (summary, entities, sentiment, category)
  - DOI link
- Export results to CSV

## Usage Tips

1. **Search**: Use keywords from title or abstract
2. **Filters**: Combine multiple filters for precise results
3. **Analysis Details**: Click on any article to expand and see AI analysis
4. **Export**: Filter articles and export to CSV for further analysis

## Troubleshooting

### "No articles found"
- Run ingestion first: `python ingest_cli.py topic "Heat-Not-Burn" --max 50`

### "Database locked"
- Close other connections to articles.db
- Stop other CLI processes

### Missing analysis details
- Run the GenAI pipeline: `python backend/scripts/run_summarization.py --limit 50`
