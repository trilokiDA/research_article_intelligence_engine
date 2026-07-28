# Future Proposed GenAI Pipeline Architecture

**Status:** Proposed - Not Yet Implemented  
**Date:** 2026-07-28  
**Goal:** Production-grade ML pipeline for processing 100k+ articles with quality control

---

## Executive Summary

This document outlines a proposed enhancement to the GenAI pipeline that introduces:
- **File-based processing** (JSON) for flexibility during experimentation
- **Quality evaluation gate** (80% threshold) before database insertion
- **Iterative refinement** (reinfer loop) for low-quality outputs
- **Separation of processing vs serving layers** for scalability

## Current vs Proposed Architecture

### Current Architecture
```
articles table (summary IS NULL)
         ↓
    GenAI Process
         ↓
article_analysis table (direct insert)
         ↓
    API/Dashboard
```

**Limitations:**
- No quality control before DB insertion
- Hard to experiment with different models/prompts
- Difficult to iterate on poor results
- DB gets cluttered with draft versions

### Proposed Architecture
```
┌─────────────────────────────────────────────────────────────┐
│ STAGE 1: FETCH PENDING                                      │
└─────────────────────────────────────────────────────────────┘
                            ↓
        SELECT * FROM articles WHERE summary IS NULL
                            ↓
                    [100k pending articles]

┌─────────────────────────────────────────────────────────────┐
│ STAGE 2: GENAI SUMMARIZATION                                │
└─────────────────────────────────────────────────────────────┘
                            ↓
            For each article → Run GenAI
                            ↓
        Save to: data/analysis/raw/{article_id}.json
                            ↓
            Example: PMID001.json, PMID002.json

┌─────────────────────────────────────────────────────────────┐
│ STAGE 3: EVALUATION (Quality Gate)                          │
└─────────────────────────────────────────────────────────────┘
                            ↓
        Read {article_id}.json → Run eval logic
                            ↓
                    ┌───────────────┐
                    │  Eval Score?  │
                    └───────┬───────┘
                            │
            ┌───────────────┼───────────────┐
            │                               │
        >= 80%                          < 80%
            │                               │
            ↓                               ↓
    ┌──────────────┐              ┌──────────────┐
    │   APPROVED   │              │   REINFER    │
    │              │              │  (retry with │
    │ Save to:     │              │   feedback)  │
    │ approved/    │              │              │
    │ {id}.json    │              └──────┬───────┘
    └──────┬───────┘                     │
           │                             │
           │                 Loop back to GenAI
           │                  with eval feedback
           │                             │
           └─────────────────────────────┘
                            ↓
                    All approved!

┌─────────────────────────────────────────────────────────────┐
│ STAGE 4: LOAD TO DATABASE (Final)                           │
└─────────────────────────────────────────────────────────────┘
                            ↓
    Read approved/*.json → Bulk insert into DB
                            ↓
            article_analysis table populated
                            ↓
        UPDATE articles SET summary_status = 'completed'

┌─────────────────────────────────────────────────────────────┐
│ STAGE 5: SERVE (Dashboard, API, SQL)                        │
└─────────────────────────────────────────────────────────────┘
                            ↓
        FastAPI / Dashboard → SQL queries on DB
                            ↓
        Fast, reliable, production-ready
```

## Proposed Folder Structure

```
data/
├── articles.db                      # Source database
└── analysis/
    ├── raw/                         # GenAI outputs (Stage 2)
    │   ├── PMID001.json            # First attempt
    │   ├── PMID002.json
    │   ├── batch_001/              # Optional: organize by batch
    │   │   ├── PMID001.json
    │   │   └── ...
    │   └── batch_002/
    │
    ├── evaluated/                   # After eval (Stage 3)
    │   ├── PMID001_eval.json       # Eval score + feedback
    │   ├── PMID002_eval.json
    │   └── ...
    │
    ├── reinfer/                     # Failed → retry (Stage 3)
    │   ├── attempt_1/
    │   │   ├── PMID005.json        # Score < 80%, needs retry
    │   │   └── PMID007.json
    │   ├── attempt_2/
    │   │   └── PMID005.json        # Second attempt
    │   └── attempt_3/
    │       └── PMID005.json        # Final attempt
    │
    ├── approved/                    # Final approved (Stage 3)
    │   ├── PMID001.json            # Score >= 80%, ready for DB
    │   ├── PMID002.json
    │   └── ...
    │
    ├── rejected/                    # Failed after max retries
    │   └── PMID999.json            # Needs manual review
    │
    └── manifest.json                # Tracking file (see below)
```

