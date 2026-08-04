"""
Repository layer for article database operations.
"""

import sqlite3
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path
from contextlib import contextmanager

import sys
from pathlib import Path as PathLib

from .schemas import Response

# Handle both import contexts: app.genai and genai
try:
    from ..db.database import get_db, DATABASE_PATH
except ImportError:
    # When imported as 'genai' package, add app directory to path
    _current_dir = PathLib(__file__).parent
    _app_dir = _current_dir.parent
    if str(_app_dir) not in sys.path:
        sys.path.insert(0, str(_app_dir))
    from db.database import get_db, DATABASE_PATH


class ArticleRepository:
    """
    Repository for managing articles and their analysis.
    """

    @staticmethod
    def get_article_by_id(article_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a single article by article_id.

        Args:
            article_id: Article identifier (e.g., PMID12345)

        Returns:
            Article dictionary or None if not found
        """
        with get_db() as conn:
            cursor = conn.cursor()

            query = """
                SELECT
                    a.id,
                    a.article_id,
                    a.title,
                    a.journal,
                    a.publication_date,
                    a.abstract,
                    a.source,
                    a.doi
                FROM articles a
                WHERE a.article_id = ?
            """

            cursor.execute(query, (article_id,))
            row = cursor.fetchone()

            if row:
                return dict(row)
            return None

    @staticmethod
    def get_articles_pending_analysis(
        limit: Optional[int] = None,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get articles that need summarization (where summary is NULL in article_analysis).

        Args:
            limit: Maximum number of articles to fetch
            offset: Number of records to skip

        Returns:
            List of article dictionaries
        """
        with get_db() as conn:
            cursor = conn.cursor()

            # Get articles where:
            # 1. No analysis record exists, OR
            # 2. Analysis record exists but summary is NULL or empty, OR
            # 3. Analysis status is 'pending' or 'failed'
            query = """
                SELECT
                    a.id,
                    a.article_id,
                    a.title,
                    a.journal,
                    a.publication_date,
                    a.abstract,
                    a.source,
                    a.doi,
                    aa.analysis_status
                FROM articles a
                LEFT JOIN article_analysis aa ON a.article_id = aa.article_id
                WHERE
                    aa.article_id IS NULL
                    OR aa.summary IS NULL
                    OR aa.summary = ''
                    OR aa.analysis_status IN ('pending', 'failed')
                ORDER BY a.ingested_at DESC
            """

            params = []
            if limit:
                query += " LIMIT ? OFFSET ?"
                params.extend([limit, offset])

            cursor.execute(query, params)
            rows = cursor.fetchall()

            return [dict(row) for row in rows]

    @staticmethod
    def count_articles_pending_analysis() -> int:
        """
        Count articles that need summarization.

        Returns:
            Count of pending articles
        """
        with get_db() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT COUNT(*) as count
                FROM articles a
                LEFT JOIN article_analysis aa ON a.article_id = aa.article_id
                WHERE
                    aa.article_id IS NULL
                    OR aa.summary IS NULL
                    OR aa.summary = ''
                    OR aa.analysis_status IN ('pending', 'failed')
            """)

            return cursor.fetchone()['count']

    @staticmethod
    def save_analysis(
        response: Response,
        model_id: str,
        prompt_version: str = "v1"
    ) -> bool:
        """
        Save or update article analysis results.

        Args:
            response: Response object from summarization
            model_id: Model identifier used for analysis
            prompt_version: Version of the prompt used

        Returns:
            True if successful, False otherwise
        """
        with get_db() as conn:
            cursor = conn.cursor()

            try:
                # Check if analysis record exists
                cursor.execute(
                    "SELECT id FROM article_analysis WHERE article_id = ?",
                    (response.articleID,)
                )
                existing = cursor.fetchone()

                # Convert entities list to JSON string
                entities_json = json.dumps([e.value for e in response.entity])

                if existing:
                    # Update existing record
                    cursor.execute("""
                        UPDATE article_analysis
                        SET
                            subject = ?,
                            category = ?,
                            summary = ?,
                            entities = ?,
                            sentiment = ?,
                            industry_affiliation = ?,
                            model_id = ?,
                            prompt_version = ?,
                            analyzed_at = ?,
                            analysis_status = 'completed'
                        WHERE article_id = ?
                    """, (
                        response.subject.value,
                        response.category.value,
                        response.summary,
                        entities_json,
                        response.sentiment.value,
                        response.industry_affiliation,
                        model_id,
                        prompt_version,
                        datetime.now().isoformat(),
                        response.articleID
                    ))
                else:
                    # Insert new record
                    cursor.execute("""
                        INSERT INTO article_analysis (
                            id, article_id, subject, category, summary,
                            entities, sentiment, industry_affiliation,
                            model_id, prompt_version, analyzed_at, analysis_status
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'completed')
                    """, (
                        f"analysis_{response.articleID}",
                        response.articleID,
                        response.subject.value,
                        response.category.value,
                        response.summary,
                        entities_json,
                        response.sentiment.value,
                        response.industry_affiliation,
                        model_id,
                        prompt_version,
                        datetime.now().isoformat()
                    ))

                conn.commit()
                return True

            except Exception as e:
                print(f"Error saving analysis for {response.articleID}: {e}")
                conn.rollback()
                return False

    @staticmethod
    def mark_analysis_failed(
        article_id: str,
        error_message: str
    ) -> bool:
        """
        Mark an article analysis as failed.

        Args:
            article_id: Article identifier
            error_message: Error description

        Returns:
            True if successful, False otherwise
        """
        with get_db() as conn:
            cursor = conn.cursor()

            try:
                cursor.execute("""
                    INSERT OR REPLACE INTO article_analysis (
                        id, article_id, analysis_status, analyzed_at
                    ) VALUES (?, ?, 'failed', ?)
                """, (
                    f"analysis_{article_id}",
                    article_id,
                    datetime.now().isoformat()
                ))

                conn.commit()
                return True

            except Exception as e:
                print(f"Error marking analysis as failed for {article_id}: {e}")
                conn.rollback()
                return False

    @staticmethod
    def get_analysis_stats() -> Dict[str, Any]:
        """
        Get statistics about article analysis.

        Returns:
            Dictionary with analysis statistics
        """
        with get_db() as conn:
            cursor = conn.cursor()

            # Total articles
            cursor.execute("SELECT COUNT(*) as count FROM articles")
            total_articles = cursor.fetchone()['count']

            # Analyzed articles (with summary)
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM article_analysis
                WHERE summary IS NOT NULL AND summary != ''
            """)
            analyzed_count = cursor.fetchone()['count']

            # By status
            cursor.execute("""
                SELECT analysis_status, COUNT(*) as count
                FROM article_analysis
                GROUP BY analysis_status
            """)
            status_counts = {row['analysis_status']: row['count']
                           for row in cursor.fetchall()}

            # By category
            cursor.execute("""
                SELECT category, COUNT(*) as count
                FROM article_analysis
                WHERE category IS NOT NULL
                GROUP BY category
            """)
            category_counts = {row['category']: row['count']
                             for row in cursor.fetchall()}

            # By sentiment
            cursor.execute("""
                SELECT sentiment, COUNT(*) as count
                FROM article_analysis
                WHERE sentiment IS NOT NULL
                GROUP BY sentiment
            """)
            sentiment_counts = {row['sentiment']: row['count']
                              for row in cursor.fetchall()}

            # Pending count
            pending_count = ArticleRepository.count_articles_pending_analysis()

            return {
                'total_articles': total_articles,
                'analyzed_count': analyzed_count,
                'pending_count': pending_count,
                'by_status': status_counts,
                'by_category': category_counts,
                'by_sentiment': sentiment_counts
            }


if __name__ == "__main__":
    # Test repository functions
    print("Testing ArticleRepository...")

    # Get pending count
    pending = ArticleRepository.count_articles_pending_analysis()
    print(f"\nArticles pending analysis: {pending}")

    # Get some pending articles
    if pending > 0:
        articles = ArticleRepository.get_articles_pending_analysis(limit=3)
        print(f"\nFirst 3 pending articles:")
        for article in articles:
            print(f"  - {article['article_id']}: {article['title'][:60]}...")

    # Get stats
    stats = ArticleRepository.get_analysis_stats()
    print(f"\nAnalysis Statistics:")
    print(f"  Total articles: {stats['total_articles']}")
    print(f"  Analyzed: {stats['analyzed_count']}")
    print(f"  Pending: {stats['pending_count']}")
    print(f"  By status: {stats['by_status']}")
