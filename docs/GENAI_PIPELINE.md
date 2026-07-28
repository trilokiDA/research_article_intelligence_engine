# Article Summarization Pipeline

Automated GenAI pipeline for summarizing research articles using Groq LLMs.

## Architecture

```
┌─────────────────────┐
│   articles.db       │
│  (ingested data)    │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────────────┐
│ backend/app/genai/          │
│   repository.py             │ ◄─── Queries articles where summary IS NULL
│   (data access)             │
└──────────┬──────────────────┘
           │
           ▼
┌─────────────────────────────┐
│ backend/app/genai/          │
│   summarizer.py             │ ◄─── Uses Groq + LangChain
│   (LLM service)             │      Validates with Pydantic schema
└──────────┬──────────────────┘
           │
           ▼
┌─────────────────────────────┐
│ backend/app/genai/          │
│   pipeline.py               │ ◄─── Orchestrates batch processing
│   (orchestration)           │      Saves to article_analysis table
└──────────┬──────────────────┘
           │
           ▼
┌─────────────────────────────┐
│ backend/scripts/            │
│   run_summarization.py      │ ◄─── CLI entry point
│   (command interface)       │
└─────────────────────────────┘
```

## Components

### 1. **backend/app/genai/schemas.py**
Pydantic models for structured output validation:
- `Response` - Main article analysis schema
- `EntityEnum` - Predefined topic entities
- `CategoryEnum` - Research categories
- `SentimentEnum` - THR sentiment options
- `SubjectEnum` - Broad research subjects

### 2. **backend/app/genai/prompts.py**
Prompt templates:
- `summarization_prompt` - Main analysis prompt
- `revalidate_prompt` - Schema validation retry
- `summary_evaluation_prompt` - Fact checking
- `reinfer_prompt` - Iterative improvement

### 3. **backend/app/genai/summarizer.py**
Core LLM service using Groq + LangChain:
- `ArticleSummarizer` class
- Structured output with automatic validation
- Retry logic for schema errors
- Batch processing support

### 4. **backend/app/genai/repository.py**
Database access layer:
- `get_articles_pending_analysis()` - Fetch articles where summary IS NULL
- `save_analysis()` - Store results in article_analysis table
- `mark_analysis_failed()` - Track failures
- `get_analysis_stats()` - Statistics

### 5. **backend/app/genai/pipeline.py**
Main orchestration pipeline:
- Batch processing with progress bars
- Rate limiting between batches
- Comprehensive error handling
- Statistics reporting

### 6. **backend/scripts/run_summarization.py**
CLI entry point:
- Command-line interface
- Statistics display
- Batch processing control

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

Required packages:
- `langchain-groq` - Groq LLM integration
- `langchain-core` - LangChain core
- `pydantic` - Schema validation
- `tqdm` - Progress bars

### 2. Configure Environment

Create/update `.env` file:

```env
# Groq API Key (get from https://console.groq.com/keys)
GROQ_API_KEY=your-groq-api-key-here

# Database
DATABASE_URL=sqlite:///./data/articles.db
```

### 3. Verify Database

Check articles pending analysis:

```bash
python backend/scripts/run_summarization.py --stats-only
```

## Usage

### Basic Usage

Process all pending articles:

```bash
python backend/scripts/run_summarization.py
```

### Common Scenarios

**Test with a few articles:**
```bash
python backend/scripts/run_summarization.py --limit 10
```

