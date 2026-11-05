import csv
import io
from datetime import date

from data import category_repo
from data import transaction_repo
from exceptions import ValidationError
from services import budget_calculator
from services import budget_service
from services import csv_validator
from services import money
from services import validators


def get_valid_category_ids():
    ids = []
    for category in category_repo.get_all_categories():
        ids.append(category["id"])
    return ids


def add_transaction(date_value, amount_text, type_text, category_id):
    cleaned = validators.validate_transaction_fields(
        date_value, amount_text, type_text, category_id, get_valid_category_ids()
    )

    new_id = transaction_repo.add_transaction(
        cleaned["date"], cleaned["amount_minor"], cleaned["type"], cleaned["category_id"]
    )

    return {"transaction_id": new_id, "alerts": budget_service.get_budget_alerts()}


def update_transaction(transaction_id, date_value, amount_text, type_text, category_id):
    cleaned = validators.validate_transaction_fields(
        date_value, amount_text, type_text, category_id, get_valid_category_ids()
    )

    rows_changed = transaction_repo.update_transaction(
        transaction_id,
        cleaned["date"],
        cleaned["amount_minor"],
        cleaned["type"],
        cleaned["category_id"],
    )


    if rows_changed == 0:
        raise ValidationError("That transaction could not be found. It may already have been deleted.")

    return {"alerts": budget_service.get_budget_alerts()}


def delete_transaction(transaction_id):
    rows_removed = transaction_repo.delete_transaction(transaction_id)

    if rows_removed == 0:
        raise ValidationError("That transaction could not be found. It may already have been deleted.")

    return {"alerts": budget_service.get_budget_alerts()}


def delete_transactions_bulk(transaction_ids):
    if not transaction_ids:
        raise ValidationError("No transactions were selected for deletion.")

    rows_removed = transaction_repo.delete_transactions_by_ids(transaction_ids)
    return {
        "deleted_count": rows_removed,
        "alerts": budget_service.get_budget_alerts(),
    }


def delete_all_transactions():
    rows_removed = transaction_repo.delete_all_transactions()
    return {
        "deleted_count": rows_removed,
        "alerts": budget_service.get_budget_alerts(),
    }


def get_transactions(newest_first=True):
    return transaction_repo.get_all_transactions(newest_first)


def get_current_month_transactions(today=None):
    if today is None:
        today = date.today()

    first_day, last_day = budget_calculator.get_month_range(today)
    return transaction_repo.get_transactions_between(first_day, last_day)


def get_transactions_for_period(start_value, end_value):
    errors = []
    start_text = None
    end_text = None

    try:
        start_text = validators.parse_date(start_value)
    except ValidationError as error:
        for message in error.messages:
            errors.append("Start date: " + message)

    try:
        end_text = validators.parse_date(end_value)
    except ValidationError as error:
        for message in error.messages:
            errors.append("End date: " + message)

    if len(errors) > 0:
        raise ValidationError(errors)


    if start_text > end_text:
        raise ValidationError("The start date must be on or before the end date.")

    return transaction_repo.get_transactions_between(start_text, end_text)


def get_transactions_for_export(scope="all", start_value=None, end_value=None):
    if scope == "this_month":
        return get_current_month_transactions()
    elif scope == "custom":
        if start_value is None or end_value is None:
            raise ValidationError("Both start date and end date are required for a custom date range.")
        return get_transactions_for_period(start_value, end_value)
    else:
        return get_transactions(newest_first=False)


def export_transactions_to_csv(transactions):


    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\n")

    writer.writerow(csv_validator.REQUIRED_HEADER)
    for transaction in transactions:
        writer.writerow([
            transaction["date"],
            transaction["category_name"],
            money.minor_to_text(transaction["amount_minor"]),
            transaction["type"],
        ])

    return buffer.getvalue()


def import_transactions_from_csv(file_bytes):


    category_lookup = {}
    for category in category_repo.get_all_categories():
        category_lookup[category["name"].lower()] = category["id"]

    result = csv_validator.validate_csv_file(file_bytes, category_lookup)

    if not result["valid"]:
        return {
            "success": False,
            "errors": result["errors"],
            "imported_count": 0,
            "alerts": [],
        }


    transaction_repo.add_many_transactions(result["rows"])

    return {
        "success": True,
        "errors": [],
        "imported_count": len(result["rows"]),
        "alerts": budget_service.get_budget_alerts(),
    }
