#!/usr/bin/env python
"""
View ingested articles with all columns.
"""
import sys
import json
import csv
from pathlib import Path
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Add backend to path
sys.path.insert(0, 'backend')

from app.db.database import get_db


def view_articles(limit=10, source=None, format='table'):
    """
    View articles from database.

    Args:
        limit: Number of articles to show
        source: Filter by source (pubmed, crossref, google_scholar)
        format: Output format ('table', 'detailed', 'csv')
    """
    with get_db() as conn:
        # Build query
        query = "SELECT * FROM articles"
        params = []

        if source:
            query += " WHERE source = ?"
            params.append(source)

        query += " ORDER BY publication_date DESC, ingested_at DESC LIMIT ?"
        params.append(limit)

        # Execute
        cursor = conn.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()

        if not rows:
            print("\n[INFO] No articles found in database.")
            print("Run: python backend/ingest_cli.py topic <topic-name> --sources pubmed --max 10")
            return

        # Convert to list of dicts
        articles = [dict(row) for row in rows]

        print(f"\n{'='*80}")
        print(f"[DATABASE] Found {len(articles)} articles")
        print(f"{'='*80}\n")

        if format == 'csv':
            # Export to CSV
            csv_file = 'articles_export.csv'

            if articles:
                with open(csv_file, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=articles[0].keys())
                    writer.writeheader()
                    writer.writerows(articles)

                print(f"[OK] Exported {len(articles)} articles to {csv_file}")
            return

        elif format == 'table':
            # Table view - key columns only
            print(f"{'ID':<15} {'Title':<50} {'Journal':<25} {'Date':<12} {'Source':<10}")
            print("-" * 115)

            for article in articles:
                article_id = article['article_id'][:14]
                title = article['title'][:48] + '..' if len(article['title']) > 50 else article['title']
                journal = (article.get('journal', 'N/A')[:23] + '..') if article.get('journal') and len(article.get('journal', '')) > 25 else article.get('journal', 'N/A')
                pub_date = article.get('publication_date', 'N/A')[:10]
                source = article['source']

                print(f"{article_id:<15} {title:<50} {journal:<25} {pub_date:<12} {source:<10}")

        elif format == 'detailed':
            # Detailed view - one article at a time
            for i, article in enumerate(articles, 1):
                print(f"\n{'='*80}")
                print(f"[ARTICLE {i}/{len(articles)}]")
                print(f"{'='*80}")
                print(f"ID:               {article['article_id']}")
                print(f"Source:           {article['source']}")
                print(f"DOI:              {article.get('doi', 'N/A')}")
                print(f"Type:             {article.get('article_type', 'N/A')}")
                print(f"Status:           {article.get('ingestion_status', 'N/A')}")
                print(f"\nTitle:            {article['title']}")
                print(f"Journal:          {article.get('journal', 'N/A')}")
                print(f"Publication Date: {article.get('publication_date', 'N/A')}")
                print(f"Country:          {article.get('country', 'N/A')}")

                # Abstract
                abstract = article.get('abstract', '')
                if abstract:
                    print(f"\nAbstract:")
                    print(f"  {abstract[:300]}..." if len(abstract) > 300 else f"  {abstract}")

                # Authors
                authors_json = article.get('authors', '[]')
                try:
                    authors = json.loads(authors_json) if authors_json else []
                    if authors:
                        print(f"\nAuthors ({len(authors)}):")
                        for author in authors[:3]:  # Show first 3
                            name = author.get('name', 'Unknown')
                            affiliation = author.get('affiliation', 'N/A')
                            print(f"  - {name}")
                            if affiliation and affiliation != 'N/A':
                                print(f"    {affiliation[:80]}")
                        if len(authors) > 3:
                            print(f"  ... and {len(authors) - 3} more")
                except:
                    pass

                # Keywords
                keywords_json = article.get('keywords', '[]')
                try:
                    keywords = json.loads(keywords_json) if keywords_json else []
                    if keywords:
                        print(f"\nKeywords ({len(keywords)}):")
                        print(f"  {', '.join(keywords[:10])}")
                        if len(keywords) > 10:
                            print(f"  ... and {len(keywords) - 10} more")
                except:
                    pass

                # Metadata
                print(f"\nMetadata:")
                print(f"  URL:        {article.get('url', 'N/A')}")
                print(f"  Ingested:   {article.get('ingested_at', 'N/A')}")
                print(f"  Updated:    {article.get('updated_at', 'N/A')}")

                if i < len(articles):
                    input("\nPress Enter for next article...")

        print(f"\n{'='*80}\n")


