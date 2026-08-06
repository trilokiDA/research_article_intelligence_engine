"""
Pipeline Cleanup Tool - Manage file lifecycle and prevent accumulation.

This script cleans up old files from the pipeline directories to prevent
unbounded growth. It handles files that have been successfully processed
and are safe to remove.

Usage:
    # Dry run (see what would be deleted)
    python scripts/cleanup_pipeline.py --dry-run

    # Archive files older than 30 days
    python scripts/cleanup_pipeline.py --archive --days 30

    # Delete files older than 90 days
    python scripts/cleanup_pipeline.py --delete --days 90

    # Clean specific directory
    python scripts/cleanup_pipeline.py --dir raw --days 7

    # Aggressive cleanup (delete everything in raw/)
    python scripts/cleanup_pipeline.py --aggressive --dir raw
"""

import argparse
import sys
import shutil
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Any


class PipelineCleanup:
    """Manages cleanup of pipeline directories."""

    def __init__(self, base_dir: str = "data/analysis", dry_run: bool = False):
        self.base_dir = Path(base_dir)
        self.dry_run = dry_run
        self.stats = {
            'raw': {'scanned': 0, 'archived': 0, 'deleted': 0},
            'evaluated': {'scanned': 0, 'archived': 0, 'deleted': 0},
            'approved': {'scanned': 0, 'archived': 0, 'deleted': 0},
            'reinfer': {'scanned': 0, 'archived': 0, 'deleted': 0},
            'rejected': {'scanned': 0, 'archived': 0, 'deleted': 0},
            'loaded': {'scanned': 0, 'archived': 0, 'deleted': 0}
        }

    def get_old_files(self, directory: Path, days: int) -> List[Path]:
        """Get files older than specified days."""
        if not directory.exists():
            return []

        cutoff = datetime.now() - timedelta(days=days)
        old_files = []

        for file in directory.glob("*.json"):
            mtime = datetime.fromtimestamp(file.stat().st_mtime)
            if mtime < cutoff:
                old_files.append(file)

        return old_files

    def archive_files(self, files: List[Path], source_dir: str) -> int:
        """Archive files to archive/ directory."""
        archive_dir = self.base_dir / "archive" / source_dir / datetime.now().strftime("%Y%m%d")
        archived_count = 0

        for file in files:
            try:
                if self.dry_run:
                    print(f"  [DRY RUN] Would archive: {file.name}")
                else:
                    archive_dir.mkdir(parents=True, exist_ok=True)
                    dest = archive_dir / file.name
                    shutil.move(str(file), str(dest))
                    print(f"  Archived: {file.name}")
                archived_count += 1
            except Exception as e:
                print(f"  [ERROR] Failed to archive {file.name}: {e}")

        return archived_count

    def delete_files(self, files: List[Path]) -> int:
        """Delete files permanently."""
        deleted_count = 0

        for file in files:
            try:
                if self.dry_run:
                    print(f"  [DRY RUN] Would delete: {file.name}")
                else:
                    file.unlink()
                    print(f"  Deleted: {file.name}")
                deleted_count += 1
            except Exception as e:
                print(f"  [ERROR] Failed to delete {file.name}: {e}")

        return deleted_count

    def cleanup_directory(
        self,
        directory_name: str,
        days: int,
        action: str = "archive"
    ) -> Dict[str, int]:
        """Clean up a specific directory."""
        directory = self.base_dir / directory_name

        print(f"\n[{directory_name.upper()}]")
        print(f"  Directory: {directory}")

        if not directory.exists():
            print(f"  Directory does not exist, skipping")
            return {'scanned': 0, 'archived': 0, 'deleted': 0}

        # Get old files
        old_files = self.get_old_files(directory, days)
        self.stats[directory_name]['scanned'] = len(old_files)

        print(f"  Files older than {days} days: {len(old_files)}")

        if len(old_files) == 0:
            print(f"  No files to clean up")
            return self.stats[directory_name]

        # Perform action
        if action == "archive":
            archived = self.archive_files(old_files, directory_name)
            self.stats[directory_name]['archived'] = archived
        elif action == "delete":
            deleted = self.delete_files(old_files)
            self.stats[directory_name]['deleted'] = deleted

        return self.stats[directory_name]

    def cleanup_all(self, days: int, action: str = "archive"):
        """Clean up all pipeline directories."""
        print("=" * 70)
        print("PIPELINE CLEANUP")
        print("=" * 70)
        print(f"Base directory: {self.base_dir}")
        print(f"Action: {action}")
        print(f"Age threshold: {days} days")
        if self.dry_run:
            print("\n*** DRY RUN MODE - No changes will be made ***")

        directories = ['raw', 'evaluated', 'approved', 'reinfer', 'rejected']

        for directory in directories:
            self.cleanup_directory(directory, days, action)

        self.print_summary()

    def cleanup_loaded_archive(self, days: int):
        """Clean up old files from loaded/ archive directory."""
        print("\n[LOADED ARCHIVE]")
        loaded_dir = self.base_dir / "loaded"

        if not loaded_dir.exists():
            print("  Archive directory does not exist")
            return

        old_files = self.get_old_files(loaded_dir, days)
        print(f"  Files older than {days} days: {len(old_files)}")

        if len(old_files) > 0:
            deleted = self.delete_files(old_files)
            self.stats['loaded']['deleted'] = deleted

    def aggressive_cleanup(self, directory_name: str):
        """Delete ALL files from a directory (use with caution)."""
        directory = self.base_dir / directory_name

        print(f"\n[AGGRESSIVE CLEANUP: {directory_name.upper()}]")
        print(f"  WARNING: This will delete ALL files in {directory}")

        if not directory.exists():
            print(f"  Directory does not exist")
            return

        files = list(directory.glob("*.json"))
        print(f"  Total files: {len(files)}")

        if not self.dry_run:
            confirm = input("  Are you sure? (yes/no): ")
            if confirm.lower() != "yes":
                print("  Aborted")
                return

        deleted = self.delete_files(files)
        self.stats[directory_name]['deleted'] = deleted

    def print_summary(self):
        """Print cleanup summary."""
        print("\n" + "=" * 70)
        print("CLEANUP SUMMARY")
        print("=" * 70)

        total_scanned = sum(s['scanned'] for s in self.stats.values())
        total_archived = sum(s['archived'] for s in self.stats.values())
        total_deleted = sum(s['deleted'] for s in self.stats.values())

        print(f"\nTotal files scanned:  {total_scanned}")
        print(f"Total files archived: {total_archived}")
        print(f"Total files deleted:  {total_deleted}")

        if self.dry_run:
            print("\n*** This was a DRY RUN - no changes were made ***")

        print("=" * 70 + "\n")


