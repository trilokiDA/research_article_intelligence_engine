"""
Database helper script for exploring and managing articles.db
Use this in your Jupyter notebook for easy database operations.
"""

import sqlite3
import pandas as pd
from pathlib import Path

# Database path
DB_PATH = Path("data/articles.db")


def get_connection():
    """Get database connection."""
    if not DB_PATH.exists():
        print(f"❌ Database not found at: {DB_PATH}")
        return None
    return sqlite3.connect(DB_PATH)


def view_all_articles(limit=10):
    """
    View all articles (limited to avoid overwhelming output).

    Args:
        limit: Number of records to show (default: 10)

    Returns:
        DataFrame with articles
    """
    conn = get_connection()
    if not conn:
        return None

    query = f"""
    SELECT id, article_id, source, title, journal, publication_date,
           SUBSTR(abstract, 1, 100) as abstract_preview
    FROM articles
    ORDER BY ingested_at DESC
    LIMIT {limit}
    """

    df = pd.read_sql_query(query, conn)
    conn.close()

    print(f"📊 Showing {len(df)} of total articles\n")
    return df


def get_stats():
    """Get database statistics."""
    conn = get_connection()
    if not conn:
        return None

    cursor = conn.cursor()

    # Total articles
    cursor.execute("SELECT COUNT(*) FROM articles")
    total = cursor.fetchone()[0]

    # By source
    cursor.execute("SELECT source, COUNT(*) FROM articles GROUP BY source")
    by_source = cursor.fetchall()

    # By status
    cursor.execute("SELECT ingestion_status, COUNT(*) FROM articles GROUP BY ingestion_status")
    by_status = cursor.fetchall()

    conn.close()

    print("📈 DATABASE STATISTICS")
    print("=" * 60)
    print(f"Total articles: {total}")
    print(f"\nBy source:")
    for source, count in by_source:
        print(f"  {source}: {count}")
    print(f"\nBy status:")
    for status, count in by_status:
        print(f"  {status}: {count}")
    print("=" * 60)

    return {
        'total': total,
        'by_source': dict(by_source),
        'by_status': dict(by_status)
    }


def view_by_source(source='pubmed', limit=10):
    """
    View articles from specific source.

    Args:
        source: 'pubmed', 'crossref', etc.
        limit: Number of records to show

    Returns:
        DataFrame with articles
    """
    conn = get_connection()
    if not conn:
        return None

    query = f"""
    SELECT id, article_id, source, title, journal, publication_date,
           SUBSTR(abstract, 1, 100) as abstract_preview
    FROM articles
    WHERE source = ?
    ORDER BY ingested_at DESC
    LIMIT {limit}
    """

    df = pd.read_sql_query(query, conn, params=(source,))
    conn.close()

    print(f"📊 {source.upper()} articles: {len(df)} shown\n")
    return df


def view_full_article(article_id):
    """
    View full details of a specific article.

    Args:
        article_id: The article_id or DOI

    Returns:
        Dictionary with full article details
    """
    conn = get_connection()
    if not conn:
        return None

    cursor = conn.cursor()
    cursor.execute("SELECT * FROM articles WHERE article_id = ?", (article_id,))

    row = cursor.fetchone()
    if not row:
        print(f"❌ Article not found: {article_id}")
        conn.close()
        return None

    columns = [description[0] for description in cursor.description]
    article = dict(zip(columns, row))

    conn.close()

    print("📄 ARTICLE DETAILS")
    print("=" * 60)
    for key, value in article.items():
        if key in ['abstract', 'authors', 'keywords']:
            print(f"{key}: {str(value)[:200]}...")
        else:
            print(f"{key}: {value}")
    print("=" * 60)

    return article


def search_articles(keyword, in_field='title', limit=20):
    """
    Search articles by keyword.

    Args:
        keyword: Search term
        in_field: Field to search in ('title', 'abstract', 'journal')
        limit: Number of results

    Returns:
        DataFrame with matching articles
    """
    conn = get_connection()
    if not conn:
        return None

    query = f"""
    SELECT id, article_id, source, title, journal, publication_date,
           SUBSTR(abstract, 1, 100) as abstract_preview
    FROM articles
    WHERE {in_field} LIKE ?
    ORDER BY publication_date DESC
    LIMIT {limit}
    """

    df = pd.read_sql_query(query, conn, params=(f'%{keyword}%',))
    conn.close()

    print(f"🔍 Found {len(df)} articles with '{keyword}' in {in_field}\n")
    return df


