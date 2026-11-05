import sqlite3
import os

DB_PATH = "expensemate.db"

def inspect():
    if not os.path.exists(DB_PATH):
        print(f"Error: Database file '{DB_PATH}' does not exist yet. Run app.py to initialize it.")
        return

    conn = sqlite3.connect(DB_PATH)

    conn.execute("PRAGMA foreign_keys = ON;")

    print("=" * 65)
    print(f"   EXPENSEMATE DATABASE INSPECTION: {DB_PATH}")
    print("=" * 65)


    fk_status = conn.execute("PRAGMA foreign_keys;").fetchone()[0]
    print(f"\n[1] Connection Status: ACTIVE")
    print(f"    PRAGMA foreign_keys = {fk_status} ({'ENABLED' if fk_status == 1 else 'DISABLED'})")


    print(f"\n[2] Tables & Row Counts:")
    tables = [row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';").fetchall()]
    for t in tables:
        count = conn.execute(f"SELECT COUNT(*) FROM {t};").fetchone()[0]
        print(f"    * {t:<15} : {count} rows")


    print(f"\n[3] Foreign Key Constraints:")
    has_fks = False
    for t in tables:
        fks = conn.execute(f"PRAGMA foreign_key_list({t});").fetchall()
        for fk in fks:
            has_fks = True

            print(f"    * {t}.{fk[3]} --(FK)--> {fk[2]}.{fk[4]} [ON DELETE: {fk[6]}, ON UPDATE: {fk[5]}]")
    if not has_fks:
        print("    (No foreign keys found)")


    print(f"\n[4] Indexes:")
    indexes = conn.execute("SELECT name, tbl_name FROM sqlite_master WHERE type='index' AND name NOT LIKE 'sqlite_%';").fetchall()
    for idx_name, tbl_name in indexes:
        print(f"    * Index '{idx_name}' on table '{tbl_name}'")


    print(f"\n[5] Complete Database Schema (DDL):")
    print("-" * 65)
    schema_rows = conn.execute("SELECT sql FROM sqlite_master WHERE type IN ('table', 'index') AND name NOT LIKE 'sqlite_%' ORDER BY type DESC, name;").fetchall()
    for row in schema_rows:
        if row[0]:
            print(row[0].strip() + ";\n")
    print("-" * 65)


    print(f"\n[6] Sample Data (First 3 rows):")
    for t in tables:
        print(f"\n  -- Table: {t} --")
        cursor = conn.execute(f"SELECT * FROM {t} LIMIT 3;")
        col_names = [desc[0] for desc in cursor.description]
        print("  " + " | ".join(col_names))
        print("  " + "-" * 40)
        rows = cursor.fetchall()
        if rows:
            for r in rows:
                print("  " + " | ".join(str(val) for val in r))
        else:
            print("  (empty table)")

    conn.close()
    print("\n" + "=" * 65)
    print("   INSPECTION COMPLETE")
    print("=" * 65)

if __name__ == "__main__":
    inspect()
