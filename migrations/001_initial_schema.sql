-- Migration 001: Initial ExpenseMate Schema (Assignment 01 Baseline)

CREATE TABLE IF NOT EXISTS categories (
    id    INTEGER PRIMARY KEY AUTOINCREMENT,
    name  TEXT NOT NULL UNIQUE COLLATE NOCASE
          CHECK (length(trim(name)) > 0)
);

CREATE TABLE IF NOT EXISTS transactions (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    date          TEXT    NOT NULL
                  CHECK (date GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]'),
    amount_minor  INTEGER NOT NULL CHECK (amount_minor > 0),
    type          TEXT    NOT NULL CHECK (type IN ('income', 'expense')),
    category_id   INTEGER NOT NULL REFERENCES categories(id)
);

CREATE INDEX IF NOT EXISTS idx_transactions_date
    ON transactions(date);

CREATE INDEX IF NOT EXISTS idx_transactions_category
    ON transactions(category_id);

CREATE TABLE IF NOT EXISTS budgets (
    category_id          INTEGER PRIMARY KEY REFERENCES categories(id),
    monthly_limit_minor  INTEGER NOT NULL CHECK (monthly_limit_minor > 0)
);

-- Seed default starter categories if not present
INSERT OR IGNORE INTO categories (name) VALUES ('Food');
INSERT OR IGNORE INTO categories (name) VALUES ('Rent');
INSERT OR IGNORE INTO categories (name) VALUES ('Transport');
INSERT OR IGNORE INTO categories (name) VALUES ('Bills');
INSERT OR IGNORE INTO categories (name) VALUES ('Entertainment');
INSERT OR IGNORE INTO categories (name) VALUES ('Other');

