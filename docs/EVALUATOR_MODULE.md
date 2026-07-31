# Evaluator Module Documentation

**Version:** v1.0  
**Date:** 2026-07-31  
**Status:** Completed ✅

---

## Overview

The `evaluator.py` module provides comprehensive quality assessment for GenAI-generated article summaries. It evaluates summaries across multiple dimensions and provides actionable feedback for improvement.

---

## Architecture

```
data/analysis/raw/*.json
        ↓
    Evaluator
        ↓
   ┌─────────────────────┐
   │  Quality Scoring    │ → 0-100% (weighted)
   │  - Factual (40%)    │
   │  - Complete (30%)   │
   │  - Clarity (20%)    │
   │  - People-1st (10%) │
   └─────────────────────┘
        ↓
   ┌─────────────────────┐
   │ Hallucination Check │ → Unsupported claims
   └─────────────────────┘
        ↓
   ┌─────────────────────┐
   │ People-First Check  │ → Language violations
   └─────────────────────┘
        ↓
   ┌─────────────────────┐
   │ Entity Consistency  │ → Extraction issues
   └─────────────────────┘
        ↓
   ┌─────────────────────┐
   │ Claim Evaluation    │ → Fact-check each sentence
   └─────────────────────┘
        ↓
   ┌─────────────────────┐
   │ Generate Feedback   │ → Actionable improvements
   └─────────────────────┘
        ↓
    >= 80% → approved/
    < 80%  → reinfer/
```

---

## Components

### 1. **SummaryEvaluator Class**

Located in: `backend/app/genai/evaluator.py`

#### Initialization

```python
from backend.app.genai.evaluator import SummaryEvaluator

evaluator = SummaryEvaluator(
    model_name="llama-3.3-70b-versatile",
    evaluation_version="v1.0",
    quality_threshold=80.0  # 0-100
)
```

#### Main Method: `evaluate()`

```python
result = evaluator.evaluate(raw_analysis)
```

**Input:** Dictionary loaded from `data/analysis/raw/*.json`

**Output:**
```python
{
    "evaluation": {
        "article_id": "PMID001",
        "quality_score": {
            "factual_accuracy": 85.0,
            "completeness": 90.0,
            "clarity": 95.0,
            "people_first_language": 100.0,
            "overall_score": 89.5
        },
        "hallucination_detected": False,
        "hallucination_examples": [],
        "people_first_violations": [],
        "entity_consistency": True,
        "entity_issues": [],
        "claim_evaluations": [
            {
                "claim": "Electronic cigarettes show mixed cardiovascular effects.",
                "label": "Supported",
                "explanation": "Directly stated in abstract."
            }
        ],
        "feedback": "Summary meets quality standards. No issues found.",
        "passed": True,
        "evaluated_at": "2026-07-31T10:30:00"
    },
    "metadata": {
        "evaluator_model": "llama-3.3-70b-versatile",
        "evaluation_version": "v1.0",
        "processing_time_ms": 1952,
        "tokens_used": 0,
        "cost_usd": 0.0
    }
}
```

---

## Evaluation Dimensions

### 1. Quality Scoring (0-100%)

**Weights:**
- Factual Accuracy: 40%
- Completeness: 30%
- Clarity: 20%
- People-First Language: 10%

**Formula:**
```
Overall = (Factual × 0.4) + (Completeness × 0.3) + (Clarity × 0.2) + (People-First × 0.1)
```

**Scoring Guidelines:**

| Score | Factual Accuracy | Completeness | Clarity | People-First |
|-------|------------------|--------------|---------|--------------|
| 90-100 | Perfect accuracy | All key points | Very clear | No violations |
| 70-89 | Minor issues | Most points covered | Clear | 1-2 violations |
| 50-69 | Some errors | Missing key points | Somewhat unclear | 3-4 violations |
| 0-49 | Major errors | Incomplete | Unclear | 5+ violations |

---

### 2. Hallucination Detection

**Purpose:** Identify claims not supported by the abstract

**Classification:**
- **Supported:** Directly stated or clearly implied
- **Not Mentioned:** Adds new information
- **Contradicted:** States the opposite

