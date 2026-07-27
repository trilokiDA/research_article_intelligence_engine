"""
PubMed E-utilities API connector.
Fetches article metadata from PubMed.
"""
from Bio import Entrez
from typing import List, Dict, Optional
import time
import os
from datetime import datetime


class PubMedConnector:
    """
    Connector for PubMed E-utilities API.

    Requires:
    - NCBI_EMAIL environment variable
    - NCBI_API_KEY environment variable (optional, for 10 req/sec vs 3 req/sec)

    Rate limits:
    - Without API key: 3 requests per second
    - With API key: 10 requests per second

    Get API key: https://www.ncbi.nlm.nih.gov/account/
    """

    def __init__(self, email: Optional[str] = None, api_key: Optional[str] = None):
        """
        Initialize PubMed connector.

        Args:
            email: Your email (required by NCBI)
            api_key: NCBI API key (optional, increases rate limit)
        """
        self.email = email or os.getenv('NCBI_EMAIL', 'your-email@example.com')
        self.api_key = api_key or os.getenv('NCBI_API_KEY')

        Entrez.email = self.email
        if self.api_key:
            Entrez.api_key = self.api_key
            self.rate_limit_delay = 0.11  # 10 req/sec = 100ms + 10ms buffer
        else:
            self.rate_limit_delay = 0.35  # 3 req/sec = 333ms + buffer

        api_status = 'YES' if self.api_key else 'NO'
        print(f"[OK] PubMed connector initialized (email: {self.email}, API key: {api_status})")

    def search_articles(
        self,
        query: str,
        max_results: int = 100,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        sort: str = 'pub_date'
    ) -> List[str]:
        """
        Search PubMed and return list of PMIDs.

        Args:
            query: Search query (e.g., "tobacco harm reduction[Title/Abstract]")
            max_results: Maximum number of results
            start_date: Start date (format: YYYY/MM/DD)
            end_date: End date (format: YYYY/MM/DD)
            sort: Sort order (pub_date, relevance)

        Returns:
            List of PMIDs (PubMed IDs)

        Example:
            >>> connector = PubMedConnector()
            >>> pmids = connector.search_articles(
            ...     query="electronic cigarettes AND youth",
            ...     max_results=50,
            ...     start_date="2024/01/01",
            ...     end_date="2024/12/31"
            ... )
        """
        print(f"[SEARCH] Searching PubMed: '{query}' (max: {max_results})")

        search_params = {
            'db': 'pubmed',
            'term': query,
            'retmax': max_results,
            'sort': sort
        }

        if start_date and end_date:
            search_params['mindate'] = start_date
            search_params['maxdate'] = end_date
            search_params['datetype'] = 'pdat'  # Publication date

        try:
            handle = Entrez.esearch(**search_params)
            results = Entrez.read(handle)
            handle.close()

            pmids = results['IdList']
            print(f"[OK] Found {len(pmids)} articles")
            return pmids

        except Exception as e:
            print(f"[ERROR] PubMed search error: {e}")
            return []

    def fetch_article_details(self, pmids: List[str]) -> List[Dict]:
        """
        Fetch full article details for list of PMIDs.

        Args:
            pmids: List of PubMed IDs

        Returns:
            List of normalized article dictionaries

        Example:
            >>> pmids = ['12345678', '87654321']
            >>> articles = connector.fetch_article_details(pmids)
        """
        if not pmids:
            return []

        print(f"[FETCH] Fetching details for {len(pmids)} articles...")

        articles = []
        batch_size = 200  # Max batch size for efetch

        for i in range(0, len(pmids), batch_size):
            batch = pmids[i:i + batch_size]

            try:
                handle = Entrez.efetch(
                    db='pubmed',
                    id=','.join(batch),
                    retmode='xml'
                )
                records = Entrez.read(handle)
                handle.close()

                for record in records['PubmedArticle']:
                    try:
                        article = self._parse_pubmed_record(record)
                        articles.append(article)
                    except Exception as e:
                        pmid = record.get('MedlineCitation', {}).get('PMID', 'unknown')
                        print(f"  [ERROR] Error parsing PMID {pmid}: {e}")

                print(f"  [OK] Batch {i // batch_size + 1}: {len(batch)} articles")

                # Rate limiting
                time.sleep(self.rate_limit_delay)

            except Exception as e:
                print(f"  [ERROR] Error fetching batch: {e}")
                continue

        print(f"[OK] Fetched {len(articles)} articles successfully")
        return articles

    def _parse_pubmed_record(self, record: Dict) -> Dict:
        """
        Parse PubMed XML record to normalized format.

        Args:
            record: PubMed article record

        Returns:
            Normalized article dictionary
        """
        medline = record.get('MedlineCitation', {})
        article = medline.get('Article', {})

        # Extract PMID
        pmid = str(medline.get('PMID', ''))

        # Extract title
        title = article.get('ArticleTitle', '')

        # Extract abstract
        abstract_list = article.get('Abstract', {}).get('AbstractText', [])
        abstract = ' '.join([str(a) for a in abstract_list])

        # Extract journal
        journal_info = article.get('Journal', {})
        journal = journal_info.get('Title', '')

        # Extract authors
        authors = []
        for author in article.get('AuthorList', []):
            last_name = author.get('LastName', '')
            fore_name = author.get('ForeName', '')
            name = f"{fore_name} {last_name}".strip()

            affiliation_info = author.get('AffiliationInfo', [])
            affiliation = affiliation_info[0].get('Affiliation', '') if affiliation_info else ''

            authors.append({
                'name': name,
                'affiliation': affiliation,
                'orcid': None  # PubMed doesn't consistently provide ORCID
            })

        # Extract keywords
        keywords = []
        keyword_list = medline.get('KeywordList', [])
        if keyword_list:
            keywords = [str(kw) for kw in keyword_list[0]]

        # Extract MeSH terms (Medical Subject Headings)
        mesh_terms = []
        for mesh in medline.get('MeshHeadingList', []):
            descriptor = mesh.get('DescriptorName', {})
            mesh_terms.append(str(descriptor))

        # Combine keywords and MeSH terms
        all_keywords = list(set(keywords + mesh_terms))

        # Extract publication date
        pub_date = self._extract_publication_date(article)

        # Extract DOI
        doi = ''
        for elocation in article.get('ELocationID', []):
            if elocation.attributes.get('EIdType') == 'doi':
                doi = str(elocation)
                break

        # Extract country (from first author affiliation)
        country = self._extract_country(authors)

        return {
            'article_id': f"PMID{pmid}",
            'source': 'pubmed',
            'source_metadata_id': pmid,
            'doi': doi,
            'title': title,
            'abstract': abstract,
            'journal': journal,
            'authors': authors,
            'keywords': all_keywords,
            'publication_date': pub_date,
            'url': f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
            'article_type': self._extract_article_type(article),
            'country': country
        }

    def _extract_publication_date(self, article: Dict) -> str:
        """Extract publication date in ISO format (YYYY-MM-DD)."""
        # Try ArticleDate first
        for article_date in article.get('ArticleDate', []):
            year = article_date.get('Year', '')
            month = article_date.get('Month', '01')
            day = article_date.get('Day', '01')
            if year:
                return f"{year}-{month.zfill(2)}-{day.zfill(2)}"

        # Fallback to Journal publish date
        journal = article.get('Journal', {})
        pub_date = journal.get('JournalIssue', {}).get('PubDate', {})

        year = pub_date.get('Year', '')
        month = pub_date.get('Month', '01')
        day = pub_date.get('Day', '01')

        if year:
            # Convert month name to number
            month_map = {
                'Jan': '01', 'Feb': '02', 'Mar': '03', 'Apr': '04',
                'May': '05', 'Jun': '06', 'Jul': '07', 'Aug': '08',
                'Sep': '09', 'Oct': '10', 'Nov': '11', 'Dec': '12'
            }
            if month in month_map:
                month = month_map[month]
            else:
                month = month.zfill(2) if month.isdigit() else '01'

            return f"{year}-{month}-{day.zfill(2) if day else '01'}"

        return ''

    def _extract_article_type(self, article: Dict) -> str:
        """Extract article type (research, review, editorial, etc.)."""
        pub_types = article.get('PublicationTypeList', [])
        if pub_types:
            first_type = str(pub_types[0]).lower()
            if 'review' in first_type:
                return 'review'
            elif 'editorial' in first_type:
                return 'editorial'
            elif 'meta-analysis' in first_type:
                return 'meta-analysis'

        return 'research'

    def _extract_country(self, authors: List[Dict]) -> str:
        """Extract country from first author affiliation."""
        if not authors or not authors[0].get('affiliation'):
            return 'n/a'

        affiliation = authors[0]['affiliation']

        # Common country name patterns
        countries = [
            'United States', 'United Kingdom', 'Canada', 'Australia',
            'Germany', 'France', 'Italy', 'Spain', 'Netherlands',
            'China', 'Japan', 'South Korea', 'India', 'Brazil',
            'Sweden', 'Norway', 'Denmark', 'Finland', 'Switzerland'
        ]

        for country in countries:
            if country.lower() in affiliation.lower():
                return country

        # Fallback: last word in affiliation (often country)
        words = affiliation.split(',')
        return words[-1].strip() if words else 'n/a'


# Example usage
if __name__ == "__main__":
    # Initialize connector
    connector = PubMedConnector()

    # Search for articles
    pmids = connector.search_articles(
        query="tobacco harm reduction",
        max_results=5,
        start_date="2024/01/01",
        end_date="2024/12/31"
    )

    # Fetch details
    if pmids:
        articles = connector.fetch_article_details(pmids)

        # Print first article
        if articles:
            print(f"\n[ARTICLE] Sample Article:")
            print(f"   ID: {articles[0]['article_id']}")
            print(f"   Title: {articles[0]['title'][:80]}...")
            print(f"   Journal: {articles[0]['journal']}")
            print(f"   Date: {articles[0]['publication_date']}")
            print(f"   Authors: {len(articles[0]['authors'])}")
            print(f"   Keywords: {len(articles[0]['keywords'])}")
