"""
Data normalizer for multi-source article ingestion.
Converts raw article data from different sources to unified schema.
"""
from typing import Dict, List
import uuid
from datetime import datetime
import json


class DataNormalizer:
    """
    Normalize articles from different sources (PubMed, Crossref, Scholar)
    to unified v2.0 schema.
    """

    def normalize(self, raw_article: Dict) -> Dict:
        """
        Convert raw article data to v2.0 schema.

        Args:
            raw_article: Raw article from connector (PubMed, Crossref, Scholar)

        Returns:
            Normalized article dictionary ready for database insertion

        Example:
            >>> normalizer = DataNormalizer()
            >>> normalized = normalizer.normalize(raw_pubmed_article)
        """
        return {
            # Generate UUID
            'id': str(uuid.uuid4()),
            'article_id': raw_article.get('article_id', f"UNKNOWN-{uuid.uuid4().hex[:8]}"),

            # Ingestion metadata
            'source': raw_article.get('source', 'unknown'),
            'source_metadata_id': raw_article.get('source_metadata_id', ''),
            'doi': raw_article.get('doi', ''),
            'url': raw_article.get('url', ''),
            'ingestion_status': 'pending',  # Will be 'processed' after GenAI analysis
            'article_type': raw_article.get('article_type', 'research'),

            # Article metadata
            'title': self._clean_text(raw_article.get('title', '')),
            'abstract': self._clean_text(raw_article.get('abstract', '')),
            'journal': raw_article.get('journal', ''),
            'keywords': json.dumps(raw_article.get('keywords', [])),
            'authors': json.dumps(self._normalize_authors(raw_article.get('authors', []))),
            'publication_date': self._normalize_date(raw_article.get('publication_date', '')),
            'country': raw_article.get('country', 'n/a'),

            # Future fields (empty for now)
            'full_text': None,
            'figures': None,
            'article_references': None,

            # Timestamps
            'ingested_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat()
        }

    def _normalize_authors(self, authors: List) -> List[Dict]:
        """
        Ensure consistent author format.

        Args:
            authors: List of author dictionaries or strings

        Returns:
            List of normalized author dictionaries
        """
        normalized = []

        for author in authors:
            if isinstance(author, str):
                # Convert string to dict
                normalized.append({
                    'name': author,
                    'affiliation': '',
                    'orcid': None
                })
            elif isinstance(author, dict):
                normalized.append({
                    'name': author.get('name', ''),
                    'affiliation': author.get('affiliation', ''),
                    'orcid': author.get('orcid', None)
                })

        return normalized

    def _normalize_date(self, date_str: str) -> str:
        """
        Convert various date formats to ISO (YYYY-MM-DD).

        Args:
            date_str: Date string in various formats

        Returns:
            ISO format date string (YYYY-MM-DD)
        """
        if not date_str:
            return ''

        # Already in ISO format
        if len(date_str) == 10 and date_str[4] == '-' and date_str[7] == '-':
            return date_str

        # Try common formats
        formats = [
            '%Y/%m/%d',
            '%Y-%m',
            '%Y'
        ]

        for fmt in formats:
            try:
                dt = datetime.strptime(date_str, fmt)
                return dt.strftime('%Y-%m-%d')
            except:
                continue

        # Return as-is if can't parse
        return date_str

    def _clean_text(self, text: str) -> str:
        """
        Clean text by removing extra whitespace and special characters.

        Args:
            text: Raw text

        Returns:
            Cleaned text
        """
        if not text:
            return ''

        # Remove extra whitespace
        text = ' '.join(text.split())

        # Strip leading/trailing whitespace
        text = text.strip()

        return text

    def validate(self, article: Dict) -> bool:
        """
        Validate normalized article has required fields.

        Args:
            article: Normalized article dictionary

        Returns:
            True if valid, False otherwise
        """
        required_fields = ['article_id', 'source', 'title']

        for field in required_fields:
            if not article.get(field):
                print(f"  [WARN]  Validation failed: Missing '{field}'")
                return False

        return True


# Example usage
if __name__ == "__main__":
    normalizer = DataNormalizer()

    # Test with sample raw article
    raw_article = {
        'article_id': 'PMID12345',
        'source': 'pubmed',
        'source_metadata_id': '12345',
        'doi': '10.1234/example',
        'title': '  Effects of E-Cigarettes   ',  # Extra whitespace
        'abstract': 'This study examines...',
        'journal': 'Tobacco Control',
        'authors': [
            {'name': 'John Smith', 'affiliation': 'Harvard', 'orcid': '0000-0001-2345-6789'},
            'Jane Doe'  # String format
        ],
        'keywords': ['vaping', 'youth'],
        'publication_date': '2024-01-15',
        'url': 'https://pubmed.ncbi.nlm.nih.gov/12345/',
        'article_type': 'research',
        'country': 'United States'
    }

    normalized = normalizer.normalize(raw_article)

    print("[OK] Normalized article:")
    print(f"  ID: {normalized['id']}")
    print(f"  Article ID: {normalized['article_id']}")
    print(f"  Title: {normalized['title']}")
    print(f"  Authors: {json.loads(normalized['authors'])}")
    print(f"  Keywords: {json.loads(normalized['keywords'])}")

    # Test validation
    is_valid = normalizer.validate(normalized)
    print(f"  Valid: {is_valid}")