**Output:**
```python
{
    "hallucination_detected": True,
    "hallucination_examples": [
        "This study was funded by PMI",  # Not in abstract
        "The device was IQOS"             # Not mentioned
    ]
}
```

---

### 3. People-First Language Check

**Rules:**

| ❌ Incorrect | ✅ Correct |
|-------------|-----------|
| smokers | people who smoke |
| asthmatics | individuals with asthma |
| vapers | people who vape |
| diabetics | individuals with diabetes |
| asthmatic smokers | participants who smoke and have asthma |

**Scoring:**
- 100 = No violations
- Deduct 20 points per violation
- Minimum score: 0

**Output:**
```python
{
    "people_first_violations": [
        "Smokers of electronic cigarettes"  # Should be "people who smoke"
    ],
    "score": 80  # 1 violation = -20 points
}
```

---

### 4. Entity Consistency Check

**Purpose:** Verify extracted entities match article content

**Checks:**
- Are extracted entities actually present?
- Are major topics missed?

**Output:**
```python
{
    "entity_consistency": False,
    "entity_issues": [
        "Entity 'IQOS' not mentioned in abstract",
        "Major topic 'cardiovascular disease' was missed"
    ]
}
```

---

### 5. Claim-by-Claim Evaluation

**Process:**
1. Break summary into sentences
2. Evaluate each against abstract
3. Label: Supported / Not Mentioned / Contradicted

**Output:**
```python
[
    {
        "claim": "Electronic cigarettes have mixed cardiovascular effects.",
        "label": "Supported",
        "explanation": "Directly stated in line 2 of abstract."
    },
    {
        "claim": "The study included 1000 participants.",
        "label": "Not mentioned",
        "explanation": "Sample size not provided in abstract."
    }
]
```

---

## Evaluation Prompts

### Added to `prompts.py`:

1. **`quality_scoring_prompt`**
   - Evaluates across 4 dimensions
   - Returns weighted overall score

2. **`hallucination_detection_prompt`**
   - Identifies unsupported claims
   - Strict verification required

3. **`people_first_check_prompt`**
   - Scans for language violations
   - Provides corrections

4. **`entity_consistency_check_prompt`**
   - Validates entity extraction
   - Identifies missed topics

---

## Schemas Added

### In `schemas.py`:

```python
class QualityScore(BaseModel):
    """Quality scoring breakdown (0-100 scale)"""
    factual_accuracy: float
    completeness: float
    clarity: float
    people_first_language: float
    overall_score: float

class EvaluationResult(BaseModel):
    """Complete evaluation result for a summary"""
    article_id: str
    quality_score: QualityScore
    hallucination_detected: bool
    hallucination_examples: List[str]
    people_first_violations: List[str]
    entity_consistency: bool
    entity_issues: List[str]
    claim_evaluations: List[ClaimEvaluation]
    feedback: str
    passed: bool
    evaluated_at: str

class EvaluationMetadata(BaseModel):
    """Metadata for evaluation process"""
    evaluator_model: str
    evaluation_version: str
    processing_time_ms: int
    tokens_used: int
    cost_usd: float
```

---

## Usage Examples

### Basic Evaluation

```python
from backend.app.genai.evaluator import SummaryEvaluator
from backend.app.genai.file_writer import AnalysisFileWriter

# Initialize
evaluator = SummaryEvaluator()
file_writer = AnalysisFileWriter()

# Load raw analysis
raw_analysis = file_writer.load_summarized_analysis("PMID001")

# Evaluate
result = evaluator.evaluate(raw_analysis)

# Check result
if result["evaluation"]["passed"]:
    print(f"✓ Passed: {result['evaluation']['quality_score']['overall_score']:.1f}/100")
else:
    print(f"✗ Failed: {result['evaluation']['quality_score']['overall_score']:.1f}/100")
    print(f"Feedback: {result['evaluation']['feedback']}")
```

### Batch Evaluation

