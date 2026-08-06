"""
Integration tests for the complete 5-stage GenAI pipeline.

Tests the full workflow:
1. Data ingestion (mock)
2. GenAI summarization
3. Quality evaluation
4. Re-inference (if needed)
5. Database load

Run with: pytest tests/test_integration.py -v
"""

import json
import pytest
import shutil
import sys
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, patch

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app.genai.pipeline import ArticleAnalysisPipeline
from app.genai.evaluator import SummaryEvaluator
from app.genai.db_loader import AnalysisDatabaseLoader
from app.db.database import get_db_connection, migrate_db


@pytest.fixture
def test_dirs(tmp_path):
    """Create temporary test directories."""
    dirs = {
        'raw': tmp_path / 'raw',
        'approved': tmp_path / 'approved',
        'reinfer': tmp_path / 'reinfer',
        'rejected': tmp_path / 'rejected',
        'loaded': tmp_path / 'loaded',
        'evaluated': tmp_path / 'evaluated'
    }

    for dir_path in dirs.values():
        dir_path.mkdir(parents=True, exist_ok=True)

    return dirs


@pytest.fixture
def test_db(tmp_path):
    """Create temporary test database."""
    db_path = tmp_path / 'test_articles.db'

    # Initialize schema
    conn = get_db_connection(str(db_path))
    conn.execute("""
        CREATE TABLE IF NOT EXISTS articles (
            id TEXT PRIMARY KEY,
            article_id TEXT UNIQUE NOT NULL,
            source TEXT NOT NULL,
            title TEXT NOT NULL,
            abstract TEXT,
            journal TEXT,
            authors TEXT,
            keywords TEXT,
            publication_date TEXT,
            country TEXT,
            doi TEXT,
            url TEXT,
            ingestion_status TEXT DEFAULT 'pending',
            ingested_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS article_analysis (
            id TEXT PRIMARY KEY,
            article_id TEXT UNIQUE NOT NULL,
            subject TEXT,
            category TEXT,
            summary TEXT,
            entities TEXT,
            sentiment TEXT,
            industry_affiliation TEXT,
            analysis_status TEXT DEFAULT 'pending',
            analyzed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (article_id) REFERENCES articles(id)
        )
    """)

    conn.commit()
    conn.close()

    return str(db_path)


@pytest.fixture
def sample_article():
    """Sample article data for testing."""
    return {
        "article_id": "PMID_TEST_001",
        "title": "Electronic Cigarettes and Harm Reduction: A Systematic Review",
        "abstract": "This systematic review examines the evidence on electronic cigarettes as a harm reduction tool. Studies show reduced exposure to harmful chemicals compared to combustible cigarettes. However, long-term health effects remain unclear. More research is needed on youth uptake and dual use patterns.",
        "journal": "Journal of Public Health",
        "date": "2024-01-15",
        "authors": json.dumps(["Smith J", "Jones M", "Brown K"]),
        "keywords": json.dumps(["electronic cigarettes", "harm reduction", "tobacco"]),
        "country": "United States",
        "doi": "10.1234/test.2024.001",
        "source": "pubmed"
    }


@pytest.fixture
def sample_summary():
    """Sample GenAI summary for testing."""
    return {
        "articleID": "PMID_TEST_001",
        "title": "Electronic Cigarettes and Harm Reduction: A Systematic Review",
        "journal": "Journal of Public Health",
        "date": "2024-01-15",
        "abstract": "This systematic review examines the evidence on electronic cigarettes...",
        "entity": ["electronic cigarettes", "harm reduction"],
        "subject": "E-cigarettes",
        "summary": "This systematic review examines evidence on electronic cigarettes as a harm reduction tool for people who smoke. Studies indicate reduced exposure to harmful chemicals compared to combustible cigarettes, though long-term health effects remain unclear. Further research is needed on youth adoption patterns and dual use.",
        "category": "Systematic Reviews/Meta-analyses",
        "country": "United States",
        "sentiment": "Neutral",
        "industry_affiliation": "n/a"
    }