## File Format Specifications

### 1. Raw GenAI Output (`raw/PMID001.json`)

```json
{
  "article_id": "PMID001",
  "stage": "raw",
  "attempt": 1,
  "processed_at": "2024-07-28T10:30:00Z",
  "model": "llama-3.3-70b-versatile",
  "prompt_version": "v1",
  "source_data": {
    "title": "E-cigarette Study",
    "journal": "Tobacco Research",
    "date": "2024-01-15",
    "abstract": "Original abstract text from database..."
  },
  "analysis": {
    "summary": "AI-generated summary with people-first language...",
    "entities": ["electronic cigarettes", "harm reduction"],
    "category": "Clinical Studies",
    "subject": "E-cigarettes",
    "sentiment": "Positive",
    "country": "United States",
    "industry_affiliation": "n/a"
  },
  "metadata": {
    "processing_time_ms": 3450,
    "tokens_used": 1250,
    "cost": 0.0015
  }
}
```

### 2. Evaluation Result (`evaluated/PMID001_eval.json`)

```json
{
  "article_id": "PMID001",
  "stage": "evaluated",
  "evaluated_at": "2024-07-28T10:31:00Z",
  "source_file": "raw/PMID001.json",
  "evaluator_version": "v1.0",
  "eval_results": {
    "score": 85,
    "passed": true,
    "threshold": 80,
    "checks": {
      "factual_accuracy": {
        "score": 90,
        "weight": 0.4,
        "details": "All claims verified against abstract"
      },
      "completeness": {
        "score": 85,
        "weight": 0.3,
        "details": "Covers main findings and methodology"
      },
      "people_first_language": {
        "score": 100,
        "weight": 0.2,
        "details": "Consistently uses 'participants who smoke'"
      },
      "entity_extraction": {
        "score": 80,
        "weight": 0.1,
        "details": "Identified 8/10 key entities"
      }
    },
    "issues": [],
    "feedback": "High-quality summary, approved for production."
  }
}
```

### 3. Reinfer Needed (`evaluated/PMID005_eval.json`)

```json
{
  "article_id": "PMID005",
  "stage": "evaluated",
  "evaluated_at": "2024-07-28T10:32:00Z",
  "source_file": "raw/PMID005.json",
  "evaluator_version": "v1.0",
  "eval_results": {
    "score": 65,
    "passed": false,
    "threshold": 80,
    "checks": {
      "factual_accuracy": {
        "score": 60,
        "weight": 0.4,
        "details": "Added information not present in abstract"
      },
      "completeness": {
        "score": 70,
        "weight": 0.3,
        "details": "Missing key methodology details"
      },
      "people_first_language": {
        "score": 50,
        "weight": 0.2,
        "details": "Used 'smokers' instead of 'participants who smoke'"
      },
      "entity_extraction": {
        "score": 80,
        "weight": 0.1,
        "details": "Entities correctly identified"
      }
    },
    "issues": [
      "Used 'smokers' instead of 'participants who smoke' (3 occurrences)",
      "Summary includes 'cardiovascular benefits' not mentioned in abstract",
      "Missing sample size information"
    ],
    "feedback": "REINFER REQUIRED: 1) Use people-first language consistently. 2) Only include information explicitly stated in abstract. 3) Include sample size and duration.",
    "reinfer_prompt_additions": "Previous attempt failed due to: using stigmatizing language and adding unsupported claims. Please strictly use 'participants who smoke' and only summarize information explicitly stated in the abstract."
  }
}
```

### 4. Approved Final (`approved/PMID001.json`)

