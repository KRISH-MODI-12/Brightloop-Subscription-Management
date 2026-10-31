import os
import sqlite3
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
DEFAULT_DB_PATH = BACKEND_DIR / "subscription_mgmt.db"
DEFAULT_BACKUP_DIR = BACKEND_DIR / "backups"


def create_sqlite_backup(
    source_db_path: Path | str = DEFAULT_DB_PATH,
    backup_dir: Path | str = DEFAULT_BACKUP_DIR
) -> Dict[str, Any]:
    """
    Creates a timestamped, integrity-verified SQLite database backup.

    Safety Guarantees:
    - Never overwrites the source database.
    - Uses SQLite's online backup API (safe during concurrent operation).
    - Runs PRAGMA integrity_check on the generated backup.
    - Compares table and row counts to ensure data fidelity.
    """
    src = Path(source_db_path).resolve()
    if not src.exists():
        raise FileNotFoundError(f"Source database not found at {src}")

    dst_dir = Path(backup_dir).resolve()
    dst_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    backup_filename = f"{src.stem}_{timestamp}.db"
    dst = dst_dir / backup_filename

    # Safety check: Never overwrite original database
    if dst.samefile(src) if dst.exists() else dst == src:
        raise ValueError("CRITICAL: Backup target cannot be the source database file.")

    if dst.exists():
        raise FileExistsError(f"Backup file already exists: {dst}")

    logger.info(f"Initiating online SQLite backup from {src} to {dst}...")

    # Perform online backup
    src_conn = sqlite3.connect(src)
    dst_conn = sqlite3.connect(dst)
    try:
        src_conn.backup(dst_conn)
    finally:
        dst_conn.close()
        src_conn.close()

    # Integrity verification
    verification = verify_backup_integrity(src, dst)
    if not verification["is_valid"]:
        # If verification fails, remove corrupt backup
        try:
            dst.unlink(missing_ok=True)
        except Exception:
            pass
        raise RuntimeError(f"Backup integrity verification failed: {verification.get('error')}")

    logger.info(f"Backup successfully created and verified: {dst}")
    return {
        "status": "success",
        "source": str(src),
        "backup_path": str(dst),
        "timestamp": timestamp,
        "size_bytes": dst.stat().st_size,
        "verification": verification
    }


def verify_backup_integrity(source_db_path: Path | str, backup_db_path: Path | str) -> Dict[str, Any]:
    """
    Verifies that the backup database is valid, passes PRAGMA integrity_check,
    and has matching tables and row counts compared to the source.
    """
    src = Path(source_db_path).resolve()
    dst = Path(backup_db_path).resolve()

    if not dst.exists():
        return {"is_valid": False, "error": "Backup file does not exist."}

    dst_conn = sqlite3.connect(dst)
    src_conn = sqlite3.connect(src)
    try:
        dst_cur = dst_conn.cursor()
        src_cur = src_conn.cursor()

        # 1. Run PRAGMA integrity_check
        dst_cur.execute("PRAGMA integrity_check;")
        check_result = dst_cur.fetchall()
        if not check_result or check_result[0][0] != "ok":
            return {"is_valid": False, "error": f"Integrity check failed: {check_result}"}

        # 2. Compare table schemas
        dst_cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
        dst_tables = set(r[0] for r in dst_cur.fetchall())

        src_cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
        src_tables = set(r[0] for r in src_cur.fetchall())

        if dst_tables != src_tables:
            return {
                "is_valid": False,
                "error": f"Table list mismatch: expected {src_tables}, got {dst_tables}"
            }

        # 3. Compare row counts for each table
        row_counts: Dict[str, int] = {}
        for tbl in dst_tables:
            dst_cur.execute(f"SELECT COUNT(*) FROM \"{tbl}\";")
            dst_count = dst_cur.fetchone()[0]

            src_cur.execute(f"SELECT COUNT(*) FROM \"{tbl}\";")
            src_count = src_cur.fetchone()[0]

            if dst_count != src_count:
                return {
                    "is_valid": False,
                    "error": f"Row count mismatch on table '{tbl}': source has {src_count}, backup has {dst_count}"
                }
            row_counts[tbl] = dst_count

        return {
            "is_valid": True,
            "integrity_check": "ok",
            "tables_count": len(dst_tables),
            "tables": list(dst_tables),
            "row_counts": row_counts
        }
    except Exception as e:
        return {"is_valid": False, "error": str(e)}
    finally:
        dst_conn.close()
        src_conn.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    res = create_sqlite_backup()
    print("Backup Result:", res)