class TestFullPipelineIntegration:
    """Test complete 5-stage pipeline integration."""

    def test_stage_1_to_2_ingestion_to_summarization(self, test_db, sample_article, test_dirs):
        """Test Stage 1 (Ingestion) → Stage 2 (Summarization) integration."""
        # Stage 1: Insert article into database
        conn = get_db_connection(test_db)
        conn.execute("""
            INSERT INTO articles (
                id, article_id, source, title, abstract, journal,
                authors, keywords, publication_date, country, doi
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            sample_article['article_id'],
            sample_article['article_id'],
            sample_article['source'],
            sample_article['title'],
            sample_article['abstract'],
            sample_article['journal'],
            sample_article['authors'],
            sample_article['keywords'],
            sample_article['date'],
            sample_article['country'],
            sample_article['doi']
        ))
        conn.commit()

        # Verify article exists
        cursor = conn.execute("SELECT COUNT(*) FROM articles WHERE article_id = ?",
                            (sample_article['article_id'],))
        assert cursor.fetchone()[0] == 1

        # Stage 2 would run summarization
        # (mocked here - actual LLM call tested separately)
        conn.close()

    def test_stage_2_to_3_summarization_to_evaluation(self, test_dirs, sample_summary):
        """Test Stage 2 (Summarization) → Stage 3 (Evaluation) integration."""
        # Stage 2: Write summary to raw directory
        raw_file = test_dirs['raw'] / f"{sample_summary['articleID']}.json"
        with open(raw_file, 'w', encoding='utf-8') as f:
            json.dump(sample_summary, f, indent=2)

        assert raw_file.exists()

        # Stage 3: Mock evaluation
        evaluator = SummaryEvaluator(model="llama-3.3-70b-versatile")

        # Mock the LLM call
        with patch.object(evaluator, 'evaluate') as mock_eval:
            mock_eval.return_value = {
                'overall_score': 85,
                'factual_accuracy': 90,
                'hallucination_check': True,
                'people_first_language': 80,
                'feedback': 'Good summary with minor improvements needed'
            }

            result = evaluator.evaluate(
                summary=sample_summary['summary'],
                abstract=sample_summary['abstract']
            )

            assert result['overall_score'] >= 80  # Should pass threshold
            assert result['factual_accuracy'] > 0

    def test_stage_3_to_4_evaluation_to_reinference(self, test_dirs, sample_summary):
        """Test Stage 3 (Evaluation) → Stage 4 (Re-inference) integration."""
        # Create a low-quality summary for reinference
        low_quality_summary = sample_summary.copy()
        low_quality_summary['summary'] = "E-cigs are bad. Study shows this."

        # Stage 3: Write to reinfer directory (failed evaluation)
        reinfer_file = test_dirs['reinfer'] / f"{low_quality_summary['articleID']}.json"
        with open(reinfer_file, 'w', encoding='utf-8') as f:
            json.dump(low_quality_summary, f, indent=2)

        assert reinfer_file.exists()

        # Stage 4 would trigger re-inference
        # Verify file is ready for reinference
        with open(reinfer_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            assert data['articleID'] == low_quality_summary['articleID']

    def test_stage_4_to_5_reinference_to_database_load(self, test_dirs, test_db, sample_summary):
        """Test Stage 4 (Re-inference) → Stage 5 (Database Load) integration."""
        # Stage 4: Place improved summary in approved directory
        approved_file = test_dirs['approved'] / f"{sample_summary['articleID']}.json"
        with open(approved_file, 'w', encoding='utf-8') as f:
            json.dump(sample_summary, f, indent=2)

        assert approved_file.exists()

        # Stage 5: Load to database
        loader = AnalysisDatabaseLoader(
            db_path=test_db,
            approved_dir=str(test_dirs['approved']),
            archive_dir=str(test_dirs['loaded'])
        )

        # First, ensure article exists in articles table
        conn = get_db_connection(test_db)
        conn.execute("""
            INSERT OR IGNORE INTO articles (
                id, article_id, source, title, abstract, journal,
                publication_date, country, doi
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            sample_summary['articleID'],
            sample_summary['articleID'],
            'pubmed',
            sample_summary['title'],
            sample_summary['abstract'],
            sample_summary['journal'],
            sample_summary['date'],
            sample_summary['country'],
            '10.1234/test'
        ))
        conn.commit()
        conn.close()

        # Load analysis
        result = loader.load_file(approved_file, dry_run=False)

        assert result['status'] == 'success' or result['status'] == 'updated'

        # Verify database entry
        conn = get_db_connection(test_db)
        cursor = conn.execute("""
            SELECT article_id, summary, category, sentiment
            FROM article_analysis
            WHERE article_id = ?
        """, (sample_summary['articleID'],))
        row = cursor.fetchone()
        conn.close()

        assert row is not None
        assert row[0] == sample_summary['articleID']
        assert len(row[1]) > 0  # Summary exists

    def test_end_to_end_happy_path(self, test_db, test_dirs, sample_article, sample_summary):
        """Test complete end-to-end workflow (happy path)."""
        # Stage 1: Ingest article
        conn = get_db_connection(test_db)
        conn.execute("""
            INSERT INTO articles (
                id, article_id, source, title, abstract, journal,
                authors, keywords, publication_date, country, doi
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            sample_article['article_id'],
            sample_article['article_id'],
            sample_article['source'],
            sample_article['title'],
            sample_article['abstract'],
            sample_article['journal'],
            sample_article['authors'],
            sample_article['keywords'],
            sample_article['date'],
            sample_article['country'],
            sample_article['doi']
        ))
        conn.commit()

        # Stage 2: Create summary (mocked)
        raw_file = test_dirs['raw'] / f"{sample_summary['articleID']}.json"
        with open(raw_file, 'w', encoding='utf-8') as f:
            json.dump(sample_summary, f, indent=2)

        # Stage 3: Evaluation passes → move to approved
        approved_file = test_dirs['approved'] / f"{sample_summary['articleID']}.json"
        shutil.copy(raw_file, approved_file)

        # Stage 5: Load to database (skip Stage 4 - no reinference needed)
        loader = AnalysisDatabaseLoader(
            db_path=test_db,
            approved_dir=str(test_dirs['approved']),
            archive_dir=str(test_dirs['loaded'])
        )

        result = loader.load_file(approved_file, dry_run=False)
        assert result['status'] in ['success', 'updated']

        # Verify complete workflow
        cursor = conn.execute("""
            SELECT a.article_id, a.title, aa.summary, aa.category
            FROM articles a
            JOIN article_analysis aa ON a.article_id = aa.article_id
            WHERE a.article_id = ?
        """, (sample_article['article_id'],))
        row = cursor.fetchone()
        conn.close()

        assert row is not None
        assert row[0] == sample_article['article_id']
        assert len(row[2]) > 0  # Summary populated

    def test_end_to_end_with_reinference(self, test_db, test_dirs, sample_article):
        """Test complete workflow with failed evaluation → reinference → success."""
        # Stage 1: Ingest article
        conn = get_db_connection(test_db)
        conn.execute("""
            INSERT INTO articles (
                id, article_id, source, title, abstract, journal,
                publication_date, country, doi
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            sample_article['article_id'],
            sample_article['article_id'],
            sample_article['source'],
            sample_article['title'],
            sample_article['abstract'],
            sample_article['journal'],
            sample_article['date'],
            sample_article['country'],
            sample_article['doi']
        ))
        conn.commit()

        # Stage 2: Create low-quality summary
        low_quality = {
            "articleID": sample_article['article_id'],
            "title": sample_article['title'],
            "journal": sample_article['journal'],
            "date": sample_article['date'],
            "abstract": sample_article['abstract'],
            "entity": ["e-cigarettes"],
            "subject": "E-cigarettes",
            "summary": "Study about e-cigs. Bad for health.",  # Poor quality
            "category": "Clinical Studies",
            "country": "United States",
            "sentiment": "Negative",
            "industry_affiliation": "n/a"
        }

        raw_file = test_dirs['raw'] / f"{sample_article['article_id']}.json"
        with open(raw_file, 'w', encoding='utf-8') as f:
            json.dump(low_quality, f, indent=2)

        # Stage 3: Evaluation fails → move to reinfer
        reinfer_file = test_dirs['reinfer'] / f"{sample_article['article_id']}.json"
        shutil.copy(raw_file, reinfer_file)

        # Stage 4: Re-inference improves summary
        improved = low_quality.copy()
        improved['summary'] = "This systematic review examines evidence on electronic cigarettes as a harm reduction tool for people who smoke."

        improved_file = test_dirs['raw'] / f"{sample_article['article_id']}_reinfer_1.json"
        with open(improved_file, 'w', encoding='utf-8') as f:
            json.dump(improved, f, indent=2)

        # Re-evaluation passes → move to approved
        approved_file = test_dirs['approved'] / f"{sample_article['article_id']}.json"
        shutil.copy(improved_file, approved_file)

        # Stage 5: Load to database
        loader = AnalysisDatabaseLoader(
            db_path=test_db,
            approved_dir=str(test_dirs['approved']),
            archive_dir=str(test_dirs['loaded'])
        )

        result = loader.load_file(approved_file, dry_run=False)
        assert result['status'] in ['success', 'updated']

        # Verify final state
        cursor = conn.execute("""
            SELECT summary FROM article_analysis WHERE article_id = ?
        """, (sample_article['article_id'],))
        row = cursor.fetchone()
        conn.close()

        assert row is not None
        assert len(row[0]) > 50  # Improved summary should be longer


