#!/usr/bin/env python3
"""
RAG Index Builder - Stage 6 of Pipeline
Embeds analyzed articles into ChromaDB for semantic search

Reads from database (articles + article_analysis tables)
"""

import json
import sys
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import List, Dict
import argparse

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

try:
    import chromadb
    from chromadb.config import Settings
    from sentence_transformers import SentenceTransformer
except ImportError as e:
    print(f"Missing dependencies: {e}")
    print("Install with: pip install chromadb sentence-transformers")
    sys.exit(1)


class RAGIndexBuilder:
    """Build and manage vector index for RAG"""

    def __init__(self,
                 db_path: Path = None,
                 collection_name: str = "research_articles",
                 embedding_model: str = "all-MiniLM-L6-v2"):
        """
        Initialize RAG index builder

        Args:
            db_path: Path to SQLite database (default: data/articles.db)
            collection_name: ChromaDB collection name
            embedding_model: Sentence transformer model name
        """
        self.db_path = db_path or Path(__file__).parent.parent / "data" / "articles.db"
        self.chroma_dir = Path(__file__).parent.parent / "data" / "chroma"
        self.collection_name = collection_name

        # Verify database exists
        if not self.db_path.exists():
            raise FileNotFoundError(f"Database not found: {self.db_path}")

        # Initialize ChromaDB client (persistent)
        self.chroma_dir.mkdir(parents=True, exist_ok=True)
        self.client = chromadb.PersistentClient(
            path=str(self.chroma_dir),
            settings=Settings(anonymized_telemetry=False)
        )

        # Load embedding model
        print(f"Loading embedding model: {embedding_model}...")
        self.embedding_model = SentenceTransformer(embedding_model)
        print("✓ Model loaded")

        # Get or create collection
        try:
            self.collection = self.client.get_collection(name=collection_name)
            print(f"✓ Using existing collection: {collection_name}")
        except:
            self.collection = self.client.create_collection(
                name=collection_name,
                metadata={"description": "Research article embeddings for RAG"}
            )
            print(f"✓ Created new collection: {collection_name}")

    def load_articles(self, status_filter: str = "completed") -> List[Dict]:
        """
        Load analyzed articles from database

        Args:
            status_filter: Analysis status filter (default: 'completed')

        Returns:
            List of article dictionaries with combined data from both tables
        """
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row  # Access columns by name
        cursor = conn.cursor()

        # Query to join articles and article_analysis tables
        query = """
            SELECT
                a.id,
                a.article_id,
                a.source,
                a.title,
                a.abstract,
                a.journal,
                a.authors,
                a.keywords,
                a.publication_date,
                a.country,
                a.doi,
                a.url,
                aa.subject,
                aa.category,
                aa.summary,
                aa.entities,
                aa.sentiment,
                aa.industry_affiliation,
                aa.analysis_status,
                aa.analyzed_at,
                aa.evaluation_score,
                aa.stage,
                aa.attempt
            FROM articles a
            INNER JOIN article_analysis aa ON a.id = aa.article_id
            WHERE aa.analysis_status = ?
        """

        try:
            cursor.execute(query, (status_filter,))
            rows = cursor.fetchall()

            articles = []
            for row in rows:
                # Convert Row to dict
                article = {
                    'article_id': row['article_id'],
                    'source_data': {
                        'title': row['title'],
                        'abstract': row['abstract'],
                        'journal': row['journal'],
                        'publication_date': row['publication_date'],
                        'doi': row['doi'],
                        'url': row['url'],
                        'source': row['source'],
                        'country': row['country'],
                        'authors': row['authors'],
                        'keywords': row['keywords']
                    },
                    'analysis': {
                        'title': row['title'],
                        'journal': row['journal'],
                        'date': row['publication_date'],
                        'abstract': row['abstract'],
                        'subject': row['subject'],
                        'category': row['category'],
                        'summary': row['summary'],
                        'entity': json.loads(row['entities']) if row['entities'] else [],
                        'sentiment': row['sentiment'],
                        'country': row['country'],
                        'industry_affiliation': row['industry_affiliation']
                    },
                    'stage': row['stage'] or 'completed',
                    'attempt': row['attempt'] or 1
                }
                articles.append(article)

            print(f"Loaded {len(articles)} articles from database (status={status_filter})")
            return articles

        except Exception as e:
            print(f"⚠ Error loading from database: {e}")
            return []
        finally:
            conn.close()

    def prepare_document_text(self, article: Dict) -> str:
        """
        Prepare text for embedding (summary + abstract)

        Args:
            article: Article dictionary

        Returns:
            Combined text for embedding
        """
        analysis = article.get('analysis', {})
        source_data = article.get('source_data', {})

        # Combine summary and abstract
        summary = analysis.get('summary', '')
        abstract = source_data.get('abstract', '')
        title = analysis.get('title', source_data.get('title', ''))

        # Format: Title | Summary | Abstract
        parts = []
        if title:
            parts.append(f"Title: {title}")
        if summary:
            parts.append(f"Summary: {summary}")
        if abstract:
            parts.append(f"Abstract: {abstract}")

        return " | ".join(parts)

    def prepare_metadata(self, article: Dict) -> Dict:
        """
        Extract metadata for filtering

        Args:
            article: Article dictionary

        Returns:
            Metadata dictionary
        """
        analysis = article.get('analysis', {})
        source_data = article.get('source_data', {})
        evaluation = article.get('evaluation', {})
        quality_score = evaluation.get('quality_score', {})

        metadata = {
            'article_id': article.get('article_id', ''),
            'title': analysis.get('title', '')[:500],  # ChromaDB has length limits
            'journal': analysis.get('journal', '')[:200],
            'publication_date': analysis.get('date', ''),
            'source': source_data.get('source', ''),
            'category': analysis.get('category', ''),
            'subject': analysis.get('subject', ''),
            'sentiment': analysis.get('sentiment', ''),
            'country': analysis.get('country', ''),
            'industry_affiliation': analysis.get('industry_affiliation', ''),
            'doi': source_data.get('doi', ''),
            'stage': article.get('stage', ''),
            'quality_score': quality_score.get('overall_score', 0.0),
        }

        # Handle entities (convert list to comma-separated string)
        entities = analysis.get('entity', [])
        if entities:
            metadata['entities'] = ', '.join(entities[:10])  # Limit to first 10

        # Remove None/empty values
        metadata = {k: str(v) for k, v in metadata.items() if v}

        return metadata

    def index_articles(self, articles: List[Dict], batch_size: int = 100) -> Dict:
        """
        Index articles into ChromaDB

        Args:
            articles: List of article dictionaries
            batch_size: Number of articles per batch

        Returns:
            Statistics dictionary
        """
        stats = {
            'total': len(articles),
            'indexed': 0,
            'skipped': 0,
            'errors': 0
        }

        if not articles:
            print("No articles to index")
            return stats

        print(f"\nIndexing {len(articles)} articles...")

        # Get existing IDs
        existing = self.collection.get()
        existing_ids = set(existing['ids']) if existing['ids'] else set()
        print(f"Found {len(existing_ids)} existing articles in index")

        # Process in batches
        for i in range(0, len(articles), batch_size):
            batch = articles[i:i+batch_size]

            batch_ids = []
            batch_documents = []
            batch_embeddings = []
            batch_metadatas = []

            for article in batch:
                article_id = article.get('article_id')

                if not article_id:
                    stats['skipped'] += 1
                    continue

                # Skip if already indexed
                if article_id in existing_ids:
                    stats['skipped'] += 1
                    continue

                try:
                    # Prepare document and metadata
                    doc_text = self.prepare_document_text(article)
                    metadata = self.prepare_metadata(article)

                    if not doc_text.strip():
                        print(f"⚠ Empty document for {article_id}, skipping")
                        stats['skipped'] += 1
                        continue

                    # Generate embedding
                    embedding = self.embedding_model.encode(doc_text).tolist()

                    batch_ids.append(article_id)
                    batch_documents.append(doc_text)
                    batch_embeddings.append(embedding)
                    batch_metadatas.append(metadata)

                except Exception as e:
                    print(f"⚠ Error processing {article_id}: {e}")
                    stats['errors'] += 1

            # Add batch to collection
            if batch_ids:
                try:
                    self.collection.add(
                        ids=batch_ids,
                        documents=batch_documents,
                        embeddings=batch_embeddings,
                        metadatas=batch_metadatas
                    )
                    stats['indexed'] += len(batch_ids)
                    print(f"✓ Indexed batch {i//batch_size + 1}: {len(batch_ids)} articles")
                except Exception as e:
                    print(f"⚠ Error adding batch: {e}")
                    stats['errors'] += len(batch_ids)

        return stats

    def get_collection_stats(self) -> Dict:
        """Get statistics about the indexed collection"""
        count = self.collection.count()

        # Sample metadata to show what's indexed
        sample = self.collection.get(limit=5)

        return {
            'total_documents': count,
            'collection_name': self.collection_name,
            'sample_ids': sample['ids'] if sample['ids'] else []
        }

    def rebuild_index(self, articles: List[Dict]) -> Dict:
        """
        Rebuild entire index (delete and recreate)

        Args:
            articles: List of article dictionaries

        Returns:
            Statistics dictionary
        """
        print(f"⚠ Rebuilding index: deleting collection '{self.collection_name}'")

        # Delete existing collection
        try:
            self.client.delete_collection(name=self.collection_name)
            print("✓ Deleted old collection")
        except:
            pass

        # Create new collection
        self.collection = self.client.create_collection(
            name=self.collection_name,
            metadata={"description": "Research article embeddings for RAG"}
        )
        print("✓ Created new collection")

        # Index all articles
        return self.index_articles(articles)


