"""
Script to check and display analysis_status statistics.

This script demonstrates the new analysis_status field in the articles table.
"""

import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

from app.db.database import get_db, get_stats, migrate_db


def display_analysis_status():
    """Display analysis status statistics."""
    print("=" * 60)
    print("ANALYSIS STATUS REPORT")
    print("=" * 60)

    # Run migration first to ensure analysis_status column exists
    print("\n[1] Running database migration...")
    migrate_db()

    # Get overall stats
    print("\n[2] Overall Statistics:")
    stats = get_stats()
    print(f"    Total articles: {stats['total_articles']}")
    print(f"    Analyzed articles: {stats['analyzed_articles']}")

    # Display analysis status breakdown
    if 'by_analysis_status' in stats:
        print(f"\n[3] Analysis Status Breakdown:")
        analysis_status = stats['by_analysis_status']
        for status, count in analysis_status.items():
            percentage = (count / stats['total_articles'] * 100) if stats['total_articles'] > 0 else 0
            print(f"    {status:15s}: {count:5d} ({percentage:.1f}%)")

    # Get pending articles count
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM articles
            WHERE analysis_status IN ('pending', 'failed')
        """)
        pending_count = cursor.fetchone()['count']

    print(f"\n[4] Articles Ready for Analysis:")
    print(f"    Pending/Failed: {pending_count}")

    # Sample some pending articles
    if pending_count > 0:
        print(f"\n[5] Sample Pending Articles (first 5):")
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT article_id, title, analysis_status
                FROM articles
                WHERE analysis_status IN ('pending', 'failed')
                LIMIT 5
            """)
            for row in cursor.fetchall():
                print(f"    - {row['article_id']}: {row['title'][:60]}...")
                print(f"      Status: {row['analysis_status']}")

    print("\n" + "=" * 60)
    print("Report complete!")
    print("=" * 60)


if __name__ == "__main__":
    display_analysis_status()
