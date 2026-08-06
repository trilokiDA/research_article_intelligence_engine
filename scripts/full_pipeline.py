"""
Full Pipeline Orchestrator - Run complete 5-stage GenAI workflow.

This script orchestrates all stages of the article analysis pipeline:
  Stage 1: Data Ingestion (PubMed API)
  Stage 2: GenAI Summarization (Groq LLM)
  Stage 3: Quality Evaluation (factual accuracy, hallucination, people-first language)
  Stage 4: Re-inference (if quality < threshold)
  Stage 5: Database Load (to article_analysis table)

Usage:
    # Complete workflow with default settings
    python scripts/full_pipeline.py --topic "Heat-Not-Burn" --max-articles 50

    # Custom workflow with specific stages
    python scripts/full_pipeline.py --stages ingest summarize evaluate load

    # Dry run (validate without changes)
    python scripts/full_pipeline.py --topic "E-Cigarettes" --dry-run

    # With quality threshold and limits
    python scripts/full_pipeline.py --topic "Nicotine-Pouch" --threshold 85 --limit 20

    # Skip ingestion (use existing articles)
    python scripts/full_pipeline.py --stages summarize evaluate reinfer load --limit 100

Examples:
    # Monthly research update
    python scripts/full_pipeline.py --topic "Heat-Not-Burn" --max-articles 50 --archive

    # Quick test run
    python scripts/full_pipeline.py --limit 10 --dry-run

    # Custom query with high quality bar
    python scripts/full_pipeline.py --query "IQOS heated tobacco" --threshold 90 --max-articles 30
"""

import argparse
import sys
import time
from pathlib import Path
from datetime import datetime
from typing import List, Optional

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

try:
    from app.ingestion.orchestrator import IngestionOrchestrator
    from app.config.query_manager import QueryManager
    from app.genai.pipeline import SummarizationPipeline
    from app.genai.evaluator import SummaryEvaluator
    from app.genai.db_loader import AnalysisDatabaseLoader
    from app.genai.config import PipelineConfig
    from app.db.database import get_db, get_stats, DATABASE_PATH

    # Get analysis directory from config
    ANALYSIS_DIR = PipelineConfig.BASE_DIR
except ImportError as e:
    print(f"Error importing modules: {e}")
    print("\nPlease ensure all dependencies are installed:")
    print("  pip install -r backend/requirements.txt")
    print("\nOr activate your virtual environment first:")
    print("  source venv/bin/activate  # Linux/Mac")
    print("  venv\\Scripts\\activate     # Windows")
    sys.exit(1)


