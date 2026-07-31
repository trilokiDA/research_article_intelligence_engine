"""
CLI tool for evaluating GenAI summaries.

Usage:
    python scripts/evaluate_summaries.py
    python scripts/evaluate_summaries.py --source raw --limit 10
    python scripts/evaluate_summaries.py --threshold 85 --dry-run
"""

import sys
import os
import argparse
from pathlib import Path
from typing import List, Optional
import time

# Don't do any imports or directory changes here - save it for runtime
SCRIPT_DIR = Path(__file__).parent.resolve()
PROJECT_ROOT = SCRIPT_DIR.parent
GENAI_DIR = PROJECT_ROOT / "backend" / "app" / "genai"


def _lazy_imports():
    """Lazy import - only called at runtime, not during module load."""
    _cwd = os.getcwd()
    try:
        os.chdir(str(GENAI_DIR))
        sys.path.insert(0, str(GENAI_DIR))

        from evaluator import SummaryEvaluator
        from file_writer import AnalysisFileWriter

        return SummaryEvaluator, AnalysisFileWriter
    finally:
        os.chdir(_cwd)


def evaluate_summaries(
    source_dir: str = "raw",
    threshold: float = 80.0,
    limit: Optional[int] = None,
    article_ids: Optional[List[str]] = None,
    dry_run: bool = False,
    model_name: str = "llama-3.3-70b-versatile"
):
    """Evaluate summaries and route based on quality score."""
    # Lazy import at runtime
    SummaryEvaluator, AnalysisFileWriter = _lazy_imports()

    # Try to import tqdm
    try:
        from tqdm import tqdm
    except ImportError:
        class tqdm:
            def __init__(self, *args, **kwargs):
                self.total = kwargs.get('total', 0)
            def update(self, n=1):
                pass
            def __enter__(self):
                return self
            def __exit__(self, *args):
                pass

    print("\n" + "="*80)
    print("EVALUATION PIPELINE")
    print("="*80)

    # Initialize
    print("\n[1/5] Initializing...")
    evaluator = SummaryEvaluator(
        model_name=model_name,
        quality_threshold=threshold
    )
    file_writer = AnalysisFileWriter()

    print(f"      Model: {model_name}")
    print(f"      Quality Threshold: {threshold}%")
    print(f"      Source Directory: data/analysis/{source_dir}/")
    print(f"      Dry Run: {dry_run}")

    # Get files to process
    print(f"\n[2/5] Discovering files...")

    if article_ids:
        files_to_process = article_ids
        print(f"      Processing {len(files_to_process)} specified articles")
    else:
        if source_dir == "raw":
            files_to_process = file_writer.list_raw_analyses()
        elif source_dir == "summarized":
            files_to_process = file_writer.list_summarized_analyses()
        else:
            print(f"[ERROR] Invalid source directory: {source_dir}")
            return

        if limit:
            files_to_process = files_to_process[:limit]

        print(f"      Found {len(files_to_process)} files to evaluate")

    if not files_to_process:
        print("\n[INFO] No files to evaluate. Exiting.")
        return

    # Statistics
    stats = {
        "total": len(files_to_process),
        "evaluated": 0,
        "passed": 0,
        "failed": 0,
        "errors": 0,
        "skipped": 0,
        "total_score": 0.0,
        "total_time_ms": 0
    }

    # Process files
    print(f"\n[3/5] Evaluating summaries...")
    results = []

    with tqdm(total=len(files_to_process), desc="Evaluating", unit="file") as pbar:
        for article_id in files_to_process:
            try:
                # Load analysis
                if source_dir == "raw":
                    raw_analysis = file_writer.load_raw_analysis(article_id)
                else:
                    raw_analysis = file_writer.load_summarized_analysis(article_id)

                if not raw_analysis:
                    print(f"\n[WARNING] Could not load {article_id}, skipping")
                    stats["skipped"] += 1
                    pbar.update(1)
                    continue

                # Evaluate
                eval_start = time.time()
                evaluation = evaluator.evaluate(raw_analysis)
                eval_time_ms = int((time.time() - eval_start) * 1000)

                stats["evaluated"] += 1
                stats["total_time_ms"] += eval_time_ms

                eval_result = evaluation["evaluation"]
                eval_metadata = evaluation["metadata"]

                quality_score = eval_result["quality_score"]["overall_score"]
                passed = eval_result["passed"]

                stats["total_score"] += quality_score

                if passed:
                    stats["passed"] += 1
                else:
                    stats["failed"] += 1

                results.append({
                    "article_id": article_id,
                    "score": quality_score,
                    "passed": passed,
                    "feedback": eval_result["feedback"]
                })

                # Save and route (unless dry run)
                if not dry_run:
                    file_writer.save_evaluated_analysis(
                        article_id=article_id,
                        raw_analysis=raw_analysis,
                        evaluation_result=eval_result,
                        evaluation_metadata=eval_metadata
                    )

                    if passed:
                        file_writer.move_to_approved(article_id)
                    else:
                        file_writer.move_to_reinfer(
                            article_id=article_id,
                            feedback=eval_result["feedback"],
                            attempt=raw_analysis.get("attempt", 1)
                        )

            except Exception as e:
                print(f"\n[ERROR] Failed to evaluate {article_id}: {e}")
                stats["errors"] += 1

            pbar.update(1)

    # Display results
    print(f"\n[4/5] Evaluation complete!")
    print(f"      Evaluated: {stats['evaluated']}")
    print(f"      Passed (>={threshold}%): {stats['passed']}")
    print(f"      Failed (<{threshold}%): {stats['failed']}")
    print(f"      Errors: {stats['errors']}")
    print(f"      Skipped: {stats['skipped']}")

    if stats["evaluated"] > 0:
        avg_score = stats["total_score"] / stats["evaluated"]
        avg_time_ms = stats["total_time_ms"] / stats["evaluated"]
        pass_rate = (stats["passed"] / stats["evaluated"]) * 100

        print(f"\n      Average Score: {avg_score:.1f}/100")
        print(f"      Pass Rate: {pass_rate:.1f}%")
        print(f"      Avg Processing Time: {avg_time_ms:.0f}ms")

    # Show sample results
    print(f"\n[5/5] Sample Results:")
    print(f"{'-'*80}")

    failed_results = [r for r in results if not r["passed"]]
    if failed_results:
        print("\nFailed Evaluations (samples):")
        for i, result in enumerate(failed_results[:5]):
            print(f"\n  {i+1}. {result['article_id']}")
            print(f"     Score: {result['score']:.1f}/100")
            feedback_lines = result['feedback'].split('\n')
            print(f"     Feedback: {feedback_lines[0][:80]}...")

    passed_results = [r for r in results if r["passed"]]
    if passed_results:
        print(f"\nPassed Evaluations: {len(passed_results)} total")
        for i, result in enumerate(passed_results[:3]):
            print(f"  - {result['article_id']}: {result['score']:.1f}/100")

    # Final summary
    print(f"\n{'='*80}")
    print("SUMMARY")
    print(f"{'='*80}")

    if not dry_run:
        print(f"Files routed:")
        print(f"  - Approved (>={threshold}%): {stats['passed']} files -> data/analysis/approved/")
        print(f"  - Re-infer (<{threshold}%): {stats['failed']} files -> data/analysis/reinfer/")
    else:
        print("[DRY RUN] No files were moved or saved.")

    print(f"\nNext steps:")
    if stats["failed"] > 0:
        print(f"  - Run re-inference on {stats['failed']} failed summaries:")
        print(f"    python scripts/reinfer_summaries.py")
    if stats["passed"] > 0:
        print(f"  - Load {stats['passed']} approved summaries to database (future)")

    print(f"{'='*80}\n")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Evaluate GenAI summaries and route based on quality score"
    )

    parser.add_argument("--source", type=str, default="raw", choices=["raw", "summarized"])
    parser.add_argument("--threshold", type=float, default=80.0)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--article-ids", type=str, default=None)
    parser.add_argument("--model", type=str, default="llama-3.3-70b-versatile")
    parser.add_argument("--dry-run", action="store_true")

    args = parser.parse_args()

    article_ids = None
    if args.article_ids:
        article_ids = [aid.strip() for aid in args.article_ids.split(",")]

    try:
        evaluate_summaries(
            source_dir=args.source,
            threshold=args.threshold,
            limit=args.limit,
            article_ids=article_ids,
            dry_run=args.dry_run,
            model_name=args.model
        )
    except KeyboardInterrupt:
        print("\n\n[INFO] Evaluation interrupted by user. Exiting gracefully...")
        sys.exit(0)
    except Exception as e:
        print(f"\n[ERROR] Evaluation failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