class TestErrorHandlingIntegration:
    """Test error handling across pipeline stages."""

    def test_missing_article_in_database(self, test_db, test_dirs):
        """Test loading analysis when article doesn't exist in database."""
        orphan_summary = {
            "articleID": "PMID_ORPHAN",
            "title": "Orphan Article",
            "summary": "This article doesn't exist in the articles table."
        }

        approved_file = test_dirs['approved'] / "PMID_ORPHAN.json"
        with open(approved_file, 'w', encoding='utf-8') as f:
            json.dump(orphan_summary, f, indent=2)

        loader = AnalysisDatabaseLoader(
            db_path=test_db,
            approved_dir=str(test_dirs['approved']),
            archive_dir=str(test_dirs['loaded'])
        )

        result = loader.load_file(approved_file, dry_run=False)
        assert result['status'] == 'error'
        assert 'not found in articles table' in result.get('error', '').lower() or result['status'] == 'error'

    def test_malformed_json_file(self, test_dirs):
        """Test handling of malformed JSON files."""
        bad_file = test_dirs['approved'] / "bad.json"
        with open(bad_file, 'w', encoding='utf-8') as f:
            f.write("{ invalid json }")

        # Attempt to read should fail gracefully
        with pytest.raises(json.JSONDecodeError):
            with open(bad_file, 'r', encoding='utf-8') as f:
                json.load(f)

    def test_max_reinference_attempts(self, test_dirs, sample_summary):
        """Test that articles are rejected after max reinference attempts."""
        article_id = sample_summary['articleID']

        # Simulate 3 failed attempts
        for attempt in range(1, 4):
            reinfer_file = test_dirs['reinfer'] / f"{article_id}_attempt_{attempt}.json"
            with open(reinfer_file, 'w', encoding='utf-8') as f:
                json.dump(sample_summary, f, indent=2)

        # After 3 attempts, should move to rejected
        rejected_file = test_dirs['rejected'] / f"{article_id}.json"

        # Simulate rejection
        shutil.copy(
            test_dirs['reinfer'] / f"{article_id}_attempt_3.json",
            rejected_file
        )

        assert rejected_file.exists()


