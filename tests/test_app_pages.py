import os
from datetime import date

from streamlit.testing.v1 import AppTest

from data import database
from services import budget_service
from services import category_service
from services import transaction_service
from ui import components


PROJECT_FOLDER = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

ALL_PAGES = [
    "pages/0_Dashboard.py",
    "pages/1_Transactions.py",
    "pages/2_Categories.py",
    "pages/3_Budgets.py",
    "pages/4_Analytics.py",
    "pages/5_Import_Export.py",
]

TODAY_TEXT = date.today().isoformat()


def open_page(page_path):
    app = AppTest.from_file(os.path.join(PROJECT_FOLDER, page_path), default_timeout=30)
    app.run()
    return app


def find_button(app, label):
    for button in app.button:
        if button.label == label:
            return button
    return None


def texts(elements):
    result = []
    for element in elements:
        result.append(element.value)
    return result


def add_sample_transactions(category_ids):
    transaction_service.add_transaction(TODAY_TEXT, "60000", "income", category_ids["Other"])
    transaction_service.add_transaction(TODAY_TEXT, "450.50", "expense", category_ids["Food"])
    transaction_service.add_transaction("2026-01-15", "999", "expense", category_ids["Rent"])


def test_application_starts_and_shows_the_brand_name(temp_database):
    app = AppTest.from_file(os.path.join(PROJECT_FOLDER, "app.py"), default_timeout=30)
    app.run()

    assert len(app.exception) == 0

    combined = " ".join(texts(app.markdown))
    assert "ExpenseMate" in combined


def test_every_page_loads_without_errors_and_shows_the_brand(temp_database):
    for page_path in ALL_PAGES:
        app = open_page(page_path)

        assert len(app.exception) == 0, page_path + " raised an exception"
        assert len(app.error) == 0, page_path + " shows an error"
        assert "ExpenseMate" in " ".join(texts(app.markdown)), page_path


def test_every_page_loads_when_the_database_has_data(category_ids):
    add_sample_transactions(category_ids)
    budget_service.set_budget(category_ids["Food"], "100")

    for page_path in ALL_PAGES:
        app = open_page(page_path)

        assert len(app.exception) == 0, page_path + " raised an exception"


def test_empty_database_shows_friendly_empty_state_messages(temp_database):
    dashboard = open_page("pages/0_Dashboard.py")
    infos = " ".join(texts(dashboard.info))

    assert "not added any transactions yet" in infos
    assert "No budgets set yet" in infos

    analytics = open_page("pages/4_Analytics.py")
    assert len(analytics.exception) == 0

    import_export = open_page("pages/5_Import_Export.py")
    assert "no transactions to export" in " ".join(texts(import_export.info)).lower()


def test_adding_a_transaction_from_the_form(category_ids):
    app = open_page("pages/1_Transactions.py")

    app.text_input[0].input("450.50")
    app.selectbox[0].select("Food")
    find_button(app, "Save transaction").click().run()

    assert "Transaction saved successfully." in texts(app.success)
    saved = transaction_service.get_transactions()
    assert len(saved) == 1
    assert saved[0]["amount_minor"] == 45050
    assert saved[0]["category_name"] == "Food"
    assert saved[0]["type"] == "expense"


    assert app.text_input[0].value == ""


def test_choosing_income_saves_an_income_transaction(category_ids):
    app = open_page("pages/1_Transactions.py")

    app.text_input[0].input("60000")
    app.radio[1].set_value("Income")
    find_button(app, "Save transaction").click().run()

    assert transaction_service.get_transactions()[0]["type"] == "income"


def test_invalid_amount_shows_an_error_and_saves_nothing(category_ids):
    app = open_page("pages/1_Transactions.py")

    app.text_input[0].input("abc")
    find_button(app, "Save transaction").click().run()

    assert len(app.error) >= 1
    assert "must be a number" in " ".join(texts(app.error))
    assert len(app.success) == 0
    assert len(transaction_service.get_transactions()) == 0


def test_negative_and_empty_amounts_show_clear_errors(category_ids):
    app = open_page("pages/1_Transactions.py")

    app.text_input[0].input("-20")
    find_button(app, "Save transaction").click().run()
    assert "cannot be negative" in " ".join(texts(app.error))

    app.text_input[0].input("")
    find_button(app, "Save transaction").click().run()
    assert "Amount is required" in " ".join(texts(app.error))

    assert len(transaction_service.get_transactions()) == 0


def test_list_shows_transactions_newest_first_and_can_be_reversed(category_ids):
    food = category_ids["Food"]
    transaction_service.add_transaction("2026-09-10", "1", "expense", food)
    transaction_service.add_transaction("2026-09-30", "2", "expense", food)

    app = open_page("pages/1_Transactions.py")
    app.radio(key="transactions_section").set_value("All Transactions").run()

    assert app.dataframe[0].value["Date"].iloc[0] == "2026-09-30"


    app.radio[1].set_value("Oldest first").run()

    assert app.dataframe[0].value["Date"].iloc[0] == "2026-09-10"


