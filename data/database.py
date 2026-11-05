import os
import sqlite3

from exceptions import DatabaseError


PROJECT_FOLDER = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATABASE_FILE = os.path.join(PROJECT_FOLDER, "expensemate.db")


DEFAULT_CATEGORIES = ["Food", "Rent", "Transport", "Bills", "Entertainment", "Other"]


SCHEMA_SQL = """
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
"""


def get_connection():
    connection = sqlite3.connect(DATABASE_FILE)


    connection.execute("PRAGMA foreign_keys = ON")


    connection.row_factory = sqlite3.Row
    return connection


def initialize_database():
    connection = None
    try:
        connection = get_connection()
        connection.executescript(SCHEMA_SQL)

        for category_name in DEFAULT_CATEGORIES:
            connection.execute(
                "INSERT OR IGNORE INTO categories (name) VALUES (?)",
                (category_name,),
            )

        connection.commit()
    except sqlite3.Error:
        raise DatabaseError(
            "Unable to open or set up the database. "
            "Please close other programs that may be using it and restart the app."
        )
    finally:


        if connection is not None:
            connection.close()


def fetch_all(sql, parameters=(), error_message=None):
    if error_message is None:
        error_message = "Unable to load your data. Please try again."

    connection = None
    try:
        connection = get_connection()
        cursor = connection.execute(sql, parameters)
        rows = cursor.fetchall()


        result = []
        for row in rows:
            result.append(dict(row))
        return result
    except sqlite3.Error:
        raise DatabaseError(error_message)
    finally:
        if connection is not None:
            connection.close()


def execute(sql, parameters, error_message):
    connection = None
    try:
        connection = get_connection()
        cursor = connection.execute(sql, parameters)


        connection.commit()

        return {"last_id": cursor.lastrowid, "rows_changed": cursor.rowcount}
    except sqlite3.Error:
        if connection is not None:
            connection.rollback()
        raise DatabaseError(error_message)
    finally:
        if connection is not None:
            connection.close()


def insert_many(sql, list_of_parameters, error_message):
    connection = None
    try:
        connection = get_connection()


        connection.executemany(sql, list_of_parameters)
        connection.commit()
    except sqlite3.Error:
        if connection is not None:
            connection.rollback()
        raise DatabaseError(error_message)
    finally:
        if connection is not None:
            connection.close()
