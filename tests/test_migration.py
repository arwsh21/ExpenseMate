import os
import sqlite3
import pytest

from data import database
from migrations import migrate


def test_apply_migrations_from_scratch(tmp_path):
    test_db = str(tmp_path / "fresh_test.db")
    applied = migrate.apply_migrations(test_db, create_backup_first=False)

    assert len(applied) == 2
    assert "001_initial_schema" in applied
    assert "002_add_transaction_note" in applied

    status = migrate.get_migration_status(test_db)
    for s in status:
        assert s["status"] == "APPLIED"
        assert s["applied_at"] is not None

    verification = migrate.verify_database_integrity(test_db)
    assert verification["exists"] is True
    assert verification["has_note_column"] is True
    assert "note" in verification["transactions_columns"]
    assert verification["foreign_key_violations"] == 0
    assert verification["counts"]["categories"] == 6
    assert verification["counts"]["transactions"] == 0


def test_apply_migrations_is_idempotent(tmp_path):
    test_db = str(tmp_path / "idempotent_test.db")
    first_run = migrate.apply_migrations(test_db, create_backup_first=False)
    assert len(first_run) == 2

    # Second run should do nothing
    second_run = migrate.apply_migrations(test_db, create_backup_first=False)
    assert second_run == []


def test_migration_preserves_existing_data_and_defaults_note(tmp_path):
    test_db = str(tmp_path / "preserve_test.db")

    # 1. Apply ONLY migration 001 manually
    conn = sqlite3.connect(test_db)
    migrate.init_migration_table(conn)
    with open(os.path.join(migrate.MIGRATIONS_DIR, "001_initial_schema.sql"), "r") as f:
        conn.executescript(f.read())
    conn.execute("INSERT INTO schema_migrations (version, applied_at) VALUES ('001_initial_schema', '2026-01-01')")

    # Insert test transactions under v1 schema (without note)
    conn.execute(
        "INSERT INTO transactions (date, amount_minor, type, category_id) VALUES (?, ?, ?, ?)",
        ("2026-09-20", 45050, "expense", 1),
    )
    conn.execute(
        "INSERT INTO transactions (date, amount_minor, type, category_id) VALUES (?, ?, ?, ?)",
        ("2026-09-21", 120000, "income", 2),
    )
    conn.commit()
    conn.close()

    # 2. Run migration engine
    applied = migrate.apply_migrations(test_db, create_backup_first=False)
    assert applied == ["002_add_transaction_note"]

    # 3. Verify data preservation
    conn = sqlite3.connect(test_db)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM transactions ORDER BY id ASC")
    rows = cursor.fetchall()
    conn.close()

    assert len(rows) == 2
    assert rows[0]["date"] == "2026-09-20"
    assert rows[0]["amount_minor"] == 45050
    assert rows[0]["type"] == "expense"
    assert rows[0]["category_id"] == 1
    assert rows[0]["note"] == ""  # Default value assigned automatically

    assert rows[1]["date"] == "2026-09-21"
    assert rows[1]["amount_minor"] == 120000
    assert rows[1]["type"] == "income"
    assert rows[1]["category_id"] == 2
    assert rows[1]["note"] == ""


def test_backup_created_when_migrating_existing_db(tmp_path):
    test_db = str(tmp_path / "backup_test.db")

    # Create baseline DB with some content
    conn = sqlite3.connect(test_db)
    migrate.init_migration_table(conn)
    with open(os.path.join(migrate.MIGRATIONS_DIR, "001_initial_schema.sql"), "r") as f:
        conn.executescript(f.read())
    conn.execute("INSERT INTO schema_migrations (version, applied_at) VALUES ('001_initial_schema', '2026-01-01')")
    conn.commit()
    conn.close()

    # Run migration with backup enabled
    applied = migrate.apply_migrations(test_db, create_backup_first=True)
    assert applied == ["002_add_transaction_note"]

    # Verify backup exists
    backups = list(tmp_path.glob("backup_test.db.bak_*"))
    assert len(backups) == 1
    assert backups[0].stat().st_size > 0


def test_failed_migration_rolls_back_and_raises(tmp_path, monkeypatch):
    test_db = str(tmp_path / "fail_test.db")
    migrate.apply_migrations(test_db, create_backup_first=False)

    # Mock an invalid migration
    fake_migrations = [
        ("001_initial_schema", os.path.join(migrate.MIGRATIONS_DIR, "001_initial_schema.sql")),
        ("002_add_transaction_note", os.path.join(migrate.MIGRATIONS_DIR, "002_add_transaction_note.sql")),
        ("003_bad_migration", str(tmp_path / "003_bad_migration.sql")),
    ]
    with open(str(tmp_path / "003_bad_migration.sql"), "w") as f:
        f.write("THIS IS TOTALLY INVALID SQL STATEMENT;")

    monkeypatch.setattr(migrate, "get_available_migrations", lambda: fake_migrations)

    with pytest.raises(migrate.MigrationError) as exc_info:
        migrate.apply_migrations(test_db, create_backup_first=False)

    assert "Failed applying migration 003_bad_migration" in str(exc_info.value)

    # Ensure 003 was not marked as applied
    conn = sqlite3.connect(test_db)
    applied = migrate.get_applied_migrations(conn)
    conn.close()
    assert "003_bad_migration" not in applied


def test_database_initialize_database_uses_migrations(tmp_path, monkeypatch):
    test_db = str(tmp_path / "init_test.db")
    monkeypatch.setattr(database, "DATABASE_FILE", test_db)

    database.initialize_database()

    verification = migrate.verify_database_integrity(test_db)
    assert verification["exists"] is True
    assert verification["has_note_column"] is True
    assert verification["counts"]["categories"] == 6

