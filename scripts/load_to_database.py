"""
Stage 5: Load approved analyses to article_analysis table.

This CLI script loads approved GenAI analyses from JSON files into the database.

Usage:
    # Load all approved files
    python scripts/load_to_database.py

    # Load specific article
    python scripts/load_to_database.py --article-id PMID42396759

    # Dry run (validate without committing)
    python scripts/load_to_database.py --dry-run

    # Load and archive source files
    python scripts/load_to_database.py --archive

    # Load with limit
    python scripts/load_to_database.py --limit 100

    # Migrate database schema first
    python scripts/load_to_database.py --migrate-only
"""

import argparse
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app.genai.db_loader import AnalysisDatabaseLoader
from app.db.database import migrate_db, get_stats, DATABASE_PATH


def print_header():
    """Print script header."""
    print("=" * 70)
    print("Stage 5: Database Load - Load Approved Analyses")
    print("=" * 70)


def print_database_stats():
    """Print current database statistics."""
    print("\n[DATABASE STATS - BEFORE]")
    stats = get_stats()
    print(f"  Total articles: {stats['total_articles']}")
    print(f"  Analyzed articles: {stats['analyzed_articles']}")

    if stats.get('by_stage'):
        print(f"  By stage:")
        for stage, count in stats['by_stage'].items():
            print(f"    - {stage}: {count}")
    else:
        print(f"  By stage: (no data)")

    print(f"  Database: {DATABASE_PATH}")


def main():
    parser = argparse.ArgumentParser(
        description="Load approved GenAI analyses to article_analysis table",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Load all approved files
  python scripts/load_to_database.py

  # Load specific articles
  python scripts/load_to_database.py --article-id PMID001 PMID002

  # Dry run (validate only)
  python scripts/load_to_database.py --dry-run

  # Load and archive
  python scripts/load_to_database.py --archive --limit 10

  # Migrate schema only
  python scripts/load_to_database.py --migrate-only
        """
    )

    parser.add_argument(
        '--article-id',
        nargs='+',
        help='Specific article IDs to load (e.g., PMID001 PMID002)'
    )

    parser.add_argument(
        '--limit',
        type=int,
        help='Maximum number of files to load'
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Validate files without committing to database'
    )

    parser.add_argument(
        '--archive',
        action='store_true',
        help='Move loaded files to archive directory (data/analysis/loaded/)'
    )

    parser.add_argument(
        '--source',
        default='approved',
        choices=['approved', 'rejected'],
        help='Source directory to load from (default: approved)'
    )

    parser.add_argument(
        '--migrate-only',
        action='store_true',
        help='Only migrate database schema, do not load files'
    )

    parser.add_argument(
        '--stats',
        action='store_true',
        help='Show database statistics and exit'
    )

    args = parser.parse_args()

    print_header()

    # Show stats and exit if requested
    if args.stats:
        print_database_stats()
        return 0

    # Migrate database schema
    print("\n[STEP 1] Migrating database schema...")
    migrations = migrate_db()

    if args.migrate_only:
        print("\n[OK] Database migration complete. Exiting.")
        return 0

    # Show database stats before loading
    print_database_stats()

    # Initialize loader
    print("\n[STEP 2] Initializing database loader...")
    loader = AnalysisDatabaseLoader()

    # Count available files
    approved_files = list(loader.approved_dir.glob("*.json"))
    print(f"  Found {len(approved_files)} approved files")

    if not approved_files:
        print("\n[WARNING] No approved files found. Run Stage 3 evaluation first.")
        print(f"  Expected directory: {loader.approved_dir}")
        return 1

    # Show dry run notice
    if args.dry_run:
        print("\n[DRY RUN MODE] Validating files without committing to database")

    # Load files
    print("\n[STEP 3] Loading files to database...")
    if args.article_id:
        print(f"  Target articles: {', '.join(args.article_id)}")
    if args.limit:
        print(f"  Limit: {args.limit} files")
    if args.archive:
        print(f"  Archive: Enabled (files will be moved to {loader.archive_dir})")

    stats = loader.load_approved_files(
        article_ids=args.article_id,
        limit=args.limit,
        dry_run=args.dry_run,
        archive=args.archive
    )

    # Print summary
    print(loader.get_load_summary())

    # Show database stats after loading
    if not args.dry_run:
        print("\n[DATABASE STATS - AFTER]")
        stats_after = get_stats()
        print(f"  Total articles: {stats_after['total_articles']}")
        print(f"  Analyzed articles: {stats_after['analyzed_articles']}")

        if stats_after.get('by_stage'):
            print(f"  By stage:")
            for stage, count in stats_after['by_stage'].items():
                print(f"    - {stage}: {count}")

        print(f"\n  Change: +{stats_after['analyzed_articles'] - get_stats()['analyzed_articles'] + stats['loaded']} analyzed articles")

    # Return status
    if stats['errors'] > 0:
        print("\n[WARNING] Completed with errors. See error details above.")
        return 1
    else:
        print("\n[SUCCESS] All files loaded successfully!")
        return 0


if __name__ == "__main__":
    sys.exit(main())
