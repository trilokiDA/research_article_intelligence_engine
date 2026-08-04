"""
Quick test script for the evaluator module.
"""

import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from app.genai.evaluator import SummaryEvaluator

print("Testing SummaryEvaluator...")
print("=" * 80)

evaluator = SummaryEvaluator()

# Test with a sample analysis (with people-first violation)
sample_analysis = {
    "article_id": "TEST001",
    "source_data": {
        "title": "Impact of electronic cigarettes on health",
        "abstract": "Electronic cigarettes have been studied for their health impacts. Research shows mixed results on cardiovascular effects in people who use these devices.",
    },
    "analysis": {
        "summary": "Smokers of electronic cigarettes show mixed cardiovascular effects.",  # Violation: "Smokers"
        "entity": ["electronic cigarettes"],
        "subject": "E-cigarettes",
        "category": "Clinical Studies",
        "sentiment": "Neutral"
    }
}

print("\n[TEST] Evaluating sample analysis...")
print(f"Article ID: {sample_analysis['article_id']}")
print(f"Summary: {sample_analysis['analysis']['summary']}")
print(f"Abstract: {sample_analysis['source_data']['abstract'][:80]}...")

result = evaluator.evaluate(sample_analysis)

print("\n" + "=" * 80)
print("EVALUATION RESULTS")
print("=" * 80)
print(f"Quality Score: {result['evaluation']['quality_score']['overall_score']:.1f}/100")
print(f"  - Factual Accuracy: {result['evaluation']['quality_score']['factual_accuracy']:.1f}/100")
print(f"  - Completeness: {result['evaluation']['quality_score']['completeness']:.1f}/100")
print(f"  - Clarity: {result['evaluation']['quality_score']['clarity']:.1f}/100")
print(f"  - People-First: {result['evaluation']['quality_score']['people_first_language']:.1f}/100")
print(f"\nPassed Threshold (>=80%): {result['evaluation']['passed']}")
print(f"Hallucinations Detected: {result['evaluation']['hallucination_detected']}")
print(f"People-First Violations: {len(result['evaluation']['people_first_violations'])}")
print(f"Entity Consistency: {result['evaluation']['entity_consistency']}")
print(f"Claim Evaluations: {len(result['evaluation']['claim_evaluations'])}")
print(f"\nProcessing Time: {result['metadata']['processing_time_ms']}ms")
print(f"Model: {result['metadata']['evaluator_model']}")
print(f"Version: {result['metadata']['evaluation_version']}")

print(f"\n{'-'*80}")
print("FEEDBACK:")
print(f"{'-'*80}")
print(result['evaluation']['feedback'])

print("\n" + "=" * 80)
print("[OK] Test complete!")
print("=" * 80)
