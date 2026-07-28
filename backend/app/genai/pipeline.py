"""
Summarization pipeline for processing articles.
Reads articles from database, summarizes them, and saves results.
"""

import os
import time
from typing import Optional, Dict, Any
from dotenv import load_dotenv
from tqdm import tqdm

from .summarizer import ArticleSummarizer
from .repository import ArticleRepository
from .schemas import Response

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
        prompt_version: str = "v1"
    ):
        """
        Initialize the pipeline.

        Args:
            model_name: Groq model to use
            batch_size: Number of articles to process in one batch
            max_retries: Max retries per article
            delay_between_batches: Delay in seconds between batches (for rate limiting)
            prompt_version: Version identifier for the prompt
        """
        self.model_name = model_name
        self.batch_size = batch_size
        self.max_retries = max_retries
        self.delay_between_batches = delay_between_batches
        self.prompt_version = prompt_version

        # Initialize summarizer
        self.summarizer = ArticleSummarizer(
            model_name=model_name,
            max_retries=max_retries
        )

        # Initialize repository
        self.repo = ArticleRepository()

    def process_article(self, article: Dict[str, Any]) -> Optional[Response]:
        """
        Process a single article.

        Args:
            article: Article dictionary from database

        Returns:
            Response object or None if failed
        """
        try:
            result = self.summarizer.summarize(
                doc_id=article['article_id'],
                title=article['title'],
                journal=article.get('journal', ''),
                date=article.get('publication_date', ''),
                abstract=article.get('abstract', '')
            )
            return result

        except Exception as e:
            print(f"\n[ERROR] Failed to process article {article['article_id']}: {e}")
            self.repo.mark_analysis_failed(
                article['article_id'],
                str(e)
            )
            return None

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
            'batches': 0
        }

        print(f"\n[2/4] Processing articles...")
        print(f"      Model: {self.model_name}")
        print(f"      Batch size: {self.batch_size}")
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
                    result = self.process_article(article)

                    if result:
                        stats['successful'] += 1

                        # Save to database (unless dry run)
                        if not dry_run:
                            saved = self.repo.save_analysis(
                                response=result,
                                model_id=self.model_name,
                                prompt_version=self.prompt_version
                            )
                            if not saved:
                                print(f"\n[WARNING] Failed to save analysis for {article['article_id']}")
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
        print(f"      Success rate: {stats['successful']/stats['processed']*100:.1f}%")

        # Get updated stats
        print(f"\n[4/4] Fetching updated database statistics...")
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
