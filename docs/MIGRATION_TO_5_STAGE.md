# Migration Plan: 2-Stage to 5-Stage Architecture

**Date:** 2026-07-31  
**Version:** v1.0 → v1.1  
**Status:** Planning

---

## Current Architecture (v1.0)

### Stage 1: Data Ingestion
```
PubMed API → Connector → Normalizer → SQLite (articles table)
```

### Stage 2: GenAI Analysis
```
SQLite → Summarizer → data/analysis/summarized/*.json
```

**Current State:**
- Files go directly to `data/analysis/summarized/`
- No quality control gate
- No evaluation pipeline
- No re-inference capability

---

## Target Architecture (v1.1)

### Stage 1: Data Ingestion (No Change)
```
PubMed API → Connector → Normalizer → SQLite (articles table)
```

### Stage 2: GenAI Summarization → RAW
```
SQLite (WHERE summary IS NULL) → Summarizer → data/analysis/raw/*.json
```
**Change:** Output goes to `raw/` instead of `summarized/`

### Stage 3: Evaluation
```
data/analysis/raw/*.json → Evaluator → Score (0-100%)
   ↓
  >= 80%  → data/analysis/approved/*.json
  < 80%   → data/analysis/reinfer/*.json (with feedback)
```

### Stage 4: Re-inference (If Needed)
```
data/analysis/reinfer/*.json → Summarizer (with feedback) → Re-evaluate
   ↓
  >= 80% after retry → data/analysis/approved/*.json
  Failed 3x         → data/analysis/rejected/*.json (manual review)
```

### Stage 5: Database Load (Future)
```
data/analysis/approved/*.json → Load to article_analysis table
```

---

## What Needs to Change

### 1. **file_writer.py** (MODIFY)

**Current:**
- Only has `summarized/` directory
- `save_summarized_analysis()` saves to `summarized/`
- Stage field always "summarized"

**Changes Needed:**
- ✅ Add `raw_dir` property (new)
- ✅ Rename `summarized_dir` → keep for backward compatibility
- ✅ Update `_ensure_directories()` to create `raw/` directory
- ✅ Add `save_raw_analysis()` method (saves to `raw/` with stage="raw")
- ✅ Add `load_raw_analysis()` method
- ✅ Add `list_raw_analyses()` method
- ✅ Keep existing methods for backward compatibility

**New Methods:**
```python
def save_raw_analysis(...) -> Path:
    """Save GenAI output to data/analysis/raw/"""
    
def load_raw_analysis(article_id) -> Dict:
    """Load from raw/ directory"""
    
def save_evaluated_analysis(...) -> Path:
    """Save to evaluated/ with evaluation metadata"""
    
def move_to_approved(article_id) -> Path:
    """Move from evaluated/ to approved/"""
    
def move_to_reinfer(article_id, feedback) -> Path:
    """Move from evaluated/ to reinfer/ with feedback"""
```

---

### 2. **pipeline.py** (MODIFY)

**Current:**
- `output_format` parameter: "json" or "database"
- Saves to `summarized/` when format="json"
- Checks `file_writer.exists_summarized_analysis()` for skip logic

**Changes Needed:**
- ✅ Change default output directory from `summarized/` to `raw/`
- ✅ Update skip logic to check `raw/` directory
- ✅ Update `save_summarized_analysis()` call to `save_raw_analysis()`
- ✅ Update stage field to "raw"
- ✅ Keep backward compatibility flag for existing behavior

**New Parameters:**
```python
def __init__(
    self,
    output_stage: str = "raw",  # NEW: "raw" or "summarized" (legacy)
    ...
):
```

---

### 3. **evaluator.py** (ADD NEW)

**Location:** `backend/app/genai/evaluator.py`

**Purpose:** Evaluate quality of summaries from `raw/` directory

