import pytest
import os
import tempfile
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from app.config import Settings
from app.core.datetime_utils import utc_now, utc_now_naive
from app.services.backup_service import create_sqlite_backup, verify_backup_integrity


# ==============================================================================
# P1.5: Environment Security Tests
# ==============================================================================

def test_production_rejects_insecure_default_secret_key():
    with pytest.raises(ValueError) as exc:
        Settings(
            ENVIRONMENT="production",
            SECRET_KEY="brightloop-dev-secret-key-change-in-production-2026"
        )
    assert "INSECURE_SECRET_KEY" in str(exc.value)


def test_production_rejects_short_secret_key():
    with pytest.raises(ValueError) as exc:
        Settings(
            ENVIRONMENT="production",
            SECRET_KEY="too-short"
        )
    assert "INSECURE_SECRET_KEY" in str(exc.value)


def test_production_accepts_strong_secret_key():
    strong_key = "a" * 40  # 40 characters, not containing 'dev'
    settings = Settings(
        ENVIRONMENT="production",
        SECRET_KEY=strong_key
    )
    assert settings.SECRET_KEY == strong_key


def test_development_allows_default_key():
    settings = Settings(ENVIRONMENT="development")
    assert settings.SECRET_KEY is not None
    assert len(settings.SECRET_KEY) > 0


# ==============================================================================
# P2.7: SQLite Backup Utility Tests
# ==============================================================================

def test_sqlite_backup_creation_and_integrity(tmp_path):
    # 1. Create a sample SQLite database
    src_db = tmp_path / "original.db"
    conn = sqlite3.connect(src_db)
    cur = conn.cursor()
    cur.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT);")
    cur.execute("CREATE TABLE invoices (id INTEGER PRIMARY KEY, total REAL);")
    cur.execute("INSERT INTO users (name) VALUES ('Alice'), ('Bob');")
    cur.execute("INSERT INTO invoices (total) VALUES (100.5), (250.0), (99.9);")
    conn.commit()
    conn.close()

    backup_dir = tmp_path / "backups"

    # 2. Run backup
    result = create_sqlite_backup(source_db_path=src_db, backup_dir=backup_dir)

    assert result["status"] == "success"
    backup_file = Path(result["backup_path"])
    assert backup_file.exists()
    assert backup_file != src_db  # Never overwrites original

    # 3. Verify integrity
    verification = result["verification"]
    assert verification["is_valid"] is True
    assert verification["integrity_check"] == "ok"
    assert verification["tables_count"] == 2
    assert verification["row_counts"]["users"] == 2
    assert verification["row_counts"]["invoices"] == 3

    # Original DB must remain completely intact
    conn_orig = sqlite3.connect(src_db)
    cur_orig = conn_orig.cursor()
    cur_orig.execute("SELECT COUNT(*) FROM users;")
    assert cur_orig.fetchone()[0] == 2
    conn_orig.close()


def test_backup_verification_detects_missing_file(tmp_path):
    src_db = tmp_path / "original.db"
    conn = sqlite3.connect(src_db)
    cur = conn.cursor()
    cur.execute("CREATE TABLE t (id INT);")
    conn.commit()
    conn.close()

    result = verify_backup_integrity(source_db_path=src_db, backup_db_path=tmp_path / "nonexistent.db")
    assert result["is_valid"] is False
    assert "does not exist" in result["error"]


# ==============================================================================
# P2.8: Date and Time Handling Tests
# ==============================================================================

def test_utc_now_returns_timezone_aware():
    now = utc_now()
    assert now.tzinfo is not None
    assert now.tzinfo == timezone.utc


def test_utc_now_naive_returns_utc_without_tz():
    naive = utc_now_naive()
    assert naive.tzinfo is None