**Dry run (don't save results):**
```bash
python backend/scripts/run_summarization.py --limit 5 --dry-run
```

**Use a different model:**
```bash
# Faster, less accurate
python backend/scripts/run_summarization.py --model llama-3.1-8b-instant --limit 20

# Default (recommended)
python backend/scripts/run_summarization.py --model llama-3.3-70b-versatile
```

**Custom batch size:**
```bash
python backend/scripts/run_summarization.py --batch-size 5 --delay 2.0
```

**Check statistics only:**
```bash
python backend/scripts/run_summarization.py --stats-only
```

### CLI Options

```
--limit N              Process max N articles (default: all pending)
--model MODEL          Groq model name (default: llama-3.3-70b-versatile)
--batch-size N         Articles per batch (default: 10)
--delay SECONDS        Delay between batches (default: 1.0)
--dry-run              Process but don't save (testing)
--stats-only           Show statistics only
```

## Pipeline Flow

1. **Fetch** - Query articles where `summary IS NULL` in article_analysis
2. **Process** - Send to Groq LLM with structured output
3. **Validate** - Pydantic validates against schema (auto-retry on error)
4. **Save** - Insert/update article_analysis table
5. **Repeat** - Process next batch with delay (rate limiting)

## Database Tables

### articles (source data)
- Populated by ingestion pipeline
- Contains: title, abstract, journal, date, etc.

### article_analysis (GenAI results)
- Populated by summarization pipeline
- Contains: summary, entities, category, sentiment, etc.

**Key Condition:**
```sql
WHERE aa.summary IS NULL OR aa.summary = '' OR aa.analysis_status = 'failed'
```

## Output Schema

Each article produces:

```json
{
  "articleID": "PMID12345678",
  "title": "Original article title",
  "journal": "Journal name",
  "date": "2024-01-15",
  "abstract": "Original abstract text",
  "entity": ["electronic cigarettes", "harm reduction"],
  "subject": "E-cigarettes",
  "summary": "People-first language summary...",
  "category": "Clinical Studies",
  "country": "United States",
  "sentiment": "Positive",
  "industry_affiliation": "n/a"
}
```

## Error Handling

### Automatic Retries
- Schema validation errors: 3 retries with feedback
- Failed articles marked in database with error message
- Pipeline continues on individual failures

### Rate Limiting
- Configurable delay between batches
- Prevents API rate limit issues
- Default: 1 second between batches

### Graceful Interruption
- Ctrl+C stops pipeline gracefully
- Already processed articles are saved
- Can resume later (only processes pending)

## Monitoring

### Progress Bar
```
Processing articles: 45%|████▌     | 45/100 [02:15<02:45, 0.33article/s]
```

### Statistics Output
```
================================================================================
DATABASE STATISTICS
================================================================================
Total articles:       250
Analyzed:             100
Pending:              150

By Category:
  Clinical Studies               45
  Epidemiology                   32
  Behavior Studies               23

By Sentiment:
  Positive                       50
  Neutral                        35
  Negative                       15
================================================================================
```

## Testing

### Run Complete Test Suite
```bash
python tests/test_genai.py
```

### Test Individual Components

**Test Repository:**
```python
from backend.app.genai.repository import ArticleRepository

repo = ArticleRepository()
pending = repo.count_articles_pending_analysis()
print(f"Pending articles: {pending}")
```

**Test Summarization:**
```python
from backend.app.genai.summarizer import summarize_article

result = summarize_article(
    doc_id="TEST001",
    title="Your article title",
    journal="Journal name",
    date="2024-01-15",
    abstract="Article abstract text..."
)
print(result.summary)
```

**Dry Run Pipeline:**
```bash
python backend/scripts/run_summarization.py --limit 5 --dry-run
```

## Available Groq Models

- `llama-3.3-70b-versatile` - **Recommended** (best quality)
- `llama-3.1-8b-instant` - Fast (lower quality)
- `mixtral-8x7b-32768` - Alternative

Check latest models: https://console.groq.com/docs/models

## Troubleshooting

### "GROQ_API_KEY not found"
- Ensure `.env` file exists with valid API key
- Get key from: https://console.groq.com/keys

### "No articles need processing"
- Run ingestion pipeline first to populate articles table
- Check: `python view_data.py --stats`

### Schema validation errors
- Check that enums in schema.py match prompt instructions
- Validation auto-retries 3 times with feedback

### Rate limiting
- Increase `--delay` between batches
- Reduce `--batch-size`

## Performance

**Processing Speed:**
- ~3-5 seconds per article (llama-3.3-70b)
- ~1-2 seconds per article (llama-3.1-8b)

**Batch Recommendations:**
- Small datasets (<100): `--batch-size 10`
- Large datasets (>1000): `--batch-size 20 --delay 0.5`

**Cost Estimation:**
- Groq offers generous free tier
- Check pricing: https://wow.groq.com/

## Next Steps

After summarization:

1. **View Results:**
   ```bash
   python view_data.py --format detailed
   ```

2. **Export Analysis:**
   ```sql
   SELECT a.*, aa.*
   FROM articles a
   JOIN article_analysis aa ON a.article_id = aa.article_id
   WHERE aa.summary IS NOT NULL
   ```

3. **Build Dashboard:**
   - Use FastAPI to serve results
   - Create visualizations from analysis data

4. **Add Fact Checking:**
   - Implement evaluation pipeline
   - Use `summary_evaluation_prompt`
   - Add LangGraph for multi-step workflows