```python
from pathlib import Path
import json

evaluator = SummaryEvaluator()
raw_dir = Path("data/analysis/raw")

results = []
for file_path in raw_dir.glob("*.json"):
    with open(file_path) as f:
        raw_analysis = json.load(f)
    
    result = evaluator.evaluate(raw_analysis)
    results.append(result)

# Statistics
passed = sum(1 for r in results if r["evaluation"]["passed"])
failed = len(results) - passed
avg_score = sum(r["evaluation"]["quality_score"]["overall_score"] for r in results) / len(results)

print(f"Passed: {passed}/{len(results)} ({passed/len(results)*100:.1f}%)")
print(f"Average Score: {avg_score:.1f}/100")
```

---

## Feedback Generation

The evaluator generates actionable feedback based on evaluation results:

### Example Feedback (Failed)

```
Overall quality score: 68.0/100 (threshold: 80.0)
- Completeness is low (60.0/100). Include key findings and conclusions from the abstract.
- People-first language score is low (0.0/100). Use 'people who smoke' instead of 'smokers', etc.
- People-first language violations: 1 found.
  • Smokers of electronic cigarettes
```

### Example Feedback (Passed)

```
Summary meets quality standards. No issues found.
```

---

## Performance

**Processing Time:**
- Average: ~2-3 seconds per summary
- Model: llama-3.3-70b-versatile

**Evaluation Steps:**
1. Quality Scoring: ~500ms
2. Hallucination Detection: ~400ms
3. People-First Check: ~300ms
4. Entity Consistency: ~300ms
5. Claim Evaluation: ~500ms

**Total:** ~2000ms (2 seconds)

---

## Error Handling

### Empty Abstract/Summary

```python
{
    "evaluation": {
        "quality_score": {"overall_score": 0.0, ...},
        "passed": False,
        "feedback": "Evaluation skipped: Empty abstract or summary"
    }
}
```

### Evaluation Failure

```python
{
    "evaluation": {
        "quality_score": {"overall_score": 0.0, ...},
        "passed": False,
        "feedback": "Evaluation failed: <error message>"
    },
    "error": "<detailed error>"
}
```

---

## Testing

### Quick Test

```bash
python test_evaluator_quick.py
```

**Expected Output:**
```
Testing SummaryEvaluator...
================================================================================
Quality Score: 68.0/100
  - Factual Accuracy: 80.0/100
  - Completeness: 60.0/100
  - Clarity: 90.0/100
  - People-First: 0.0/100

Passed Threshold (>=80%): False
Hallucinations Detected: False
People-First Violations: 1
Processing Time: 1952ms
================================================================================
```

---

## Next Steps

1. **Create CLI Tool** (`scripts/evaluate_summaries.py`)
   - Batch evaluation from `raw/` directory
   - Route files based on score
   - Progress tracking

2. **File Routing Logic** (Update `file_writer.py`)
   - `move_to_approved()` for passed evaluations
   - `move_to_reinfer()` for failed evaluations
   - Save evaluation results alongside summaries

3. **Re-inference Pipeline** (`scripts/reinfer_summaries.py`)
   - Re-summarize with feedback
   - Max 3 attempts
   - Move to `rejected/` after failures

---

## Success Metrics (ROADMAP v1.1)

### Targets
- ✅ **Evaluation:** 95%+ of summaries pass 80% threshold
- ✅ **Reinfer:** <5% of articles need 3+ attempts
- ✅ **Quality:** User-validated accuracy >90%

### Current Status
- ✅ Evaluator module: Complete
- ⏳ CLI tool: Pending
- ⏳ File routing: Pending
- ⏳ Re-inference: Pending

---

## References

- [ROADMAP.md](../ROADMAP.md) - v1.1 evaluation pipeline plan
- [MIGRATION_TO_5_STAGE.md](MIGRATION_TO_5_STAGE.md) - Architecture migration guide
- [schemas.py](../backend/app/genai/schemas.py) - Evaluation schemas
- [prompts.py](../backend/app/genai/prompts.py) - Evaluation prompts
- [evaluator.py](../backend/app/genai/evaluator.py) - Evaluator implementation
