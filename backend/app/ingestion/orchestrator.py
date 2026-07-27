"""
Ingestion orchestrator.
Coordinates multi-source article ingestion and storage.
"""
from typing import List, Dict, Optional
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.ingestion.pubmed_connector import PubMedConnector
from app.ingestion.crossref_connector import CrossrefConnector
from app.ingestion.normalizer import DataNormalizer
from app.db.database import get_db
import json


class IngestionOrchestrator:
    """
    Orchestrate multi-source article ingestion.

    Features:
    - Fetch from PubMed, Crossref, Google Scholar
    - Normalize data to unified schema
    - Store in database
    - Handle duplicates
    - Track statistics
    """

    def __init__(self):
        """Initialize orchestrator with all connectors."""
        self.pubmed = PubMedConnector()
        self.crossref = CrossrefConnector()
        self.normalizer = DataNormalizer()

        print("[OK] Ingestion orchestrator initialized")

    def ingest_from_query(
        self,
        query: str,
        sources: List[str] = ['pubmed', 'crossref'],
        max_per_source: int = 100,
        date_range: Optional[Dict] = None
    ) -> Dict:
        """
        Ingest articles from multiple sources based on query.

        Args:
            query: Search query (e.g., "tobacco harm reduction")
            sources: List of sources ('pubmed', 'crossref', 'google_scholar')
            max_per_source: Maximum results per source
            date_range: Date range dict with 'from' and 'to' keys (format: YYYY-MM-DD)

        Returns:
            Summary dictionary with statistics

        Example:
            >>> orchestrator = IngestionOrchestrator()
            >>> results = orchestrator.ingest_from_query(
            ...     query="electronic cigarettes youth",
            ...     sources=['pubmed', 'crossref'],
            ...     max_per_source=50,
            ...     date_range={'from': '2024-01-01', 'to': '2024-12-31'}
            ... )
        """
        print(f"\n{'='*60}")
        print(f"[START] Starting ingestion")
        print(f"   Query: '{query}'")
        print(f"   Sources: {', '.join(sources)}")
        print(f"   Max per source: {max_per_source}")
        if date_range:
            print(f"   Date range: {date_range.get('from')} to {date_range.get('to')}")
        print(f"{'='*60}\n")

        results = {
            'total': 0,
            'by_source': {},
            'duplicates': 0,
            'errors': []
        }

        for source in sources:
            print(f"\n[SOURCE] Processing source: {source.upper()}")
            print("-" * 60)

            try:
                if source == 'pubmed':
                    raw_articles = self._fetch_from_pubmed(query, max_per_source, date_range)
                elif source == 'crossref':
                    raw_articles = self._fetch_from_crossref(query, max_per_source, date_range)
                elif source == 'google_scholar':
                    print("[WARN]  Google Scholar connector not implemented yet")
                    raw_articles = []
                else:
                    print(f"[WARN]  Unknown source: {source}")
                    continue

                # Store articles
                stored, duplicates, errors = self._store_articles(raw_articles)

                results['by_source'][source] = {
                    'fetched': len(raw_articles),
                    'stored': stored,
                    'duplicates': duplicates,
                    'errors': errors
                }
                results['total'] += stored
                results['duplicates'] += duplicates

                print(f"[OK] {source.upper()} complete:")
                print(f"  Fetched: {len(raw_articles)}")
                print(f"  Stored: {stored}")
                print(f"  Duplicates: {duplicates}")
                print(f"  Errors: {errors}")

            except Exception as e:
                error_msg = f"{source}: {str(e)}"
                results['errors'].append(error_msg)
                print(f"[ERROR] Error with {source}: {e}")

        # Print summary
        print(f"\n{'='*60}")
        print(f"[DONE] INGESTION COMPLETE")
        print(f"{'='*60}")
        print(f"Total articles stored: {results['total']}")
        print(f"Duplicates skipped: {results['duplicates']}")
        if results['errors']:
            print(f"Errors: {len(results['errors'])}")
        print(f"\nBy source:")
        for source, stats in results['by_source'].items():
            print(f"  {source}: {stats['stored']} stored, {stats['duplicates']} duplicates")
        print(f"{'='*60}\n")

        return results

    def _fetch_from_pubmed(
        self,
        query: str,
        max_results: int,
        date_range: Optional[Dict]
    ) -> List[Dict]:
        """Fetch articles from PubMed."""
        # Convert date format for PubMed (YYYY/MM/DD)
        start_date = None
        end_date = None
        if date_range:
            start_date = date_range.get('from', '').replace('-', '/')
            end_date = date_range.get('to', '').replace('-', '/')

        # Search PubMed
        pmids = self.pubmed.search_articles(
            query=query,
            max_results=max_results,
            start_date=start_date,
            end_date=end_date
        )

        # Fetch details
        if pmids:
            return self.pubmed.fetch_article_details(pmids)

        return []

    def _fetch_from_crossref(
        self,
        query: str,
        max_results: int,
        date_range: Optional[Dict]
    ) -> List[Dict]:
        """Fetch articles from Crossref."""
        filter_params = {}
        if date_range:
            filter_params['from-pub-date'] = date_range.get('from', '')
            filter_params['until-pub-date'] = date_range.get('to', '')

        return self.crossref.search_articles(
            query=query,
            max_results=max_results,
            filter_params=filter_params if filter_params else None
        )

    def _store_articles(self, raw_articles: List[Dict]) -> tuple[int, int, int]:
        """
        Store articles in database.

        Args:
            raw_articles: List of raw article dictionaries

        Returns:
            Tuple of (stored_count, duplicate_count, error_count)
        """
        if not raw_articles:
            return 0, 0, 0

        stored = 0
        duplicates = 0
        errors = 0

        with get_db() as conn:
            cursor = conn.cursor()

            for raw in raw_articles:
                try:
                    # Normalize
                    normalized = self.normalizer.normalize(raw)

                    # Validate
                    if not self.normalizer.validate(normalized):
                        errors += 1
                        continue

                    # Check for duplicate
                    cursor.execute(
                        "SELECT id FROM articles WHERE article_id = ?",
                        (normalized['article_id'],)
                    )
                    if cursor.fetchone():
                        duplicates += 1
                        continue

                    # Insert
                    cursor.execute("""
                        INSERT INTO articles (
                            id, article_id, source, source_metadata_id, doi, url,
                            ingestion_status, article_type, title, abstract, journal,
                            keywords, authors, publication_date, country,
                            full_text, figures, article_references, ingested_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        normalized['id'],
                        normalized['article_id'],
                        normalized['source'],
                        normalized['source_metadata_id'],
                        normalized['doi'],
                        normalized['url'],
                        normalized['ingestion_status'],
                        normalized['article_type'],
                        normalized['title'],
                        normalized['abstract'],
                        normalized['journal'],
                        normalized['keywords'],
                        normalized['authors'],
                        normalized['publication_date'],
                        normalized['country'],
                        normalized['full_text'],
                        normalized['figures'],
                        normalized['article_references'],
                        normalized['ingested_at'],
                        normalized['updated_at']
                    ))

                    stored += 1

                except Exception as e:
                    errors += 1
                    print(f"  [ERROR] Error storing article: {e}")

            conn.commit()

        return stored, duplicates, errors

    def get_pending_articles(self, limit: int = 100) -> List[Dict]:
        """
        Get articles pending GenAI analysis.

        Args:
            limit: Maximum number of articles to return

        Returns:
            List of article dictionaries
        """
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT a.id, a.article_id, a.title, a.abstract, a.journal,
                       a.publication_date, a.source
                FROM articles a
                LEFT JOIN article_analysis aa ON a.id = aa.article_id
                WHERE aa.id IS NULL
                  AND a.ingestion_status = 'pending'
                ORDER BY a.publication_date DESC
                LIMIT ?
            """, (limit,))

            articles = []
            for row in cursor.fetchall():
                articles.append(dict(row))

            return articles


# Example usage
if __name__ == "__main__":
    # Initialize orchestrator
    orchestrator = IngestionOrchestrator()

    # Ingest articles
    results = orchestrator.ingest_from_query(
        query="tobacco harm reduction",
        sources=['pubmed', 'crossref'],
        max_per_source=10,
        date_range={'from': '2024-01-01', 'to': '2024-12-31'}
    )

    # Get pending articles
    pending = orchestrator.get_pending_articles(limit=5)
    print(f"\n[PENDING] Pending articles for analysis: {len(pending)}")
    if pending:
        print(f"   First article: {pending[0]['title'][:60]}...")
