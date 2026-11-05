from datetime import date

from data import budget_repo
from data import category_repo
from data import transaction_repo
from exceptions import ValidationError
from services import budget_calculator
from services import money


def set_budget(category_id, limit_text):
    errors = []

    limit_minor = None
    try:
        limit_minor = money.parse_amount(limit_text, "Budget limit")
    except ValidationError as error:
        errors.extend(error.messages)


    category_exists = False
    for category in category_repo.get_all_categories():
        if category["id"] == category_id:
            category_exists = True
    if not category_exists:
        errors.append("Please choose a category.")

    if len(errors) > 0:
        raise ValidationError(errors)

    budget_repo.set_budget(category_id, limit_minor)

    return {"alerts": get_budget_alerts()}


def get_budget_status(today=None, month_transactions=None):
    budgets = budget_repo.get_all_budgets()


    if len(budgets) == 0:
        return []

    if month_transactions is None:
        if today is None:
            today = date.today()
        first_day, last_day = budget_calculator.get_month_range(today)
        month_transactions = transaction_repo.get_transactions_between(first_day, last_day)

    return budget_calculator.calculate_budget_status(budgets, month_transactions)


def get_budget_alerts(status_list=None, today=None):
    if status_list is None:
        status_list = get_budget_status(today)

    return budget_calculator.create_alert_messages(status_list)
