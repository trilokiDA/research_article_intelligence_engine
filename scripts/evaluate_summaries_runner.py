"""
Runner script for evaluation pipeline.
This script changes to the genai directory to handle imports correctly.
"""

import sys
import os
import argparse
from pathlib import Path
from typing import List, Optional
import time
import json

# Setup paths for imports
PROJECT_ROOT = Path(__file__).parent.parent

# Add backend/app to path so we can import genai package
backend_app_dir = PROJECT_ROOT / "backend" / "app"
if str(backend_app_dir) not in sys.path:
    sys.path.insert(0, str(backend_app_dir))

# Import from genai package properly
from genai.evaluator import SummaryEvaluator
from genai.file_writer import AnalysisFileWriter

# Import tqdm
try:
    from tqdm import tqdm
except ImportError:
    # Fallback if tqdm not available
    class tqdm:
        def __init__(self, *args, **kwargs):
            self.total = kwargs.get('total', 0)
            self.n = 0
        def update(self, n=1):
            self.n += n
        def __enter__(self):
            return self
        def __exit__(self, *args):
            pass


def evaluate_summaries(
    source_dir: str = "raw",
    threshold: float = 80.0,
    limit: Optional[int] = None,
    article_ids: Optional[List[str]] = None,
    dry_run: bool = False,
    model_name: str = "llama-3.3-70b-versatile"
):
    """
    Evaluate summaries and route based on quality score.

    Args:
        source_dir: Source directory (raw, summarized)
        threshold: Quality threshold (0-100)
        limit: Maximum number of files to process
        article_ids: Specific article IDs to evaluate
        dry_run: If True, don't save/move files
        model_name: Groq model for evaluation
    """
    print("\n" + "="*80)
    print("EVALUATION PIPELINE")
    print("="*80)

    # Initialize
    print("\n[1/5] Initializing...")

    # Use absolute path for data directory (since we changed to genai dir)
    data_dir = PROJECT_ROOT / "data" / "analysis"

    evaluator = SummaryEvaluator(
        model_name=model_name,
        quality_threshold=threshold
    )
    file_writer = AnalysisFileWriter(base_dir=str(data_dir))

    print(f"      Model: {model_name}")
    print(f"      Quality Threshold: {threshold}%")
    print(f"      Source Directory: data/analysis/{source_dir}/")
    print(f"      Dry Run: {dry_run}")

    # Get files to process
    print(f"\n[2/5] Discovering files...")

    if article_ids:
        # Process specific article IDs
        files_to_process = article_ids
        print(f"      Processing {len(files_to_process)} specified articles")
    else:
        # Get all files from source directory
        if source_dir == "raw":
            all_raw_files = file_writer.list_raw_analyses()

            # Skip articles already evaluated (in approved, reinfer, loaded, or rejected)
            already_approved = set(file_writer.list_approved_analyses())
            already_reinfer = set(file_writer.list_reinfer_analyses())
            already_loaded = set(file_writer.list_loaded_analyses())
            already_rejected = set(file_writer.list_rejected_analyses())
            already_evaluated = already_approved | already_reinfer | already_loaded | already_rejected

            files_to_process = [f for f in all_raw_files if f not in already_evaluated]

            print(f"      Found {len(all_raw_files)} raw analyses")

            # Check if all raw files have been processed
            if len(files_to_process) == 0 and len(all_raw_files) > 0:
                print(f"      [OK] All {len(all_raw_files)} raw articles have been analyzed!")
                print(f"      Distribution:")
                print(f"        - Approved: {len(already_approved)} (ready for database load)")
                print(f"        - Reinfer: {len(already_reinfer)} (waiting for re-inference)")
                print(f"        - Loaded: {len(already_loaded)} (already in database)")
                print(f"        - Rejected: {len(already_rejected)} (failed after max retries)")
            else:
                print(f"      Already evaluated: {len(already_evaluated)}")
                print(f"        - Approved: {len(already_approved)}")
                print(f"        - Reinfer: {len(already_reinfer)}")
                print(f"        - Loaded: {len(already_loaded)}")
                print(f"        - Rejected: {len(already_rejected)}")
                print(f"      Pending evaluation: {len(files_to_process)}")
        elif source_dir == "summarized":
            files_to_process = file_writer.list_summarized_analyses()
            print(f"      Found {len(files_to_process)} summarized analyses")
        else:
            print(f"[ERROR] Invalid source directory: {source_dir}")
            return

        if limit:
            files_to_process = files_to_process[:limit]

        if files_to_process:
            print(f"      Will evaluate {len(files_to_process)} files")

    if not files_to_process:
        print("\n" + "="*80)
        print("[INFO] No files to evaluate. All articles have been processed!")
        print("="*80)

        if source_dir == "raw":
            print("\nNext steps:")
            if len(already_approved) > 0:
                print(f"  - Load {len(already_approved)} approved articles to database:")
                print(f"    python scripts/load_to_database.py")
            if len(already_reinfer) > 0:
                print(f"  - Re-infer {len(already_reinfer)} articles that need improvement:")
                print(f"    python scripts/reinfer_summaries.py")
            print("\n" + "="*80)

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
                # Load raw/summarized analysis
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

                # Store result
                results.append({
                    "article_id": article_id,
                    "score": quality_score,
                    "passed": passed,
                    "feedback": eval_result["feedback"]
                })

                # Save and route (unless dry run)
                if not dry_run:
                    # Save evaluated version
                    file_writer.save_evaluated_analysis(
                        article_id=article_id,
                        raw_analysis=raw_analysis,
                        evaluation_result=eval_result,
                        evaluation_metadata=eval_metadata
                    )

                    # Route based on score
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

    # Show up to 5 failed results (most important to review)
    failed_results = [r for r in results if not r["passed"]]
    if failed_results:
        print("\nFailed Evaluations (samples):")
        for i, result in enumerate(failed_results[:5]):
            print(f"\n  {i+1}. {result['article_id']}")
            print(f"     Score: {result['score']:.1f}/100")
            # Truncate feedback for display
            feedback_lines = result['feedback'].split('\n')
            print(f"     Feedback: {feedback_lines[0][:80]}...")

    # Show up to 3 passed results
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
        description="Evaluate GenAI summaries and route based on quality score",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        "--source",
        type=str,
        default="raw",
        choices=["raw", "summarized"],
        help="Source directory (default: raw)"
    )

    parser.add_argument(
        "--threshold",
        type=float,
        default=80.0,
        help="Quality threshold 0-100 (default: 80.0)"
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Maximum number of files to process (default: all)"
    )

    parser.add_argument(
        "--article-ids",
        type=str,
        default=None,
        help="Comma-separated article IDs to evaluate (e.g., PMID001,PMID002)"
    )

    parser.add_argument(
        "--model",
        type=str,
        default="llama-3.3-70b-versatile",
        help="Groq model for evaluation (default: llama-3.3-70b-versatile)"
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run evaluation without saving/moving files"
    )

    args = parser.parse_args()

    # Parse article IDs if provided
    article_ids = None
    if args.article_ids:
        article_ids = [aid.strip() for aid in args.article_ids.split(",")]

    # Run evaluation
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
