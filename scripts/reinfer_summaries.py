"""
CLI tool for re-inferring failed summaries with evaluation feedback.

Usage:
    python scripts/reinfer_summaries.py
    python scripts/reinfer_summaries.py --article-id PMID001
    python scripts/reinfer_summaries.py --max-attempts 3 --limit 10
    python scripts/reinfer_summaries.py --dry-run
"""

import sys
import os
import argparse
from pathlib import Path
from typing import List, Optional
import time
import json

# Don't do any imports or directory changes here - save it for runtime
SCRIPT_DIR = Path(__file__).parent.resolve()
PROJECT_ROOT = SCRIPT_DIR.parent
GENAI_DIR = PROJECT_ROOT / "backend" / "app" / "genai"


def _lazy_imports():
    """Import genai modules using proper package path."""
    # Add backend/app to path so we can import genai package
    backend_app_dir = PROJECT_ROOT / "backend" / "app"
    if str(backend_app_dir) not in sys.path:
        sys.path.insert(0, str(backend_app_dir))

    # Now import from the genai package properly
    from genai.evaluator import SummaryEvaluator
    from genai.file_writer import AnalysisFileWriter
    from genai.repository import ArticleRepository
    from genai.summarizer import ArticleSummarizer

    return SummaryEvaluator, AnalysisFileWriter, ArticleRepository, ArticleSummarizer


