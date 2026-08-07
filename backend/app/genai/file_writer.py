"""
File-based output writer for GenAI pipeline.
Saves article analysis results to JSON files for quality control workflow.
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime

from .schemas import Response


class AnalysisFileWriter:
    """
    Handles writing and reading analysis results to/from JSON files.

    Directory structure:
        data/analysis/
        ├── summarized/    - GenAI summarization outputs (Stage 2)
        ├── evaluated/     - After quality evaluation (Stage 3)
        ├── approved/      - Passed quality gate (Stage 3)
        ├── reinfer/       - Failed, needs retry (Stage 3)
        └── rejected/      - Failed after max retries (Stage 3)
    """

    def __init__(self, base_dir: str = "data/analysis"):
        """
        Initialize the file writer.

        Args:
            base_dir: Base directory for analysis files
        """
        self.base_dir = Path(base_dir)
        self.raw_dir = self.base_dir / "raw"  # NEW: raw outputs
        self.summarized_dir = self.base_dir / "summarized"  # LEGACY: for backward compatibility
        self.evaluated_dir = self.base_dir / "evaluated"
        self.approved_dir = self.base_dir / "approved"
        self.reinfer_dir = self.base_dir / "reinfer"
        self.rejected_dir = self.base_dir / "rejected"

        # Ensure directories exist
        self._ensure_directories()

    def _ensure_directories(self):
        """Create directories if they don't exist."""
        for directory in [
            self.raw_dir,  # NEW
            self.summarized_dir,
            self.evaluated_dir,
            self.approved_dir,
            self.reinfer_dir,
            self.rejected_dir
        ]:
            directory.mkdir(parents=True, exist_ok=True)

    def save_summarized_analysis(
        self,
        article_id: str,
        response: Response,
        source_data: Dict[str, Any],
        metadata: Dict[str, Any],
        attempt: int = 1
    ) -> Path:
        """
        Save GenAI summarization output to JSON file.

        Args:
            article_id: Unique article identifier (e.g., PMID001)
            response: Response object from summarization
            source_data: Original article data (title, abstract, journal, etc.)
            metadata: Processing metadata (time, tokens, cost, model info)
            attempt: Attempt number (default: 1)

        Returns:
            Path to saved file

        Raises:
            IOError: If file cannot be written
        """
        file_path = self.summarized_dir / f"{article_id}.json"

        # Build complete analysis record
        analysis_record = {
            "article_id": article_id,
            "stage": "summarized",
            "attempt": attempt,
            "processed_at": datetime.now().isoformat(),
            "model": metadata.get("model_id", "unknown"),
            "prompt_version": metadata.get("prompt_version", "v1"),

            "source_data": source_data,

            "analysis": {
                "articleID": response.articleID,
                "title": response.title,
                "journal": response.journal,
                "date": response.date,
                "abstract": response.abstract,
                "entity": [e.value for e in response.entity],
                "subject": response.subject.value,
                "summary": response.summary,
                "category": response.category.value,
                "country": response.country,
                "sentiment": response.sentiment.value,
                "industry_affiliation": response.industry_affiliation
            },

            "metadata": {
                "processing_time_ms": metadata.get("processing_time_ms", 0),
                "tokens_used": metadata.get("tokens_used", 0),
                "cost_usd": metadata.get("cost_usd", 0.0),
                "model_id": metadata.get("model_id", "unknown"),
                "prompt_version": metadata.get("prompt_version", "v1"),
                "success": metadata.get("success", True),
                "error": metadata.get("error", None)
            }
        }

        try:
            # Ensure directory exists
            file_path.parent.mkdir(parents=True, exist_ok=True)

            with open(file_path, 'w', encoding='utf-8', errors='replace') as f:
                json.dump(analysis_record, f, indent=2, ensure_ascii=False)
            return file_path

        except Exception as e:
            # Try again with ASCII-safe encoding as fallback
            try:
                with open(file_path, 'w', encoding='utf-8', errors='replace') as f:
                    json.dump(analysis_record, f, indent=2, ensure_ascii=True)
                print(f"[WARNING] Saved {article_id} with ASCII encoding due to Unicode error")
                return file_path
            except Exception as e2:
                raise IOError(f"Failed to write analysis file for {article_id}: {e} / {e2}")

    def load_summarized_analysis(self, article_id: str) -> Optional[Dict[str, Any]]:
        """
        Load summarized analysis from JSON file.

        Args:
            article_id: Article identifier

        Returns:
            Analysis dictionary or None if file doesn't exist
        """
        file_path = self.summarized_dir / f"{article_id}.json"

        if not file_path.exists():
            return None

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"[WARNING] Failed to load {file_path}: {e}")
            return None

    def exists_summarized_analysis(self, article_id: str) -> bool:
        """
        Check if summarized analysis file exists.

        Args:
            article_id: Article identifier

        Returns:
            True if file exists, False otherwise
        """
        file_path = self.summarized_dir / f"{article_id}.json"
        return file_path.exists()

    def list_summarized_analyses(self) -> List[str]:
        """
        List all article IDs with summarized analysis files.

        Returns:
            List of article IDs (without .json extension)
        """
        return [f.stem for f in self.summarized_dir.glob("*.json")]

    def count_summarized_analyses(self) -> int:
        """
        Count number of summarized analysis files.

        Returns:
            Count of JSON files in summarized directory
        """
        return len(list(self.summarized_dir.glob("*.json")))

    def get_processing_stats(self) -> Dict[str, Any]:
        """
        Get statistics from all analysis files (checks raw/ and summarized/ for backward compatibility).

        Returns:
            Dictionary with processing statistics
        """
        stats = {
            "total_files": 0,
            "successful": 0,
            "failed": 0,
            "total_processing_time_ms": 0,
            "total_tokens": 0,
            "total_cost_usd": 0.0,
            "by_model": {},
            "by_category": {},
            "by_sentiment": {},
            "by_subject": {}
        }

        # Check raw/ directory (Stage 2 output) and summarized/ (legacy)
        for directory in [self.raw_dir, self.summarized_dir]:
            if not directory.exists():
                continue

            for file_path in directory.glob("*.json"):
                stats["total_files"] += 1

                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)

                    # Success/failure
                    if data.get("metadata", {}).get("success", True):
                        stats["successful"] += 1
                    else:
                        stats["failed"] += 1

                    # Aggregate metadata
                    metadata = data.get("metadata", {})
                    stats["total_processing_time_ms"] += metadata.get("processing_time_ms", 0)
                    stats["total_tokens"] += metadata.get("tokens_used", 0)
                    stats["total_cost_usd"] += metadata.get("cost_usd", 0.0)

                    # By model
                    model = metadata.get("model_id", "unknown")
                    stats["by_model"][model] = stats["by_model"].get(model, 0) + 1

                    # By category, sentiment, subject
                    analysis = data.get("analysis", {})
                    category = analysis.get("category", "unknown")
                    sentiment = analysis.get("sentiment", "unknown")
                    subject = analysis.get("subject", "unknown")

                    stats["by_category"][category] = stats["by_category"].get(category, 0) + 1
                    stats["by_sentiment"][sentiment] = stats["by_sentiment"].get(sentiment, 0) + 1
                    stats["by_subject"][subject] = stats["by_subject"].get(subject, 0) + 1

                except Exception as e:
                    print(f"[WARNING] Failed to process {file_path}: {e}")
                    stats["failed"] += 1

        # Calculate averages
        if stats["total_files"] > 0:
            stats["avg_processing_time_ms"] = stats["total_processing_time_ms"] / stats["total_files"]
            stats["avg_tokens"] = stats["total_tokens"] / stats["total_files"]
            stats["avg_cost_usd"] = stats["total_cost_usd"] / stats["total_files"]
        else:
            stats["avg_processing_time_ms"] = 0
            stats["avg_tokens"] = 0
            stats["avg_cost_usd"] = 0.0

        return stats

    def delete_summarized_analysis(self, article_id: str) -> bool:
        """
        Delete summarized analysis file.

        Args:
            article_id: Article identifier

        Returns:
            True if deleted, False if file didn't exist
        """
        file_path = self.summarized_dir / f"{article_id}.json"

        if file_path.exists():
            try:
                file_path.unlink()
                return True
            except Exception as e:
                print(f"[WARNING] Failed to delete {file_path}: {e}")
                return False
        return False

    def get_file_path(self, article_id: str, stage: str = "raw") -> Path:
        """
        Get file path for an article at a specific stage.

        Args:
            article_id: Article identifier
            stage: Stage name (raw, summarized, evaluated, approved, reinfer, rejected)

        Returns:
            Path object for the file
        """
        stage_dirs = {
            "raw": self.raw_dir,  # NEW
            "summarized": self.summarized_dir,
            "evaluated": self.evaluated_dir,
            "approved": self.approved_dir,
            "reinfer": self.reinfer_dir,
            "rejected": self.rejected_dir
        }

        if stage not in stage_dirs:
            raise ValueError(f"Invalid stage: {stage}. Must be one of: {list(stage_dirs.keys())}")

        return stage_dirs[stage] / f"{article_id}.json"

    # NEW METHODS FOR 5-STAGE ARCHITECTURE

    def save_raw_analysis(
        self,
        article_id: str,
        response: Response,
        source_data: Dict[str, Any],
        metadata: Dict[str, Any],
        attempt: int = 1
    ) -> Path:
        """
        Save GenAI summarization output to raw/ directory.

        Args:
            article_id: Unique article identifier (e.g., PMID001)
            response: Response object from summarization
            source_data: Original article data (title, abstract, journal, etc.)
            metadata: Processing metadata (time, tokens, cost, model info)
            attempt: Attempt number (default: 1)

        Returns:
            Path to saved file
        """
        file_path = self.raw_dir / f"{article_id}.json"

        # Build complete analysis record
        analysis_record = {
            "article_id": article_id,
            "stage": "raw",  # Stage 2: Raw GenAI output
            "attempt": attempt,
            "processed_at": datetime.now().isoformat(),
            "model": metadata.get("model_id", "unknown"),
            "prompt_version": metadata.get("prompt_version", "v1"),

            "source_data": source_data,

            "analysis": {
                "articleID": response.articleID,
                "title": response.title,
                "journal": response.journal,
                "date": response.date,
                "abstract": response.abstract,
                "entity": [e.value for e in response.entity],
                "subject": response.subject.value,
                "summary": response.summary,
                "category": response.category.value,
                "country": response.country,
                "sentiment": response.sentiment.value,
                "industry_affiliation": response.industry_affiliation
            },

            "metadata": {
                "processing_time_ms": metadata.get("processing_time_ms", 0),
                "tokens_used": metadata.get("tokens_used", 0),
                "cost_usd": metadata.get("cost_usd", 0.0),
                "model_id": metadata.get("model_id", "unknown"),
                "prompt_version": metadata.get("prompt_version", "v1"),
                "success": metadata.get("success", True),
                "error": metadata.get("error", None)
            }
        }

        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, 'w', encoding='utf-8', errors='replace') as f:
                json.dump(analysis_record, f, indent=2, ensure_ascii=False)
            return file_path
        except Exception as e:
            try:
                with open(file_path, 'w', encoding='utf-8', errors='replace') as f:
                    json.dump(analysis_record, f, indent=2, ensure_ascii=True)
                print(f"[WARNING] Saved {article_id} with ASCII encoding due to Unicode error")
                return file_path
            except Exception as e2:
                raise IOError(f"Failed to write raw analysis file for {article_id}: {e} / {e2}")

    def load_raw_analysis(self, article_id: str) -> Optional[Dict[str, Any]]:
        """Load raw analysis from JSON file."""
        file_path = self.raw_dir / f"{article_id}.json"
        if not file_path.exists():
            return None
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"[WARNING] Failed to load {file_path}: {e}")
            return None

    def list_raw_analyses(self) -> List[str]:
        """List all article IDs with raw analysis files."""
        return [f.stem for f in self.raw_dir.glob("*.json")]

    def save_evaluated_analysis(
        self,
        article_id: str,
        raw_analysis: Dict[str, Any],
        evaluation_result: Dict[str, Any],
        evaluation_metadata: Dict[str, Any]
    ) -> Path:
        """
        Save evaluated analysis with evaluation results attached.

        Args:
            article_id: Article identifier
            raw_analysis: Original raw analysis data
            evaluation_result: Evaluation result from evaluator
            evaluation_metadata: Evaluation metadata

        Returns:
            Path to saved file
        """
        file_path = self.evaluated_dir / f"{article_id}.json"

        # Combine raw analysis with evaluation
        evaluated_record = {
            **raw_analysis,
            "stage": "evaluated",
            "evaluation": evaluation_result,
            "evaluation_metadata": evaluation_metadata
        }

        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, 'w', encoding='utf-8', errors='replace') as f:
                json.dump(evaluated_record, f, indent=2, ensure_ascii=False)
            return file_path
        except Exception as e:
            raise IOError(f"Failed to write evaluated analysis file for {article_id}: {e}")

    def move_to_approved(self, article_id: str) -> Path:
        """
        Move evaluated analysis to approved directory.

        Args:
            article_id: Article identifier

        Returns:
            Path to new location
        """
        source = self.evaluated_dir / f"{article_id}.json"
        destination = self.approved_dir / f"{article_id}.json"

        if not source.exists():
            raise FileNotFoundError(f"Evaluated file not found: {source}")

        try:
            # Load, update stage, and save
            with open(source, 'r', encoding='utf-8') as f:
                data = json.load(f)

            data["stage"] = "approved"

            with open(destination, 'w', encoding='utf-8', errors='replace') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            # Remove from evaluated
            source.unlink()

            return destination
        except Exception as e:
            raise IOError(f"Failed to move {article_id} to approved: {e}")

    def move_to_reinfer(
        self,
        article_id: str,
        feedback: str,
        attempt: int = 1
    ) -> Path:
        """
        Move evaluated analysis to reinfer directory with feedback.

        Args:
            article_id: Article identifier
            feedback: Feedback for improvement
            attempt: Attempt number

        Returns:
            Path to new location
        """
        source = self.evaluated_dir / f"{article_id}.json"
        destination = self.reinfer_dir / f"{article_id}.json"

        if not source.exists():
            raise FileNotFoundError(f"Evaluated file not found: {source}")

        try:
            # Load, update stage and feedback, and save
            with open(source, 'r', encoding='utf-8') as f:
                data = json.load(f)

            data["stage"] = "reinfer"
            data["reinfer_feedback"] = feedback
            data["attempt"] = attempt

            with open(destination, 'w', encoding='utf-8', errors='replace') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            # Remove from evaluated
            source.unlink()

            return destination
        except Exception as e:
            raise IOError(f"Failed to move {article_id} to reinfer: {e}")

    def move_to_rejected(self, article_id: str, reason: str) -> Path:
        """
        Move analysis to rejected directory after max retries.

        Args:
            article_id: Article identifier
            reason: Reason for rejection

        Returns:
            Path to new location
        """
        # Try to find in reinfer or evaluated
        source = self.reinfer_dir / f"{article_id}.json"
        if not source.exists():
            source = self.evaluated_dir / f"{article_id}.json"

        if not source.exists():
            raise FileNotFoundError(f"File not found for {article_id}")

        destination = self.rejected_dir / f"{article_id}.json"

        try:
            # Load, update stage and reason, and save
            with open(source, 'r', encoding='utf-8') as f:
                data = json.load(f)

            data["stage"] = "rejected"
            data["rejection_reason"] = reason

            with open(destination, 'w', encoding='utf-8', errors='replace') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            # Remove from source
            source.unlink()

            return destination
        except Exception as e:
            raise IOError(f"Failed to move {article_id} to rejected: {e}")

    def load_reinfer_analysis(self, article_id: str) -> Optional[Dict[str, Any]]:
        """
        Load analysis from reinfer directory.

        Args:
            article_id: Article identifier

        Returns:
            Analysis data dict or None if not found
        """
        file_path = self.reinfer_dir / f"{article_id}.json"
        if not file_path.exists():
            return None
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"[WARNING] Failed to load {file_path}: {e}")
            return None

    def list_reinfer_analyses(self) -> List[str]:
        """
        List all article IDs in reinfer directory.

        Returns:
            List of article IDs (filenames without .json extension)
        """
        return [f.stem for f in self.reinfer_dir.glob("*.json")]

    def list_approved_analyses(self) -> List[str]:
        """
        List all article IDs in approved directory.

        Returns:
            List of article IDs (filenames without .json extension)
        """
        return [f.stem for f in self.approved_dir.glob("*.json")]

    def list_rejected_analyses(self) -> List[str]:
        """
        List all article IDs in rejected directory.

        Returns:
            List of article IDs (filenames without .json extension)
        """
        return [f.stem for f in self.rejected_dir.glob("*.json")]

    def list_loaded_analyses(self) -> List[str]:
        """
        List all article IDs in loaded directory (archives after database load).

        Returns:
            List of article IDs (filenames without .json extension)
        """
        loaded_dir = self.base_dir / "loaded"
        if not loaded_dir.exists():
            return []
        return [f.stem for f in loaded_dir.glob("*.json")]


if __name__ == "__main__":
    # Test the file writer
    print("Testing AnalysisFileWriter...")

    writer = AnalysisFileWriter()

    # Check directories
    print(f"\n[OK] Base directory: {writer.base_dir}")
    print(f"[OK] Summarized directory: {writer.summarized_dir}")
    print(f"[OK] Directories exist: {writer.summarized_dir.exists()}")

    # Get statistics
    stats = writer.get_processing_stats()
    print(f"\n[STATS] Current statistics:")
    print(f"        Total files: {stats['total_files']}")
    print(f"        Successful: {stats['successful']}")
    print(f"        Failed: {stats['failed']}")

    if stats['total_files'] > 0:
        print(f"        Avg processing time: {stats['avg_processing_time_ms']:.1f}ms")
        print(f"        Total cost: ${stats['total_cost_usd']:.4f}")
        print(f"        By category: {stats['by_category']}")
        print(f"        By sentiment: {stats['by_sentiment']}")

    print("\n[OK] AnalysisFileWriter test complete!")