def delete_by_source(source, confirm=False):
    """
    Delete all articles from a specific source.

    Args:
        source: Source name ('pubmed', 'crossref', etc.)
        confirm: Must be True to actually delete (safety check)

    Returns:
        Number of deleted records
    """
    conn = get_connection()
    if not conn:
        return 0

    cursor = conn.cursor()

    # Count first
    cursor.execute("SELECT COUNT(*) FROM articles WHERE source = ?", (source,))
    count = cursor.fetchone()[0]

    if count == 0:
        print(f"ℹ️  No articles found for source: {source}")
        conn.close()
        return 0

    if not confirm:
        print(f"⚠️  WARNING: This will delete {count} articles from source '{source}'")
        print("⚠️  Set confirm=True to proceed")
        conn.close()
        return 0

    cursor.execute("DELETE FROM articles WHERE source = ?", (source,))
    conn.commit()
    deleted = cursor.rowcount

    conn.close()

    print(f"✅ Deleted {deleted} articles from source '{source}'")
    return deleted


def delete_by_article_id(article_id, confirm=False):
    """
    Delete a specific article by article_id.

    Args:
        article_id: The article_id or DOI
        confirm: Must be True to actually delete (safety check)

    Returns:
        True if deleted, False otherwise
    """
    conn = get_connection()
    if not conn:
        return False

    cursor = conn.cursor()

    # Check if exists
    cursor.execute("SELECT title FROM articles WHERE article_id = ?", (article_id,))
    row = cursor.fetchone()

    if not row:
        print(f"❌ Article not found: {article_id}")
        conn.close()
        return False

    if not confirm:
        print(f"⚠️  WARNING: This will delete article:")
        print(f"   {row[0][:80]}...")
        print("⚠️  Set confirm=True to proceed")
        conn.close()
        return False

    cursor.execute("DELETE FROM articles WHERE article_id = ?", (article_id,))
    conn.commit()

    conn.close()

    print(f"✅ Deleted article: {article_id}")
    return True


def delete_all(confirm=False):
    """
    Delete ALL articles from database.

    Args:
        confirm: Must be True to actually delete (safety check)

    Returns:
        Number of deleted records
    """
    conn = get_connection()
    if not conn:
        return 0

    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM articles")
    count = cursor.fetchone()[0]

    if count == 0:
        print("ℹ️  Database is already empty")
        conn.close()
        return 0

    if not confirm:
        print(f"⚠️  WARNING: This will delete ALL {count} articles!")
        print("⚠️  Set confirm=True to proceed")
        conn.close()
        return 0

    cursor.execute("DELETE FROM articles")
    conn.commit()
    deleted = cursor.rowcount

    conn.close()

    print(f"✅ Deleted all {deleted} articles from database")
    return deleted


def export_to_csv(filename='articles_export.csv', source=None):
    """
    Export articles to CSV file.

    Args:
        filename: Output CSV filename
        source: Optional - filter by source

    Returns:
        Path to exported file
    """
    conn = get_connection()
    if not conn:
        return None

    if source:
        query = "SELECT * FROM articles WHERE source = ?"
        df = pd.read_sql_query(query, conn, params=(source,))
    else:
        df = pd.read_sql_query("SELECT * FROM articles", conn)

    conn.close()

    df.to_csv(filename, index=False)
    print(f"✅ Exported {len(df)} articles to {filename}")

    return filename


# Quick reference for notebook
def help():
    """Print available functions."""
    print("""
📚 DATABASE HELPER FUNCTIONS
============================

VIEWING DATA:
  get_stats()                          - Show database statistics
  view_all_articles(limit=10)          - View recent articles
  view_by_source('pubmed', limit=10)   - View articles from specific source
  view_full_article('article_id')      - View full details of one article
  search_articles('keyword', in_field='title', limit=20)  - Search articles

DELETING DATA:
  delete_by_source('crossref', confirm=True)     - Delete all from a source
  delete_by_article_id('article_id', confirm=True)  - Delete specific article
  delete_all(confirm=True)                       - Delete ALL articles (careful!)

EXPORTING:
  export_to_csv('output.csv')          - Export all articles to CSV
  export_to_csv('output.csv', source='pubmed')  - Export specific source

EXAMPLES:
  # View CrossRef articles
  view_by_source('crossref', limit=20)

  # Delete all CrossRef articles
  delete_by_source('crossref', confirm=True)

  # Search for articles
  search_articles('reduction', in_field='title')

  # Export PubMed only
  export_to_csv('pubmed_only.csv', source='pubmed')
""")


if __name__ == "__main__":
    help()