def main():
    parser = argparse.ArgumentParser(
        description="Pipeline cleanup tool - manage file lifecycle",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Dry run (see what would be cleaned)
  python scripts/cleanup_pipeline.py --dry-run

  # Archive files older than 30 days
  python scripts/cleanup_pipeline.py --archive --days 30

  # Delete files older than 90 days
  python scripts/cleanup_pipeline.py --delete --days 90

  # Clean specific directory
  python scripts/cleanup_pipeline.py --dir raw --days 7

  # Aggressive cleanup (delete everything in raw/)
  python scripts/cleanup_pipeline.py --aggressive --dir raw

Recommended Schedule:
  # Weekly: Archive processed files
  0 3 * * 0 python scripts/cleanup_pipeline.py --archive --days 7

  # Monthly: Delete old archives
  0 4 1 * * python scripts/cleanup_pipeline.py --delete --days 90 --archive-only
        """
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be cleaned without making changes'
    )

    parser.add_argument(
        '--days',
        type=int,
        default=30,
        help='Delete/archive files older than N days (default: 30)'
    )

    parser.add_argument(
        '--archive',
        action='store_true',
        help='Archive old files instead of deleting'
    )

    parser.add_argument(
        '--delete',
        action='store_true',
        help='Delete old files permanently'
    )

    parser.add_argument(
        '--dir',
        choices=['raw', 'evaluated', 'approved', 'reinfer', 'rejected', 'loaded'],
        help='Clean up specific directory only'
    )

    parser.add_argument(
        '--aggressive',
        action='store_true',
        help='Delete ALL files in directory (requires --dir)'
    )

    parser.add_argument(
        '--archive-only',
        action='store_true',
        help='Only clean loaded/ archive directory'
    )

    args = parser.parse_args()

    # Validate arguments
    if args.aggressive and not args.dir:
        parser.error("--aggressive requires --dir to be specified")

    if not args.archive and not args.delete and not args.aggressive:
        parser.error("Must specify --archive, --delete, or --aggressive")

    # Determine action
    action = "archive" if args.archive else "delete"

    # Run cleanup
    cleanup = PipelineCleanup(dry_run=args.dry_run)

    try:
        if args.aggressive:
            cleanup.aggressive_cleanup(args.dir)
        elif args.archive_only:
            cleanup.cleanup_loaded_archive(args.days)
        elif args.dir:
            cleanup.cleanup_directory(args.dir, args.days, action)
        else:
            cleanup.cleanup_all(args.days, action)

        sys.exit(0)

    except KeyboardInterrupt:
        print("\n\nCleanup interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nFATAL ERROR: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
