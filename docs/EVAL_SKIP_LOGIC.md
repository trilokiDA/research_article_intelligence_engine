# Evaluation & Re-inference Skip Logic

## Overview
Both the evaluation and re-inference stages now intelligently skip articles that have already been processed to avoid duplicate work and wasted API calls.

## Problem Statement

### Evaluation Stage
Previously, the evaluation script (`evaluate_summaries_runner.py`) would process **all** articles in the `raw/` folder, even if they had already been evaluated and routed to:
- `approved/` - Articles that passed quality threshold
- `reinfer/` - Articles that failed and need re-inference
- `loaded/` - Articles successfully loaded to database (archived)
- `rejected/` - Articles failed after max retries

### Re-inference Stage
Similarly, the re-inference script (`reinfer_summaries.py`) would process **all** articles in the `reinfer/` folder, even if they had already been finalized:
- `approved/` - Articles that passed after re-inference
- `rejected/` - Articles that failed after max attempts

This caused:
- ❌ Duplicate evaluations/re-inferences
- ❌ Wasted API calls and costs
- ❌ Potential inconsistent state
- ❌ Processing already-finalized articles

## Solution

### 1. Added List Methods for All Directories
**File**: `backend/app/genai/file_writer.py`

```python
def list_approved_analyses(self) -> List[str]:
    """List all article IDs in approved directory."""
    return [f.stem for f in self.approved_dir.glob("*.json")]

def list_rejected_analyses(self) -> List[str]:
    """List all article IDs in rejected directory."""
    return [f.stem for f in self.rejected_dir.glob("*.json")]

def list_loaded_analyses(self) -> List[str]:
    """List all article IDs in loaded directory (archives after database load)."""
    loaded_dir = self.base_dir / "loaded"
    if not loaded_dir.exists():
        return []
    return [f.stem for f in loaded_dir.glob("*.json")]
```

### 2. Updated Evaluation Discovery Logic
**File**: `scripts/evaluate_summaries_runner.py`

The script now:
1. Lists all raw analyses
2. Gets already-approved articles
3. Gets already-reinfer articles
4. Gets already-loaded articles (archived after database load)
5. Gets already-rejected articles (failed after max retries)
6. **Filters out** articles that exist in any of these folders
7. Only processes remaining (unevaluated) articles

```python
if source_dir == "raw":
    all_raw_files = file_writer.list_raw_analyses()
    
    # Skip articles already evaluated (in approved, reinfer, loaded, or rejected)
    already_approved = set(file_writer.list_approved_analyses())
    already_reinfer = set(file_writer.list_reinfer_analyses())
    already_loaded = set(file_writer.list_loaded_analyses())
    already_rejected = set(file_writer.list_rejected_analyses())
    already_evaluated = already_approved | already_reinfer | already_loaded | already_rejected
    
    files_to_process = [f for f in all_raw_files if f not in already_evaluated]
```

### 3. Updated Re-inference Discovery Logic
**File**: `scripts/reinfer_summaries.py`

The script now:
1. Lists all reinfer analyses
2. Gets already-approved articles
3. Gets already-rejected articles
4. **Filters out** articles that exist in either approved or rejected folders
5. Only processes remaining (pending re-inference) articles

```python
all_reinfer_files = file_writer.list_reinfer_analyses()

# Skip articles already finalized (in approved or rejected)
already_approved = set(file_writer.list_approved_analyses())
already_rejected = set(file_writer.list_rejected_analyses())
already_finalized = already_approved | already_rejected

files_to_process = [f for f in all_reinfer_files if f not in already_finalized]
```

## Benefits

✅ **Avoids duplicate evaluations** - Each article evaluated only once  
✅ **Saves API costs** - No unnecessary LLM calls  
✅ **Clear visibility** - Shows how many articles already evaluated vs pending  
✅ **Consistent state** - Articles appear in only one stage folder at a time

## Output Examples

### Evaluation Stage Output
```
[2/5] Discovering files...
      Found 126 raw analyses
      Already evaluated: 119
        - Approved: 60
        - Reinfer: 15
        - Loaded: 40
        - Rejected: 4
      Pending evaluation: 7
      Will evaluate 7 files
```

### Re-inference Stage Output
```
[2/6] Discovering files in reinfer/...
      Found 50 files in reinfer/
      Already finalized: 30 (approved: 25, rejected: 5)
      Pending re-inference: 20
```

## File Writer Methods Summary

The `AnalysisFileWriter` class now provides these listing methods:

| Method | Directory | Purpose |
|--------|-----------|---------|
| `list_raw_analyses()` | `raw/` | Articles after summarization |
| `list_summarized_analyses()` | `summarized/` | Legacy directory |
| `list_reinfer_analyses()` | `reinfer/` | Articles needing re-inference |
| `list_approved_analyses()` | `approved/` | Articles passed quality gate |
| `list_rejected_analyses()` | `rejected/` | Articles failed after max attempts |
| `list_loaded_analyses()` | `loaded/` | Articles archived after database load |

## Pipeline Flow

```
raw/
  ↓
  ├─ evaluate_summaries_runner.py
  │  └─ Checks: NOT IN (approved/ OR reinfer/ OR loaded/ OR rejected/)
  │  └─ Skip Logic: Only process unevaluated articles
  │
  ├─ PASS (≥80%) → approved/ → (Stage 5) db_loader.py → loaded/
  └─ FAIL (<80%) → reinfer/
                    ↓
                    reinfer_summaries.py
                    └─ Checks: NOT IN (approved/ OR rejected/)
                    └─ Skip Logic: Only process pending articles
                    ↓
                    ├─ PASS → approved/ → (Stage 5) db_loader.py → loaded/
                    ├─ FAIL → reinfer/ (with attempt++)
                    └─ MAX_ATTEMPTS → rejected/
```

## Current State (Example from Data)

### Evaluation Stage
```
Raw analyses: 5 files
├─ Already evaluated: 2 files
│  ├─ Approved: 2 (PMID41418992, PMID41852138)
│  └─ Reinfer: 5 (includes overlaps)
└─ Pending evaluation: 3 files
   └─ PMID42448862, PMID42462344, PMID42469028
```

### Re-inference Stage
```
Reinfer analyses: 5 files
├─ Already finalized: 3 files
│  ├─ Approved: 2 (PMID41418992, PMID41852138)
│  └─ Rejected: 1 (PMID42387888)
└─ Pending re-inference: 2 files
   └─ PMID42294124, PMID42396759
```

## Related Files
- `backend/app/genai/file_writer.py` - Core file operations (added `list_approved_analyses()` and `list_rejected_analyses()`)
- `scripts/evaluate_summaries_runner.py` - Evaluation orchestration (added skip logic)
- `scripts/reinfer_summaries.py` - Re-inference with feedback (added skip logic)
