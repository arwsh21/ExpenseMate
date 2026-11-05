import os
import time
from datetime import date
from datetime import timedelta

from streamlit.testing.v1 import AppTest

from data import transaction_repo
from services import budget_service
from services import savings_logic
from services import transaction_service


PROJECT_FOLDER = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


MAX_SECONDS = 2.0

TRANSACTION_COUNT = 500


def fill_with_500_transactions(category_ids):
    category_id_list = list(category_ids.values())
    first_day = date.today() - timedelta(days=500)

    rows = []
    for number in range(TRANSACTION_COUNT):
        day = first_day + timedelta(days=number)
        if number % 10 == 0:
            type_text = "income"
        else:
            type_text = "expense"

        rows.append({
            "date": day.isoformat(),
            "amount_minor": 10000 + number * 37,
            "type": type_text,
            "category_id": category_id_list[number % len(category_id_list)],
        })

    transaction_repo.add_many_transactions(rows)


def seconds_since(start_time):
    return time.perf_counter() - start_time


def test_loading_500_transactions_is_fast(category_ids):
    fill_with_500_transactions(category_ids)

    start = time.perf_counter()
    transactions = transaction_service.get_transactions()
    seconds = seconds_since(start)

    assert len(transactions) == TRANSACTION_COUNT
    assert seconds < MAX_SECONDS


def test_transactions_page_with_500_rows_renders_within_two_seconds(category_ids):
    fill_with_500_transactions(category_ids)
    app = AppTest.from_file(os.path.join(PROJECT_FOLDER, "pages/1_Transactions.py"), default_timeout=30)
    app.run()


    start = time.perf_counter()
    app.radio(key="transactions_section").set_value("All Transactions").run()
    seconds = seconds_since(start)

    assert len(app.exception) == 0
    assert len(app.dataframe[0].value) == TRANSACTION_COUNT
    assert seconds < MAX_SECONDS


def test_dashboard_and_analytics_with_500_transactions_are_fast(category_ids):
    fill_with_500_transactions(category_ids)
    budget_service.set_budget(category_ids["Food"], "1000")

    for page_path in ["pages/0_Dashboard.py", "pages/4_Analytics.py"]:
        app = AppTest.from_file(os.path.join(PROJECT_FOLDER, page_path), default_timeout=30)

        start = time.perf_counter()
        app.run()
        seconds = seconds_since(start)

        assert len(app.exception) == 0, page_path
        assert seconds < MAX_SECONDS, page_path + " took " + str(seconds) + " seconds"


def test_calculations_over_500_transactions_are_fast(category_ids):
    fill_with_500_transactions(category_ids)
    budget_service.set_budget(category_ids["Food"], "1000")
    transactions = transaction_service.get_transactions()

    start = time.perf_counter()
    budget_service.get_budget_status()
    status_seconds = seconds_since(start)

    start = time.perf_counter()
    savings_logic.calculate_monthly_summary(transactions)
    summary_seconds = seconds_since(start)

    assert status_seconds < MAX_SECONDS
    assert summary_seconds < MAX_SECONDS


def test_add_edit_and_delete_each_respond_within_two_seconds(category_ids):
    fill_with_500_transactions(category_ids)
    food = category_ids["Food"]
    budget_service.set_budget(food, "1000")
    today_text = date.today().isoformat()


    start = time.perf_counter()
    added = transaction_service.add_transaction(today_text, "123.45", "expense", food)
    add_seconds = seconds_since(start)
    new_id = added["transaction_id"]


    start = time.perf_counter()
    transaction_service.update_transaction(new_id, today_text, "200", "expense", food)
    edit_seconds = seconds_since(start)


    start = time.perf_counter()
    transaction_service.delete_transaction(new_id)
    delete_seconds = seconds_since(start)

    assert add_seconds < MAX_SECONDS
    assert edit_seconds < MAX_SECONDS
    assert delete_seconds < MAX_SECONDS
    assert len(transaction_service.get_transactions()) == TRANSACTION_COUNT


def test_adding_a_transaction_through_the_page_is_fast(category_ids):
    fill_with_500_transactions(category_ids)
    app = AppTest.from_file(os.path.join(PROJECT_FOLDER, "pages/1_Transactions.py"), default_timeout=30)
    app.run()
    app.text_input[0].input("99")

    start = time.perf_counter()
    app.button[0].click().run()
    seconds = seconds_since(start)

    assert app.success[0].value == "Transaction saved successfully."
    assert seconds < MAX_SECONDS
