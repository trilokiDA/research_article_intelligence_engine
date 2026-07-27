"""
Crossref REST API connector.
Fetches article metadata from Crossref.
"""
import requests
from typing import List, Dict, Optional
import time
import os


class CrossrefConnector:
    """
    Connector for Crossref REST API.

    Rate limits:
    - Standard: 50 requests per second
    - Polite pool: Include email in User-Agent

    API docs: https://api.crossref.org/
    """

    BASE_URL = "https://api.crossref.org/works"

    def __init__(self, email: Optional[str] = None):
        """
        Initialize Crossref connector.

        Args:
            email: Your email for polite pool (faster rate limits)
        """
        self.email = email or os.getenv('CROSSREF_EMAIL', 'your-email@example.com')
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': f'TobaccoResearchPlatform/2.0 (mailto:{self.email})'
        })
        self.rate_limit_delay = 0.02  # 50 req/sec = 20ms

        print(f"[OK] Crossref connector initialized (email: {self.email})")

    def search_articles(
        self,
        query: str,
        max_results: int = 100,
        filter_params: Optional[Dict] = None,
        sort: str = 'published'
    ) -> List[Dict]:
        """
        Search Crossref and return article metadata.

        Args:
            query: Search query (e.g., "tobacco harm reduction")
            max_results: Maximum number of results
            filter_params: Filter parameters (e.g., {'from-pub-date': '2024-01-01'})
            sort: Sort order (published, relevance, score)

        Returns:
            List of normalized article dictionaries

        Example:
            >>> connector = CrossrefConnector()
            >>> articles = connector.search_articles(
            ...     query="electronic cigarettes youth",
            ...     max_results=50,
            ...     filter_params={'from-pub-date': '2024-01-01'}
            ... )
        """
        print(f"[SEARCH] Searching Crossref: '{query}' (max: {max_results})")

        articles = []
        rows_per_page = 100
        offset = 0

        while len(articles) < max_results:
            params = {
                'query': query,
                'rows': min(rows_per_page, max_results - len(articles)),
                'offset': offset,
                'mailto': self.email,
                'sort': sort
            }

            if filter_params:
                # Format filters: key1:value1,key2:value2
                params['filter'] = ','.join(f"{k}:{v}" for k, v in filter_params.items())

            try:
                response = self.session.get(self.BASE_URL, params=params, timeout=30)
                response.raise_for_status()

                data = response.json()
                items = data['message']['items']

                if not items:
                    break

                for item in items:
                    try:
                        article = self._parse_crossref_item(item)
                        articles.append(article)
                    except Exception as e:
                        doi = item.get('DOI', 'unknown')
                        print(f"  [ERROR] Error parsing DOI {doi}: {e}")

                offset += len(items)
                print(f"  [OK] Fetched {len(articles)}/{max_results} articles")

                # Rate limiting
                time.sleep(self.rate_limit_delay)

            except requests.exceptions.RequestException as e:
                print(f"  [ERROR] Request error: {e}")
                break

        print(f"[OK] Found {len(articles)} articles")
        return articles[:max_results]

    def fetch_by_doi(self, doi: str) -> Optional[Dict]:
        """
        Fetch single article by DOI.

        Args:
            doi: Digital Object Identifier

        Returns:
            Normalized article dictionary or None

        Example:
            >>> article = connector.fetch_by_doi("10.1234/example")
        """
        print(f"[FETCH] Fetching DOI: {doi}")

        try:
            response = self.session.get(f"{self.BASE_URL}/{doi}", timeout=30)
            response.raise_for_status()

            item = response.json()['message']
            article = self._parse_crossref_item(item)

            print(f"[OK] Fetched article")
            return article

        except requests.exceptions.RequestException as e:
            print(f"[ERROR] Error fetching DOI: {e}")
            return None

    def _parse_crossref_item(self, item: Dict) -> Dict:
        """
        Parse Crossref JSON item to normalized format.

        Args:
            item: Crossref work item

        Returns:
            Normalized article dictionary
        """
        # Extract DOI
        doi = item.get('DOI', '')

        # Extract title
        title_list = item.get('title', [''])
        title = title_list[0] if title_list else ''

        # Extract abstract (often empty in Crossref)
        abstract = item.get('abstract', '')

        # Extract journal
        container_title = item.get('container-title', [''])
        journal = container_title[0] if container_title else ''

        # Extract authors
        authors = []
        for author in item.get('author', []):
            given = author.get('given', '')
            family = author.get('family', '')
            name = f"{given} {family}".strip()

            # Extract affiliations
            affiliations = author.get('affiliation', [])
            affiliation = ', '.join([aff.get('name', '') for aff in affiliations])

            # Extract ORCID
            orcid = author.get('ORCID', '').replace('http://orcid.org/', '')

            authors.append({
                'name': name,
                'affiliation': affiliation,
                'orcid': orcid or None
            })

        # Extract keywords/subjects
        keywords = item.get('subject', [])

        # Extract publication date
        pub_date = self._extract_publication_date(item)

        # Extract URL
        url = item.get('URL', '')

        # Extract article type
        article_type = item.get('type', 'journal-article')
        if 'review' in article_type.lower():
            article_type = 'review'
        elif 'editorial' in article_type.lower():
            article_type = 'editorial'
        else:
            article_type = 'research'

        return {
            'article_id': doi,
            'source': 'crossref',
            'source_metadata_id': doi,
            'doi': doi,
            'title': title,
            'abstract': abstract,
            'journal': journal,
            'authors': authors,
            'keywords': keywords,
            'publication_date': pub_date,
            'url': url,
            'article_type': article_type,
            'country': 'n/a'  # Crossref doesn't consistently provide country
        }

    def _extract_publication_date(self, item: Dict) -> str:
        """
        Extract publication date in ISO format (YYYY-MM-DD).

        Args:
            item: Crossref work item

        Returns:
            ISO date string
        """
        # Try published-print date first
        pub_date = item.get('published-print', item.get('published-online', {}))

        date_parts = pub_date.get('date-parts', [[]])[0]

        if not date_parts:
            return ''

        # Pad parts to YYYY-MM-DD
        year = str(date_parts[0]) if len(date_parts) > 0 else ''
        month = str(date_parts[1]).zfill(2) if len(date_parts) > 1 else '01'
        day = str(date_parts[2]).zfill(2) if len(date_parts) > 2 else '01'

        if year:
            return f"{year}-{month}-{day}"

        return ''


# Example usage
if __name__ == "__main__":
    # Initialize connector
    connector = CrossrefConnector()

    # Search for articles
    articles = connector.search_articles(
        query="tobacco harm reduction",
        max_results=5,
        filter_params={
            'from-pub-date': '2024-01-01',
            'until-pub-date': '2024-12-31'
        }
    )

    # Print first article
    if articles:
        print(f"\n[ARTICLE] Sample Article:")
        print(f"   DOI: {articles[0]['doi']}")
        print(f"   Title: {articles[0]['title'][:80]}...")
        print(f"   Journal: {articles[0]['journal']}")
        print(f"   Date: {articles[0]['publication_date']}")
        print(f"   Authors: {len(articles[0]['authors'])}")

    # Fetch specific DOI
    print("\n" + "="*60)
    article = connector.fetch_by_doi("10.1186/s12889-024-12345-x")
    if article:
        print(f"   Title: {article['title'][:80]}...")
