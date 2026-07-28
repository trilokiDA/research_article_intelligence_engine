#!/usr/bin/env python
"""
CLI for running the article summarization pipeline.
"""

import os
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from app.genai.pipeline import SummarizationPipeline
from app.genai.repository import ArticleRepository

# Load environment variables
load_dotenv()


def main():
    """Main entry point for the pipeline."""
    import argparse

    parser = argparse.ArgumentParser(
        description='Summarization pipeline for research articles',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process all pending articles
  python backend/scripts/run_summarization.py

  # Process only 10 articles
  python backend/scripts/run_summarization.py --limit 10

  # Dry run (don't save results)
  python backend/scripts/run_summarization.py --limit 5 --dry-run

  # Use a different model
  python backend/scripts/run_summarization.py --model llama-3.1-8b-instant --limit 20

  # Custom batch size
  python backend/scripts/run_summarization.py --batch-size 5

  # Show statistics only
  python backend/scripts/run_summarization.py --stats-only
        """
    )

    parser.add_argument(
        '--limit',
        type=int,
        help='Maximum number of articles to process (default: all pending)'
    )
    parser.add_argument(
        '--model',
        default='llama-3.3-70b-versatile',
        help='Groq model to use (default: llama-3.3-70b-versatile)'
    )
    parser.add_argument(
        '--batch-size',
        type=int,
        default=10,
        help='Number of articles per batch (default: 10)'
    )
    parser.add_argument(
        '--delay',
        type=float,
        default=1.0,
        help='Delay between batches in seconds (default: 1.0)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Process but don\'t save results (for testing)'
    )
    parser.add_argument(
        '--stats-only',
        action='store_true',
        help='Show statistics only, don\'t process'
    )

    args = parser.parse_args()

    # Check for API key
    if not os.getenv('GROQ_API_KEY') and not args.stats_only:
        print("\n[ERROR] GROQ_API_KEY not found in environment.")
        print("        Please set it in your .env file or environment variables.")
        print("\n        Get your API key from: https://console.groq.com/keys\n")
        return

    # Show stats only
    if args.stats_only:
        repo = ArticleRepository()
        stats = repo.get_analysis_stats()

        print("\n" + "="*80)
        print("DATABASE STATISTICS")
        print("="*80)
        print(f"Total articles:       {stats['total_articles']}")
        print(f"Analyzed:             {stats['analyzed_count']}")
        print(f"Pending:              {stats['pending_count']}")
        print(f"\nBy Status:")
        for status, count in sorted(stats['by_status'].items()):
            print(f"  {status:<30} {count:>5}")
        print(f"\nBy Category:")
        for category, count in sorted(stats['by_category'].items()):
            print(f"  {category:<30} {count:>5}")
        print(f"\nBy Sentiment:")
        for sentiment, count in sorted(stats['by_sentiment'].items()):
            print(f"  {sentiment:<30} {count:>5}")
        print("="*80 + "\n")
        return

    # Run pipeline
    pipeline = SummarizationPipeline(
        model_name=args.model,
        batch_size=args.batch_size,
        delay_between_batches=args.delay
    )

    try:
        stats = pipeline.run(
            limit=args.limit,
            dry_run=args.dry_run
        )

    except KeyboardInterrupt:
        print("\n\n[INFO] Pipeline interrupted by user. Exiting gracefully...")

    except Exception as e:
        print(f"\n\n[ERROR] Pipeline failed with error: {e}")
        raise


if __name__ == "__main__":
    main()