class PipelineOrchestrator:
    """Orchestrates the complete 5-stage GenAI pipeline."""

    def __init__(self, dry_run: bool = False, verbose: bool = True, auto_cleanup: bool = False):
        self.dry_run = dry_run
        self.verbose = verbose
        self.auto_cleanup = auto_cleanup
        self.stats = {
            'start_time': datetime.now(),
            'ingested': 0,
            'summarized': 0,
            'evaluated': 0,
            'reinferred': 0,
            'loaded': 0,
            'cleaned': 0,
            'errors': []
        }

    def log(self, message: str, level: str = "INFO"):
        """Log message with timestamp."""
        if self.verbose:
            timestamp = datetime.now().strftime("%H:%M:%S")
            prefix = {
                "INFO": "ℹ",
                "SUCCESS": "✓",
                "ERROR": "✗",
                "WARN": "⚠"
            }.get(level, "•")
            print(f"[{timestamp}] {prefix} {message}")

    def print_header(self, title: str):
        """Print section header."""
        if self.verbose:
            print("\n" + "=" * 70)
            print(f"  {title}")
            print("=" * 70)

    def stage_1_ingest(
        self,
        topic: Optional[str] = None,
        query: Optional[str] = None,
        sources: List[str] = None,
        max_articles: int = 100,
        date_range: Optional[dict] = None
    ) -> int:
        """
        Stage 1: Data Ingestion from PubMed.

        Returns: Number of articles ingested
        """
        self.print_header("STAGE 1: Data Ingestion")

        if self.dry_run:
            self.log("DRY RUN: Skipping ingestion", "WARN")
            return 0

        try:
            orchestrator = IngestionOrchestrator()
            query_manager = QueryManager()

            # Determine search query
            if topic:
                self.log(f"Using predefined topic: {topic}")
                search_query = query_manager.get_query(topic, 'pubmed')
            elif query:
                self.log(f"Using custom query: {query}")
                search_query = query
            else:
                raise ValueError("Either --topic or --query must be provided for ingestion")

            # Run ingestion
            self.log(f"Ingesting from sources: {', '.join(sources)}")
            self.log(f"Max articles per source: {max_articles}")

            results = orchestrator.ingest_from_query(
                query=search_query,
                sources=sources or ['pubmed'],
                max_per_source=max_articles,
                date_range=date_range
            )

            ingested_count = results.get('total', 0)
            duplicates = results.get('duplicates', 0)

            self.stats['ingested'] = ingested_count
            self.log(f"Ingested {ingested_count} new articles (skipped {duplicates} duplicates)", "SUCCESS")

            return ingested_count

        except Exception as e:
            error_msg = f"Stage 1 failed: {str(e)}"
            self.log(error_msg, "ERROR")
            self.stats['errors'].append(error_msg)
            return 0

    def stage_2_summarize(
        self,
        limit: Optional[int] = None,
        model: str = "llama-3.3-70b-versatile",
        batch_size: int = 10
    ) -> int:
        """
        Stage 2: GenAI Summarization using Groq LLM.

        Returns: Number of articles summarized
        """
        self.print_header("STAGE 2: GenAI Summarization")

        try:
            pipeline = SummarizationPipeline(
                model_name=model,
                batch_size=batch_size,
                output_format='json'
            )

            if self.dry_run:
                from app.genai.repository import ArticleRepository
                repo = ArticleRepository()
                pending_count = repo.count_articles_pending_analysis()
                self.log(f"DRY RUN: Would process {min(pending_count, limit or pending_count)} articles", "WARN")
                return 0

            self.log(f"Using model: {model}")
            self.log(f"Batch size: {batch_size}")

            results = pipeline.run(
                limit=limit,
                dry_run=False
            )

            summarized_count = results.get('successful', 0)
            self.stats['summarized'] = summarized_count

            self.log(f"Summarized {summarized_count} articles", "SUCCESS")
            if results.get('failed', 0) > 0:
                self.log(f"Failed: {results['failed']} articles", "WARN")

            return summarized_count

        except Exception as e:
            error_msg = f"Stage 2 failed: {str(e)}"
            self.log(error_msg, "ERROR")
            self.stats['errors'].append(error_msg)
            return 0

    def stage_3_evaluate(
        self,
        source_dir: str = "raw",
        threshold: int = 80,
        limit: Optional[int] = None
    ) -> dict:
        """
        Stage 3: Quality Evaluation and Routing.

        Returns: Dict with counts of approved/reinfer files
        """
        self.print_header("STAGE 3: Quality Evaluation")

        try:
            evaluator = SummaryEvaluator(model_name="llama-3.3-70b-versatile")

            source_path = ANALYSIS_DIR / source_dir
            approved_path = ANALYSIS_DIR / "approved"
            reinfer_path = ANALYSIS_DIR / "reinfer"

            if not source_path.exists():
                self.log(f"Source directory not found: {source_path}", "ERROR")
                return {'approved': 0, 'reinfer': 0}

            files = list(source_path.glob("*.json"))
            if limit:
                files = files[:limit]

            self.log(f"Evaluating {len(files)} summaries from {source_dir}/")
            self.log(f"Quality threshold: {threshold}%")

            if self.dry_run:
                self.log(f"DRY RUN: Would evaluate {len(files)} files", "WARN")
                return {'approved': 0, 'reinfer': 0}

            approved_count = 0
            reinfer_count = 0

            import json
            import shutil

            for file in files:
                try:
                    with open(file, 'r', encoding='utf-8') as f:
                        data = json.load(f)

                    # Evaluate the raw analysis
                    eval_result = evaluator.evaluate(data)

                    score = eval_result.get('evaluation', {}).get('overall_score', 0)

                    # Route based on score
                    if score >= threshold:
                        dest = approved_path / file.name
                        approved_count += 1
                    else:
                        dest = reinfer_path / file.name
                        reinfer_count += 1

                    # Move file
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    shutil.move(str(file), str(dest))

                except Exception as e:
                    self.log(f"Failed to evaluate {file.name}: {e}", "WARN")
                    self.stats['errors'].append(f"Evaluation error: {file.name}")

            self.stats['evaluated'] = approved_count + reinfer_count
            self.log(f"Approved: {approved_count} | Reinfer: {reinfer_count}", "SUCCESS")

            return {'approved': approved_count, 'reinfer': reinfer_count}

        except Exception as e:
            error_msg = f"Stage 3 failed: {str(e)}"
            self.log(error_msg, "ERROR")
            self.stats['errors'].append(error_msg)
            return {'approved': 0, 'reinfer': 0}

    def stage_4_reinfer(
        self,
        max_attempts: int = 3,
        limit: Optional[int] = None
    ) -> int:
        """
        Stage 4: Re-inference for failed summaries.

        Returns: Number of articles re-inferred
        """
        self.print_header("STAGE 4: Re-inference")

        try:
            reinfer_path = ANALYSIS_DIR / "reinfer"

            if not reinfer_path.exists():
                self.log("No files need re-inference", "INFO")
                return 0

            files = list(reinfer_path.glob("*.json"))
            if limit:
                files = files[:limit]

            self.log(f"Found {len(files)} files for re-inference")

            if self.dry_run:
                self.log(f"DRY RUN: Would re-infer {len(files)} summaries", "WARN")
                return 0

            if len(files) == 0:
                self.log("No summaries need re-inference", "SUCCESS")
                return 0

            # Import and run reinfer script
            sys.path.insert(0, str(Path(__file__).parent))
            try:
                from reinfer_summaries import reinfer_summaries

                # Run reinference on all files
                result = reinfer_summaries(
                    max_attempts=max_attempts,
                    threshold=80.0,
                    limit=limit,
                    dry_run=False
                )

                reinfer_count = result.get('reinferred', 0) if isinstance(result, dict) else len(files)
                self.stats['reinferred'] = reinfer_count
                self.log(f"Re-inferred {reinfer_count} summaries", "SUCCESS")

                return reinfer_count

            except ImportError as e:
                error_msg = f"Re-inference module not available: {e}"
                self.log(error_msg, "WARN")
                return 0
        except Exception as e:
            error_msg = f"Stage 4 failed: {str(e)}"
            self.log(error_msg, "ERROR")
            self.stats['errors'].append(error_msg)
            return 0

    def stage_5_load(
        self,
        limit: Optional[int] = None,
        archive: bool = False
    ) -> int:
        """
        Stage 5: Load approved analyses to database.

        Returns: Number of analyses loaded
        """
        self.print_header("STAGE 5: Database Load")

        try:
            approved_path = ANALYSIS_DIR / "approved"
            archive_path = ANALYSIS_DIR / "loaded"

            if not approved_path.exists():
                self.log("No approved files to load", "WARN")
                return 0

            files = list(approved_path.glob("*.json"))
            if limit:
                files = files[:limit]

            self.log(f"Loading {len(files)} approved analyses")

            if self.dry_run:
                self.log(f"DRY RUN: Would load {len(files)} files to database", "WARN")
                return 0

            loader = AnalysisDatabaseLoader(base_dir=str(ANALYSIS_DIR))

            # Use the high-level load method that handles connection
            result = loader.load_approved_files(
                limit=limit,
                dry_run=False,
                archive=archive
            )

            loaded_count = result.get('loaded', 0) + result.get('updated', 0)
            error_count = result.get('errors', 0)

            self.stats['loaded'] = loaded_count

            if error_count > 0:
                self.log(f"Loaded {loaded_count} analyses with {error_count} errors", "WARN")
                for error_detail in result.get('error_details', []):
                    self.log(f"  {error_detail['file']}: {error_detail['error']}", "WARN")
                    self.stats['errors'].append(f"Load error: {error_detail['file']}")
            else:
                self.log(f"Loaded {loaded_count} analyses to database", "SUCCESS")

            if archive and loaded_count > 0:
                self.log(f"Archived {loaded_count} files", "INFO")

            return loaded_count

        except Exception as e:
            error_msg = f"Stage 5 failed: {str(e)}"
            self.log(error_msg, "ERROR")
            self.stats['errors'].append(error_msg)
            return 0

    def cleanup_old_files(self, days: int = 7):
        """
        Clean up old processed files from raw/ and evaluated/ directories.

        This prevents unbounded file accumulation by archiving files older
        than the specified number of days.
        """
        self.print_header("FILE CLEANUP")

        try:
            from datetime import timedelta
            import shutil

            cutoff = datetime.now() - timedelta(days=days)
            cleaned_count = 0

            # Directories to clean (files that have been processed)
            cleanup_dirs = {
                'raw': 'Raw summaries (after evaluation)',
                'evaluated': 'Evaluated files (after routing)'
            }

            for dir_name, description in cleanup_dirs.items():
                dir_path = ANALYSIS_DIR / dir_name

                if not dir_path.exists():
                    continue

                old_files = [
                    f for f in dir_path.glob("*.json")
                    if datetime.fromtimestamp(f.stat().st_mtime) < cutoff
                ]

                if old_files:
                    self.log(f"Found {len(old_files)} old files in {dir_name}/")

                    if self.dry_run:
                        self.log(f"DRY RUN: Would archive {len(old_files)} files", "WARN")
                    else:
                        # Archive to timestamped directory
                        archive_dir = ANALYSIS_DIR / "archive" / dir_name / datetime.now().strftime("%Y%m%d")
                        archive_dir.mkdir(parents=True, exist_ok=True)

                        for file in old_files:
                            try:
                                shutil.move(str(file), str(archive_dir / file.name))
                                cleaned_count += 1
                            except Exception as e:
                                self.log(f"Failed to archive {file.name}: {e}", "WARN")

            self.stats['cleaned'] = cleaned_count

            if cleaned_count > 0:
                self.log(f"Archived {cleaned_count} old files", "SUCCESS")
            else:
                self.log(f"No old files to clean (< {days} days)", "INFO")

        except Exception as e:
            error_msg = f"Cleanup failed: {str(e)}"
            self.log(error_msg, "WARN")
            self.stats['errors'].append(error_msg)

    def run(
        self,
        stages: List[str],
        topic: Optional[str] = None,
        query: Optional[str] = None,
        max_articles: int = 100,
        limit: Optional[int] = None,
        threshold: int = 80,
        archive: bool = False,
        date_range: Optional[dict] = None
    ):
        """Run specified pipeline stages."""
        self.print_header("FULL PIPELINE ORCHESTRATOR")

        if self.dry_run:
            self.log("DRY RUN MODE - No changes will be made", "WARN")

        self.log(f"Stages: {' → '.join(stages)}")
        self.log(f"Database: {DATABASE_PATH}")
        self.log(f"Analysis directory: {ANALYSIS_DIR}")

        # Stage 1: Ingest
        if 'ingest' in stages:
            self.stage_1_ingest(
                topic=topic,
                query=query,
                max_articles=max_articles,
                date_range=date_range
            )
            time.sleep(1)  # Brief pause between stages

        # Stage 2: Summarize
        if 'summarize' in stages:
            self.stage_2_summarize(
                limit=limit,
                model="llama-3.3-70b-versatile",
                batch_size=10
            )
            time.sleep(1)

        # Stage 3: Evaluate
        if 'evaluate' in stages:
            eval_results = self.stage_3_evaluate(
                source_dir="raw",
                threshold=threshold,
                limit=limit
            )
            time.sleep(1)

            # Stage 4: Re-inference (if needed)
            if 'reinfer' in stages and eval_results.get('reinfer', 0) > 0:
                self.stage_4_reinfer(limit=limit)
                time.sleep(1)

        # Stage 5: Load
        if 'load' in stages:
            self.stage_5_load(
                limit=limit,
                archive=archive
            )

        # Cleanup old files (if enabled)
        if self.auto_cleanup:
            self.cleanup_old_files(days=7)

        # Print summary
        self.print_summary()

    def print_summary(self):
        """Print pipeline execution summary."""
        self.print_header("PIPELINE SUMMARY")

        duration = (datetime.now() - self.stats['start_time']).total_seconds()

        print(f"\n  Duration: {duration:.1f} seconds")
        print(f"  Ingested: {self.stats['ingested']}")
        print(f"  Summarized: {self.stats['summarized']}")
        print(f"  Evaluated: {self.stats['evaluated']}")
        print(f"  Re-inferred: {self.stats['reinferred']}")
        print(f"  Loaded to DB: {self.stats['loaded']}")

        if self.stats['cleaned'] > 0:
            print(f"  Cleaned up: {self.stats['cleaned']} old files")

        if self.stats['errors']:
            print(f"\n  Errors: {len(self.stats['errors'])}")
            for error in self.stats['errors'][:5]:  # Show first 5
                print(f"    - {error}")

        # Show database stats
        print("\n  Database Statistics:")
        db_stats = get_stats()
        print(f"    Total articles: {db_stats.get('total_articles', 0)}")
        print(f"    Analyzed: {db_stats.get('analyzed_articles', 0)}")

        print("\n" + "=" * 70 + "\n")


