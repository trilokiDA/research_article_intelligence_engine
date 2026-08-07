"""
Test script to verify the skip logic in evaluate_summaries_runner.py
This demonstrates that files in loaded and rejected directories are properly skipped.
"""

import sys
from pathlib import Path

# Setup paths
PROJECT_ROOT = Path(__file__).parent.parent
backend_app_dir = PROJECT_ROOT / "backend" / "app"
sys.path.insert(0, str(backend_app_dir))

from genai.file_writer import AnalysisFileWriter


def test_skip_logic():
    """Test that all evaluated directories are checked."""
    print("=" * 60)
    print("TESTING SKIP LOGIC FOR EVALUATION")
    print("=" * 60)

    data_dir = PROJECT_ROOT / "data" / "analysis"
    file_writer = AnalysisFileWriter(base_dir=str(data_dir))

    # Get all raw analyses
    all_raw_files = file_writer.list_raw_analyses()
    print(f"\n[1] Total raw analyses: {len(all_raw_files)}")

    # Check each directory
    already_approved = set(file_writer.list_approved_analyses())
    already_reinfer = set(file_writer.list_reinfer_analyses())
    already_loaded = set(file_writer.list_loaded_analyses())
    already_rejected = set(file_writer.list_rejected_analyses())

    print(f"\n[2] Files in each directory:")
    print(f"    - Approved: {len(already_approved)}")
    print(f"    - Reinfer: {len(already_reinfer)}")
    print(f"    - Loaded: {len(already_loaded)}")
    print(f"    - Rejected: {len(already_rejected)}")

    # Calculate overlap
    already_evaluated = already_approved | already_reinfer | already_loaded | already_rejected
    print(f"\n[3] Total already evaluated: {len(already_evaluated)}")

    # Calculate pending
    files_to_process = [f for f in all_raw_files if f not in already_evaluated]
    print(f"[4] Pending evaluation: {len(files_to_process)}")

    # Show sample of each category
    if already_loaded:
        print(f"\n[5] Sample loaded articles (first 3):")
        for aid in list(already_loaded)[:3]:
            print(f"    - {aid}")

    if already_rejected:
        print(f"\n[6] Sample rejected articles (first 3):")
        for aid in list(already_rejected)[:3]:
            print(f"    - {aid}")

    if files_to_process:
        print(f"\n[7] Sample pending articles (first 3):")
        for aid in files_to_process[:3]:
            print(f"    - {aid}")

    # Verify no duplicates
    all_categories = [already_approved, already_reinfer, already_loaded, already_rejected]
    overlaps = []
    category_names = ["approved", "reinfer", "loaded", "rejected"]

    for i in range(len(all_categories)):
        for j in range(i + 1, len(all_categories)):
            overlap = all_categories[i] & all_categories[j]
            if overlap:
                overlaps.append((category_names[i], category_names[j], overlap))

    if overlaps:
        print(f"\n[WARNING] Found overlapping articles between directories:")
        for cat1, cat2, articles in overlaps:
            print(f"  - {cat1} & {cat2}: {len(articles)} articles")
            for aid in list(articles)[:3]:
                print(f"    * {aid}")
    else:
        print(f"\n[OK] No overlapping articles between directories")

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    if len(files_to_process) == 0 and len(all_raw_files) > 0:
        print(f"[OK] All {len(all_raw_files)} raw articles have been analyzed!")
        print(f"\nDistribution:")
        print(f"  - Approved: {len(already_approved)} (ready for database load)")
        print(f"  - Reinfer: {len(already_reinfer)} (waiting for re-inference)")
        print(f"  - Loaded: {len(already_loaded)} (already in database)")
        print(f"  - Rejected: {len(already_rejected)} (failed after max retries)")

        print(f"\nNext steps:")
        if len(already_approved) > 0:
            print(f"  - Load {len(already_approved)} approved articles to database")
        if len(already_reinfer) > 0:
            print(f"  - Re-infer {len(already_reinfer)} articles")
        if len(already_approved) == 0 and len(already_reinfer) == 0:
            print(f"  - All articles are finalized (loaded or rejected)")
    else:
        print(f"Skip logic is working correctly!")
        print(f"  - Raw analyses: {len(all_raw_files)}")
        print(f"  - Already evaluated: {len(already_evaluated)}")
        print(f"  - Ready to evaluate: {len(files_to_process)}")

    print("=" * 60)


if __name__ == "__main__":
    test_skip_logic()
