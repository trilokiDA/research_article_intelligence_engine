"""
Query manager for predefined topic searches.
Loads search queries from configuration file.
"""
import json
from pathlib import Path
from typing import Dict, List, Optional


class QueryManager:
    """
    Manage predefined search queries for different topics.

    Loads queries from search_queries.json and provides
    easy access by topic name.
    """

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize query manager.

        Args:
            config_path: Path to search_queries.json (optional)
        """
        if config_path is None:
            config_path = Path(__file__).parent / "search_queries.json"

        self.config_path = Path(config_path)
        self.queries = self._load_queries()

    def _load_queries(self) -> Dict:
        """Load queries from JSON file."""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return {q['name']: q for q in data['queries']}
        except FileNotFoundError:
            print(f"[WARNING] Query config not found: {self.config_path}")
            return {}
        except json.JSONDecodeError as e:
            print(f"[ERROR] Invalid JSON in query config: {e}")
            return {}

    def list_topics(self) -> List[str]:
        """
        Get list of available topic names.

        Returns:
            List of topic names

        Example:
            >>> manager = QueryManager()
            >>> topics = manager.list_topics()
            >>> print(topics)
            ['Heat-Not-Burn', 'E-Cigarettes', 'Nicotine-Pouch', 'Snus']
        """
        return list(self.queries.keys())

    def get_query(self, topic: str, source: str) -> Optional[str]:
        """
        Get query string for a specific topic and source.

        Args:
            topic: Topic name (e.g., 'Heat-Not-Burn')
            source: Source name ('pubmed' or 'google_scholar')

        Returns:
            Query string or None if not found

        Example:
            >>> manager = QueryManager()
            >>> query = manager.get_query('E-Cigarettes', 'pubmed')
            >>> print(query[:50])
            (("electronic cigarettes*"[Title/Abstract]) OR...
        """
        if topic not in self.queries:
            return None

        topic_data = self.queries[topic]
        source_data = topic_data.get('sources', {}).get(source)

        if not source_data:
            return None

        return source_data.get('query')

    def get_topic_info(self, topic: str) -> Optional[Dict]:
        """
        Get full information about a topic.

        Args:
            topic: Topic name

        Returns:
            Dictionary with topic info or None

        Example:
            >>> manager = QueryManager()
            >>> info = manager.get_topic_info('Heat-Not-Burn')
            >>> print(info['description'])
            Heated tobacco products (IQOS, HEETS, THS)
        """
        return self.queries.get(topic)

    def get_all_queries_for_topic(self, topic: str) -> Dict[str, str]:
        """
        Get all source queries for a topic.

        Args:
            topic: Topic name

        Returns:
            Dictionary mapping source -> query string

        Example:
            >>> manager = QueryManager()
            >>> queries = manager.get_all_queries_for_topic('Snus')
            >>> print(queries.keys())
            dict_keys(['pubmed', 'google_scholar'])
        """
        if topic not in self.queries:
            return {}

        topic_data = self.queries[topic]
        sources = topic_data.get('sources', {})

        return {
            source: data.get('query')
            for source, data in sources.items()
            if data.get('query')
        }

    def print_summary(self):
        """Print summary of available queries."""
        print("\n" + "="*70)
        print("[CONFIG] AVAILABLE TOPIC QUERIES")
        print("="*70)

        if not self.queries:
            print("No queries loaded.")
            return

        for topic_name, topic_data in self.queries.items():
            print(f"\n{topic_name}")
            print(f"  Description: {topic_data.get('description', 'N/A')}")
            print(f"  Sources:")

            for source, source_data in topic_data.get('sources', {}).items():
                query = source_data.get('query', '')
                query_preview = query[:60] + "..." if len(query) > 60 else query
                print(f"    - {source}: {query_preview}")

        print("\n" + "="*70 + "\n")


# Example usage
if __name__ == "__main__":
    manager = QueryManager()

    # Print summary
    manager.print_summary()

    # Get specific query
    pubmed_query = manager.get_query('E-Cigarettes', 'pubmed')
    print(f"\n[EXAMPLE] E-Cigarettes PubMed Query:")
    print(f"{pubmed_query}\n")

    # List all topics
    topics = manager.list_topics()
    print(f"[TOPICS] Available: {', '.join(topics)}")
