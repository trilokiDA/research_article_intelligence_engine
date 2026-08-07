"""
Database loader for Stage 5: Load approved analyses to article_analysis table.

This module handles:
1. Reading approved JSON files from data/analysis/approved/
2. Transforming JSON to database schema
3. UPSERT operations to article_analysis table
4. Archiving loaded files
5. Statistics and error tracking
"""

import json
import sqlite3
import shutil
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import uuid

from ..db.database import get_db, DATABASE_PATH


class AnalysisDatabaseLoader:
    """
    Loads approved GenAI analyses from JSON files into the article_analysis table.

    Features:
    - Idempotent UPSERT operations (safe to re-run)
    - Foreign key validation (article must exist)
    - Transaction support (all-or-nothing batch loads)
    - Archiving of loaded files
    - Detailed error tracking
    """

    def __init__(self, base_dir: str = "data/analysis"):
        """
        Initialize the database loader.

        Args:
            base_dir: Base directory for analysis files
        """
        self.base_dir = Path(base_dir)
        self.approved_dir = self.base_dir / "approved"
        self.archive_dir = self.base_dir / "loaded"

        # Create archive directory if it doesn't exist
        self.archive_dir.mkdir(parents=True, exist_ok=True)

        # Statistics tracking
        self.stats = {
            'total_files': 0,
            'loaded': 0,
            'updated': 0,
            'skipped': 0,
            'errors': 0,
            'error_details': []
        }

    def get_article_uuid(self, conn: sqlite3.Connection, article_id: str) -> Optional[str]:
        """
        Get the UUID (id) for an article by its article_id (e.g., PMID42396759).

        The article_analysis table has a foreign key to articles(id) which is a UUID,
        but our JSON files reference article_id (e.g., PMID42396759).
        This method maps article_id -> UUID id.

        Args:
            conn: Database connection
            article_id: Article identifier to look up (e.g., PMID42396759)

        Returns:
            UUID string if found, None otherwise
        """
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM articles WHERE article_id = ?", (article_id,))
        result = cursor.fetchone()
        return result['id'] if result else None

    def transform_json_to_record(self, json_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform approved JSON file to database record format.

        Args:
            json_data: Loaded JSON data from approved file

        Returns:
            Dictionary with database column names and values
        """
        article_id = json_data.get('article_id')
        analysis = json_data.get('analysis', {})
        metadata = json_data.get('metadata', {})
        evaluation = json_data.get('evaluation', {})

        # Generate unique ID
        record_id = str(uuid.uuid4())

        # Transform entities list to JSON string
        entities = analysis.get('entity', [])
        if isinstance(entities, list):
            entities_json = json.dumps(entities)
        else:
            entities_json = json.dumps([entities])

        # Extract evaluation score
        quality_score = evaluation.get('quality_score', {})
        if isinstance(quality_score, dict):
            evaluation_score = quality_score.get('overall_score', None)
        else:
            evaluation_score = None

        # Prepare evaluation metadata
        evaluation_metadata = json.dumps({
            'quality_score': quality_score,
            'hallucination_detected': evaluation.get('hallucination_detected', False),
            'people_first_violations': evaluation.get('people_first_violations', []),
            'entity_consistency': evaluation.get('entity_consistency', True),
            'claim_evaluations': evaluation.get('claim_evaluations', []),
            'feedback': evaluation.get('feedback', ''),
            'passed': evaluation.get('passed', True),
            'evaluated_at': evaluation.get('evaluated_at', '')
        })

        # Build database record
        record = {
            'id': record_id,
            'article_id': article_id,
            'subject': analysis.get('subject', None),
            'category': analysis.get('category', None),
            'summary': analysis.get('summary', None),
            'entities': entities_json,
            'sentiment': analysis.get('sentiment', None),
            'industry_affiliation': analysis.get('industry_affiliation', None),
            'model_id': metadata.get('model_id', 'unknown'),
            'prompt_version': metadata.get('prompt_version', 'v1'),
            'analyzed_at': json_data.get('processed_at', datetime.now().isoformat()),
            'analysis_status': 'completed',
            'evaluation_score': evaluation_score,
            'evaluation_metadata': evaluation_metadata,
            'stage': json_data.get('stage', 'approved'),
            'attempt': json_data.get('attempt', 1),
            'loaded_at': datetime.now().isoformat()
        }

        return record

    def load_single_file(
        self,
        file_path: Path,
        conn: sqlite3.Connection,
        dry_run: bool = False
    ) -> Tuple[bool, Optional[str]]:
        """
        Load a single approved JSON file to database.

        Args:
            file_path: Path to JSON file
            conn: Database connection
            dry_run: If True, validate but don't commit

        Returns:
            Tuple of (success: bool, error_message: Optional[str])
        """
        try:
            # Read JSON file
            with open(file_path, 'r', encoding='utf-8') as f:
                json_data = json.load(f)

            article_id = json_data.get('article_id')
            if not article_id:
                return False, "Missing article_id in JSON"

            # Get article UUID (foreign key reference)
            article_uuid = self.get_article_uuid(conn, article_id)
            if not article_uuid:
                return False, f"Article {article_id} not found in articles table (orphaned analysis)"

            # Transform to database record
            record = self.transform_json_to_record(json_data)

            if dry_run:
                # Dry run: just validate, don't insert
                return True, None

            # Check if record already exists
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id FROM article_analysis WHERE article_id = ?",
                (article_uuid,)
            )
            existing = cursor.fetchone()

            if existing:
                # Update existing record
                cursor.execute("""
                    UPDATE article_analysis SET
                        subject = ?,
                        category = ?,
                        summary = ?,
                        entities = ?,
                        sentiment = ?,
                        industry_affiliation = ?,
                        model_id = ?,
                        prompt_version = ?,
                        analyzed_at = ?,
                        analysis_status = ?,
                        evaluation_score = ?,
                        evaluation_metadata = ?,
                        stage = ?,
                        attempt = ?,
                        loaded_at = ?
                    WHERE article_id = ?
                """, (
                    record['subject'],
                    record['category'],
                    record['summary'],
                    record['entities'],
                    record['sentiment'],
                    record['industry_affiliation'],
                    record['model_id'],
                    record['prompt_version'],
                    record['analyzed_at'],
                    record['analysis_status'],
                    record['evaluation_score'],
                    record['evaluation_metadata'],
                    record['stage'],
                    record['attempt'],
                    record['loaded_at'],
                    article_uuid
                ))
                self.stats['updated'] += 1
            else:
                # Insert new record (use article_uuid for foreign key)
                cursor.execute("""
                    INSERT INTO article_analysis (
                        id, article_id, subject, category, summary,
                        entities, sentiment, industry_affiliation,
                        model_id, prompt_version, analyzed_at, analysis_status,
                        evaluation_score, evaluation_metadata, stage, attempt, loaded_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    record['id'],
                    article_uuid,  # Use UUID for foreign key reference
                    record['subject'],
                    record['category'],
                    record['summary'],
                    record['entities'],
                    record['sentiment'],
                    record['industry_affiliation'],
                    record['model_id'],
                    record['prompt_version'],
                    record['analyzed_at'],
                    record['analysis_status'],
                    record['evaluation_score'],
                    record['evaluation_metadata'],
                    record['stage'],
                    record['attempt'],
                    record['loaded_at']
                ))
                self.stats['loaded'] += 1

            # Update articles table: mark this article as analyzed
            cursor.execute("""
                UPDATE articles
                SET analysis_status = 'analyzed',
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (article_uuid,))

            conn.commit()
            return True, None

        except json.JSONDecodeError as e:
            return False, f"Invalid JSON: {e}"
        except sqlite3.IntegrityError as e:
            return False, f"Database constraint violation: {e}"
        except Exception as e:
            return False, f"Unexpected error: {e}"

    def archive_file(self, file_path: Path) -> bool:
        """
        Move loaded file to archive directory.

        Args:
            file_path: Path to file to archive

        Returns:
            True if archived successfully, False otherwise
        """
        try:
            destination = self.archive_dir / file_path.name
            shutil.move(str(file_path), str(destination))
            return True
        except Exception as e:
            print(f"[WARNING] Failed to archive {file_path.name}: {e}")
            return False

    def load_approved_files(
        self,
        article_ids: Optional[List[str]] = None,
        limit: Optional[int] = None,
        dry_run: bool = False,
        archive: bool = False
    ) -> Dict[str, Any]:
        """
        Load all approved files (or specific article IDs) to database.

        Args:
            article_ids: Optional list of specific article IDs to load
            limit: Maximum number of files to load
            dry_run: If True, validate but don't commit to database
            archive: If True, move loaded files to archive directory

        Returns:
            Dictionary with statistics and results
        """
        # Reset statistics
        self.stats = {
            'total_files': 0,
            'loaded': 0,
            'updated': 0,
            'skipped': 0,
            'errors': 0,
            'error_details': []
        }

        # Find files to load
        if article_ids:
            files = [self.approved_dir / f"{aid}.json" for aid in article_ids]
            files = [f for f in files if f.exists()]
        else:
            files = list(self.approved_dir.glob("*.json"))

        # Apply limit
        if limit:
            files = files[:limit]

        self.stats['total_files'] = len(files)

        if not files:
            return self.stats

        # Process files
        with get_db() as conn:
            for file_path in files:
                success, error = self.load_single_file(file_path, conn, dry_run)

                if success:
                    # Archive if requested and not dry run
                    if archive and not dry_run:
                        self.archive_file(file_path)
                else:
                    self.stats['errors'] += 1
                    self.stats['error_details'].append({
                        'file': file_path.name,
                        'error': error
                    })

        return self.stats

    def batch_load(
        self,
        files: List[Path],
        dry_run: bool = False,
        archive: bool = False
    ) -> Dict[str, Any]:
        """
        Load a batch of files with transaction support.

        Args:
            files: List of file paths to load
            dry_run: If True, validate but don't commit
            archive: If True, move loaded files to archive

        Returns:
            Statistics dictionary
        """
        self.stats = {
            'total_files': len(files),
            'loaded': 0,
            'updated': 0,
            'skipped': 0,
            'errors': 0,
            'error_details': []
        }

        with get_db() as conn:
            for file_path in files:
                success, error = self.load_single_file(file_path, conn, dry_run)

                if success:
                    if archive and not dry_run:
                        self.archive_file(file_path)
                else:
                    self.stats['errors'] += 1
                    self.stats['error_details'].append({
                        'file': file_path.name,
                        'error': error
                    })

        return self.stats

    def get_load_summary(self) -> str:
        """
        Get human-readable summary of load operation.

        Returns:
            Formatted summary string
        """
        summary = f"""
[LOAD SUMMARY]
Total files: {self.stats['total_files']}
Loaded (new): {self.stats['loaded']}
Updated (existing): {self.stats['updated']}
Errors: {self.stats['errors']}
"""
        if self.stats['error_details']:
            summary += "\n[ERRORS]\n"
            for error in self.stats['error_details'][:5]:  # Show first 5 errors
                summary += f"  - {error['file']}: {error['error']}\n"
            if len(self.stats['error_details']) > 5:
                summary += f"  ... and {len(self.stats['error_details']) - 5} more errors\n"

        return summary


if __name__ == "__main__":
    import sys
    from pathlib import Path

    # Add parent directories to path for standalone testing
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))

    from app.db.database import get_db, DATABASE_PATH

    # Test the database loader
    print("Testing AnalysisDatabaseLoader...")

    loader = AnalysisDatabaseLoader()

    print(f"\n[OK] Base directory: {loader.base_dir}")
    print(f"[OK] Approved directory: {loader.approved_dir}")
    print(f"[OK] Archive directory: {loader.archive_dir}")

    # Count approved files
    approved_files = list(loader.approved_dir.glob("*.json"))
    print(f"\n[INFO] Found {len(approved_files)} approved files")

    if approved_files:
        print("\n[TEST] Dry run on first file...")
        stats = loader.load_approved_files(limit=1, dry_run=True)
        print(loader.get_load_summary())

    print("\n[OK] AnalysisDatabaseLoader test complete!")
