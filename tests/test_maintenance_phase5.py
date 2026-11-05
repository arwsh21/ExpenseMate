from datetime import date

from data import category_repo
from data import transaction_repo
from exceptions import ValidationError
from services import budget_calculator
from services import money
from services import transaction_service


def test_bug1_is_over_budget_strict_evaluation():
    limit = 500000
    spent_under = 400000
    spent_equal = 500000
    spent_over = 2454258

    assert budget_calculator.is_over_budget(limit, spent_under) is False
    assert budget_calculator.is_over_budget(limit, spent_equal) is False
    assert budget_calculator.is_over_budget(limit, spent_over) is True


def test_bug1_calculate_budget_status_flags_overspent_categories():
    budgets = [{"category_id": 1, "category_name": "Bills", "monthly_limit_minor": 500000}]
    transactions = [
        {"id": 1, "category_id": 1, "type": "expense", "amount_minor": 2454258}
    ]

    status_list = budget_calculator.calculate_budget_status(budgets, transactions)
    assert len(status_list) == 1
    assert status_list[0]["category_name"] == "Bills"
    assert status_list[0]["over_budget"] is True
    assert status_list[0]["remaining_minor"] == -1954258
    assert status_list[0]["percent_used"] == 490


def test_bug2_negative_minor_units_money_formatting():

    assert money.minor_to_text(-50) == "-0.50"
    assert money.format_amount(-50) == "-0.50"


    assert money.minor_to_text(-120) == "-1.20"
    assert money.format_amount(-120) == "-1.20"


    assert money.minor_to_text(-1954258) == "-19542.58"
    assert money.format_amount(-1954258) == "-19,542.58"


def test_adaptive_export_all_scope(temp_database):
    cat_id = category_repo.add_category("Utilities")
    transaction_repo.add_transaction("2026-08-10", 10000, "expense", cat_id)
    transaction_repo.add_transaction("2026-09-15", 20000, "expense", cat_id)

    txs = transaction_service.get_transactions_for_export(scope="all")
    assert len(txs) == 2


def test_adaptive_export_this_month_scope(temp_database):
    cat_id = category_repo.add_category("Groceries")
    today = date.today()
    this_month_date = today.strftime("%Y-%m-10")
    last_month_date = "2020-01-01"

    transaction_repo.add_transaction(this_month_date, 15000, "expense", cat_id)
    transaction_repo.add_transaction(last_month_date, 30000, "expense", cat_id)

    txs = transaction_service.get_transactions_for_export(scope="this_month")
    assert len(txs) == 1
    assert txs[0]["date"] == this_month_date


def test_adaptive_export_custom_range_scope(temp_database):
    cat_id = category_repo.add_category("Supplies")
    transaction_repo.add_transaction("2026-06-01", 10000, "expense", cat_id)
    transaction_repo.add_transaction("2026-06-15", 25000, "expense", cat_id)
    transaction_repo.add_transaction("2026-07-01", 50000, "expense", cat_id)

    txs = transaction_service.get_transactions_for_export(
        scope="custom", start_value="2026-06-01", end_value="2026-06-20"
    )
    assert len(txs) == 2


def test_perfective_bulk_delete_transactions(temp_database):
    cat_id = category_repo.add_category("Gaming")
    t1 = transaction_repo.add_transaction("2026-09-01", 5000, "expense", cat_id)
    t2 = transaction_repo.add_transaction("2026-09-02", 7000, "expense", cat_id)
    t3 = transaction_repo.add_transaction("2026-09-03", 9000, "expense", cat_id)

    result = transaction_service.delete_transactions_bulk([t1, t3])
    assert result["deleted_count"] == 2

    remaining = transaction_repo.get_all_transactions()
    assert len(remaining) == 1
    assert remaining[0]["id"] == t2


def test_perfective_delete_all_transactions(temp_database):
    cat_id = category_repo.add_category("Dining")
    transaction_repo.add_transaction("2026-09-01", 1000, "expense", cat_id)
    transaction_repo.add_transaction("2026-09-02", 2000, "expense", cat_id)
    transaction_repo.add_transaction("2026-09-03", 3000, "expense", cat_id)

    assert len(transaction_repo.get_all_transactions()) == 3

    result = transaction_service.delete_all_transactions()
    assert result["deleted_count"] == 3
    assert len(transaction_repo.get_all_transactions()) == 0