def reinfer_summaries(
    max_attempts: int = 3,
    threshold: float = 80.0,
    limit: Optional[int] = None,
    article_id: Optional[str] = None,
    dry_run: bool = False,
    model_name: str = "llama-3.3-70b-versatile"
):
    """Re-infer failed summaries with evaluation feedback."""
    # Import genai modules
    SummaryEvaluator, AnalysisFileWriter, ArticleRepository, ArticleSummarizer = _lazy_imports()

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
    print("RE-INFERENCE PIPELINE")
    print("="*80)

    # Initialize
    print("\n[1/6] Initializing...")

    # Use absolute path for data directory (since we changed to genai dir)
    data_dir = PROJECT_ROOT / "data" / "analysis"

    evaluator = SummaryEvaluator(
        model_name=model_name,
        quality_threshold=threshold
    )
    file_writer = AnalysisFileWriter(base_dir=str(data_dir))
    summarizer = ArticleSummarizer(
        model_name=model_name,
        max_retries=3
    )
    repo = ArticleRepository()

    print(f"      Model: {model_name}")
    print(f"      Quality Threshold: {threshold}%")
    print(f"      Max Attempts: {max_attempts}")
    print(f"      Dry Run: {dry_run}")

    # Get files to process
    print(f"\n[2/6] Discovering files in reinfer/...")

    if article_id:
        files_to_process = [article_id]
        print(f"      Processing 1 specified article: {article_id}")
    else:
        files_to_process = file_writer.list_reinfer_analyses()

        if limit:
            files_to_process = files_to_process[:limit]

        print(f"      Found {len(files_to_process)} files to re-infer")

    if not files_to_process:
        print("\n[INFO] No files to re-infer. Exiting.")
        return

    # Statistics
    stats = {
        "total": len(files_to_process),
        "reinferred": 0,
        "passed_after_reinfer": 0,
        "failed_after_reinfer": 0,
        "rejected": 0,
        "errors": 0,
        "skipped": 0,
        "total_score_before": 0.0,
        "total_score_after": 0.0,
        "total_time_ms": 0
    }

    # Process files
    print(f"\n[3/6] Re-inferring summaries with feedback...")
    results = []

    with tqdm(total=len(files_to_process), desc="Re-inferring", unit="file") as pbar:
        for article_id_item in files_to_process:
            try:
                # Load reinfer analysis
                reinfer_analysis = file_writer.load_reinfer_analysis(article_id_item)

                if not reinfer_analysis:
                    print(f"\n[WARNING] Could not load {article_id_item}, skipping")
                    stats["skipped"] += 1
                    pbar.update(1)
                    continue

                # Check attempt count
                current_attempt = reinfer_analysis.get("attempt", 1)

                if current_attempt >= max_attempts:
                    print(f"\n[INFO] {article_id_item} has reached max attempts ({current_attempt}), moving to rejected")

                    if not dry_run:
                        file_writer.move_to_rejected(
                            article_id_item,
                            reason=f"Failed quality check after {max_attempts} attempts"
                        )

                    stats["rejected"] += 1
                    pbar.update(1)
                    continue

                # Get feedback from previous evaluation
                feedback = reinfer_analysis.get("reinfer_feedback", "")
                previous_summary = reinfer_analysis.get("analysis", {}).get("summary", "")

                # Get previous evaluation details for claims
                previous_claims = ""
                if "evaluation" in reinfer_analysis:
                    claim_evals = reinfer_analysis["evaluation"].get("claim_evaluations", [])
                    if claim_evals:
                        previous_claims = "\n".join([
                            f"- {c.get('claim', '')}: {c.get('label', '')} ({c.get('explanation', '')})"
                            for c in claim_evals
                        ])

                # Fetch article from database
                article = repo.get_article_by_id(article_id_item)

                if not article:
                    print(f"\n[WARNING] Article {article_id_item} not found in database, skipping")
                    stats["skipped"] += 1
                    pbar.update(1)
                    continue

                # Re-infer with feedback
                reinfer_start = time.time()
                try:
                    response = summarizer.summarize(
                        doc_id=article['article_id'],
                        title=article['title'],
                        journal=article.get('journal', ''),
                        date=article.get('publication_date', ''),
                        abstract=article.get('abstract', ''),
                        feedback=feedback,
                        previous_summary=previous_summary,
                        previous_claims=previous_claims
                    )
                    reinfer_time_ms = int((time.time() - reinfer_start) * 1000)

                    # Build metadata
                    metadata = {
                        'processing_time_ms': reinfer_time_ms,
                        'tokens_used': 0,
                        'cost_usd': 0.0,
                        'model_id': model_name,
                        'prompt_version': 'v1',
                        'success': True,
                        'error': None
                    }

                except Exception as e:
                    print(f"\n[ERROR] Re-inference failed for {article_id_item}: {e}")
                    stats["errors"] += 1
                    pbar.update(1)
                    continue

                # Save new raw analysis
                if not dry_run:
                    file_writer.save_raw_analysis(
                        article_id=article_id_item,
                        source_data=article,
                        response=response,
                        metadata=metadata
                    )

                # Re-evaluate
                eval_start = time.time()

                # Load the newly saved raw analysis
                new_raw_analysis = file_writer.load_raw_analysis(article_id_item)
                evaluation = evaluator.evaluate(new_raw_analysis)
                eval_time_ms = int((time.time() - eval_start) * 1000)

                stats["reinferred"] += 1
                stats["total_time_ms"] += (reinfer_time_ms + eval_time_ms)

                eval_result = evaluation["evaluation"]
                eval_metadata = evaluation["metadata"]

                # Get previous and new scores
                previous_score = reinfer_analysis.get("evaluation", {}).get("quality_score", {}).get("overall_score", 0)
                new_score = eval_result["quality_score"]["overall_score"]
                passed = eval_result["passed"]

                stats["total_score_before"] += previous_score
                stats["total_score_after"] += new_score

                if passed:
                    stats["passed_after_reinfer"] += 1
                else:
                    stats["failed_after_reinfer"] += 1

                results.append({
                    "article_id": article_id_item,
                    "attempt": current_attempt + 1,
                    "score_before": previous_score,
                    "score_after": new_score,
                    "improvement": new_score - previous_score,
                    "passed": passed,
                    "feedback": eval_result["feedback"]
                })

                # Save and route (unless dry run)
                if not dry_run:
                    file_writer.save_evaluated_analysis(
                        article_id=article_id_item,
                        raw_analysis=new_raw_analysis,
                        evaluation_result=eval_result,
                        evaluation_metadata=eval_metadata
                    )

                    # Remove from reinfer directory
                    reinfer_file = file_writer.reinfer_dir / f"{article_id_item}.json"
                    if reinfer_file.exists():
                        reinfer_file.unlink()

                    if passed:
                        file_writer.move_to_approved(article_id_item)
                    else:
                        # Still failing, increment attempt and move back to reinfer
                        file_writer.move_to_reinfer(
                            article_id=article_id_item,
                            feedback=eval_result["feedback"],
                            attempt=current_attempt + 1
                        )

            except Exception as e:
                print(f"\n[ERROR] Failed to re-infer {article_id_item}: {e}")
                stats["errors"] += 1

            pbar.update(1)

    # Display results
    print(f"\n[4/6] Re-inference complete!")
    print(f"      Re-inferred: {stats['reinferred']}")
    print(f"      Passed after re-inference: {stats['passed_after_reinfer']}")
    print(f"      Failed after re-inference: {stats['failed_after_reinfer']}")
    print(f"      Rejected (max attempts): {stats['rejected']}")
    print(f"      Errors: {stats['errors']}")
    print(f"      Skipped: {stats['skipped']}")

    if stats["reinferred"] > 0:
        avg_score_before = stats["total_score_before"] / stats["reinferred"]
        avg_score_after = stats["total_score_after"] / stats["reinferred"]
        improvement = avg_score_after - avg_score_before
        success_rate = (stats["passed_after_reinfer"] / stats["reinferred"]) * 100
        avg_time_ms = stats["total_time_ms"] / stats["reinferred"]

        print(f"\n      Average Score Before: {avg_score_before:.1f}/100")
        print(f"      Average Score After: {avg_score_after:.1f}/100")
        print(f"      Average Improvement: {improvement:+.1f} points")
        print(f"      Success Rate: {success_rate:.1f}%")
        print(f"      Avg Processing Time: {avg_time_ms:.0f}ms")

    # Show sample results
    print(f"\n[5/6] Sample Results:")
    print(f"{'-'*80}")

    # Sort by improvement
    results.sort(key=lambda x: x["improvement"], reverse=True)

    if results:
        print("\nTop Improvements:")
        for i, result in enumerate(results[:5]):
            status = "PASSED" if result["passed"] else "FAILED"
            print(f"\n  {i+1}. {result['article_id']} [Attempt {result['attempt']}]")
            print(f"     {result['score_before']:.1f} -> {result['score_after']:.1f} ({result['improvement']:+.1f}) {status}")

        failed_results = [r for r in results if not r["passed"]]
        if failed_results:
            print(f"\nStill Failing ({len(failed_results)} total):")
            for i, result in enumerate(failed_results[:3]):
                print(f"  - {result['article_id']}: {result['score_after']:.1f}/100 (attempt {result['attempt']})")

    # Final summary
    print(f"\n{'='*80}")
    print("SUMMARY")
    print(f"{'='*80}")

    if not dry_run:
        print(f"Files routed:")
        print(f"  - Approved: {stats['passed_after_reinfer']} files -> data/analysis/approved/")
        print(f"  - Re-infer: {stats['failed_after_reinfer']} files -> data/analysis/reinfer/")
        print(f"  - Rejected: {stats['rejected']} files -> data/analysis/rejected/")
    else:
        print("[DRY RUN] No files were moved or saved.")

    print(f"\nNext steps:")
    if stats["failed_after_reinfer"] > 0:
        print(f"  - {stats['failed_after_reinfer']} summaries still need improvement")
        print(f"    Run again: python scripts/reinfer_summaries.py")
    if stats["rejected"] > 0:
        print(f"  - {stats['rejected']} summaries rejected (manual review needed)")
    if stats["passed_after_reinfer"] > 0:
        print(f"  - {stats['passed_after_reinfer']} summaries approved and ready for database load")

    print(f"{'='*80}\n")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Re-infer failed summaries with evaluation feedback"
    )

    parser.add_argument("--article-id", type=str, default=None)
    parser.add_argument("--max-attempts", type=int, default=3)
    parser.add_argument("--threshold", type=float, default=80.0)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--model", type=str, default="llama-3.3-70b-versatile")
    parser.add_argument("--dry-run", action="store_true")

    args = parser.parse_args()

    try:
        reinfer_summaries(
            max_attempts=args.max_attempts,
            threshold=args.threshold,
            limit=args.limit,
            article_id=args.article_id,
            dry_run=args.dry_run,
            model_name=args.model
        )
    except KeyboardInterrupt:
        print("\n\n[INFO] Re-inference interrupted by user. Exiting gracefully...")
        sys.exit(0)
    except Exception as e:
        print(f"\n[ERROR] Re-inference failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
