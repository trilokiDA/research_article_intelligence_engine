# Bug Fix: Reinfer Validation and Attempt Counter

## Bug Description

**Issue**: Articles in `reinfer/` folder that fail multiple times never get moved to `rejected/` even after exceeding max attempts (3).

**Root Cause**: Files were improperly placed in `reinfer/` without:
1. Proper evaluation data
2. `reinfer_feedback` field
3. Correct `stage` field
4. Proper `attempt` counter

**Example**: `PMID42396759` was in `reinfer/` with:
```json
{
  "attempt": 1,          // ❌ Never incremented
  "stage": "raw",         // ❌ Should be "reinfer"
  "reinfer_feedback": missing,  // ❌ No feedback
  "evaluation": missing   // ❌ No evaluation data
}
```

## How Files Should Flow

### Correct Flow:
```
1. raw/ 
   ↓
2. evaluate_summaries.py
   ↓ (saves evaluation + feedback)
3. evaluated/
   ↓ (if failed)
4. move_to_reinfer() → reinfer/
   ↓ (with attempt=1, reinfer_feedback, evaluation)
5. reinfer_summaries.py
   ↓ (if still fails)
6. move_to_reinfer() → reinfer/
   ↓ (with attempt=2, updated feedback)
7. reinfer_summaries.py
   ↓ (if still fails)
8. move_to_reinfer() → reinfer/
   ↓ (with attempt=3)
9. reinfer_summaries.py
   ↓ (attempt >= max_attempts)
10. rejected/
```

### What Was Happening (Bug):
```
1. raw/
   ↓ (file manually moved or improperly copied)
2. reinfer/ ❌ (missing evaluation data)
   ↓
3. reinfer_summaries.py
   ↓ (attempt=1, never increments)
4. STUCK IN REINFER FOREVER ❌
```

## Fix Implemented

### 1. Added Validation in `scripts/reinfer_summaries.py`

**Location**: Lines 151-167

```python
# Validate file has evaluation data and feedback
if "evaluation" not in reinfer_analysis or not reinfer_analysis.get("reinfer_feedback"):
    print(f"\n[WARNING] {article_id_item} missing evaluation/feedback - needs proper evaluation first")
    print(f"          Moving back to raw/ for re-evaluation")
    if not dry_run:
        # Move back to raw for proper evaluation
        reinfer_file = file_writer.reinfer_dir / f"{article_id_item}.json"
        raw_file = file_writer.raw_dir / f"{article_id_item}.json"
        if reinfer_file.exists() and not raw_file.exists():
            import shutil
            shutil.move(str(reinfer_file), str(raw_file))
    stats["skipped"] += 1
    pbar.update(1)
    continue
```

### 2. What This Fix Does

✅ **Validates file structure** - Checks for required fields before processing  
✅ **Auto-recovery** - Moves invalid files back to `raw/` for proper evaluation  
✅ **Clear warnings** - Tells user why file was skipped  
✅ **Prevents infinite loops** - Files can't stay in reinfer without proper data

## Testing the Fix

### Before Fix:
```bash
$ python scripts/reinfer_summaries.py --article-id PMID42396759
# Would fail silently or error out
# File stays in reinfer/ with attempt=1 forever
```

### After Fix:
```bash
$ python scripts/reinfer_summaries.py --article-id PMID42396759
# Output:
[WARNING] PMID42396759 missing evaluation/feedback - needs proper evaluation first
          Moving back to raw/ for re-evaluation

# File moved: reinfer/PMID42396759.json → raw/PMID42396759.json
```

### Verify Move:
```bash
$ python -c "from pathlib import Path; print('raw:', Path('data/analysis/raw/PMID42396759.json').exists())"
raw: True  ✓

$ python -c "from pathlib import Path; print('reinfer:', Path('data/analysis/reinfer/PMID42396759.json').exists())"
reinfer: False  ✓
```

## Proper Workflow Now

### Step 1: Evaluate
```bash
python scripts/evaluate_summaries.py --source raw --article-ids PMID42396759
```

This will:
- Load from `raw/`
- Run evaluation
- Save evaluation data + feedback
- Move to `approved/` (if passed) or `reinfer/` (if failed, with attempt=1)

### Step 2: Re-infer (if needed)
```bash
python scripts/reinfer_summaries.py --article-id PMID42396759
```

This will:
- Load from `reinfer/` with evaluation data
- Re-run summarization with feedback
- Re-evaluate
- Move to `approved/` (if passed) or back to `reinfer/` (with attempt=2)

### Step 3: Continue until rejected or approved
- Each failed re-inference increments `attempt`
- When `attempt >= 3`, moves to `rejected/`

## Prevention

To prevent this bug in the future:

### ✅ Always use the proper scripts:
1. `evaluate_summaries.py` for initial evaluation
2. `reinfer_summaries.py` for re-inference

### ❌ Never:
- Manually copy files to `reinfer/`
- Move files without using `file_writer.move_to_reinfer()`
- Skip the evaluation step

## Files Modified

1. **`scripts/reinfer_summaries.py`**
   - Added validation for evaluation data and feedback
   - Auto-recovery: moves invalid files back to raw/
   - Lines 151-167

## Related Files

- `scripts/evaluate_summaries.py` - Proper evaluation with feedback
- `backend/app/genai/file_writer.py` - File movement methods
- `docs/SKIP_LOGIC_SUMMARY.md` - Overall pipeline skip logic
- `docs/EVAL_SKIP_LOGIC.md` - Detailed evaluation flow
