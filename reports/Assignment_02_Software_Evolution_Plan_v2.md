# Software Evolution & Engineering Plan: Assignment 02
**Project:** ExpenseMate (Burhan’s Budget Buddy)  
**Course:** Software Construction & Development  
**Team Members:** Member 1 (Burhan) & Member 2 (Teammate)  
**Target Architecture:** Layered Architecture (`Controller -> Services -> Repository -> Database`)  
**Status:** Approved Implementation Blueprint  

---

## 1. Executive Summary & Objective

In Assignment 01, our team delivered **ExpenseMate**, a personal financial manager built with Python, Streamlit, and SQLite. In Assignment 02, our objective is to evolve this existing codebase strictly following the three mandatory software construction concepts:

1. **Concept A (Migration):** Implement an automated, version-tracked database schema migration engine (`migrations/migrate.py`) that applies incremental SQL migrations (`001_initial_schema.sql`, `002_add_transaction_note.sql`) and demonstrates zero data loss on existing database records.
2. **Concept B (Refactoring):** Refactor two core features (**Add Expense** and **Monthly Budget Summary**) into the mandatory 4-layer architecture (`Controller -> Services -> Repository -> Database`). Introduce `controllers/` to eliminate direct coupling between Streamlit UI and backend services.
3. **Concept C (Rewriting):** Consolidate and rewrite procedural functions from `validators.py`, `csv_validator.py`, `budget_calculator.py`, and `savings_logic.py` into two cohesive, testable, object-oriented domain classes: `TransactionValidator` and `BudgetCalculator`.

---

## 2. Concept A: Migration (Versioned Database Schema Migration)

### 2.1 Why We Pivoted From Settings Centralization
Our preliminary code audit proved that database path and connection management were **already centralized** in `data/database.py` (`DATABASE_FILE = os.path.join(...)` and `get_connection()`). Moving a single variable to a new `config/settings.py` file would be viewed by evaluators as trivial refactoring rather than a legitimate migration.

### 2.2 Migration Target & Strategy
We are implementing a production-grade **Versioned Schema Migration Subsystem**:
- **Baseline Schema (`migrations/001_initial_schema.sql`):** Captures existing Assignment 01 tables (`categories`, `transactions`, `budgets`).
- **Incremental Evolution (`migrations/002_add_transaction_note.sql`):** Safely adds an optional `note TEXT DEFAULT ''` column to the `transactions` table.
- **Migration Runner (`migrations/migrate.py`):**
  - Maintains a `schema_migrations (version TEXT PRIMARY KEY, applied_at TIMESTAMP)` table.
  - Automatically executes pending migration scripts in order.
  - Wraps all operations in SQLite transactions with automated rollbacks on failure.
  - Generates a timestamped database backup before executing any DDL statements.
  - Provides verification routines proving existing transaction and budget records remain 100% intact.

---

## 3. Concept B: Refactoring (Required 4-Layer Architecture)

### 3.1 Architecture Rules
The rubric explicitly requires strict downward dependency flow:
$$\text{Controller} \longrightarrow \text{Services} \longrightarrow \text{Repository} \longrightarrow \text{Database}$$

- **Controller (`controllers/`):** Receives UI actions, validates presence of basic fields, coordinates the appropriate service, and returns a standardized `ControllerResponse`. Zero SQL queries.
- **Services (`services/`):** Contains business logic, orchestrates domain calculators, and calls repositories. Completely decoupled from Streamlit UI.
- **Repository (`data/`):** Dedicated classes/functions executing parameterized SQL queries. Zero business formulas or UI logic.
- **Database (`expensemate.db`):** Persistent SQLite store.

### 3.2 Refactored Feature 1: Add Expense
- **Streamlit UI (`pages/1_Transactions.py`):** Collects form input and delegates directly to `ExpenseController.handle_add_expense(date, amount, type, category)`.
- **`ExpenseController`:** Checks input presence and invokes `ExpenseService.create_expense(...)`.
- **`ExpenseService`:** Validates fields via `TransactionValidator`, calls `ExpenseRepository.add_transaction(...)`, and queries budget alerts.
- **`ExpenseRepository`:** Executes parameterized `INSERT INTO transactions ...`.