def main():
    parser = argparse.ArgumentParser(
        description="Full Pipeline Orchestrator - Run complete 5-stage workflow",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    # Pipeline control
    parser.add_argument(
        '--stages',
        nargs='+',
        default=['ingest', 'summarize', 'evaluate', 'reinfer', 'load'],
        choices=['ingest', 'summarize', 'evaluate', 'reinfer', 'load'],
        help='Stages to run (default: all)'
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Validate workflow without making changes'
    )

    # Stage 1: Ingestion
    parser.add_argument(
        '--topic',
        help='Predefined topic name (e.g., "Heat-Not-Burn", "E-Cigarettes")'
    )

    parser.add_argument(
        '--query',
        help='Custom search query'
    )

    parser.add_argument(
        '--max-articles',
        type=int,
        default=100,
        help='Maximum articles to ingest (default: 100)'
    )

    parser.add_argument(
        '--from-date',
        help='Start date for ingestion (YYYY-MM-DD)'
    )

    parser.add_argument(
        '--to-date',
        help='End date for ingestion (YYYY-MM-DD)'
    )

    # Stage 2-5: Processing
    parser.add_argument(
        '--limit',
        type=int,
        help='Limit articles to process in each stage'
    )

    parser.add_argument(
        '--threshold',
        type=int,
        default=80,
        help='Quality threshold for evaluation (0-100, default: 80)'
    )

    parser.add_argument(
        '--archive',
        action='store_true',
        help='Archive loaded files after Stage 5'
    )

    parser.add_argument(
        '--quiet',
        action='store_true',
        help='Suppress verbose output'
    )

    parser.add_argument(
        '--auto-cleanup',
        action='store_true',
        help='Automatically archive old files (>7 days) after pipeline runs'
    )

    args = parser.parse_args()

    # Validate arguments
    if 'ingest' in args.stages and not (args.topic or args.query):
        parser.error("--topic or --query required for ingestion stage")

    # Build date range
    date_range = None
    if args.from_date or args.to_date:
        date_range = {}
        if args.from_date:
            date_range['from'] = args.from_date
        if args.to_date:
            date_range['to'] = args.to_date

    # Run pipeline
    orchestrator = PipelineOrchestrator(
        dry_run=args.dry_run,
        verbose=not args.quiet,
        auto_cleanup=args.auto_cleanup
    )

    try:
        orchestrator.run(
            stages=args.stages,
            topic=args.topic,
            query=args.query,
            max_articles=args.max_articles,
            limit=args.limit,
            threshold=args.threshold,
            archive=args.archive,
            date_range=date_range
        )

        sys.exit(0)

    except KeyboardInterrupt:
        print("\n\nPipeline interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nFATAL ERROR: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
