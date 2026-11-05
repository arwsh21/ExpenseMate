from datetime import date, datetime

from exceptions import ValidationError
from services import money


VALID_TYPES = ["income", "expense"]


EARLIEST_YEAR = 1900
LATEST_YEAR = 2100
MAX_CATEGORY_NAME_LENGTH = 50


def parse_date(value):
    if value is None or value == "":
        raise ValidationError("Date is required.")


    if isinstance(value, datetime):
        value = value.date()
    if isinstance(value, date):
        date_text = value.isoformat()
    else:
        date_text = str(value)


    if len(date_text) != 10 or date_text[4] != "-" or date_text[7] != "-":
        raise ValidationError("Date must use the format YYYY-MM-DD (for example 2026-09-20).")


    try:
        parsed = datetime.strptime(date_text, "%Y-%m-%d")
    except ValueError:
        raise ValidationError("Date is not a real calendar date. Use the format YYYY-MM-DD.")

    if parsed.year < EARLIEST_YEAR or parsed.year > LATEST_YEAR:
        raise ValidationError(
            "Date must be between the years "
            + str(EARLIEST_YEAR) + " and " + str(LATEST_YEAR) + "."
        )

    return parsed.strftime("%Y-%m-%d")


def parse_type(value):
    if value not in VALID_TYPES:
        raise ValidationError("Type must be either income or expense.")
    return value


def parse_category_name(name):
    if name is None:
        name = ""
    name = str(name).strip()

    if name == "":
        raise ValidationError("Category name is required.")

    if len(name) > MAX_CATEGORY_NAME_LENGTH:
        raise ValidationError(
            "Category name can have at most " + str(MAX_CATEGORY_NAME_LENGTH) + " characters."
        )

    return name


def validate_transaction_fields(date_value, amount_text, type_text, category_id, valid_category_ids):
    errors = []
    cleaned = {}


    try:
        cleaned["date"] = parse_date(date_value)
    except ValidationError as error:
        errors.extend(error.messages)

    try:
        cleaned["amount_minor"] = money.parse_amount(amount_text, "Amount")
    except ValidationError as error:
        errors.extend(error.messages)

    try:
        cleaned["type"] = parse_type(type_text)
    except ValidationError as error:
        errors.extend(error.messages)


    if category_id is None or category_id not in valid_category_ids:
        errors.append("Please choose a category.")
    else:
        cleaned["category_id"] = category_id

    if len(errors) > 0:
        raise ValidationError(errors)

    return cleaned
