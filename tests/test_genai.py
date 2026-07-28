"""
Test suite for GenAI summarization pipeline.
"""

import os
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()


def test_imports():
    """Test that all modules can be imported."""
    print("Testing imports...")
    try:
        from backend.app.genai.schemas import Response, EntityEnum, CategoryEnum, SentimentEnum, SubjectEnum
        from backend.app.genai.prompts import summarization_prompt, revalidate_prompt
        from backend.app.genai.summarizer import ArticleSummarizer, summarize_article
        from backend.app.genai.repository import ArticleRepository
        from backend.app.genai.pipeline import SummarizationPipeline
        print("✓ All imports successful")
        return True
    except Exception as e:
        print(f"✗ Import failed: {e}")
        return False


def test_repository():
    """Test repository functions."""
    print("\nTesting repository...")
    try:
        from backend.app.genai.repository import ArticleRepository

        repo = ArticleRepository()

        # Test pending count
        pending = repo.count_articles_pending_analysis()
        print(f"✓ Pending articles: {pending}")

        # Test stats
        stats = repo.get_analysis_stats()
        print(f"✓ Total articles: {stats['total_articles']}")
        print(f"✓ Analyzed: {stats['analyzed_count']}")

        return True
    except Exception as e:
        print(f"✗ Repository test failed: {e}")
        return False


def test_schema():
    """Test schema validation."""
    print("\nTesting schema...")
    try:
        from backend.app.genai.schemas import Response, EntityEnum, CategoryEnum, SentimentEnum, SubjectEnum

        # Create a valid response
        response = Response(
            articleID="TEST001",
            title="Test Article",
            journal="Test Journal",
            date="2024-01-15",
            abstract="Test abstract",
            entity=[EntityEnum.electronic_cigarettes],
            subject=SubjectEnum.e_cigarettes,
            summary="Test summary",
            category=CategoryEnum.clinical_studies,
            country="United States",
            sentiment=SentimentEnum.neutral,
            industry_affiliation="n/a"
        )

        print(f"✓ Schema validation successful")
        print(f"  - Article ID: {response.articleID}")
        print(f"  - Subject: {response.subject.value}")
        print(f"  - Entities: {[e.value for e in response.entity]}")

        return True
    except Exception as e:
        print(f"✗ Schema test failed: {e}")
        return False


def test_api_key():
    """Test API key configuration."""
    print("\nTesting API key...")
    api_key = os.getenv('GROQ_API_KEY')

    if not api_key:
        print("✗ GROQ_API_KEY not found")
        print("  Set it in .env file:")
        print("  GROQ_API_KEY=your-key-here")
        return False

    print(f"✓ GROQ_API_KEY found ({api_key[:10]}...)")
    return True


def test_summarizer():
    """Test summarizer initialization."""
    print("\nTesting summarizer...")

    if not os.getenv('GROQ_API_KEY'):
        print("⊘ Skipping (no API key)")
        return None

    try:
        from backend.app.genai.summarizer import ArticleSummarizer

        summarizer = ArticleSummarizer()
        print(f"✓ Summarizer initialized")
        print(f"  - Model: {summarizer.model_name}")
        print(f"  - Temperature: {summarizer.temperature}")

        return True
    except Exception as e:
        print(f"✗ Summarizer test failed: {e}")
        return False


def test_sample_article():
    """Test summarizing a sample article."""
    print("\nTesting sample article summarization...")

    if not os.getenv('GROQ_API_KEY'):
        print("⊘ Skipping (no API key)")
        return None

    try:
        from backend.app.genai.summarizer import summarize_article

        print("  Sending request to Groq...")

        result = summarize_article(
            doc_id="TEST001",
            title="Electronic Cigarettes and Cardiovascular Health: A Clinical Study",
            journal="Journal of Tobacco Research",
            date="2024-01-15",
            abstract="This randomized controlled trial examined cardiovascular effects in 200 participants who smoke. Participants who switched to electronic cigarettes showed improved cardiovascular markers compared to those who continued smoking traditional cigarettes over a 12-month period."
        )

        print(f"✓ Summarization successful!")
        print(f"\n  Results:")
        print(f"  - Subject: {result.subject.value}")
        print(f"  - Category: {result.category.value}")
        print(f"  - Entities: {[e.value for e in result.entity]}")
        print(f"  - Sentiment: {result.sentiment.value}")
        print(f"  - Summary: {result.summary[:100]}...")

        return True
    except Exception as e:
        print(f"✗ Sample article test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("="*80)
    print("GENAI SUMMARIZATION PIPELINE - TEST SUITE")
    print("="*80)

    results = []

    # Run tests
    results.append(("Imports", test_imports()))
    results.append(("Schema", test_schema()))
    results.append(("Repository", test_repository()))
    results.append(("API Key", test_api_key()))
    results.append(("Summarizer Init", test_summarizer()))
    results.append(("Sample Article", test_sample_article()))

    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)

    passed = sum(1 for _, result in results if result is True)
    failed = sum(1 for _, result in results if result is False)
    skipped = sum(1 for _, result in results if result is None)

    for name, result in results:
        if result is True:
            status = "✓ PASS"
        elif result is False:
            status = "✗ FAIL"
        else:
            status = "⊘ SKIP"

        print(f"{status:<10} {name}")

    print(f"\nTotal: {len(results)} | Passed: {passed} | Failed: {failed} | Skipped: {skipped}")

    if failed > 0:
        print("\n⚠ Some tests failed. Check output above for details.")
        return False
    elif passed == len(results):
        print("\n✓ All tests passed! Pipeline is ready to use.")
        print("\nNext steps:")
        print("  1. Check pending articles: python backend/scripts/run_summarization.py --stats-only")
        print("  2. Run pipeline: python backend/scripts/run_summarization.py --limit 10")
        return True
    else:
        print("\n⊘ Some tests were skipped (likely missing API key).")
        print("  Set GROQ_API_KEY in .env to run all tests.")
        return True

    print("="*80 + "\n")


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
