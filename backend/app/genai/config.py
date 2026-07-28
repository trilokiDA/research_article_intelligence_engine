"""
Configuration settings for GenAI pipeline.
Centralized configuration for file paths, processing settings, and model parameters.
"""

from pathlib import Path
from typing import Dict, Any


class PipelineConfig:
    """
    Configuration settings for the GenAI summarization pipeline.
    """

    # ==================== File Paths ====================
    BASE_DIR = Path("data/analysis")
    SUMMARIZED_DIR = BASE_DIR / "summarized"
    EVALUATED_DIR = BASE_DIR / "evaluated"
    APPROVED_DIR = BASE_DIR / "approved"
    REINFER_DIR = BASE_DIR / "reinfer"
    REJECTED_DIR = BASE_DIR / "rejected"
    MANIFEST_FILE = BASE_DIR / "manifest.json"

    # ==================== Processing Settings ====================
    # Batch processing
    DEFAULT_BATCH_SIZE = 10
    DELAY_BETWEEN_BATCHES = 1.0  # seconds

    # Retry logic
    MAX_RETRIES = 3  # Max retries for API/validation errors
    RETRY_DELAY = 2.0  # seconds between retries

    # ==================== Model Settings ====================
    DEFAULT_MODEL = "llama-3.3-70b-versatile"
    DEFAULT_TEMPERATURE = 0.0  # 0 for consistency, >0 for creativity
    PROMPT_VERSION = "v1"

    # Alternative models (for experimentation)
    MODELS = {
        "llama-3.3-70b": "llama-3.3-70b-versatile",
        "llama-3.1-8b": "llama-3.1-8b-instant",
        "mixtral-8x7b": "mixtral-8x7b-32768",
    }

    # ==================== Cost Estimation ====================
    # Groq pricing (as of 2024, approximate)
    # Update these based on actual pricing from Groq
    MODEL_COSTS = {
        "llama-3.3-70b-versatile": {
            "input": 0.59 / 1_000_000,   # $ per token
            "output": 0.79 / 1_000_000,  # $ per token
        },
        "llama-3.1-8b-instant": {
            "input": 0.05 / 1_000_000,
            "output": 0.08 / 1_000_000,
        },
        "mixtral-8x7b-32768": {
            "input": 0.24 / 1_000_000,
            "output": 0.24 / 1_000_000,
        },
    }

    # ==================== Quality Control (Stage 3 - Future) ====================
    # Evaluation thresholds
    PASSING_SCORE_THRESHOLD = 80  # Minimum score to approve
    MAX_REINFER_ATTEMPTS = 3  # Max times to retry with feedback

    # Evaluation weights
    EVAL_WEIGHTS = {
        "factual_accuracy": 0.4,
        "completeness": 0.3,
        "people_first_language": 0.2,
        "entity_extraction": 0.1,
    }

    # ==================== Database Settings ====================
    # Status values for articles.summary_status column
    STATUS_PENDING = None  # Not yet processed
    STATUS_PROCESSING = "processing"  # Currently being processed
    STATUS_COMPLETED = "completed"  # Analysis loaded to database
    STATUS_FAILED = "failed"  # Needs manual review

    # ==================== Logging & Monitoring ====================
    LOG_LEVEL = "INFO"  # DEBUG, INFO, WARNING, ERROR
    SHOW_PROGRESS_BAR = True
    VERBOSE = False  # Print detailed processing info

    # ==================== Helper Methods ====================

    @staticmethod
    def get_model_cost(model_name: str, input_tokens: int, output_tokens: int) -> float:
        """
        Calculate cost for a model run.

        Args:
            model_name: Name of the model
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens

        Returns:
            Estimated cost in USD
        """
        costs = PipelineConfig.MODEL_COSTS.get(
            model_name,
            {"input": 0.0, "output": 0.0}
        )

        input_cost = input_tokens * costs["input"]
        output_cost = output_tokens * costs["output"]

        return input_cost + output_cost

    @staticmethod
    def get_model_name(alias: str) -> str:
        """
        Get full model name from alias.

        Args:
            alias: Model alias (e.g., "llama-3.3-70b")

        Returns:
            Full model name (e.g., "llama-3.3-70b-versatile")
        """
        return PipelineConfig.MODELS.get(alias, alias)

    @staticmethod
    def validate_config() -> Dict[str, Any]:
        """
        Validate configuration and return status.

        Returns:
            Dictionary with validation results
        """
        results = {
            "valid": True,
            "errors": [],
            "warnings": []
        }

        # Check directories exist
        if not PipelineConfig.BASE_DIR.exists():
            results["warnings"].append(
                f"Base directory does not exist: {PipelineConfig.BASE_DIR}"
            )

        # Check threshold
        if not 0 <= PipelineConfig.PASSING_SCORE_THRESHOLD <= 100:
            results["valid"] = False
            results["errors"].append(
                "PASSING_SCORE_THRESHOLD must be between 0 and 100"
            )

        # Check weights sum to 1.0
        weight_sum = sum(PipelineConfig.EVAL_WEIGHTS.values())
        if abs(weight_sum - 1.0) > 0.01:
            results["valid"] = False
            results["errors"].append(
                f"EVAL_WEIGHTS must sum to 1.0 (currently: {weight_sum})"
            )

        return results

    @staticmethod
    def print_config():
        """Print current configuration (for debugging)."""
        print("\n" + "=" * 80)
        print("PIPELINE CONFIGURATION")
        print("=" * 80)
        print(f"\n[File Paths]")
        print(f"  Base directory:     {PipelineConfig.BASE_DIR}")
        print(f"  Raw directory:      {PipelineConfig.SUMMARIZED_DIR}")
        print(f"  Approved directory: {PipelineConfig.APPROVED_DIR}")

        print(f"\n[Processing]")
        print(f"  Batch size:         {PipelineConfig.DEFAULT_BATCH_SIZE}")
        print(f"  Max retries:        {PipelineConfig.MAX_RETRIES}")
        print(f"  Batch delay:        {PipelineConfig.DELAY_BETWEEN_BATCHES}s")

        print(f"\n[Model]")
        print(f"  Default model:      {PipelineConfig.DEFAULT_MODEL}")
        print(f"  Temperature:        {PipelineConfig.DEFAULT_TEMPERATURE}")
        print(f"  Prompt version:     {PipelineConfig.PROMPT_VERSION}")

        print(f"\n[Quality Control]")
        print(f"  Passing threshold:  {PipelineConfig.PASSING_SCORE_THRESHOLD}%")
        print(f"  Max reinfer:        {PipelineConfig.MAX_REINFER_ATTEMPTS}")
        print(f"  Eval weights:       {PipelineConfig.EVAL_WEIGHTS}")

        print("=" * 80 + "\n")