def show_schema():
    """Show database schema."""
    with get_db() as conn:
        cursor = conn.cursor()

        # Get articles table schema
        cursor.execute("PRAGMA table_info(articles)")
        columns = cursor.fetchall()

        print(f"\n{'='*80}")
        print("[SCHEMA] Articles Table Columns")
        print(f"{'='*80}")
        print(f"{'Column':<25} {'Type':<15} {'Nullable':<10}")
        print("-" * 80)

        for col in columns:
            col_name = col[1]
            col_type = col[2]
            nullable = "NO" if col[3] else "YES"
            print(f"{col_name:<25} {col_type:<15} {nullable:<10}")

        print(f"{'='*80}\n")


def show_stats():
    """Show database statistics."""
    with get_db() as conn:
        cursor = conn.cursor()

        # Total count
        cursor.execute("SELECT COUNT(*) FROM articles")
        total = cursor.fetchone()[0]

        # By source
        cursor.execute("SELECT source, COUNT(*) FROM articles GROUP BY source")
        by_source = cursor.fetchall()

        # By status
        cursor.execute("SELECT ingestion_status, COUNT(*) FROM articles GROUP BY ingestion_status")
        by_status = cursor.fetchall()

        # By type
        cursor.execute("SELECT article_type, COUNT(*) FROM articles GROUP BY article_type")
        by_type = cursor.fetchall()

        # Date range
        cursor.execute("SELECT MIN(publication_date), MAX(publication_date) FROM articles")
        date_range = cursor.fetchone()

        print(f"\n{'='*80}")
        print("[STATISTICS] Database Summary")
        print(f"{'='*80}")
        print(f"Total Articles: {total}")

        if by_source:
            print(f"\nBy Source:")
            for source, count in by_source:
                print(f"  {source:<20} {count:>5}")

        if by_status:
            print(f"\nBy Status:")
            for status, count in by_status:
                print(f"  {status:<20} {count:>5}")

        if by_type:
            print(f"\nBy Type:")
            for atype, count in by_type:
                print(f"  {atype:<20} {count:>5}")

        print(f"\nPublication Date Range:")
        print(f"  From: {date_range[0] or 'N/A'}")
        print(f"  To:   {date_range[1] or 'N/A'}")

        print(f"{'='*80}\n")


def show_columns():
    """Show all available columns with sample data."""
    with get_db() as conn:
        cursor = conn.cursor()

        # Get one article
        cursor.execute("SELECT * FROM articles LIMIT 1")
        row = cursor.fetchone()

        if not row:
            print("\n[INFO] No articles in database yet.")
            return

        article = dict(row)

        print(f"\n{'='*80}")
        print("[COLUMNS] Available Columns (with sample data)")
        print(f"{'='*80}\n")

        for key, value in article.items():
            # Truncate long values
            if value and isinstance(value, str) and len(value) > 100:
                display_value = value[:100] + "..."
            else:
                display_value = value

            print(f"{key:<25} : {display_value}")

        print(f"\n{'='*80}\n")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description='View ingested articles',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Show statistics
  python view_data.py --stats

  # Show database schema
  python view_data.py --schema

  # Show all columns with sample data
  python view_data.py --columns

  # View 10 articles (table format)
  python view_data.py --limit 10

  # View detailed information
  python view_data.py --limit 5 --format detailed

  # Export to CSV
  python view_data.py --limit 100 --format csv

  # Filter by source
  python view_data.py --source pubmed --limit 20
        """
    )
    parser.add_argument('--limit', type=int, default=10, help='Number of articles to show (default: 10)')
    parser.add_argument('--source', choices=['pubmed', 'crossref', 'google_scholar'], help='Filter by source')
    parser.add_argument('--format', choices=['table', 'detailed', 'csv'], default='table',
                        help='Output format (default: table)')
    parser.add_argument('--schema', action='store_true', help='Show database schema')
    parser.add_argument('--stats', action='store_true', help='Show statistics')
    parser.add_argument('--columns', action='store_true', help='Show all available columns with sample data')

    args = parser.parse_args()

    if args.schema:
        show_schema()
    elif args.stats:
        show_stats()
    elif args.columns:
        show_columns()
    else:
        view_articles(limit=args.limit, source=args.source, format=args.format)
