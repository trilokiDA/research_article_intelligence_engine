#!/usr/bin/env python
"""
Command-line interface for article ingestion.

Usage:
    python ingest_cli.py search "tobacco harm reduction" --sources pubmed --max 50
    python ingest_cli.py stats
    python ingest_cli.py pending

Note: CrossRef is disabled as it doesn't provide abstracts. Only PubMed is active.
"""
import argparse
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Clear any existing NCBI env vars to force reload from .env
os.environ.pop('NCBI_EMAIL', None)
os.environ.pop('NCBI_API_KEY', None)

# Load environment variables from .env with override
load_dotenv(override=True)

# Add app to path
sys.path.insert(0, str(Path(__file__).parent))

from app.db.database import init_db, get_stats
from app.ingestion.orchestrator import IngestionOrchestrator
from app.config.query_manager import QueryManager


def cmd_search(args):
    """Search and ingest articles from external sources."""
    orchestrator = IngestionOrchestrator()

    # Build date range
    date_range = None
    if args.from_date and args.to_date:
        date_range = {'from': args.from_date, 'to': args.to_date}

    # Run ingestion
    results = orchestrator.ingest_from_query(
        query=args.query,
        sources=args.sources,
        max_per_source=args.max,
        date_range=date_range
    )

    return 0 if not results['errors'] else 1


def cmd_stats(args):
    """Show database statistics."""
    stats = get_stats()

    print("\n" + "="*60)
    print("[STATS] DATABASE STATISTICS")
    print("="*60)
    print(f"Total articles: {stats['total_articles']}")
    print(f"Analyzed: {stats['analyzed_articles']}")
    print(f"Pending analysis: {stats['total_articles'] - stats['analyzed_articles']}")

    if stats['by_status']:
        print(f"\nBy status:")
        for status, count in stats['by_status'].items():
            print(f"  {status}: {count}")

    if stats['by_source']:
        print(f"\nBy source:")
        for source, count in stats['by_source'].items():
            print(f"  {source}: {count}")

    print("="*60 + "\n")
    return 0


def cmd_pending(args):
    """Show articles pending GenAI analysis."""
    orchestrator = IngestionOrchestrator()
    pending = orchestrator.get_pending_articles(limit=args.limit)

    print("\n" + "="*60)
    print(f"[PENDING] ARTICLES AWAITING ANALYSIS ({len(pending)})")
    print("="*60)

    for i, article in enumerate(pending, 1):
        print(f"\n{i}. {article['article_id']}")
        print(f"   Title: {article['title'][:70]}...")
        print(f"   Journal: {article['journal']}")
        print(f"   Date: {article['publication_date']}")
        print(f"   Source: {article['source']}")

    print("\n" + "="*60 + "\n")
    return 0


def cmd_init(args):
    """Initialize database."""
    init_db()
    return 0


def cmd_topics(args):
    """List available predefined topic queries."""
    manager = QueryManager()
    manager.print_summary()
    return 0


def cmd_topic_search(args):
    """Search using predefined topic query."""
    manager = QueryManager()
    orchestrator = IngestionOrchestrator()

    # Get topic info
    topic_info = manager.get_topic_info(args.topic)
    if not topic_info:
        print(f"[ERROR] Unknown topic: {args.topic}")
        print(f"Available topics: {', '.join(manager.list_topics())}")
        return 1

    print(f"\n[TOPIC] {args.topic}")
    print(f"Description: {topic_info.get('description', 'N/A')}")
    print("="*60 + "\n")

    # Get queries for requested sources
    all_topic_queries = manager.get_all_queries_for_topic(args.topic)

    # Build date range
    date_range = None
    if args.from_date and args.to_date:
        date_range = {'from': args.from_date, 'to': args.to_date}

    results = {
        'total': 0,
        'by_source': {},
        'duplicates': 0,
        'errors': []
    }

    # Ingest from each source
    for source in args.sources:
        if source not in all_topic_queries:
            print(f"[SKIP] No {source} query defined for topic '{args.topic}'")
            continue

        query = all_topic_queries[source]
        print(f"\n[{source.upper()}] Using predefined query:")
        print(f"  {query[:100]}..." if len(query) > 100 else f"  {query}")
        print()

        # Run ingestion for this source
        source_results = orchestrator.ingest_from_query(
            query=query,
            sources=[source],
            max_per_source=args.max,
            date_range=date_range
        )

        # Aggregate results
        results['total'] += source_results['total']
        results['duplicates'] += source_results['duplicates']
        results['errors'].extend(source_results['errors'])
        results['by_source'][source] = source_results['by_source'].get(source, {})

    return 0 if not results['errors'] else 1


def main():
    parser = argparse.ArgumentParser(
        description='Article ingestion CLI for Tobacco Research Platform'
    )
    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # Init command
    init_parser = subparsers.add_parser('init', help='Initialize database')

    # Topics command
    topics_parser = subparsers.add_parser('topics', help='List available predefined topic queries')

    # Topic search command
    topic_search_parser = subparsers.add_parser('topic', help='Search using predefined topic query')
    topic_search_parser.add_argument(
        'topic',
        help='Topic name (use "topics" command to see available topics)'
    )
    topic_search_parser.add_argument(
        '--sources',
        nargs='+',
        choices=['pubmed', 'crossref', 'google_scholar'],
        default=['pubmed'],
        help='Sources to search (default: pubmed, CrossRef disabled - no abstracts)'
    )
    topic_search_parser.add_argument(
        '--max',
        type=int,
        default=100,
        help='Maximum results per source (default: 100)'
    )
    topic_search_parser.add_argument(
        '--from-date',
        help='Start date (YYYY-MM-DD)'
    )
    topic_search_parser.add_argument(
        '--to-date',
        help='End date (YYYY-MM-DD)'
    )

    # Search command (custom queries)
    search_parser = subparsers.add_parser('search', help='Search and ingest articles (custom query)')
    search_parser.add_argument('query', help='Search query')
    search_parser.add_argument(
        '--sources',
        nargs='+',
        choices=['pubmed', 'crossref', 'google_scholar'],
        default=['pubmed'],
        help='Sources to search (default: pubmed, CrossRef disabled - no abstracts)'
    )
    search_parser.add_argument(
        '--max',
        type=int,
        default=100,
        help='Maximum results per source (default: 100)'
    )
    search_parser.add_argument(
        '--from-date',
        help='Start date (YYYY-MM-DD)'
    )
    search_parser.add_argument(
        '--to-date',
        help='End date (YYYY-MM-DD)'
    )

    # Stats command
    stats_parser = subparsers.add_parser('stats', help='Show database statistics')

    # Pending command
    pending_parser = subparsers.add_parser('pending', help='Show pending articles')
    pending_parser.add_argument(
        '--limit',
        type=int,
        default=10,
        help='Number of articles to show (default: 10)'
    )

    # Parse arguments
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    # Run command
    if args.command == 'init':
        return cmd_init(args)
    elif args.command == 'topics':
        return cmd_topics(args)
    elif args.command == 'topic':
        return cmd_topic_search(args)
    elif args.command == 'search':
        return cmd_search(args)
    elif args.command == 'stats':
        return cmd_stats(args)
    elif args.command == 'pending':
        return cmd_pending(args)

    return 0


if __name__ == "__main__":
    sys.exit(main())