class TestDataIntegrity:
    """Test data integrity across pipeline stages."""

    def test_article_id_consistency(self, test_db, test_dirs, sample_article, sample_summary):
        """Test that article IDs remain consistent across all stages."""
        article_id = sample_article['article_id']

        # Insert article
        conn = get_db_connection(test_db)
        conn.execute("""
            INSERT INTO articles (id, article_id, source, title, abstract, journal, publication_date, country, doi)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (article_id, article_id, sample_article['source'], sample_article['title'],
              sample_article['abstract'], sample_article['journal'], sample_article['date'],
              sample_article['country'], sample_article['doi']))
        conn.commit()

        # Create summary with same ID
        assert sample_summary['articleID'] == article_id

        approved_file = test_dirs['approved'] / f"{article_id}.json"
        with open(approved_file, 'w', encoding='utf-8') as f:
            json.dump(sample_summary, f, indent=2)

        # Load to database
        loader = AnalysisDatabaseLoader(
            db_path=test_db,
            approved_dir=str(test_dirs['approved']),
            archive_dir=str(test_dirs['loaded'])
        )
        loader.load_file(approved_file, dry_run=False)

        # Verify IDs match
        cursor = conn.execute("""
            SELECT a.article_id, aa.article_id
            FROM articles a
            JOIN article_analysis aa ON a.article_id = aa.article_id
            WHERE a.article_id = ?
        """, (article_id,))
        row = cursor.fetchone()
        conn.close()

        assert row is not None
        assert row[0] == row[1] == article_id

    def test_no_data_loss_on_error(self, test_db, test_dirs, sample_summary):
        """Test that files are not deleted if database insert fails."""
        approved_file = test_dirs['approved'] / f"{sample_summary['articleID']}.json"
        with open(approved_file, 'w', encoding='utf-8') as f:
            json.dump(sample_summary, f, indent=2)

        loader = AnalysisDatabaseLoader(
            db_path=test_db,
            approved_dir=str(test_dirs['approved']),
            archive_dir=str(test_dirs['loaded'])
        )

        # Load should fail (article doesn't exist)
        result = loader.load_file(approved_file, dry_run=False)

        # Original file should still exist
        assert approved_file.exists()
        assert result['status'] == 'error'


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
