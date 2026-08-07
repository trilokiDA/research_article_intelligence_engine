"""
Database connection and session management.
"""
import sqlite3
import json
from contextlib import contextmanager
from pathlib import Path
from typing import Generator

# Database path
DB_DIR = Path(__file__).parent.parent.parent.parent / "data"
DB_DIR.mkdir(exist_ok=True)
DATABASE_PATH = DB_DIR / "articles.db"


@contextmanager
def get_db() -> Generator[sqlite3.Connection, None, None]:
    """
    Get database connection with context manager.

    Usage:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM articles")
    """
    conn = sqlite3.connect(str(DATABASE_PATH))
    conn.row_factory = sqlite3.Row  # Return rows as dict-like objects
    try:
        yield conn
    finally:
        conn.close()


def init_db():
    """
    Initialize database with schema.
    Creates tables if they don't exist.
    """
    conn = sqlite3.connect(str(DATABASE_PATH))

    # Create articles table (ingestion data)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS articles (
            id TEXT PRIMARY KEY,
            article_id TEXT UNIQUE NOT NULL,
            source TEXT NOT NULL,
            source_metadata_id TEXT,
            doi TEXT,
            url TEXT,
            ingestion_status TEXT DEFAULT 'pending',
            analysis_status TEXT DEFAULT 'pending',
            article_type TEXT,
            title TEXT NOT NULL,
            abstract TEXT,
            journal TEXT,
            keywords TEXT,
            authors TEXT,
            publication_date TEXT,
            country TEXT,
            full_text TEXT,
            figures TEXT,
            article_references TEXT,
            ingested_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Create indexes for articles
    conn.execute("CREATE INDEX IF NOT EXISTS idx_articles_source ON articles(source)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_articles_doi ON articles(doi)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_articles_date ON articles(publication_date)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_articles_status ON articles(ingestion_status)")

    # Index for analysis_status will be created by migrate_db() if column exists
    # or when the table is first created with the column

    # Create article_analysis table (GenAI results)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS article_analysis (
            id TEXT PRIMARY KEY,
            article_id TEXT UNIQUE NOT NULL,
            subject TEXT,
            category TEXT,
            summary TEXT,
            entities TEXT,
            sentiment TEXT,
            industry_affiliation TEXT,
            coi_details TEXT,
            author_affiliations TEXT,
            citation_string TEXT,
            confidence_scores TEXT,
            fact_check_results TEXT,
            model_id TEXT,
            prompt_used TEXT,
            prompt_version TEXT,
            analyzed_at DATETIME,
            analysis_status TEXT DEFAULT 'pending',
            fact_check_status TEXT,
            evaluation_score REAL,
            evaluation_metadata TEXT,
            stage TEXT,
            attempt INTEGER DEFAULT 1,
            loaded_at DATETIME,
            FOREIGN KEY (article_id) REFERENCES articles(id) ON DELETE CASCADE
        )
    """)

    # Create indexes for article_analysis
    conn.execute("CREATE INDEX IF NOT EXISTS idx_analysis_status ON article_analysis(analysis_status)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_analysis_sentiment ON article_analysis(sentiment)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_analysis_category ON article_analysis(category)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_analysis_stage ON article_analysis(stage)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_analysis_score ON article_analysis(evaluation_score)")

    # Create full-text search virtual table
    conn.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS articles_fts USING fts5(
            title, abstract, content='articles', content_rowid='rowid'
        )
    """)

    conn.commit()
    conn.close()

    print(f"[OK] Database initialized at: {DATABASE_PATH}")
    print(f"     Tables: articles, article_analysis, articles_fts")


