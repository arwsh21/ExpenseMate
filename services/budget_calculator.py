import calendar
from datetime import date

from services import money


def get_month_range(today):
    first_day = date(today.year, today.month, 1)


    days_in_month = calendar.monthrange(today.year, today.month)[1]
    last_day = date(today.year, today.month, days_in_month)

    return first_day.isoformat(), last_day.isoformat()


def calculate_spent(transactions):
    total = 0


    for transaction in transactions:
        if transaction["type"] == "expense":
            total = total + transaction["amount_minor"]

    return total


def calculate_spent_by_category(transactions):
    spent_by_category = {}

    for transaction in transactions:
        if transaction["type"] != "expense":
            continue

        category_id = transaction["category_id"]
        if category_id not in spent_by_category:
            spent_by_category[category_id] = 0
        spent_by_category[category_id] = spent_by_category[category_id] + transaction["amount_minor"]

    return spent_by_category


def calculate_remaining(limit, spent):
    remaining = limit - spent
    return remaining


def is_over_budget(limit, spent):
    return spent > limit


def calculate_percent_used(limit, spent):
    if limit <= 0:
        return 0
    return spent * 100 // limit


def calculate_budget_status(budgets, transactions):
    spent_by_category = calculate_spent_by_category(transactions)

    status_list = []
    for budget in budgets:
        category_id = budget["category_id"]
        limit = budget["monthly_limit_minor"]


        spent = spent_by_category.get(category_id, 0)

        status = {
            "category_id": category_id,
            "category_name": budget["category_name"],
            "limit_minor": limit,
            "spent_minor": spent,
            "remaining_minor": calculate_remaining(limit, spent),
            "percent_used": calculate_percent_used(limit, spent),
            "over_budget": is_over_budget(limit, spent),
        }
        status_list.append(status)

    return status_list


def create_alert_messages(status_list):
    messages = []

    for status in status_list:
        if not status["over_budget"]:
            continue

        over_by = status["spent_minor"] - status["limit_minor"]
        message = (
            status["category_name"] + " is over budget this month: spent "
            + money.format_amount(status["spent_minor"]) + " of "
            + money.format_amount(status["limit_minor"])
            + " (over by " + money.format_amount(over_by) + ")."
        )
        messages.append(message)

    return messages
