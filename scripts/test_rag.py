#!/usr/bin/env python3
"""
Quick RAG Test Script
Test the RAG system with sample queries
"""

import sys
from pathlib import Path

# Add parent to path
sys.path.append(str(Path(__file__).parent.parent))

from backend.app.rag import RAGQueryService
from dotenv import load_dotenv

# Load environment
load_dotenv()


def main():
    print("=" * 60)
    print("RAG System Test")
    print("=" * 60)

    # Initialize service
    print("\n1. Initializing RAG service...")
    try:
        service = RAGQueryService()
        info = service.get_collection_info()
        print(f"   ✓ Collection: {info['collection_name']}")
        print(f"   ✓ Documents: {info['total_documents']}")
        print(f"   ✓ Status: {info['status']}")
    except Exception as e:
        print(f"   ✗ Error: {e}")
        print("\n   Fix: Run 'python scripts/build_rag_index.py' first")
        sys.exit(1)

    # Test queries
    test_queries = [
        "What are the cardiovascular effects of e-cigarettes?",
        "Show studies on youth vaping behavior",
        "Studies with PMI affiliation"
    ]

    print("\n2. Running test queries...\n")

    for i, query in enumerate(test_queries, 1):
        print(f"Q{i}: {query}")
        print("-" * 60)

        try:
            result = service.query(query, n_results=3)

            print(f"Answer: {result['answer'][:200]}...")
            print(f"\nSources ({result['n_sources']}):")
            for j, source in enumerate(result['sources'], 1):
                print(f"  [{j}] {source['article_id']}: {source['title'][:60]}...")

            print("\n" + "=" * 60 + "\n")

        except Exception as e:
            print(f"   ✗ Error: {e}\n")

    print("✓ Test complete!")


if __name__ == "__main__":
    main()
