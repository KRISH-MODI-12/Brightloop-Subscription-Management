#!/usr/bin/env python3
"""
Brightloop Subscription Management System — SQLite Backup Utility
Usage: python backend/backup_db.py [--src SOURCE_DB] [--dst-dir BACKUP_DIR]
"""
import sys
import argparse
from pathlib import Path

# Add backend to sys.path
backend_dir = Path(__file__).resolve().parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.services.backup_service import create_sqlite_backup, DEFAULT_DB_PATH, DEFAULT_BACKUP_DIR


def main():
    parser = argparse.ArgumentParser(description="Backup SQLite database with integrity verification.")
    parser.add_argument("--src", default=str(DEFAULT_DB_PATH), help="Path to source SQLite database")
    parser.add_argument("--dst-dir", default=str(DEFAULT_BACKUP_DIR), help="Directory to store backup file")
    args = parser.parse_args()

    print(f"Starting backup of: {args.src}")
    print(f"Target directory: {args.dst_dir}")

    try:
        result = create_sqlite_backup(source_db_path=args.src, backup_dir=args.dst_dir)
        print("\n[SUCCESS] Backup completed successfully!")
        print(f"  Backup Path: {result['backup_path']}")
        print(f"  Size: {result['size_bytes']:,} bytes")
        print(f"  Integrity Check: {result['verification']['integrity_check']}")
        print(f"  Tables Verified: {result['verification']['tables_count']}")
        print(f"  Row Counts: {result['verification']['row_counts']}")
    except Exception as e:
        print(f"\n[ERROR] Backup failed: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