```json
{
  "article_id": "PMID001",
  "stage": "approved",
  "approved_at": "2024-07-28T10:31:00Z",
  "total_attempts": 1,
  "final_score": 85,
  "ready_for_db": true,
  "lineage": {
    "raw_file": "raw/PMID001.json",
    "eval_file": "evaluated/PMID001_eval.json",
    "reinfer_files": []
  },
  "analysis": {
    "summary": "Final approved summary...",
    "entities": ["electronic cigarettes", "harm reduction"],
    "category": "Clinical Studies",
    "subject": "E-cigarettes",
    "sentiment": "Positive",
    "country": "United States",
    "industry_affiliation": "n/a"
  },
  "quality_metrics": {
    "final_score": 85,
    "factual_accuracy": 90,
    "completeness": 85,
    "people_first_language": 100,
    "entity_extraction": 80
  }
}
```

### 5. Manifest File (`manifest.json`)

```json
{
  "pipeline_version": "1.0",
  "last_updated": "2024-07-28T12:00:00Z",
  "configuration": {
    "passing_score_threshold": 80,
    "max_reinfer_attempts": 3,
    "evaluation_checks": [
      "factual_accuracy",
      "completeness",
      "people_first_language",
      "entity_extraction"
    ],
    "model": "llama-3.3-70b-versatile",
    "prompt_version": "v1"
  },
  "statistics": {
    "total_articles_processed": 100000,
    "by_stage": {
      "raw": 100000,
      "evaluated": 100000,
      "approved": 85000,
      "reinfer_needed": 10000,
      "rejected": 5000,
      "loaded_to_db": 85000
    },
    "quality_metrics": {
      "average_score": 82.5,
      "average_attempts": 1.15,
      "approval_rate": 0.85
    },
    "cost_metrics": {
      "total_api_calls": 115000,
      "total_tokens": 143750000,
      "estimated_cost_usd": 172.50
    }
  },
  "by_article": {
    "PMID001": {
      "status": "approved",
      "attempts": 1,
      "score": 85,
      "loaded_to_db": true,
      "loaded_at": "2024-07-28T14:00:00Z"
    },
    "PMID005": {
      "status": "reinfer",
      "attempts": 2,
      "current_score": 75,
      "loaded_to_db": false
    },
    "PMID999": {
      "status": "rejected",
      "attempts": 3,
      "final_score": 55,
      "loaded_to_db": false,
      "needs_manual_review": true
    }
  }
}
```

## Pipeline Workflow Details

### Stage 1: Fetch Pending Articles

```python
# Query articles without summaries
query = """
    SELECT article_id, title, journal, publication_date, abstract
    FROM articles
    WHERE summary_status IS NULL
    ORDER BY ingested_at DESC
"""

pending_articles = execute_query(query)
# Result: List of 100k articles
```

### Stage 2: GenAI Summarization

```python
for article in pending_articles:
    # Run GenAI
    result = summarize_article(
        article_id=article['article_id'],
        title=article['title'],
        journal=article['journal'],
        date=article['publication_date'],
        abstract=article['abstract']
    )
    
    # Save to raw/
    save_json(
        path=f"data/analysis/raw/{article['article_id']}.json",
        data={
            "article_id": article['article_id'],
            "stage": "raw",
            "attempt": 1,
            "processed_at": now(),
            "analysis": result
        }
    )
```

### Stage 3: Evaluation & Reinfer Loop