def test_editing_a_transaction_from_the_form(category_ids):
    added = transaction_service.add_transaction("2026-09-10", "100", "expense", category_ids["Food"])
    transaction_id = added["transaction_id"]

    app = open_page("pages/1_Transactions.py")
    app.radio(key="transactions_section").set_value("Edit Transaction").run()


    assert app.text_input(key="edit_amount_" + str(transaction_id)).value == "100.00"

    app.text_input(key="edit_amount_" + str(transaction_id)).input("999.99")
    app.selectbox(key="edit_category_" + str(transaction_id)).select("Rent")
    find_button(app, "Save changes").click().run()

    assert "Transaction updated successfully." in texts(app.success)
    saved = transaction_service.get_transactions()[0]
    assert saved["amount_minor"] == 99999
    assert saved["category_name"] == "Rent"


def test_invalid_edit_shows_an_error_and_changes_nothing(category_ids):
    added = transaction_service.add_transaction("2026-09-10", "100", "expense", category_ids["Food"])
    transaction_id = added["transaction_id"]

    app = open_page("pages/1_Transactions.py")
    app.radio(key="transactions_section").set_value("Edit Transaction").run()
    app.text_input(key="edit_amount_" + str(transaction_id)).input("0")
    find_button(app, "Save changes").click().run()

    assert "greater than zero" in " ".join(texts(app.error))
    assert transaction_service.get_transactions()[0]["amount_minor"] == 10000


def test_delete_needs_confirmation_before_anything_is_removed(category_ids):
    transaction_service.add_transaction("2026-09-10", "100", "expense", category_ids["Food"])

    app = open_page("pages/1_Transactions.py")
    app.radio(key="transactions_section").set_value("Delete Transaction").run()


    assert len(transaction_service.get_transactions()) == 1
    assert find_button(app, "Yes, delete it") is None


    find_button(app, "Delete this transaction").click().run()
    assert "Are you sure" in " ".join(texts(app.warning))
    assert find_button(app, "Yes, delete it") is not None
    assert len(transaction_service.get_transactions()) == 1


    find_button(app, "Yes, delete it").click().run()
    assert len(transaction_service.get_transactions()) == 0
    assert "Transaction deleted." in texts(app.success)


def test_cancelling_a_delete_keeps_the_transaction(category_ids):
    transaction_service.add_transaction("2026-09-10", "100", "expense", category_ids["Food"])

    app = open_page("pages/1_Transactions.py")
    app.radio(key="transactions_section").set_value("Delete Transaction").run()
    find_button(app, "Delete this transaction").click().run()
    find_button(app, "Cancel").click().run()

    assert len(transaction_service.get_transactions()) == 1
    assert find_button(app, "Yes, delete it") is None


def test_creating_a_category_from_the_page(temp_database):
    app = open_page("pages/2_Categories.py")

    app.text_input[0].input("Groceries")
    find_button(app, "Create category").click().run()

    assert "Category 'Groceries' created successfully." in texts(app.success)
    names = []
    for category in category_service.get_categories():
        names.append(category["name"])
    assert "Groceries" in names


def test_duplicate_category_shows_an_error(temp_database):
    app = open_page("pages/2_Categories.py")

    app.text_input[0].input("food")
    find_button(app, "Create category").click().run()

    assert "already exists" in " ".join(texts(app.error))
    assert len(category_service.get_categories()) == 6


def test_setting_a_budget_from_the_page(category_ids):
    app = open_page("pages/3_Budgets.py")

    app.selectbox[0].select("Food")
    app.text_input[0].input("5000")
    find_button(app, "Save budget").click().run()

    assert "Budget for 'Food' saved successfully." in texts(app.success)
    assert budget_service.get_budget_status()[0]["limit_minor"] == 500000

    assert len(app.dataframe) == 1


def test_invalid_budget_limit_shows_an_error(category_ids):
    app = open_page("pages/3_Budgets.py")

    app.text_input[0].input("-50")
    find_button(app, "Save budget").click().run()

    assert "cannot be negative" in " ".join(texts(app.error))
    assert budget_service.get_budget_status() == []


def test_budget_page_and_dashboard_warn_when_over_budget(category_ids):
    budget_service.set_budget(category_ids["Food"], "100")
    transaction_service.add_transaction(TODAY_TEXT, "500", "expense", category_ids["Food"])

    budgets_page = open_page("pages/3_Budgets.py")
    assert "Food is over budget" in " ".join(texts(budgets_page.warning))

    dashboard = open_page("pages/0_Dashboard.py")
    assert "Food is over budget" in " ".join(texts(dashboard.warning))


