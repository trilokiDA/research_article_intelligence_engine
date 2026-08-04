"""
Summarization pipeline for processing articles.
Reads articles from database, summarizes them, and saves results.
Supports both JSON file output (for quality control) and direct database writes.
"""

import os
import time
from typing import Optional, Dict, Any
from datetime import datetime
from dotenv import load_dotenv
from tqdm import tqdm

from .summarizer import ArticleSummarizer
from .repository import ArticleRepository
from .schemas import Response
from .file_writer import AnalysisFileWriter
from .config import PipelineConfig

# Load environment variables
load_dotenv()


class SummarizationPipeline:
    """
    Pipeline for processing articles through summarization.
    """

    def __init__(
        self,
        model_name: str = "llama-3.3-70b-versatile",
        batch_size: int = 10,
        max_retries: int = 3,
        delay_between_batches: float = 1.0,
        prompt_version: str = "v1",
        output_format: str = "json"  # NEW: 'json' or 'database'
    ):
        """
        Initialize the pipeline.

        Args:
            model_name: Groq model to use
            batch_size: Number of articles to process in one batch
            max_retries: Max retries per article
            delay_between_batches: Delay in seconds between batches (for rate limiting)
            prompt_version: Version identifier for the prompt
            output_format: Output format - 'json' (file-based) or 'database' (direct DB write)
        """
        self.model_name = model_name
        self.batch_size = batch_size
        self.max_retries = max_retries
        self.delay_between_batches = delay_between_batches
        self.prompt_version = prompt_version
        self.output_format = output_format  # NEW

        # Initialize summarizer
        self.summarizer = ArticleSummarizer(
            model_name=model_name,
            max_retries=max_retries
        )

        # Initialize repository
        self.repo = ArticleRepository()

        # Initialize file writer (for JSON output)
        self.file_writer = AnalysisFileWriter()  # NEW

    def process_article(
        self,
        article: Dict[str, Any],
        feedback: Optional[str] = None,
        previous_summary: Optional[str] = None,
        previous_claims: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Process a single article.

        Args:
            article: Article dictionary from database
            feedback: Optional feedback from evaluation (for re-inference)
            previous_summary: Previous summary text (for re-inference)
            previous_claims: Previous claim evaluations (for re-inference)

        Returns:
            Dictionary with 'result' (Response object) and 'metadata', or None if failed
        """
        start_time = time.time()

        try:
            result = self.summarizer.summarize(
                doc_id=article['article_id'],
                title=article['title'],
                journal=article.get('journal', ''),
                date=article.get('publication_date', ''),
                abstract=article.get('abstract', ''),
                feedback=feedback,
                previous_summary=previous_summary,
                previous_claims=previous_claims
            )

            # Calculate processing time
            processing_time_ms = int((time.time() - start_time) * 1000)

            # Build metadata
            metadata = {
                'processing_time_ms': processing_time_ms,
                'tokens_used': 0,  # TODO: Extract from Groq response if available
                'cost_usd': 0.0,  # TODO: Calculate based on token usage
                'model_id': self.model_name,
                'prompt_version': self.prompt_version,
                'success': True,
                'error': None
            }

            return {
                'result': result,
                'metadata': metadata
            }

        except Exception as e:
            processing_time_ms = int((time.time() - start_time) * 1000)

            # Handle Unicode in error messages for Windows console
            try:
                print(f"\n[ERROR] Failed to process article {article['article_id']}: {e}")
            except UnicodeEncodeError:
                print(f"\n[ERROR] Failed to process article {article['article_id']}: [Unicode error in message]")

            # Mark as failed in database (regardless of output format)
            self.repo.mark_analysis_failed(
                article['article_id'],
                str(e)
            )

            # Return metadata with error
            return {
                'result': None,
                'metadata': {
                    'processing_time_ms': processing_time_ms,
                    'tokens_used': 0,
                    'cost_usd': 0.0,
                    'model_id': self.model_name,
                    'prompt_version': self.prompt_version,
                    'success': False,
                    'error': str(e)
                }
            }

    def run(
        self,
        limit: Optional[int] = None,
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """
        Run the summarization pipeline.

        Args:
            limit: Maximum number of articles to process (None = all pending)
            dry_run: If True, don't save results (for testing)

        Returns:
            Dictionary with processing statistics
        """
        print("\n" + "="*80)
        print("SUMMARIZATION PIPELINE")
        print("="*80)

        # Get pending articles
        print("\n[1/4] Fetching articles pending analysis...")
        pending_count = self.repo.count_articles_pending_analysis()
        print(f"      Found {pending_count} articles pending analysis")

        if pending_count == 0:
            print("\n[INFO] No articles need processing. All done!")
            return {
                'total_pending': 0,
                'processed': 0,
                'successful': 0,
                'failed': 0
            }

        # Determine how many to process
        to_process = min(limit, pending_count) if limit else pending_count
        print(f"      Processing {to_process} articles")

        # Statistics
        stats = {
            'total_pending': pending_count,
            'processed': 0,
            'successful': 0,
            'failed': 0,
            'skipped': 0,
            'batches': 0
        }

        print(f"\n[2/4] Processing articles...")
        print(f"      Model: {self.model_name}")
        print(f"      Batch size: {self.batch_size}")
        print(f"      Output format: {self.output_format}")
        print(f"      Dry run: {dry_run}")

        # Process in batches
        offset = 0
        with tqdm(total=to_process, desc="Processing articles", unit="article") as pbar:
            while offset < to_process:
                # Fetch batch
                batch_size = min(self.batch_size, to_process - offset)
                articles = self.repo.get_articles_pending_analysis(
                    limit=batch_size,
                    offset=offset
                )

                if not articles:
                    break

                stats['batches'] += 1

                # Process each article in batch
                for article in articles:
                    # Skip if raw JSON file already exists (Stage 2 output)
                    if self.output_format == 'json' and not dry_run:
                        raw_file = self.file_writer.raw_dir / f"{article['article_id']}.json"
                        if raw_file.exists():
                            stats['skipped'] += 1
                            stats['processed'] += 1
                            pbar.update(1)
                            continue

                    process_result = self.process_article(article)

                    if process_result and process_result['result']:
                        stats['successful'] += 1

                        if not dry_run:
                            # Save based on output format
                            if self.output_format == 'json':
                                # Stage 2: Save to raw/ directory
                                try:
                                    source_data = {
                                        'title': article.get('title', ''),
                                        'journal': article.get('journal', ''),
                                        'publication_date': article.get('publication_date', ''),
                                        'abstract': article.get('abstract', ''),
                                        'doi': article.get('doi', ''),
                                        'source': article.get('source', '')
                                    }

                                    file_path = self.file_writer.save_raw_analysis(
                                        article_id=article['article_id'],
                                        response=process_result['result'],
                                        source_data=source_data,
                                        metadata=process_result['metadata'],
                                        attempt=1
                                    )
                                    # Success - file saved to raw/
                                except Exception as e:
                                    print(f"\n[WARNING] Failed to save JSON for {article['article_id']}: {e}")
                                    stats['failed'] += 1
                                    stats['successful'] -= 1

                            elif self.output_format == 'database':
                                # OLD: Save directly to database
                                saved = self.repo.save_analysis(
                                    response=process_result['result'],
                                    model_id=self.model_name,
                                    prompt_version=self.prompt_version
                                )
                                if not saved:
                                    print(f"\n[WARNING] Failed to save to database for {article['article_id']}")
                                    stats['failed'] += 1
                                    stats['successful'] -= 1
                    else:
                        stats['failed'] += 1

                    stats['processed'] += 1
                    pbar.update(1)

                offset += batch_size

                # Delay between batches (rate limiting)
                if offset < to_process and self.delay_between_batches > 0:
                    time.sleep(self.delay_between_batches)

        # Final statistics
        print(f"\n[3/4] Processing complete!")
        print(f"      Processed: {stats['processed']}")
        print(f"      Successful: {stats['successful']}")
        print(f"      Failed: {stats['failed']}")
        if stats['skipped'] > 0:
            print(f"      Skipped: {stats['skipped']} (already summarized)")
        if stats['processed'] > 0:
            print(f"      Success rate: {stats['successful']/stats['processed']*100:.1f}%")

        # Get updated stats based on output format
        print(f"\n[4/4] Fetching statistics...")

        if self.output_format == 'json':
            # Get file-based statistics
            file_stats = self.file_writer.get_processing_stats()

            print(f"\n" + "="*80)
            print("FILE-BASED STATISTICS")
            print("="*80)
            print(f"Total JSON files:     {file_stats['total_files']}")
            print(f"Successful:           {file_stats['successful']}")
            print(f"Failed:               {file_stats['failed']}")
            if file_stats['total_files'] > 0:
                print(f"\nPerformance Metrics:")
                print(f"  Avg processing time: {file_stats['avg_processing_time_ms']:.1f}ms")
                print(f"  Total tokens:        {file_stats['total_tokens']}")
                print(f"  Total cost:          ${file_stats['total_cost_usd']:.4f}")
            print(f"\nBy Category:")
            for category, count in sorted(file_stats['by_category'].items()):
                print(f"  {category:<30} {count:>5}")
            print(f"\nBy Sentiment:")
            for sentiment, count in sorted(file_stats['by_sentiment'].items()):
                print(f"  {sentiment:<30} {count:>5}")
            print(f"\nBy Subject:")
            for subject, count in sorted(file_stats['by_subject'].items()):
                print(f"  {subject:<30} {count:>5}")
            print("="*80 + "\n")

        else:  # database output
            # Get database statistics
            db_stats = self.repo.get_analysis_stats()

            print(f"\n" + "="*80)
            print("DATABASE STATISTICS")
            print("="*80)
            print(f"Total articles:       {db_stats['total_articles']}")
            print(f"Analyzed:             {db_stats['analyzed_count']}")
            print(f"Pending:              {db_stats['pending_count']}")
            print(f"\nBy Category:")
            for category, count in sorted(db_stats['by_category'].items()):
                print(f"  {category:<30} {count:>5}")
            print(f"\nBy Sentiment:")
            for sentiment, count in sorted(db_stats['by_sentiment'].items()):
                print(f"  {sentiment:<30} {count:>5}")
            print("="*80 + "\n")

        return stats
