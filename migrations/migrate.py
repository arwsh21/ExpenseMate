import glob
import os
import shutil
import sqlite3
import sys
from datetime import datetime


MIGRATIONS_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(MIGRATIONS_DIR)
DEFAULT_DB_FILE = os.path.join(PROJECT_DIR, "expensemate.db")


class MigrationError(Exception):
    """Raised when a database migration fails."""
    pass


def get_default_db_path():
    try:
        from data import database
        return database.DATABASE_FILE
    except (ImportError, AttributeError):
        return DEFAULT_DB_FILE


def create_backup(db_path):
    """Creates a timestamped backup copy of the SQLite database file if it exists."""
    if not os.path.exists(db_path) or os.path.getsize(db_path) == 0:
        return None

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"{db_path}.bak_{timestamp}"
    shutil.copy2(db_path, backup_path)
    return backup_path


def init_migration_table(connection):
    """Ensures the schema_migrations tracking table exists."""
    connection.execute("""
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version TEXT PRIMARY KEY,
            applied_at TEXT NOT NULL
        );
    """)
    connection.commit()


def get_applied_migrations(connection):
    """Returns a set of version identifiers that have already been applied."""
    init_migration_table(connection)
    cursor = connection.cursor()
    cursor.execute("SELECT version FROM schema_migrations ORDER BY version ASC")
    rows = cursor.fetchall()
    return {row[0] for row in rows}


def get_available_migrations():
    """Discovers and returns all .sql migration files in the migrations directory."""
    pattern = os.path.join(MIGRATIONS_DIR, "*.sql")
    sql_files = sorted(glob.glob(pattern))
    migrations = []
    for filepath in sql_files:
        filename = os.path.basename(filepath)
        version = os.path.splitext(filename)[0]
        migrations.append((version, filepath))
    return migrations


def apply_migrations(db_path=None, create_backup_first=True):
    """
    Applies all pending migrations to the specified database in ascending order.
    Returns a list of versions that were newly applied.
    """
    if db_path is None:
        db_path = get_default_db_path()

    available = get_available_migrations()
    if not available:
        return []

    connection = sqlite3.connect(db_path)
    connection.execute("PRAGMA foreign_keys = ON")

    try:
        applied = get_applied_migrations(connection)
        pending = [(v, p) for v, p in available if v not in applied]

        if not pending:
            return []

        # If there are pending migrations, create an automated backup first
        backup_file = None
        if create_backup_first and os.path.exists(db_path) and os.path.getsize(db_path) > 0:
            backup_file = create_backup(db_path)

        newly_applied = []
        for version, filepath in pending:
            with open(filepath, "r", encoding="utf-8") as f:
                sql_content = f.read()

            try:
                # Execute the migration script atomically
                connection.executescript(sql_content)
                now_iso = datetime.now().isoformat()
                connection.execute(
                    "INSERT INTO schema_migrations (version, applied_at) VALUES (?, ?)",
                    (version, now_iso),
                )
                connection.commit()
                newly_applied.append(version)
            except sqlite3.Error as exc:
                connection.rollback()
                error_msg = f"Failed applying migration {version} from {filepath}: {exc}"
                if backup_file:
                    error_msg += f"\nAutomated backup created prior to failure at: {backup_file}"
                raise MigrationError(error_msg) from exc

        return newly_applied
    finally:
        connection.close()


def get_migration_status(db_path=None):
    """Returns a list of dictionaries detailing the status of every migration."""
    if db_path is None:
        db_path = get_default_db_path()

    if not os.path.exists(db_path):
        return []

    connection = sqlite3.connect(db_path)
    try:
        init_migration_table(connection)
        cursor = connection.cursor()
        cursor.execute("SELECT version, applied_at FROM schema_migrations")
        applied_map = dict(cursor.fetchall())

        available = get_available_migrations()
        status_list = []
        for version, filepath in available:
            is_applied = version in applied_map
            status_list.append({
                "version": version,
                "file": os.path.basename(filepath),
                "status": "APPLIED" if is_applied else "PENDING",
                "applied_at": applied_map.get(version),
            })
        return status_list
    finally:
        connection.close()


def verify_database_integrity(db_path=None):
    """
    Inspects and returns a snapshot of database tables, row counts,
    foreign key validity, and schema attributes.
    """
    if db_path is None:
        db_path = get_default_db_path()

    if not os.path.exists(db_path):
        return {"exists": False}

    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    try:
        cursor = connection.cursor()

        # Check table counts
        counts = {}
        for table in ["categories", "transactions", "budgets", "schema_migrations"]:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                counts[table] = cursor.fetchone()[0]
            except sqlite3.OperationalError:
                counts[table] = None

        # Verify foreign keys
        cursor.execute("PRAGMA foreign_key_check")
        fk_violations = cursor.fetchall()

        # Inspect columns of transactions table
        cursor.execute("PRAGMA table_info(transactions)")
        tx_columns = [row["name"] for row in cursor.fetchall()]

        return {
            "exists": True,
            "database_path": db_path,
            "counts": counts,
            "foreign_key_violations": len(fk_violations),
            "transactions_columns": tx_columns,
            "has_note_column": "note" in tx_columns,
        }
    finally:
        connection.close()


def print_status_table(db_path=None):
    statuses = get_migration_status(db_path)
    print("=" * 70)
    print("EXPENSEMATE SCHEMA MIGRATION STATUS")
    print("=" * 70)
    if not statuses:
        print("Database not found or no migrations discovered.")
        return

    print(f"{'Version':<28} | {'Status':<9} | {'Applied At':<26}")
    print("-" * 70)
    for s in statuses:
        applied_at = s['applied_at'] or "-"
        print(f"{s['version']:<28} | {s['status']:<9} | {applied_at:<26}")
    print("=" * 70)


def print_verification(db_path=None):
    info = verify_database_integrity(db_path)
    print("=" * 70)
    print("DATABASE INTEGRITY & SNAPSHOT VERIFICATION")
    print("=" * 70)
    if not info.get("exists"):
        print("Database does not exist at target path.")
        return

    print(f"Database File: {info['database_path']}")
    print(f"Has 'note' column in transactions: {info['has_note_column']}")
    print(f"Columns in transactions: {', '.join(info['transactions_columns'])}")
    print(f"Foreign Key Violations: {info['foreign_key_violations']}")
    print("-" * 70)
    print("Record Counts:")
    for tbl, count in info["counts"].items():
        print(f"  • {tbl:<20}: {count}")
    print("=" * 70)


def main():
    command = "apply" if len(sys.argv) < 2 else sys.argv[1].lower()

    if command == "status":
        print_status_table()
    elif command == "verify":
        print_verification()
    elif command in ("apply", "run"):
        print("Applying pending database migrations...")
        try:
            applied = apply_migrations()
            if applied:
                print(f"Successfully applied {len(applied)} migration(s):")
                for version in applied:
                    print(f"  + {version}")
            else:
                print("Database is already up to date. No pending migrations.")
            print()
            print_status_table()
            print()
            print_verification()
        except MigrationError as e:
            print(f"MIGRATION FAILED:\n{e}", file=sys.stderr)
            sys.exit(1)
    else:
        print("Usage: python -m migrations.migrate [apply|status|verify]")


if __name__ == "__main__":
    main()