def test_adding_an_expense_that_goes_over_budget_shows_an_alert(category_ids):
    budget_service.set_budget(category_ids["Food"], "100")

    app = open_page("pages/1_Transactions.py")
    app.text_input[0].input("500")
    app.selectbox[0].select("Food")
    find_button(app, "Save transaction").click().run()

    assert "Transaction saved successfully." in texts(app.success)
    assert "Food is over budget" in " ".join(texts(app.warning))


def test_dashboard_cards_show_this_months_totals(category_ids):
    add_sample_transactions(category_ids)
    budget_service.set_budget(category_ids["Food"], "100")

    dashboard = open_page("pages/0_Dashboard.py")

    cards = {}
    for metric in dashboard.metric:
        cards[metric.label] = metric.value
    assert cards["Income"] == "60,000.00"
    assert cards["Expenses"] == "450.50"
    assert cards["Net balance"] == "59,549.50"
    assert cards["Categories over budget"] == "1"


def test_financial_summary_defaults_to_the_current_month(category_ids):
    add_sample_transactions(category_ids)

    analytics = open_page("pages/4_Analytics.py")

    cards = {}
    for metric in analytics.metric:
        cards[metric.label] = metric.value

    assert cards["Total income"] == "60,000.00"
    assert cards["Total expenses"] == "450.50"
    assert cards["Net balance"] == "59,549.50"


def test_summary_period_can_be_changed_with_start_and_end_dates(category_ids):
    add_sample_transactions(category_ids)

    analytics = open_page("pages/4_Analytics.py")
    analytics.date_input(key="summary_start_date").set_value(date(2026, 1, 1))
    analytics.run()

    cards = {}
    for metric in analytics.metric:
        cards[metric.label] = metric.value
    assert cards["Total expenses"] == "1,449.50"


def test_start_date_after_end_date_shows_an_error(category_ids):
    analytics = open_page("pages/4_Analytics.py")
    analytics.date_input(key="summary_start_date").set_value(date(2030, 1, 1))
    analytics.date_input(key="summary_end_date").set_value(date(2029, 1, 1))
    analytics.run()

    assert "start date must be on or before" in " ".join(texts(analytics.error))


def test_charts_and_tables_appear_when_there_is_data(category_ids):
    add_sample_transactions(category_ids)
    budget_service.set_budget(category_ids["Food"], "1000")

    analytics = open_page("pages/4_Analytics.py")

    assert len(analytics.exception) == 0

    assert len(analytics.dataframe) == 2


def test_valid_csv_is_imported_from_the_page(category_ids):
    app = open_page("pages/5_Import_Export.py")
    csv_bytes = b"date,category,amount,type\n2026-09-01,Food,450,expense\n2026-09-02,Other,50000,income\n"

    app.file_uploader[0].upload("my_transactions.csv", csv_bytes, "text/csv").run()
    find_button(app, "Import transactions").click().run()

    assert "Imported 2 transaction(s) successfully." in texts(app.success)
    assert len(transaction_service.get_transactions()) == 2


def test_invalid_csv_is_rejected_and_shows_row_numbers(category_ids):
    app = open_page("pages/5_Import_Export.py")
    csv_bytes = (
        b"date,category,amount,type\n"
        b"2026-09-01,Food,450,expense\n"
        b"2026-09-02,Nowhere,10,expense\n"
    )

    app.file_uploader[0].upload("bad.csv", csv_bytes, "text/csv").run()
    find_button(app, "Import transactions").click().run()

    assert "rejected and nothing was imported" in " ".join(texts(app.error))

    problems = app.dataframe[-1].value
    assert "Row 3" in list(problems["Where"])
    assert len(transaction_service.get_transactions()) == 0


def test_csv_with_missing_column_is_rejected_from_the_page(category_ids):
    app = open_page("pages/5_Import_Export.py")

    app.file_uploader[0].upload("bad.csv", b"date,category,amount\n2026-09-01,Food,5\n", "text/csv").run()
    find_button(app, "Import transactions").click().run()

    problems = app.dataframe[-1].value
    assert "Missing required column(s): type" in " ".join(problems["Problem"])
    assert len(transaction_service.get_transactions()) == 0


def test_export_button_appears_when_there_are_transactions(category_ids):
    add_sample_transactions(category_ids)

    app = open_page("pages/5_Import_Export.py")

    assert len(app.exception) == 0
    assert "3 transaction(s) will be exported" in " ".join(texts(app.markdown))


def test_pages_show_a_friendly_message_when_the_database_fails(temp_database, monkeypatch, tmp_path):
    monkeypatch.setattr(database, "DATABASE_FILE", str(tmp_path / "gone" / "broken.db"))

    for page_path in ALL_PAGES:
        app = open_page(page_path)


        assert len(app.exception) == 0, page_path

        assert len(app.error) >= 1, page_path
        assert "sqlite" not in " ".join(texts(app.error)).lower(), page_path


def test_the_brand_constant_matches_the_required_name():
    assert components.APP_NAME == "ExpenseMate"
