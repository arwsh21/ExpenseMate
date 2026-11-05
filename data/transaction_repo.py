from data import database


SELECT_TRANSACTIONS = """
    SELECT t.id, t.date, t.amount_minor, t.type,
           t.category_id, c.name AS category_name
    FROM transactions AS t
    JOIN categories AS c ON c.id = t.category_id
"""


def add_transaction(date_text, amount_minor, type_text, category_id):
    sql = """
        INSERT INTO transactions (date, amount_minor, type, category_id)
        VALUES (?, ?, ?, ?)
    """
    result = database.execute(
        sql,
        (date_text, amount_minor, type_text, category_id),
        "Unable to save the transaction. "
        "Please check the entered information and try again.",
    )
    return result["last_id"]


def add_many_transactions(rows):
    sql = """
        INSERT INTO transactions (date, amount_minor, type, category_id)
        VALUES (?, ?, ?, ?)
    """


    list_of_parameters = []
    for row in rows:
        parameters = (row["date"], row["amount_minor"], row["type"], row["category_id"])
        list_of_parameters.append(parameters)

    database.insert_many(
        sql,
        list_of_parameters,
        "Unable to import the transactions. Nothing was imported. Please try again.",
    )


def update_transaction(transaction_id, date_text, amount_minor, type_text, category_id):
    sql = """
        UPDATE transactions
        SET date = ?, amount_minor = ?, type = ?, category_id = ?
        WHERE id = ?
    """
    result = database.execute(
        sql,
        (date_text, amount_minor, type_text, category_id, transaction_id),
        "Unable to update the transaction. "
        "Please check the entered information and try again.",
    )
    return result["rows_changed"]


def delete_transaction(transaction_id):
    sql = "DELETE FROM transactions WHERE id = ?"
    result = database.execute(
        sql,
        (transaction_id,),
        "Unable to delete the transaction. Please try again.",
    )
    return result["rows_changed"]


def delete_transactions_by_ids(transaction_ids):
    if not transaction_ids:
        return 0
    placeholders = ",".join(["?"] * len(transaction_ids))
    sql = f"DELETE FROM transactions WHERE id IN ({placeholders})"
    result = database.execute(
        sql,
        tuple(transaction_ids),
        "Unable to delete the selected transactions. Please try again.",
    )
    return result["rows_changed"]


def delete_all_transactions():
    sql = "DELETE FROM transactions"
    result = database.execute(
        sql,
        (),
        "Unable to delete all transactions. Please try again.",
    )
    return result["rows_changed"]


def get_all_transactions(newest_first=True):
    if newest_first:
        sql = SELECT_TRANSACTIONS + " ORDER BY t.date DESC, t.id DESC"
    else:
        sql = SELECT_TRANSACTIONS + " ORDER BY t.date ASC, t.id ASC"

    return database.fetch_all(
        sql,
        (),
        "Unable to load the transactions. Please try again.",
    )


def get_transactions_between(start_date_text, end_date_text):
    sql = (
        SELECT_TRANSACTIONS
        + " WHERE t.date BETWEEN ? AND ? ORDER BY t.date DESC, t.id DESC"
    )
    return database.fetch_all(
        sql,
        (start_date_text, end_date_text),
        "Unable to load the transactions. Please try again.",
    )
