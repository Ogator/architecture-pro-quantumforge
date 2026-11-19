#!/usr/bin/env python3
"""Automatic knowledge base and vector index updater.

Monitors a directory for new/changed .md files, updates the vector index,
and logs all operations. Designed to run via cron or other scheduler.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'task_5' / 'tools'))

from add_to_index import add_document_to_index


def compute_file_hash(path: Path) -> str:
    """Compute SHA256 hash of file."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_state(state_file: Path) -> dict:
    """Load previous update state."""
    if not state_file.exists():
        return {"files": {}, "last_update": None}
    return json.loads(state_file.read_text())


def save_state(state_file: Path, state: dict):
    """Save update state."""
    state_file.parent.mkdir(parents=True, exist_ok=True)
    state_file.write_text(json.dumps(state, indent=2, ensure_ascii=False))


def update_index(
    watch_dir: Path,
    index_path: Path,
    state_file: Path,
    log_file: Path,
) -> dict:
    """
    Scan watch_dir for new/changed .md files and update the index.

    Returns:
        Update report dict
    """
    report = {
        "timestamp": datetime.now().isoformat(),
        "watch_dir": str(watch_dir),
        "index_path": str(index_path),
        "files_added": [],
        "files_updated": [],
        "files_removed": [],
        "errors": [],
    }

    # Load previous state
    state = load_state(state_file)
    old_files = state.get("files", {})
    new_files = {}

    # Scan directory
    md_files = list(watch_dir.rglob("*.md"))

    print(f"Scanning {watch_dir} for .md files...")
    print(f"Found {len(md_files)} files")

    for md_file in md_files:
        try:
            file_hash = compute_file_hash(md_file)
            rel_path = str(md_file.relative_to(watch_dir))
            new_files[rel_path] = file_hash

            if rel_path not in old_files:
                # New file
                print(f"\n[NEW] {rel_path}")
                add_document_to_index(md_file, index_path)
                report["files_added"].append(rel_path)
            elif old_files[rel_path] != file_hash:
                # Changed file
                print(f"\n[UPDATED] {rel_path}")
                add_document_to_index(md_file, index_path)
                report["files_updated"].append(rel_path)
            else:
                # Unchanged
                print(f"[SKIP] {rel_path} (unchanged)")

        except Exception as e:
            error_msg = f"{rel_path}: {e}"
            print(f"[ERROR] {error_msg}")
            report["errors"].append(error_msg)

    # Detect removed files
    for old_path in old_files:
        if old_path not in new_files:
            print(f"\n[REMOVED] {old_path} (file deleted, but still in index)")
            report["files_removed"].append(old_path)

    # Update state
    state["files"] = new_files
    state["last_update"] = report["timestamp"]
    save_state(state_file, state)

    # Write log
    log_file.parent.mkdir(parents=True, exist_ok=True)
    with log_file.open('a', encoding='utf-8') as f:
        f.write(json.dumps(report, ensure_ascii=False) + '\n')

    return report


def print_summary(report: dict):
    """Print human-readable summary."""
    print("\n" + "=" * 70)
    print("UPDATE SUMMARY")
    print("=" * 70)
    print(f"Timestamp: {report['timestamp']}")
    print(f"Files added: {len(report['files_added'])}")
    print(f"Files updated: {len(report['files_updated'])}")
    print(f"Files removed: {len(report['files_removed'])}")
    print(f"Errors: {len(report['errors'])}")

    if report['files_added']:
        print("\nAdded:")
        for f in report['files_added']:
            print(f"  + {f}")

    if report['files_updated']:
        print("\nUpdated:")
        for f in report['files_updated']:
            print(f"  ~ {f}")

    if report['files_removed']:
        print("\nRemoved from watch_dir (still in index):")
        for f in report['files_removed']:
            print(f"  - {f}")

    if report['errors']:
        print("\nErrors:")
        for e in report['errors']:
            print(f"  ✗ {e}")

    print("=" * 70)


def main():
    parser = argparse.ArgumentParser(
        description="Automatic knowledge base updater"
    )
    parser.add_argument(
        '--watch-dir',
        type=Path,
        default=ROOT / 'task_6' / 'watch_dir',
        help='Directory to monitor for .md files'
    )
    parser.add_argument(
        '--index',
        type=Path,
        default=ROOT / 'task_3' / 'artifacts' / 'index',
        help='Path to vector index'
    )
    parser.add_argument(
        '--state-file',
        type=Path,
        default=ROOT / 'task_6' / 'artifacts' / 'update_state.json',
        help='State file tracking processed files'
    )
    parser.add_argument(
        '--log-file',
        type=Path,
        default=ROOT / 'task_6' / 'artifacts' / 'logs' / 'update.log',
        help='Log file for updates'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be updated without actually updating'
    )

    args = parser.parse_args()

    if not args.watch_dir.exists():
        print(f"Error: watch directory not found: {args.watch_dir}")
        return 1

    if not args.index.exists():
        print(f"Error: index not found: {args.index}")
        return 1

    try:
        if args.dry_run:
            print("DRY RUN MODE — no changes will be made")
            # TODO: implement dry-run logic
            print("Dry-run not fully implemented, exiting")
            return 0

        report = update_index(
            watch_dir=args.watch_dir,
            index_path=args.index,
            state_file=args.state_file,
            log_file=args.log_file,
        )

        print_summary(report)

        # Exit with error code if there were errors
        return 1 if report['errors'] else 0

    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
