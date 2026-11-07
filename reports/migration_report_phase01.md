# EXPENSEMATE
## Database Schema Evolution & Migration Report (Part A)
### Members: Areesha 24k-3043, Burhan 24k-3056

| Technology | Migration Scope | Target Architecture | Final Status |
| :--- | :--- | :--- | :--- |
| Python • SQLite3 | Schema Evolution & Versioning | Version-Controlled Migration Engine | Verified • Zero Data Loss (1,002 Records) |

---

### 1. Introduction & Migration Objective
In Assignment 01, ExpenseMate relied on a static table creation script executed during application startup. While sufficient for a prototype, production systems require a safe, version-controlled mechanism to modify database structures as business requirements evolve. The objective of this migration is to transition ExpenseMate from static table initialization to an automated, incremental database migration subsystem capable of applying schema evolutions while preserving existing records and database constraints.

• Primary objective: establish an automated migration pipeline capable of tracking schema revisions, executing incremental DDL changes, and safeguarding existing production data.  
• Scope includes the implementation of a dedicated migration runner, version tracking metadata, automated pre-migration database backups, and backward-compatible transaction table evolution.

---

### 2. Baseline Analysis & Migration Rationale
A code audit of the Assignment 01 codebase revealed that database configuration was already centralized within `data/database.py`, where `DATABASE_FILE` and connection pooling helpers resided in a single module. Relocating these definitions into a configuration file would constitute superficial code movement rather than a substantive software migration.

The genuine operational bottleneck was the inability to alter database structures incrementally. The baseline setup used `SCHEMA_SQL` containing `CREATE TABLE IF NOT EXISTS`. Adding columns or modifying constraints under this model would fail silently or require deleting the database file, causing total user data loss.

| Evaluation Area | Assignment 01 Baseline | Migration Target State |
| :--- | :--- | :--- |
| Schema Management | Static `SCHEMA_SQL` script in `data/database.py` | Standalone version-ordered SQL migration files |
| Revision Tracking | None (no record of applied schema changes) | `schema_migrations` audit table in SQLite |
| Schema Evolution | Manual table manipulation or database recreation | Automated forward migration engine with atomic transactions |
| Data Protection | No safety backups during application initialization | Automated timestamped database backups before DDL execution |

---

### 3. Schema Evolution & Target Architecture
The migration architecture introduces a dedicated `migrations/` subsystem decoupled from presentation and business services. The runner inspects the target database, identifies unapplied migrations, and applies them sequentially inside isolated database transactions.

```
migrations/
├── __init__.py
├── 001_initial_schema.sql         (Assignment 01 baseline tables & categories)
├── 002_add_transaction_note.sql   (Evolution: adds note TEXT column to transactions)
└── migrate.py                     (Migration engine with backup & verification logic)
```

#### Migration 001: Baseline Schema Specification (`001_initial_schema.sql`)
Formalizes the baseline categories, transactions, and budgets tables with strict CHECK constraints, foreign key references, and indexes on `date` and `category_id`. It also populates default starter categories using `INSERT OR IGNORE`.

#### Migration 002: Incremental Evolution (`002_add_transaction_note.sql`)
Demonstrates forward schema evolution by adding an optional note column to financial transactions:
```sql
ALTER TABLE transactions ADD COLUMN note TEXT DEFAULT '';
```
The `DEFAULT ''` clause guarantees backward compatibility. Existing application queries that insert four transaction parameters continue to succeed without schema violations.

---

### 4. Migration Procedure & Implementation Steps
The migration was carried out through the following structured engineering steps:

1. **Subsystem Construction:** Created the `migrations/` directory and authored baseline migration `001_initial_schema.sql` and evolution script `002_add_transaction_note.sql`.
2. **Runner Implementation:** Developed `migrations/migrate.py` providing transactional execution, audit logging into `schema_migrations`, automated backup creation, and command-line interfaces (`apply`, `status`, `verify`).
3. **Database Integration:** Updated `data/database.py` so that `initialize_database()` delegates directly to `migrate.apply_migrations(DATABASE_FILE)`.
4. **Live Execution:** Applied migrations against the live project database `expensemate.db`.
5. **Automated Testing:** Authored `tests/test_migration.py` covering idempotent execution, data preservation, backup creation, and transactional rollbacks.

---

### 5. Risk Management & Safety Controls
Database migrations carry inherent operational risks. The migration pipeline incorporates strict defensive controls to prevent corruption and downtime:

| Operational Risk | Severity | Implemented Safety Control |
| :--- | :--- | :--- |
| Database Corruption | Critical | `create_backup()` creates a timestamped file (`.db.bak_<timestamp>`) before any DDL statements run. |
| Partial Script Failure | High | All migration scripts run within atomic transactions; failure triggers immediate rollback. |
| Data Loss on Existing Records | High | The `ALTER TABLE` statement uses non-destructive column additions with default values. |
| Duplicate Execution | Medium | The `schema_migrations` table records applied versions, preventing re-execution of completed scripts. |
| Foreign Key Invalidation | Medium | SQLite foreign keys are enforced via `PRAGMA foreign_keys = ON` during migration runs. |

---

### 6. Verification, Testing & Data Integrity Evidence
Verification was performed using both live database inspection and automated test suites.

#### Live Database Integrity Snapshot
Executing `python -m migrations.migrate verify` against the production `expensemate.db` yielded exact preservation of all records:

| Table Name | Before Migration | After Migration | Verification Outcome |
| :--- | :--- | :--- | :--- |
| `categories` | 21 records | 21 records | 100% Preserved • Zero Data Loss |
| `transactions` | 1,002 records | 1,002 records | 1,002 records verified • note column added |
| `budgets` | 4 records | 4 records | 100% Preserved • Zero Data Loss |
| `schema_migrations` | 0 records (untracked) | 2 records | Versions 001 and 002 recorded with timestamps |

Foreign key verification (`PRAGMA foreign_key_check`) confirmed zero constraint violations.

#### Automated Test Suite Execution
A dedicated test suite `tests/test_migration.py` was executed alongside the project regression suite using pytest:
• `test_apply_migrations_from_scratch`: verifies fresh database setup with 2 applied migrations.  
• `test_apply_migrations_is_idempotent`: verifies second execution applies 0 migrations safely.  
• `test_migration_preserves_existing_data_and_defaults_note`: verifies mock transactions remain intact with default empty string notes.  
• `test_backup_created_when_migrating_existing_db`: verifies backup file creation and file size integrity.  
• `test_failed_migration_rolls_back_and_raises`: verifies transactional rollback when invalid SQL is encountered.  
• `test_database_initialize_database_uses_migrations`: verifies framework hook in `data/database.py`.  
• **Full Regression Run:** 122 out of 122 automated unit and service tests passed in 8.99 seconds with zero regressions.

---

### 7. Conclusion & Operational Impact
ExpenseMate successfully migrated from unversioned static table creation to a robust, version-tracked database migration pipeline. The system now supports continuous schema evolution, protects production databases via automated pre-migration backups, and guarantees atomic execution with rollbacks. All 1,002 existing transactions and related records remain completely intact, and all automated regression tests continue to pass.

| Applied Migrations | Preserved Records | Integrity Violations | Automated Tests |
| :---: | :---: | :---: | :---: |
| **2 / 2** | **1,002 / 1,002** | **0** | **122 / 122 Passed** |