```python
max_attempts = 3

for article_id in processed_articles:
    for attempt in range(1, max_attempts + 1):
        # Load raw result
        raw_file = f"raw/{article_id}.json"
        result = load_json(raw_file)
        
        # Evaluate quality
        eval_result = evaluate_summary(result)
        
        # Save evaluation
        save_json(
            path=f"evaluated/{article_id}_eval.json",
            data=eval_result
        )
        
        if eval_result['score'] >= 80:
            # APPROVED - Save to approved/
            save_json(
                path=f"approved/{article_id}.json",
                data={
                    "article_id": article_id,
                    "stage": "approved",
                    "total_attempts": attempt,
                    "final_score": eval_result['score'],
                    "analysis": result['analysis']
                }
            )
            break
        else:
            # REINFER - Retry with feedback
            if attempt < max_attempts:
                feedback = eval_result['feedback']
                
                # Retry with feedback in prompt
                result = summarize_article_with_feedback(
                    article=article,
                    previous_attempt=result,
                    feedback=feedback
                )
                
                # Save reinfer attempt
                save_json(
                    path=f"reinfer/attempt_{attempt + 1}/{article_id}.json",
                    data=result
                )
            else:
                # REJECTED - Max attempts reached
                save_json(
                    path=f"rejected/{article_id}.json",
                    data={
                        "article_id": article_id,
                        "stage": "rejected",
                        "total_attempts": attempt,
                        "final_score": eval_result['score'],
                        "reason": "Failed after max attempts",
                        "needs_manual_review": True
                    }
                )
```

### Stage 4: Load to Database

```python
# Load all approved articles into DB
approved_files = glob("data/analysis/approved/*.json")

batch = []
for file_path in approved_files:
    data = load_json(file_path)
    batch.append(data)
    
    # Bulk insert every 1000 records
    if len(batch) >= 1000:
        bulk_insert_to_article_analysis(batch)
        
        # Update articles table
        article_ids = [item['article_id'] for item in batch]
        update_query = """
            UPDATE articles 
            SET summary_status = 'completed'
            WHERE article_id IN (?)
        """
        execute_query(update_query, article_ids)
        
        batch = []

# Insert remaining
if batch:
    bulk_insert_to_article_analysis(batch)
```

### Stage 5: Serve via API/Dashboard

```python
# Now data is in DB, can use SQL for fast queries
@app.get("/articles/summary")
def get_articles(
    sentiment: str = None,
    category: str = None,
    limit: int = 100
):
    query = """
        SELECT 
            a.title,
            a.journal,
            a.publication_date,
            aa.summary,
            aa.sentiment,
            aa.category,
            aa.entities
        FROM articles a
        JOIN article_analysis aa ON a.article_id = aa.article_id
        WHERE 1=1
    """
    
    if sentiment:
        query += f" AND aa.sentiment = '{sentiment}'"
    if category:
        query += f" AND aa.category = '{category}'"
    
    query += f" LIMIT {limit}"
    
    return execute_query(query)
```

## Key Benefits

### 1. Quality Control ✅
- Only summaries with score ≥ 80% reach production database
- Clear pass/fail criteria
- Audit trail for every article
- Reduces manual review burden

### 2. Iterative Improvement 🔄
- Poor summaries get specific feedback and retry
- Can adjust threshold as quality improves
- Learn from common failure patterns
- Maximum 3 attempts prevents infinite loops

### 3. Separation of Concerns 🎯
```
Processing Layer  → JSON files (flexible, versioned)
Serving Layer     → Database (fast, queryable)
Archive Layer     → S3/Local storage (long-term)
```

### 4. Cost Optimization 💰
- Don't waste DB storage on draft versions
- Only final approved data in DB
- Can delete intermediate files after loading
- Track API costs per article

### 5. Traceability 📊
Complete lineage for every article:
```
PMID001 journey:
1. raw/PMID001.json (attempt 1) → score 65
2. reinfer/attempt_1/PMID001.json → score 75
3. reinfer/attempt_2/PMID001.json → score 85 ✓
4. approved/PMID001.json
5. article_analysis table
6. Production API
```

### 6. Scalability 📈
- Process 100k articles without DB load during experimentation
- Parallel processing on file system
- Can distribute across multiple workers
- Resume from any point using manifest.json

### 7. Experimentation 🧪
```
# Try new model without affecting production
data/analysis_v2/
  ├── raw/           (new model outputs)
  ├── evaluated/     (compare scores)
  └── approved/      (compare quality)

# Choose better version, load to DB
```

### 8. Human Review Integration 👥
```
rejected/ folder contains articles that need manual review:
- Export to CSV
- Review by domain experts
- Manual corrections
- Re-add to approved/
- Load to DB
```

## Article Lifecycle States