**Class:**
```python
class SummaryEvaluator:
    def __init__(self, model_name: str = "llama-3.3-70b-versatile"):
        """Initialize evaluator with Groq LLM"""
        
    def evaluate(self, raw_analysis: Dict) -> Dict:
        """
        Evaluate a raw analysis file.
        
        Returns:
        {
            "article_id": "PMID001",
            "quality_score": 85,  # 0-100
            "factual_accuracy": 90,  # 0-100
            "hallucination_detected": False,
            "people_first_language": True,
            "entity_consistency": True,
            "claim_evaluations": [
                {"claim": "...", "label": "Supported", "explanation": "..."}
            ],
            "feedback": "Improve X by...",
            "passed": True  # >= 80%
        }
        """
        
    def batch_evaluate(self, article_ids: List[str]) -> Dict:
        """Batch evaluation with progress tracking"""
```

---

### 4. **schemas.py** (ADD NEW)

**Current:**
- Has `FactualEvaluationResponse` (already exists!)
- Has `ClaimEvaluation` (already exists!)

**Changes Needed:**
- ✅ Add `EvaluationResult` schema
- ✅ Add `EvaluationMetadata` schema
- ✅ Keep existing `FactualEvaluationResponse` for fact-checking

**New Schemas:**
```python
class EvaluationResult(BaseModel):
    """Complete evaluation result"""
    article_id: str
    quality_score: float = Field(ge=0, le=100)
    factual_accuracy: float = Field(ge=0, le=100)
    hallucination_detected: bool
    people_first_language: bool
    entity_consistency: bool
    claim_evaluations: List[ClaimEvaluation]
    feedback: str
    passed: bool
    evaluated_at: str
    
class EvaluationMetadata(BaseModel):
    """Metadata for evaluation process"""
    evaluator_model: str
    evaluation_version: str
    processing_time_ms: int
```

---

### 5. **prompts.py** (ADD NEW)

**Current:**
- Has `summary_evaluation_prompt` (fact-checking)
- Has `reinfer_prompt` (re-inference with feedback)

**Changes Needed:**
- ✅ Add `quality_scoring_prompt` (overall quality 0-100)
- ✅ Add `hallucination_detection_prompt` (find unsupported claims)
- ✅ Add `people_first_check_prompt` (validate language)
- ✅ Keep existing prompts

**New Prompts:**
```python
quality_scoring_prompt = """
You are evaluating the quality of a generated summary.
Score from 0-100 based on:
- Factual accuracy (40%)
- Completeness (30%)
- Clarity (20%)
- People-first language (10%)
...
"""

hallucination_detection_prompt = """
Identify any claims in the summary that are:
1. Not supported by the abstract
2. Add information not present
3. Contradict the abstract
...
"""
```

---

### 6. **scripts/evaluate_summaries.py** (ADD NEW)

**Location:** `scripts/evaluate_summaries.py`

**Purpose:** CLI tool to run evaluation pipeline

**Usage:**
```bash
# Evaluate all files in raw/
python scripts/evaluate_summaries.py

# Evaluate specific files
python scripts/evaluate_summaries.py --article-ids PMID001,PMID002

# Evaluate with different threshold
python scripts/evaluate_summaries.py --threshold 85

# Dry run
python scripts/evaluate_summaries.py --dry-run
```

**Features:**
- Read from `data/analysis/raw/`
- Evaluate each file
- Route based on score:
  - ≥80% → `approved/`
  - <80% → `reinfer/`
- Progress tracking
- Statistics report

---

### 7. **scripts/reinfer_summaries.py** (ADD NEW)

**Location:** `scripts/reinfer_summaries.py`

**Purpose:** Re-run summarization on failed evaluations with feedback

**Usage:**
```bash
# Reinfer all files in reinfer/
python scripts/reinfer_summaries.py

# Reinfer specific article
python scripts/reinfer_summaries.py --article-id PMID001

# Max attempts
python scripts/reinfer_summaries.py --max-attempts 3
```