### 3.3 Refactored Feature 2: Monthly Budget Summary
- **Problem in Assignment 01:** In `pages/0_Dashboard.py`, loop counting (`categories_over_budget`) and financial calculations were executed directly inside the UI rendering script.
- **Refactored Flow:**
  - `pages/0_Dashboard.py` & `pages/3_Budgets.py` call `BudgetController.get_monthly_summary(year, month)`.
  - `BudgetController` delegates to `BudgetService.get_monthly_summary(...)`.
  - `BudgetService` retrieves data via `BudgetRepository` and `TransactionRepository`, invokes `BudgetCalculator` for numerical analysis, and returns a clean DTO.
  - The UI receives a ready-to-display DTO; all inline loop calculations are eliminated from the UI.

---

## 4. Concept C: Class Rewriting & Consolidation

### 4.1 Justification for Full Rewrite
In Assignment 01, neither `TransactionValidator` nor `BudgetCalculator` existed as an object-oriented class. Instead:
- Validation was fragmented across `validators.py`, `money.py`, and `csv_validator.py` with duplicated logic and divergent error messages.
- Calculations were fragmented across `budget_calculator.py` and `savings_logic.py`, with leaky UI string formatting (`create_alert_messages`) mixed into mathematical functions.

### 4.2 Rewritten Class 1: `TransactionValidator`
Consolidates transaction validation for both manual UI entry and batch CSV import into a single class:
- `validate_amount(amount_text: str) -> int`: Parses currency strings into minor units without floating-point error.
- `validate_date(date_value: Any) -> str`: Validates format and range.
- `validate_type(type_text: str) -> str`: Validates allowed transaction types.
- `validate_category(category_name: str, valid_categories: dict) -> int`: Case-insensitive resolution.
- `validate_transaction(data: dict, valid_categories: dict) -> dict`: Aggregates all errors in a single pass.

### 4.3 Rewritten Class 2: `BudgetCalculator`
Creates a pure mathematical calculation engine:
- `calculate_totals(transactions: list) -> dict`: Single-pass calculation of income, expenses, and net balance.
- `calculate_spent_by_category(transactions: list) -> dict`: Aggregates expenditures.
- `calculate_remaining(limit: int, spent: int) -> int` & `calculate_percent_used(...)`
- `is_over_budget(limit: int, spent: int) -> bool`
- `calculate_monthly_budget_status(budgets: list, transactions: list) -> list`: Pure data output.
*String alert formatting is relocated to `services/alert_service.py` to preserve separation of concerns.*

---

## 5. Testing & Quality Assurance Plan

### 5.1 Test Baseline
All 116 existing unit and service tests must continue to pass with zero regressions.

### 5.2 Mandatory 5 Integration / System Tests
Implemented in `tests/test_assignment02_integration.py`:
1. **IT-01 (Add Expense Flow):** `ExpenseController -> ExpenseService -> ExpenseRepository -> DB` (verifies storage and retrieved minor units).
2. **IT-02 (Add Income Flow):** Verifies income persistence and automatic recalculation of overall net balance.
3. **IT-03 (Monthly Budget Summary Flow):** Verifies end-to-end flow from `BudgetController` down to SQLite and `BudgetCalculator`.
4. **IT-04 (Category-Wise Spending Flow):** Verifies multi-transaction category aggregation and exclusion of income records.
5. **IT-05 (Batch CSV Import with Layered Validation):** Verifies atomic import of valid records and granular error reporting for invalid rows.

---

## 6. Two-Member Task Split & Roadmap

| Task Area | Primary Owner | Reviewer / Support |
| :--- | :--- | :--- |
| **Concept A: Migration** | Member 1 (Burhan) | Member 2 (Teammate) |
| **Concept B: Layered Refactoring** | Member 1 (Burhan) | Member 2 (Teammate) |
| **Concept C: Class Rewriting** | Member 2 (Teammate) | Member 1 (Burhan) |
| **Testing & Integration (IT-01 - IT-05)** | Member 2 (Teammate) | Member 1 (Burhan) |
| **Documentation & Metrics Report** | Shared | Shared |

### Commit Roadmap
1. `v1.0-baseline`: Tag current Assignment 01 state on `main`.
2. `feat(migration)`: Implement `migrations/` and `migrate.py`.
3. `feat(refactor)`: Introduce `controllers/` and refactor Add Expense & Monthly Summary.
4. `feat(rewrite)`: Implement `TransactionValidator` and `BudgetCalculator` with unit tests.
5. `test(integration)`: Add IT-01 through IT-05 in `test_assignment02_integration.py`.
6. `docs`: Compile maintainability metrics, changelog, and final report.