def migrate_db():
    """
    Migrate existing database to add new Stage 5 columns.
    Safe to run on both new and existing databases.
    """
    conn = sqlite3.connect(str(DATABASE_PATH))
    cursor = conn.cursor()

    # Check if new columns exist
    cursor.execute("PRAGMA table_info(article_analysis)")
    columns = {row[1] for row in cursor.fetchall()}

    migrations_applied = []

    # Add evaluation_score column if missing
    if 'evaluation_score' not in columns:
        try:
            conn.execute("ALTER TABLE article_analysis ADD COLUMN evaluation_score REAL")
            migrations_applied.append("evaluation_score")
        except Exception as e:
            print(f"[WARNING] Could not add evaluation_score: {e}")

    # Add evaluation_metadata column if missing
    if 'evaluation_metadata' not in columns:
        try:
            conn.execute("ALTER TABLE article_analysis ADD COLUMN evaluation_metadata TEXT")
            migrations_applied.append("evaluation_metadata")
        except Exception as e:
            print(f"[WARNING] Could not add evaluation_metadata: {e}")

    # Add stage column if missing
    if 'stage' not in columns:
        try:
            conn.execute("ALTER TABLE article_analysis ADD COLUMN stage TEXT")
            migrations_applied.append("stage")
        except Exception as e:
            print(f"[WARNING] Could not add stage: {e}")

    # Add attempt column if missing
    if 'attempt' not in columns:
        try:
            conn.execute("ALTER TABLE article_analysis ADD COLUMN attempt INTEGER DEFAULT 1")
            migrations_applied.append("attempt")
        except Exception as e:
            print(f"[WARNING] Could not add attempt: {e}")

    # Add loaded_at column if missing
    if 'loaded_at' not in columns:
        try:
            conn.execute("ALTER TABLE article_analysis ADD COLUMN loaded_at DATETIME")
            migrations_applied.append("loaded_at")
        except Exception as e:
            print(f"[WARNING] Could not add loaded_at: {e}")

    # Create new indexes if they don't exist
    try:
        conn.execute("CREATE INDEX IF NOT EXISTS idx_analysis_stage ON article_analysis(stage)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_analysis_score ON article_analysis(evaluation_score)")
    except Exception as e:
        print(f"[WARNING] Could not create indexes: {e}")

    # Add analysis_status column to articles table if missing
    cursor.execute("PRAGMA table_info(articles)")
    article_columns = {row[1] for row in cursor.fetchall()}

    if 'analysis_status' not in article_columns:
        try:
            conn.execute("ALTER TABLE articles ADD COLUMN analysis_status TEXT DEFAULT 'pending'")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_articles_analysis_status ON articles(analysis_status)")
            migrations_applied.append("analysis_status")

            # Update existing records: mark articles with analysis as 'analyzed'
            conn.execute("""
                UPDATE articles
                SET analysis_status = 'analyzed'
                WHERE id IN (SELECT article_id FROM article_analysis)
            """)
            updated_count = cursor.rowcount
            print(f"[OK] Marked {updated_count} existing articles as 'analyzed'")
        except Exception as e:
            print(f"[WARNING] Could not add analysis_status: {e}")

    conn.commit()
    conn.close()

    if migrations_applied:
        print(f"[OK] Database migrated. Added columns: {', '.join(migrations_applied)}")
    else:
        print(f"[OK] Database schema is up to date")

    return migrations_applied


def get_stats():
    """Get database statistics."""
    with get_db() as conn:
        cursor = conn.cursor()

        # Count articles
        cursor.execute("SELECT COUNT(*) as count FROM articles")
        article_count = cursor.fetchone()['count']

        # Count by status
        cursor.execute("""
            SELECT ingestion_status, COUNT(*) as count
            FROM articles
            GROUP BY ingestion_status
        """)
        status_counts = {row['ingestion_status']: row['count'] for row in cursor.fetchall()}

        # Count by source
        cursor.execute("""
            SELECT source, COUNT(*) as count
            FROM articles
            GROUP BY source
        """)
        source_counts = {row['source']: row['count'] for row in cursor.fetchall()}

        # Count analyzed
        cursor.execute("SELECT COUNT(*) as count FROM article_analysis")
        analyzed_count = cursor.fetchone()['count']

        # Count by stage (Stage 5 addition)
        cursor.execute("""
            SELECT stage, COUNT(*) as count
            FROM article_analysis
            WHERE stage IS NOT NULL
            GROUP BY stage
        """)
        stage_counts = {row['stage']: row['count'] for row in cursor.fetchall()}

        # Count by analysis_status
        cursor.execute("""
            SELECT analysis_status, COUNT(*) as count
            FROM articles
            GROUP BY analysis_status
        """)
        analysis_status_counts = {row['analysis_status']: row['count'] for row in cursor.fetchall()}

        return {
            'total_articles': article_count,
            'analyzed_articles': analyzed_count,
            'by_status': status_counts,
            'by_source': source_counts,
            'by_stage': stage_counts,
            'by_analysis_status': analysis_status_counts
        }


if __name__ == "__main__":
    init_db()
    migrate_db()
    stats = get_stats()
    print(f"\n[STATS] Database Statistics:")
    print(f"        Total articles: {stats['total_articles']}")
    print(f"        Analyzed: {stats['analyzed_articles']}")
    print(f"        By status: {stats['by_status']}")
    print(f"        By source: {stats['by_source']}")
    if 'by_analysis_status' in stats:
        print(f"        By analysis status: {stats['by_analysis_status']}")
