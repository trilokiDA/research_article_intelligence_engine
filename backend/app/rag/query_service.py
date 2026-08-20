"""
RAG Query Service - Retrieval and Generation for Research Articles
"""

import os
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime

from dotenv import load_dotenv
# Load environment
load_dotenv()

try:
    import chromadb
    from chromadb.config import Settings
    from sentence_transformers import SentenceTransformer
    from langchain_groq import ChatGroq
    from langchain_core.messages import HumanMessage, SystemMessage
except ImportError as e:
    raise ImportError(
        f"Missing RAG dependencies: {e}\n"
        "Install with: pip install chromadb sentence-transformers langchain-groq"
    )


class RAGQueryService:
    """Service for querying research articles using RAG"""

    def __init__(self,
                 chroma_dir: Optional[Path] = None,
                 collection_name: str = "research_articles",
                 embedding_model: str = "all-MiniLM-L6-v2",
                 llm_model: str = "openai/gpt-oss-20b"):
        """
        Initialize RAG query service

        Args:
            chroma_dir: ChromaDB storage directory
            collection_name: Collection name to query
            embedding_model: Sentence transformer model
            llm_model: Groq LLM model for generation
        """
        # Default paths
        if chroma_dir is None:
            chroma_dir = Path(__file__).parent.parent.parent.parent / "data" / "chroma"

        self.chroma_dir = chroma_dir
        self.collection_name = collection_name

        # Initialize ChromaDB client
        if not chroma_dir.exists():
            raise FileNotFoundError(
                f"ChromaDB directory not found: {chroma_dir}\n"
                "Run: python scripts/build_rag_index.py first"
            )

        self.client = chromadb.PersistentClient(
            path=str(chroma_dir),
            settings=Settings(anonymized_telemetry=False)
        )

        # Get collection
        try:
            self.collection = self.client.get_collection(name=collection_name)
        except Exception as e:
            raise ValueError(
                f"Collection '{collection_name}' not found: {e}\n"
                "Run: python scripts/build_rag_index.py first"
            )

        # Load embedding model
        self.embedding_model = SentenceTransformer(embedding_model)

        # Initialize Groq LLM
        api_key = os.getenv('GROQ_API_KEY')
        if not api_key:
            raise ValueError("GROQ_API_KEY not found in environment")

        self.llm = ChatGroq(
            groq_api_key=api_key,
            model_name=llm_model,
            temperature=0.3,  # Lower temperature for factual responses
        )

    def retrieve(self,
                 query: str,
                 n_results: int = 5,
                 filters: Optional[Dict] = None) -> Dict:
        """
        Retrieve relevant articles for a query

        Args:
            query: User question
            n_results: Number of results to retrieve
            filters: Optional metadata filters (e.g., {"category": "Clinical Studies"})

        Returns:
            Dictionary with retrieved documents and metadata
        """
        # Generate query embedding
        query_embedding = self.embedding_model.encode(query).tolist()

        # Query ChromaDB
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=filters  # Optional metadata filtering
        )

        return results

    def format_context(self, results: Dict) -> str:
        """
        Format retrieved documents as context for LLM

        Args:
            results: ChromaDB query results

        Returns:
            Formatted context string
        """
        if not results['documents'] or not results['documents'][0]:
            return "No relevant articles found."

        documents = results['documents'][0]
        metadatas = results['metadatas'][0]

        context_parts = []

        for i, (doc, meta) in enumerate(zip(documents, metadatas), 1):
            article_id = meta.get('article_id', 'Unknown')
            title = meta.get('title', 'No title')
            journal = meta.get('journal', 'Unknown journal')
            date = meta.get('publication_date', 'Unknown date')
            category = meta.get('category', 'Unknown')
            sentiment = meta.get('sentiment', 'Unknown')

            context_parts.append(
                f"[Article {i}] {article_id}\n"
                f"Title: {title}\n"
                f"Journal: {journal} ({date})\n"
                f"Category: {category} | Sentiment: {sentiment}\n"
                f"Content: {doc}\n"
            )

        return "\n\n".join(context_parts)

    def generate_response(self, query: str, context: str) -> str:
        """
        Generate answer using LLM with retrieved context

        Args:
            query: User question
            context: Retrieved article context

        Returns:
            Generated answer
        """
        system_prompt = """You are a research assistant specializing in tobacco and nicotine research.

Your role:
- Answer questions based ONLY on the provided research articles
- Cite article IDs (e.g., PMID12345678) when making claims
- If information is not in the articles, say so clearly
- Maintain scientific accuracy and neutrality
- Use people-first language (e.g., "people who use tobacco" not "tobacco users")

Guidelines:
- Be concise but comprehensive
- Highlight consensus vs. conflicting findings
- Note study limitations when relevant
- Reference specific studies by their article ID
"""

        user_prompt = f"""Research Articles:

{context}

---

User Question: {query}

Please answer based on the articles above. Always cite article IDs when referencing specific findings."""

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]

        # Generate response
        response = self.llm.invoke(messages)
        return response.content

    def query(self,
              question: str,
              n_results: int = 5,
              filters: Optional[Dict] = None) -> Dict:
        """
        Complete RAG query: retrieve + generate

        Args:
            question: User question
            n_results: Number of articles to retrieve
            filters: Optional metadata filters

        Returns:
            Dictionary with answer, sources, and metadata
        """
        # Retrieve relevant articles
        retrieval_results = self.retrieve(
            query=question,
            n_results=n_results,
            filters=filters
        )

        # Format context
        context = self.format_context(retrieval_results)

        # Generate answer
        answer = self.generate_response(question, context)

        # Extract sources
        sources = []
        if retrieval_results['metadatas'] and retrieval_results['metadatas'][0]:
            for meta in retrieval_results['metadatas'][0]:
                sources.append({
                    'article_id': meta.get('article_id', ''),
                    'title': meta.get('title', ''),
                    'journal': meta.get('journal', ''),
                    'date': meta.get('publication_date', ''),
                    'doi': meta.get('doi', ''),
                    'category': meta.get('category', ''),
                    'sentiment': meta.get('sentiment', ''),
                })

        return {
            'question': question,
            'answer': answer,
            'sources': sources,
            'n_sources': len(sources),
            'timestamp': datetime.now().isoformat()
        }

    def get_collection_info(self) -> Dict:
        """Get information about the indexed collection"""
        count = self.collection.count()
        sample = self.collection.get(limit=1)

        return {
            'collection_name': self.collection_name,
            'total_documents': count,
            'status': 'ready' if count > 0 else 'empty'
        }


# Convenience function for quick queries
def ask(question: str, n_results: int = 5) -> Dict:
    """
    Quick query function

    Args:
        question: User question
        n_results: Number of sources to retrieve

    Returns:
        RAG response dictionary

    Example:
        >>> result = ask("What are the cardiovascular risks of vaping?")
        >>> print(result['answer'])
    """
    service = RAGQueryService()
    return service.query(question, n_results=n_results)


if __name__ == "__main__":
    # Test query
    import sys
    from dotenv import load_dotenv

    load_dotenv()

    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
    else:
        query = "What are the cardiovascular effects of e-cigarettes?"

    print(f"Query: {query}\n")

    service = RAGQueryService()
    result = service.query(query)

    print("Answer:")
    print(result['answer'])
    print(f"\nSources ({result['n_sources']}):")
    for i, source in enumerate(result['sources'], 1):
        print(f"  [{i}] {source['article_id']}: {source['title'][:80]}...")
