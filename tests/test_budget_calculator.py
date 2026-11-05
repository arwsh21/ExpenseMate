from datetime import date

from services import budget_calculator


def make_transaction(category_id, amount_minor, type_text="expense"):
    return {
        "category_id": category_id,
        "amount_minor": amount_minor,
        "type": type_text,
    }


def test_month_range_for_a_30_day_month():

    first_day, last_day = budget_calculator.get_month_range(date(2026, 9, 23))

    assert first_day == "2026-09-01"
    assert last_day == "2026-09-30"


def test_month_range_handles_february_in_leap_and_normal_years():

    assert budget_calculator.get_month_range(date(2028, 2, 10))[1] == "2028-02-29"
    assert budget_calculator.get_month_range(date(2027, 2, 10))[1] == "2027-02-28"


def test_month_range_for_december():
    first_day, last_day = budget_calculator.get_month_range(date(2026, 12, 31))

    assert first_day == "2026-12-01"
    assert last_day == "2026-12-31"


def test_spent_adds_up_expenses():
    transactions = [make_transaction(1, 1000), make_transaction(1, 2500)]

    assert budget_calculator.calculate_spent(transactions) == 3500


def test_spent_ignores_income():

    transactions = [
        make_transaction(1, 1000, "expense"),
        make_transaction(1, 9999, "income"),
    ]

    assert budget_calculator.calculate_spent(transactions) == 1000


def test_spent_is_zero_for_no_transactions():
    assert budget_calculator.calculate_spent([]) == 0


def test_spent_by_category_groups_expenses_and_skips_income():
    transactions = [
        make_transaction(1, 1000),
        make_transaction(2, 500),
        make_transaction(1, 250),
        make_transaction(2, 800, "income"),
    ]

    result = budget_calculator.calculate_spent_by_category(transactions)

    assert result == {1: 1250, 2: 500}


def test_remaining_budget():


    assert budget_calculator.calculate_remaining(10000, 4000) == 6000


def test_remaining_is_negative_when_overspent():
    assert budget_calculator.calculate_remaining(10000, 12500) == -2500


def test_over_budget_only_when_strictly_greater_than_limit():

    assert budget_calculator.is_over_budget(10000, 10001) is True
    assert budget_calculator.is_over_budget(10000, 10000) is False
    assert budget_calculator.is_over_budget(10000, 9999) is False


def test_percent_used():
    assert budget_calculator.calculate_percent_used(10000, 2500) == 25
    assert budget_calculator.calculate_percent_used(10000, 0) == 0
    assert budget_calculator.calculate_percent_used(10000, 15000) == 150


def test_budget_status_for_several_categories():
    budgets = [
        {"category_id": 1, "category_name": "Food", "monthly_limit_minor": 500000},
        {"category_id": 2, "category_name": "Transport", "monthly_limit_minor": 100000},
        {"category_id": 3, "category_name": "Bills", "monthly_limit_minor": 300000},
    ]
    transactions = [
        make_transaction(1, 200000),
        make_transaction(1, 350000),
        make_transaction(2, 40000),
        make_transaction(2, 90000, "income"),
        make_transaction(9, 777777),
    ]

    status_list = budget_calculator.calculate_budget_status(budgets, transactions)


    assert len(status_list) == 3

    food = status_list[0]
    assert food["category_name"] == "Food"
    assert food["spent_minor"] == 550000
    assert food["remaining_minor"] == -50000
    assert food["over_budget"] is True

    transport = status_list[1]
    assert transport["spent_minor"] == 40000
    assert transport["remaining_minor"] == 60000
    assert transport["over_budget"] is False


    bills = status_list[2]
    assert bills["spent_minor"] == 0
    assert bills["remaining_minor"] == 300000
    assert bills["percent_used"] == 0


def test_budget_status_with_no_budgets_is_empty():
    assert budget_calculator.calculate_budget_status([], [make_transaction(1, 500)]) == []


def test_alert_message_for_a_category_over_budget():
    status_list = [{
        "category_name": "Food",
        "limit_minor": 500000,
        "spent_minor": 520050,
        "over_budget": True,
    }]

    messages = budget_calculator.create_alert_messages(status_list)

    assert messages == [
        "Food is over budget this month: spent 5,200.50 of 5,000.00 (over by 200.50)."
    ]


def test_no_alert_when_spending_equals_the_limit_or_is_below():
    status_list = [
        {"category_name": "Food", "limit_minor": 1000, "spent_minor": 1000, "over_budget": False},
        {"category_name": "Rent", "limit_minor": 1000, "spent_minor": 10, "over_budget": False},
    ]

    assert budget_calculator.create_alert_messages(status_list) == []