**Logic:**
```python
for file in reinfer/:
    if attempt < max_attempts:
        # Re-summarize with feedback from evaluation
        new_summary = summarizer.summarize(article, feedback=evaluation.feedback)
        # Re-evaluate
        new_evaluation = evaluator.evaluate(new_summary)
        if new_evaluation.passed:
            move_to_approved()
        else:
            increment_attempt()
    else:
        # Failed after max attempts
        move_to_rejected()
```

---

## File Structure Changes

### Before (v1.0)
```
data/analysis/
├── summarized/     # All GenAI outputs
├── evaluated/      # (empty - not used)
├── approved/       # (empty - not used)
├── reinfer/        # (empty - not used)
└── rejected/       # (empty - not used)
```

### After (v1.1)
```
data/analysis/
├── raw/            # NEW: Initial GenAI outputs (Stage 2)
├── evaluated/      # Evaluation results attached
├── approved/       # Passed quality gate (≥80%)
├── reinfer/        # Failed, waiting for retry (<80%)
├── rejected/       # Failed after 3 attempts (manual review)
└── summarized/     # LEGACY: Keep for backward compatibility
```

---

## Migration Strategy

### Phase 1: Add New Components (Non-Breaking)
1. ✅ Add `raw/` directory support to `file_writer.py`
2. ✅ Add `EvaluationResult` schema to `schemas.py`
3. ✅ Add evaluation prompts to `prompts.py`
4. ✅ Create `evaluator.py` module
5. ✅ Create `evaluate_summaries.py` CLI script
6. ✅ Create `reinfer_summaries.py` CLI script

### Phase 2: Update Existing Pipeline (Optional)
7. Add `--output-stage raw` flag to `run_summarization.py`
8. Default to `raw/` for new runs
9. Keep `summarized/` for legacy compatibility

### Phase 3: Move Existing Files (Optional)
10. Move existing `summarized/*.json` to `raw/` if needed
11. Run evaluation pipeline on all existing files

---

## Backward Compatibility

### Keep Working:
- Existing `summarized/` directory and files
- Existing CLI commands
- Existing database schema

### New Features:
- New `raw/` output directory
- Evaluation pipeline (optional)
- Re-inference pipeline (optional)

### Migration Path:
- Users can continue using `summarized/` (no breaking changes)
- New users start with 5-stage architecture
- Gradual migration of existing files

---

## Testing Plan

### Unit Tests
- `test_evaluator.py` - Evaluation logic
- `test_file_writer.py` - Raw directory operations
- `test_schemas.py` - New evaluation schemas

### Integration Tests
- End-to-end: raw → evaluate → approved
- End-to-end: raw → evaluate → reinfer → re-evaluate → approved
- End-to-end: raw → evaluate → reinfer (3x) → rejected

### Manual Testing
1. Run `run_summarization.py --output-stage raw --limit 10`
2. Check `data/analysis/raw/` for files
3. Run `evaluate_summaries.py`
4. Check routing: `approved/` vs `reinfer/`
5. Run `reinfer_summaries.py`
6. Verify re-evaluation and routing

---

## Success Metrics (from ROADMAP)

### v1.1 Targets
- ✅ **Evaluation:** 95%+ of summaries pass 80% threshold
- ✅ **Reinfer:** <5% of articles need 3+ attempts
- ✅ **Quality:** User-validated accuracy >90%

---

## Timeline

**Week 1 (Aug 1-7):** Phase 1 - Add new components  
**Week 2 (Aug 8-14):** Phase 2 - Update existing pipeline  
**Week 3 (Aug 15-21):** Phase 3 - Testing and documentation  
**Week 4 (Aug 22-31):** Phase 4 - Migration and validation

**Target Completion:** End of August 2026

---

## Next Steps

1. Review and approve migration plan
2. Start Phase 1: Add `raw/` directory support
3. Implement `evaluator.py` module
4. Create evaluation CLI scripts
5. Test end-to-end workflow
6. Update documentation
7. Deploy to production
