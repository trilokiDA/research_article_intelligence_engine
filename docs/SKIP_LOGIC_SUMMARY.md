# Skip Logic Implementation Summary

## Changes Made

### 1. Added New Methods to `AnalysisFileWriter`

**File**: `backend/app/genai/file_writer.py`

```python
def list_approved_analyses(self) -> List[str]:
    """List all article IDs in approved directory."""
    return [f.stem for f in self.approved_dir.glob("*.json")]

def list_rejected_analyses(self) -> List[str]:
    """List all article IDs in rejected directory."""
    return [f.stem for f in self.rejected_dir.glob("*.json")]
```

### 2. Updated Evaluation Script

**File**: `scripts/evaluate_summaries_runner.py`

**Logic**: Skip articles already in `approved/` OR `reinfer/`

```python
if source_dir == "raw":
    all_raw_files = file_writer.list_raw_analyses()
    
    # Skip articles already evaluated (in approved or reinfer)
    already_approved = set(file_writer.list_approved_analyses())
    already_reinfer = set(file_writer.list_reinfer_analyses())
    already_evaluated = already_approved | already_reinfer
    
    files_to_process = [f for f in all_raw_files if f not in already_evaluated]
```

### 3. Updated Re-inference Script

**File**: `scripts/reinfer_summaries.py`

**Logic**: Skip articles already in `approved/` OR `rejected/`

```python
all_reinfer_files = file_writer.list_reinfer_analyses()

# Skip articles already finalized (in approved or rejected)
already_approved = set(file_writer.list_approved_analyses())
already_rejected = set(file_writer.list_rejected_analyses())
already_finalized = already_approved | already_rejected

files_to_process = [f for f in all_reinfer_files if f not in already_finalized]
```

## Verification Results

```
[1] Directory Counts:
  raw/        : 5 files
  summarized/ : 0 files (legacy)
  reinfer/    : 5 files
  approved/   : 2 files
  rejected/   : 1 files

[2] Evaluation Stage Skip Logic:
  Input: raw/ (5 files)
  Skip: approved/ OR reinfer/ (5 files)
  ✓ Will process: 3 files
    → PMID42448862, PMID42462344, PMID42469028

[3] Re-inference Stage Skip Logic:
  Input: reinfer/ (5 files)
  Skip: approved/ OR rejected/ (3 files)
  ✓ Will process: 2 files
    → PMID42294124, PMID42396759

[4] Consistency Checks:
  ✓ No overlap between approved/ and rejected/
  ℹ Articles in both approved/ and reinfer/: 2 (will be skipped)
  ℹ Articles in both rejected/ and reinfer/: 1 (will be skipped)
```

## Benefits

✅ **Prevents duplicate processing**
   - Evaluation won't re-evaluate already-processed articles
   - Re-inference won't re-process finalized articles

✅ **Saves API costs**
   - No wasted LLM calls on already-evaluated content
   - No redundant re-inference attempts

✅ **Clear progress tracking**
   - Shows exactly how many articles pending vs already processed
   - Transparent reporting of skip decisions

✅ **Maintains data consistency**
   - Articles progress through pipeline once
   - No conflicting states across directories

## Pipeline Flow

```
Stage 2: Summarization
  ↓
data/analysis/raw/
  ↓
Stage 3: Evaluation ────→ Skip if in: approved/ OR reinfer/
  ↓
  ├─ PASS (≥80%) → data/analysis/approved/
  └─ FAIL (<80%) → data/analysis/reinfer/
                    ↓
Stage 4: Re-inference ──→ Skip if in: approved/ OR rejected/
                    ↓
                    ├─ PASS → data/analysis/approved/
                    ├─ FAIL (attempt < max) → data/analysis/reinfer/
                    └─ FAIL (attempt ≥ max) → data/analysis/rejected/
```

## File Writer API Summary

| Method | Directory | Stage | Purpose |
|--------|-----------|-------|---------|
| `list_raw_analyses()` | `raw/` | 2 | After summarization |
| `list_reinfer_analyses()` | `reinfer/` | 4 | Need re-inference |
| `list_approved_analyses()` | `approved/` | 3/4 | Passed quality gate |
| `list_rejected_analyses()` | `rejected/` | 4 | Failed after max attempts |
| `list_summarized_analyses()` | `summarized/` | - | Legacy (backward compatibility) |

## Testing

Run the verification script:

```bash
python -c "
import sys
from pathlib import Path
sys.path.insert(0, str(Path('backend/app').resolve()))
from genai.file_writer import AnalysisFileWriter

writer = AnalysisFileWriter()

raw = set(writer.list_raw_analyses())
reinfer = set(writer.list_reinfer_analyses())
approved = set(writer.list_approved_analyses())
rejected = set(writer.list_rejected_analyses())

# Eval skip logic
already_evaluated = approved | reinfer
pending_eval = raw - already_evaluated

# Reinfer skip logic
already_finalized = approved | rejected
pending_reinfer = reinfer - already_finalized

print(f'Pending evaluation: {len(pending_eval)} files')
print(f'Pending re-inference: {len(pending_reinfer)} files')
"
```

## Related Documentation

- `docs/EVAL_SKIP_LOGIC.md` - Detailed explanation of skip logic
- `docs/GENAI_PIPELINE.md` - Complete pipeline documentation
- `docs/DATA_SOURCES.md` - Data flow and directory structure