# Development/Testing overrides
class DevConfig(PipelineConfig):
    """
    Development configuration with smaller batches and more logging.
    """
    DEFAULT_BATCH_SIZE = 5
    VERBOSE = True
    LOG_LEVEL = "DEBUG"


# Production configuration
class ProdConfig(PipelineConfig):
    """
    Production configuration with optimized settings.
    """
    DEFAULT_BATCH_SIZE = 50
    VERBOSE = False
    LOG_LEVEL = "INFO"
    DELAY_BETWEEN_BATCHES = 0.5  # Faster processing


if __name__ == "__main__":
    # Test configuration
    print("Testing PipelineConfig...")

    # Print config
    PipelineConfig.print_config()

    # Validate
    validation = PipelineConfig.validate_config()
    print(f"[VALIDATION] Valid: {validation['valid']}")
    if validation['errors']:
        print(f"[ERRORS] {validation['errors']}")
    if validation['warnings']:
        print(f"[WARNINGS] {validation['warnings']}")

    # Test cost calculation
    cost = PipelineConfig.get_model_cost(
        "llama-3.3-70b-versatile",
        input_tokens=1000,
        output_tokens=500
    )
    print(f"\n[COST] Estimated cost for 1000 in + 500 out tokens: ${cost:.6f}")

    # Test model alias
    model = PipelineConfig.get_model_name("llama-3.3-70b")
    print(f"[MODEL] Alias 'llama-3.3-70b' -> '{model}'")

    print("\n[OK] Configuration test complete!")