def main():
    parser = argparse.ArgumentParser(
        description="Build RAG index from analyzed articles in database"
    )
    parser.add_argument(
        '--db-path',
        type=Path,
        help='Path to SQLite database (default: data/articles.db)'
    )
    parser.add_argument(
        '--status',
        type=str,
        default='completed',
        help='Analysis status filter (default: completed)'
    )
    parser.add_argument(
        '--rebuild',
        action='store_true',
        help='Rebuild entire index (delete existing)'
    )
    parser.add_argument(
        '--stats',
        action='store_true',
        help='Show collection statistics only'
    )
    parser.add_argument(
        '--batch-size',
        type=int,
        default=100,
        help='Batch size for indexing (default: 100)'
    )

    args = parser.parse_args()

    # Initialize builder
    print("=" * 60)
    print("RAG Index Builder - Stage 6")
    print("=" * 60)

    try:
        builder = RAGIndexBuilder(db_path=args.db_path)
    except FileNotFoundError as e:
        print(f"\n⚠ {e}")
        print("Run: python ingest_cli.py init")
        return

    # Show stats only
    if args.stats:
        stats = builder.get_collection_stats()
        print(f"\nCollection Stats:")
        print(f"  Name: {stats['collection_name']}")
        print(f"  Total Documents: {stats['total_documents']}")
        if stats['sample_ids']:
            print(f"  Sample IDs: {', '.join(stats['sample_ids'][:5])}")
        return

    # Load articles from database
    print(f"\nLoading articles from database (status={args.status})...")
    articles = builder.load_articles(status_filter=args.status)

    if not articles:
        print(f"\n⚠ No articles found with status='{args.status}'")
        print("Run the GenAI pipeline to analyze articles first:")
        print("  python scripts/full_pipeline.py --topic 'Heat-Not-Burn' --max-articles 50")
        return

    # Index or rebuild
    if args.rebuild:
        stats = builder.rebuild_index(articles)
    else:
        stats = builder.index_articles(articles, batch_size=args.batch_size)

    # Print results
    print("\n" + "=" * 60)
    print("Indexing Complete")
    print("=" * 60)
    print(f"  Total Articles: {stats['total']}")
    print(f"  Indexed: {stats['indexed']}")
    print(f"  Skipped: {stats['skipped']}")
    print(f"  Errors: {stats['errors']}")

    # Final collection stats
    final_stats = builder.get_collection_stats()
    print(f"\nCollection now contains {final_stats['total_documents']} documents")
    print(f"Location: {builder.chroma_dir}")


if __name__ == "__main__":
    main()
