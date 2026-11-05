from datetime import date
from datetime import datetime

import pytest

from exceptions import ValidationError
from services import money
from services import validators


def test_amount_text_is_converted_to_whole_minor_units():

    assert money.parse_amount("450.50") == 45050
    assert money.parse_amount("450") == 45000
    assert money.parse_amount("0.05") == 5
    assert money.parse_amount(".5") == 50
    assert money.parse_amount("  12.3  ") == 1230


def test_amount_conversion_has_no_floating_point_error():


    total = money.parse_amount("0.10") + money.parse_amount("0.20")

    assert total == money.parse_amount("0.30")


def test_negative_amount_is_rejected():


    with pytest.raises(ValidationError) as problem:
        money.parse_amount("-10")

    assert "cannot be negative" in str(problem.value)


def test_zero_amount_is_rejected():
    with pytest.raises(ValidationError):
        money.parse_amount("0")
    with pytest.raises(ValidationError):
        money.parse_amount("0.00")


def test_non_numeric_amounts_are_rejected():
    for bad_text in ["abc", "12abc", "1,000", "1e3", "+5", "1.2.3", ".", "$5"]:
        with pytest.raises(ValidationError):
            money.parse_amount(bad_text)


def test_empty_amount_is_rejected():
    with pytest.raises(ValidationError) as problem:
        money.parse_amount("")
    assert "required" in str(problem.value)

    with pytest.raises(ValidationError):
        money.parse_amount(None)


def test_more_than_two_decimals_is_rejected():
    with pytest.raises(ValidationError) as problem:
        money.parse_amount("1.234")

    assert "2 decimal places" in str(problem.value)


def test_absurdly_large_amount_is_rejected():

    with pytest.raises(ValidationError):
        money.parse_amount("1000000000000")


    assert money.parse_amount("999999999999") == 99999999999900


def test_budget_limit_uses_its_own_name_in_messages():
    with pytest.raises(ValidationError) as problem:
        money.parse_amount("", "Budget limit")

    assert "Budget limit is required" in str(problem.value)


def test_amounts_are_shown_with_two_decimals():
    assert money.minor_to_text(45050) == "450.50"
    assert money.minor_to_text(5) == "0.05"
    assert money.minor_to_text(-250) == "-2.50"


def test_amounts_on_screen_have_thousands_separators():
    assert money.format_amount(123456789) == "1,234,567.89"
    assert money.format_amount(100) == "1.00"
    assert money.format_amount(-1250000) == "-12,500.00"


def test_valid_dates_are_accepted_as_text_or_date_objects():
    assert validators.parse_date("2026-09-20") == "2026-09-20"
    assert validators.parse_date(date(2026, 9, 20)) == "2026-09-20"
    assert validators.parse_date(datetime(2026, 9, 20, 15, 30)) == "2026-09-20"


def test_future_dates_are_allowed():
    assert validators.parse_date("2031-01-01") == "2031-01-01"


def test_impossible_and_badly_formatted_dates_are_rejected():
    for bad_date in ["2026-02-30", "2026-13-01", "2026-9-1", "20/09/2026", "abc", "2026-09-2x"]:
        with pytest.raises(ValidationError):
            validators.parse_date(bad_date)


def test_missing_date_is_rejected():
    with pytest.raises(ValidationError):
        validators.parse_date(None)
    with pytest.raises(ValidationError):
        validators.parse_date("")


def test_dates_outside_the_supported_years_are_rejected():
    with pytest.raises(ValidationError):
        validators.parse_date("1899-12-31")
    with pytest.raises(ValidationError):
        validators.parse_date("2101-01-01")


def test_type_must_be_income_or_expense():
    assert validators.parse_type("income") == "income"
    assert validators.parse_type("expense") == "expense"

    for bad_type in ["Income", "EXPENSE", "", None, "refund"]:
        with pytest.raises(ValidationError):
            validators.parse_type(bad_type)


def test_category_name_is_trimmed():
    assert validators.parse_category_name("  Groceries  ") == "Groceries"


def test_blank_or_too_long_category_names_are_rejected():
    for bad_name in ["", "   ", None, "x" * 51]:
        with pytest.raises(ValidationError):
            validators.parse_category_name(bad_name)


def test_valid_transaction_fields_are_cleaned():
    cleaned = validators.validate_transaction_fields(
        date(2026, 9, 20), "450.50", "expense", 2, [1, 2, 3]
    )

    assert cleaned == {
        "date": "2026-09-20",
        "amount_minor": 45050,
        "type": "expense",
        "category_id": 2,
    }


def test_all_problems_are_reported_together():
    with pytest.raises(ValidationError) as problem:
        validators.validate_transaction_fields("2026-02-30", "abc", "other", None, [1, 2, 3])


    assert len(problem.value.messages) == 4


def test_a_category_that_does_not_exist_is_rejected():

    with pytest.raises(ValidationError) as problem:
        validators.validate_transaction_fields("2026-09-20", "10", "expense", 99, [1, 2, 3])

    assert "choose a category" in str(problem.value)