```
┌──────────────────────────────────────────────────────────┐
│                   Article States                         │
└──────────────────────────────────────────────────────────┘

1. PENDING       → articles.summary_status = NULL
                    No processing started

2. PROCESSING    → GenAI running
                    Saving to raw/

3. EVALUATING    → Quality check in progress
                    Calculating scores

4. REINFER       → Score < 80%
                    Retry with feedback
                    (Max 3 attempts)

5. APPROVED      → Score >= 80%
                    Ready for DB load
                    In approved/ folder

6. REJECTED      → Failed after 3 attempts
                    Needs manual review
                    In rejected/ folder

7. LOADED        → In article_analysis table
                    articles.summary_status = 'completed'

8. SERVING       → Available via API/Dashboard
                    Production ready
```

## Advantages for 100k+ Scale

### 1. Checkpointing & Recovery
```json
// manifest.json tracks progress
{
  "last_processed_batch": 5,
  "last_article_id": "PMID005000",
  "checkpoint_time": "2024-07-28T12:00:00Z"
}

// Resume from crash
python pipeline.py --resume-from-checkpoint
```

### 2. Parallel Processing
```bash
# Split work across workers
Worker 1: Process articles 1-20k     → raw_worker1/
Worker 2: Process articles 20k-40k   → raw_worker2/
Worker 3: Process articles 40k-60k   → raw_worker3/
Worker 4: Process articles 60k-80k   → raw_worker4/
Worker 5: Process articles 80k-100k  → raw_worker5/

# Merge results
python merge_results.py
```

### 3. Progressive Loading
```python
# Don't wait for all 100k to finish
# Load approved articles incrementally

while processing_in_progress:
    # Every hour, load newly approved articles
    new_approved = get_approved_since_last_load()
    bulk_insert_to_db(new_approved)
    
    # Dashboard shows growing dataset
    sleep(3600)  # 1 hour
```

### 4. A/B Testing Models
```
Compare different models on same articles:

data/analysis/
  ├── llama_3.3_70b/
  │   ├── raw/
  │   ├── evaluated/
  │   └── approved/
  │
  └── gpt_4/
      ├── raw/
      ├── evaluated/
      └── approved/

# Compare quality and cost
model_comparison = {
    "llama": {"avg_score": 82, "cost": $150},
    "gpt4": {"avg_score": 88, "cost": $450}
}
```

### 5. Batch Processing Insights
```json
// Per-batch metrics
{
  "batch_001": {
    "articles": 1000,
    "approved": 850,
    "reinfer": 100,
    "rejected": 50,
    "avg_score": 83,
    "processing_time_minutes": 45
  }
}

// Identify problematic batches
// Adjust parameters for future batches
```

## Database Schema Updates Needed

### Add summary_status column to articles table:

```sql
-- Migration
ALTER TABLE articles 
ADD COLUMN summary_status TEXT DEFAULT NULL;

-- Create index
CREATE INDEX idx_articles_summary_status 
ON articles(summary_status);

-- Possible values:
-- NULL          = Not yet processed
-- 'processing'  = Currently being processed
-- 'completed'   = Analysis in article_analysis table
-- 'failed'      = Needs manual review
```

### article_analysis table remains the same:
- Only stores final approved summaries
- No draft versions
- Clean production data

## Evaluation Logic (To Be Defined)

### Evaluation Components:

1. **Factual Accuracy (40% weight)**
   - Claims verification against abstract
   - No hallucinated information
   - Proper attribution

2. **Completeness (30% weight)**
   - Key findings included
   - Methodology mentioned
   - Sample size stated (if available)

3. **People-First Language (20% weight)**
   - "participants who smoke" not "smokers"
   - "individuals with asthma" not "asthmatics"
   - Consistent throughout

4. **Entity Extraction (10% weight)**
   - Correct entities identified
   - No missing key entities
   - No false positives

### Scoring Formula:
```python
final_score = (
    factual_accuracy * 0.4 +
    completeness * 0.3 +
    people_first_language * 0.2 +
    entity_extraction * 0.1
)

# Score >= 80 = Approved
# Score < 80 = Reinfer (with specific feedback)
```

