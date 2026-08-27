"""
One-time migration script to load existing rejected articles into the database.

This script:
1. Reads all JSON files from data/analysis/rejected/
2. Loads them into the article_analysis table with status='rejected'
3. Updates the articles table to mark them as rejected
4. Optionally archives the loaded files

Usage:
    # Dry run (preview what will be loaded)
    python scripts/migrate_rejected_articles.py --dry-run

    # Load rejected articles to database
    python scripts/migrate_rejected_articles.py

    # Load and archive source files
    python scripts/migrate_rejected_articles.py --archive
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
    print("Rejected Articles Migration - Load Existing Rejected Articles")
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

    # Check for rejected articles
    from app.db.database import get_db
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) as count FROM article_analysis WHERE analysis_status = 'rejected'")
        rejected_count = cursor.fetchone()['count']
        print(f"  Rejected articles in DB: {rejected_count}")

    print(f"  Database: {DATABASE_PATH}")


def main():
    parser = argparse.ArgumentParser(
        description="One-time migration: Load existing rejected articles to database",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Preview what will be loaded (no changes)
  python scripts/migrate_rejected_articles.py --dry-run

  # Load all rejected files
  python scripts/migrate_rejected_articles.py

  # Load and archive source files
  python scripts/migrate_rejected_articles.py --archive
        """
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Preview files without committing to database'
    )

    parser.add_argument(
        '--archive',
        action='store_true',
        help='Move loaded files to archive directory (data/analysis/loaded/)'
    )

    parser.add_argument(
        '--limit',
        type=int,
        help='Maximum number of files to load (for testing)'
    )

    args = parser.parse_args()

    print_header()

    # Migrate database schema first
    print("\n[STEP 1] Migrating database schema...")
    migrations = migrate_db()
    if 'rejection_reason' not in migrations and migrations:
        print("  ✓ Schema already includes rejection_reason column")

    # Show database stats before loading
    print_database_stats()

    # Initialize loader
    print("\n[STEP 2] Initializing database loader...")
    loader = AnalysisDatabaseLoader()

    # Count available rejected files
    rejected_files = list(loader.rejected_dir.glob("*.json"))
    print(f"  Found {len(rejected_files)} rejected files in {loader.rejected_dir}")

    if not rejected_files:
        print("\n[INFO] No rejected files found. Nothing to migrate.")
        return 0

    # Show dry run notice
    if args.dry_run:
        print("\n[DRY RUN MODE] Validating files without committing to database")

    # Load files
    print("\n[STEP 3] Loading rejected files to database...")
    if args.limit:
        print(f"  Limit: {args.limit} files")
    if args.archive:
        print(f"  Archive: Enabled (files will be moved to {loader.archive_dir})")

    stats = loader.load_rejected_files(
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

        # Check rejected count
        from app.db.database import get_db
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) as count FROM article_analysis WHERE analysis_status = 'rejected'")
            rejected_count = cursor.fetchone()['count']
            print(f"  Rejected articles in DB: {rejected_count}")

        if stats_after.get('by_stage'):
            print(f"  By stage:")
            for stage, count in stats_after['by_stage'].items():
                print(f"    - {stage}: {count}")

        print(f"\n  Change: +{stats['loaded']} rejected articles loaded")

    # Return status
    if stats['errors'] > 0:
        print("\n[WARNING] Completed with errors. See error details above.")
        return 1
    else:
        print("\n[SUCCESS] All rejected articles migrated successfully!")
        if not args.dry_run:
            print(f"\n[NEXT STEPS]")
            print(f"  - View rejected articles in Streamlit: filter by 'Analysis Status' = 'rejected'")
            print(f"  - Check rejection reasons in the dashboard")
            print(f"  - Review rejection patterns to improve the pipeline")
        return 0


if __name__ == "__main__":
    sys.exit(main())
