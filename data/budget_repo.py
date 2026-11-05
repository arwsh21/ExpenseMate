from data import database


def get_all_budgets():
    sql = """
        SELECT b.category_id, c.name AS category_name, b.monthly_limit_minor
        FROM budgets AS b
        JOIN categories AS c ON c.id = b.category_id
        ORDER BY c.name COLLATE NOCASE
    """
    return database.fetch_all(
        sql,
        (),
        "Unable to load the budgets. Please try again.",
    )


def set_budget(category_id, monthly_limit_minor):
    sql = """
        INSERT OR REPLACE INTO budgets (category_id, monthly_limit_minor)
        VALUES (?, ?)
    """
    database.execute(
        sql,
        (category_id, monthly_limit_minor),
        "Unable to save the budget. Please check the amount and try again.",
    )