## Reinfer Strategy (To Be Defined)

### Feedback Generation:
```python
if score < 80:
    feedback = []
    
    if factual_accuracy < 70:
        feedback.append("Claims not supported by abstract. Only include explicitly stated information.")
    
    if people_first_language < 70:
        feedback.append("Use people-first language: 'participants who smoke' not 'smokers'.")
    
    if completeness < 70:
        feedback.append("Missing key information: sample size, methodology, or main findings.")
    
    # Add feedback to next attempt's prompt
    reinfer_prompt = base_prompt + "\n\nPrevious attempt feedback:\n" + "\n".join(feedback)
```

## Implementation Phases

### Phase 1: Proof of Concept (2-3 weeks)
- [ ] Implement file-based processing for 100 articles
- [ ] Create basic evaluation logic
- [ ] Test reinfer loop
- [ ] Validate folder structure

### Phase 2: Scale Testing (2-3 weeks)
- [ ] Process 10k articles
- [ ] Tune evaluation thresholds
- [ ] Optimize reinfer prompts
- [ ] Performance benchmarking

### Phase 3: Production Pipeline (3-4 weeks)
- [ ] Parallel processing implementation
- [ ] Checkpointing and recovery
- [ ] Monitoring and alerting
- [ ] Cost tracking

### Phase 4: Database Loading (1-2 weeks)
- [ ] Bulk insert optimization
- [ ] Data validation
- [ ] API integration
- [ ] Dashboard updates

## Open Questions & Future Discussion

### 1. Evaluation Logic Details
- Exact scoring algorithm for each component?
- How to measure factual accuracy automatically?
- Benchmark evaluation against human reviewers?

### 2. Reinfer Strategy
- What specific feedback is most effective?
- Should feedback be structured or free-form?
- Track which feedback leads to improvement?

### 3. Parallel Processing
- How many concurrent workers optimal?
- Worker coordination strategy?
- Handling race conditions?

### 4. Error Handling
- API rate limits and failures?
- Malformed JSON outputs?
- File system errors?
- Recovery strategies?

### 5. Monitoring & Alerting
- Real-time progress tracking?
- Quality metrics dashboard?
- Alert on low approval rates?
- Cost monitoring and budgets?

### 6. Manual Review Process
- Interface for reviewing rejected articles?
- Expert reviewer workflow?
- Feedback incorporation into model?

### 7. S3 Integration
- When to move to S3?
- Cost analysis: local vs S3?
- Sync strategy between local and S3?

### 8. Version Control
- How to version evaluation logic?
- Track prompt version effectiveness?
- Model comparison framework?

## Success Metrics

### Quality Metrics
- **Approval Rate**: Target 85%+ on first attempt
- **Average Score**: Target 82+ overall
- **Reinfer Success Rate**: Target 70%+ succeed on 2nd attempt
- **Rejection Rate**: Target <5% after max attempts

### Performance Metrics
- **Processing Speed**: Target 3-5 articles/second
- **Throughput**: 100k articles in <10 hours
- **API Success Rate**: Target 99%+
- **Cost per Article**: Target <$0.002

### Business Metrics
- **Manual Review Load**: Reduce by 80%
- **Time to Production**: <24 hours from ingestion
- **Data Quality**: User-reported issues <1%

## Conclusion

This proposed architecture provides:
- ✅ **Quality control** through evaluation gates
- ✅ **Flexibility** for experimentation and iteration
- ✅ **Scalability** for 100k+ articles
- ✅ **Cost efficiency** by separating processing from serving
- ✅ **Traceability** with complete audit trails
- ✅ **Production readiness** with only high-quality data in DB

**Next Steps:**
1. Review and approve this proposal
2. Implement proof of concept (Phase 1)
3. Define detailed evaluation logic
4. Build reinfer feedback system
5. Scale to full 100k dataset

---

**Document Status:** Proposed  
**Requires Approval From:** Technical Lead, Product Owner  
**Estimated Implementation Time:** 8-12 weeks  
**Dependencies:** Current GenAI pipeline must remain operational during transition
