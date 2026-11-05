import os
import subprocess
import sys
from datetime import date

import pytest

from data import database
from data import transaction_repo
from exceptions import DatabaseError
from exceptions import ValidationError
from services import budget_service
from services import category_service
from services import transaction_service


PROJECT_FOLDER = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


TODAY = date.today()
THIS_MONTH_DAY = TODAY.replace(day=1)


def count_transactions():
    return len(transaction_service.get_transactions())


def get_dates(transactions):
    dates = []
    for transaction in transactions:
        dates.append(transaction["date"])
    return dates


def test_starter_categories_are_created(temp_database):
    names = []
    for category in category_service.get_categories():
        names.append(category["name"])

    for expected in ["Food", "Rent", "Transport", "Bills", "Entertainment", "Other"]:
        assert expected in names
    assert len(names) == 6


def test_initializing_twice_does_not_duplicate_categories(temp_database):
    database.initialize_database()
    database.initialize_database()

    assert len(category_service.get_categories()) == 6


def test_data_survives_after_the_program_is_closed(temp_database):


    writer = (
        "import sys\n"
        "from data import database\n"
        "database.DATABASE_FILE = sys.argv[1]\n"
        "from services import transaction_service\n"
        "transaction_service.add_transaction('2026-09-20', '450.50', 'expense', 1)\n"
    )
    reader = (
        "import sys\n"
        "from data import database\n"
        "database.DATABASE_FILE = sys.argv[1]\n"
        "from services import transaction_service\n"
        "rows = transaction_service.get_transactions()\n"
        "print(len(rows), rows[0]['amount_minor'])\n"
    )

    subprocess.run([sys.executable, "-c", writer, temp_database], cwd=PROJECT_FOLDER, check=True)
    finished = subprocess.run(
        [sys.executable, "-c", reader, temp_database],
        cwd=PROJECT_FOLDER, check=True, capture_output=True, text=True,
    )

    assert finished.stdout.strip() == "1 45050"


def test_a_new_category_can_be_created(temp_database):
    new_id = category_service.add_category("  Groceries ")

    names = []
    for category in category_service.get_categories():
        names.append(category["name"])
    assert "Groceries" in names
    assert new_id > 0


def test_duplicate_category_names_are_rejected_ignoring_case(temp_database):
    with pytest.raises(ValidationError) as problem:
        category_service.add_category("fOOd")

    assert "already exists" in str(problem.value)
    assert len(category_service.get_categories()) == 6


def test_blank_category_name_is_rejected(temp_database):
    with pytest.raises(ValidationError):
        category_service.add_category("   ")


def test_a_transaction_can_be_added_and_read_back(category_ids):
    result = transaction_service.add_transaction("2026-09-20", "450.50", "expense", category_ids["Food"])

    transactions = transaction_service.get_transactions()
    assert len(transactions) == 1
    saved = transactions[0]
    assert saved["id"] == result["transaction_id"]
    assert saved["date"] == "2026-09-20"
    assert saved["amount_minor"] == 45050
    assert saved["type"] == "expense"
    assert saved["category_name"] == "Food"


def test_invalid_transaction_is_not_saved(category_ids):

    with pytest.raises(ValidationError):
        transaction_service.add_transaction("2026-09-20", "-5", "expense", category_ids["Food"])
    with pytest.raises(ValidationError):
        transaction_service.add_transaction("2026-09-20", "10", "expense", None)

    assert count_transactions() == 0


def test_unknown_category_id_is_rejected(category_ids):

    with pytest.raises(ValidationError):
        transaction_service.add_transaction("2026-09-20", "10", "expense", 9999)

    assert count_transactions() == 0


def test_future_dated_transaction_is_allowed(category_ids):
    transaction_service.add_transaction("2031-05-01", "100", "expense", category_ids["Food"])

    assert count_transactions() == 1


def test_transactions_are_newest_first_by_default_and_can_be_reversed(category_ids):
    food = category_ids["Food"]
    transaction_service.add_transaction("2026-09-10", "1", "expense", food)
    transaction_service.add_transaction("2026-09-30", "2", "expense", food)
    transaction_service.add_transaction("2026-09-20", "3", "expense", food)

    newest_first = transaction_service.get_transactions()
    oldest_first = transaction_service.get_transactions(newest_first=False)

    assert get_dates(newest_first) == ["2026-09-30", "2026-09-20", "2026-09-10"]
    assert get_dates(oldest_first) == ["2026-09-10", "2026-09-20", "2026-09-30"]


def test_same_date_transactions_keep_a_predictable_order(category_ids):
    food = category_ids["Food"]
    first = transaction_service.add_transaction("2026-09-10", "1", "expense", food)["transaction_id"]
    second = transaction_service.add_transaction("2026-09-10", "2", "expense", food)["transaction_id"]

    newest_first = transaction_service.get_transactions()


    assert newest_first[0]["id"] == second
    assert newest_first[1]["id"] == first


def test_all_four_fields_of_a_transaction_can_be_edited(category_ids):
    added = transaction_service.add_transaction("2026-09-10", "100", "expense", category_ids["Food"])
    transaction_id = added["transaction_id"]

    transaction_service.update_transaction(
        transaction_id, "2026-10-01", "2500.75", "income", category_ids["Other"]
    )

    saved = transaction_service.get_transactions()[0]
    assert saved["date"] == "2026-10-01"
    assert saved["amount_minor"] == 250075
    assert saved["type"] == "income"
    assert saved["category_name"] == "Other"
    assert count_transactions() == 1


def test_invalid_edit_leaves_the_transaction_unchanged(category_ids):
    added = transaction_service.add_transaction("2026-09-10", "100", "expense", category_ids["Food"])

    with pytest.raises(ValidationError):
        transaction_service.update_transaction(
            added["transaction_id"], "2026-09-10", "abc", "expense", category_ids["Food"]
        )

    assert transaction_service.get_transactions()[0]["amount_minor"] == 10000


def test_editing_a_missing_transaction_is_reported(category_ids):
    with pytest.raises(ValidationError) as problem:
        transaction_service.update_transaction(999, "2026-09-10", "5", "expense", category_ids["Food"])

    assert "could not be found" in str(problem.value)


def test_a_transaction_can_be_deleted(category_ids):
    keep = transaction_service.add_transaction("2026-09-10", "1", "expense", category_ids["Food"])
    remove = transaction_service.add_transaction("2026-09-11", "2", "expense", category_ids["Food"])

    transaction_service.delete_transaction(remove["transaction_id"])

    remaining = transaction_service.get_transactions()
    assert len(remaining) == 1
    assert remaining[0]["id"] == keep["transaction_id"]


def test_deleting_a_missing_transaction_is_reported(category_ids):
    with pytest.raises(ValidationError):
        transaction_service.delete_transaction(12345)


def test_a_budget_can_be_set_and_replaced_with_one_row_per_category(category_ids):
    food = category_ids["Food"]

    budget_service.set_budget(food, "5000")
    budget_service.set_budget(food, "6000.50")

    status = budget_service.get_budget_status()
    assert len(status) == 1
    assert status[0]["limit_minor"] == 600050


def test_invalid_budget_limits_are_rejected(category_ids):
    for bad_limit in ["", "-5", "0", "abc", "1.234"]:
        with pytest.raises(ValidationError):
            budget_service.set_budget(category_ids["Food"], bad_limit)

    with pytest.raises(ValidationError):
        budget_service.set_budget(9999, "100")

    assert budget_service.get_budget_status() == []


def test_remaining_budget_uses_only_this_months_expenses(category_ids):
    food = category_ids["Food"]
    budget_service.set_budget(food, "1000")

    this_month = THIS_MONTH_DAY.isoformat()
    transaction_service.add_transaction(this_month, "300", "expense", food)
    transaction_service.add_transaction(this_month, "999", "income", food)
    transaction_service.add_transaction("2020-01-15", "500", "expense", food)

    status = budget_service.get_budget_status()[0]

    assert status["spent_minor"] == 30000
    assert status["remaining_minor"] == 70000
    assert status["over_budget"] is False


def test_categories_without_a_budget_are_left_out(category_ids):
    budget_service.set_budget(category_ids["Food"], "1000")
    transaction_service.add_transaction(THIS_MONTH_DAY.isoformat(), "50", "expense", category_ids["Rent"])

    names = []
    for status in budget_service.get_budget_status():
        names.append(status["category_name"])

    assert names == ["Food"]


def test_budget_status_can_be_calculated_for_another_month(category_ids):

    food = category_ids["Food"]
    budget_service.set_budget(food, "1000")
    transaction_service.add_transaction("2026-03-10", "400", "expense", food)

    status = budget_service.get_budget_status(today=date(2026, 3, 25))[0]

    assert status["spent_minor"] == 40000


def test_alert_appears_only_when_spending_is_strictly_over_the_limit(category_ids):
    food = category_ids["Food"]
    budget_service.set_budget(food, "1000")
    this_month = THIS_MONTH_DAY.isoformat()

    exactly_at_limit = transaction_service.add_transaction(this_month, "1000", "expense", food)
    assert exactly_at_limit["alerts"] == []

    over_the_limit = transaction_service.add_transaction(this_month, "0.01", "expense", food)
    assert len(over_the_limit["alerts"]) == 1
    assert "Food is over budget" in over_the_limit["alerts"][0]


def test_budget_is_recalculated_after_edit_and_delete(category_ids):
    food = category_ids["Food"]
    budget_service.set_budget(food, "1000")
    this_month = THIS_MONTH_DAY.isoformat()
    added = transaction_service.add_transaction(this_month, "1500", "expense", food)
    assert len(added["alerts"]) == 1


    edited = transaction_service.update_transaction(
        added["transaction_id"], this_month, "400", "expense", food
    )
    assert edited["alerts"] == []
    assert budget_service.get_budget_status()[0]["spent_minor"] == 40000


    transaction_service.update_transaction(added["transaction_id"], this_month, "2000", "expense", food)
    deleted = transaction_service.delete_transaction(added["transaction_id"])
    assert deleted["alerts"] == []
    assert budget_service.get_budget_status()[0]["spent_minor"] == 0


def test_alert_is_reported_when_a_budget_is_lowered(category_ids):
    food = category_ids["Food"]
    budget_service.set_budget(food, "5000")
    transaction_service.add_transaction(THIS_MONTH_DAY.isoformat(), "2000", "expense", food)

    result = budget_service.set_budget(food, "1000")

    assert len(result["alerts"]) == 1


def test_moving_a_transaction_to_another_category_moves_the_spending(category_ids):
    food = category_ids["Food"]
    rent = category_ids["Rent"]
    budget_service.set_budget(food, "1000")
    budget_service.set_budget(rent, "1000")
    this_month = THIS_MONTH_DAY.isoformat()
    added = transaction_service.add_transaction(this_month, "700", "expense", food)

    transaction_service.update_transaction(added["transaction_id"], this_month, "700", "expense", rent)

    by_name = {}
    for status in budget_service.get_budget_status():
        by_name[status["category_name"]] = status["spent_minor"]
    assert by_name == {"Food": 0, "Rent": 70000}


def test_period_includes_both_start_and_end_dates(category_ids):
    food = category_ids["Food"]
    for day in ["2026-09-09", "2026-09-10", "2026-09-15", "2026-09-20", "2026-09-21"]:
        transaction_service.add_transaction(day, "1", "expense", food)

    found = transaction_service.get_transactions_for_period(date(2026, 9, 10), date(2026, 9, 20))

    dates = []
    for transaction in found:
        dates.append(transaction["date"])
    assert sorted(dates) == ["2026-09-10", "2026-09-15", "2026-09-20"]


def test_start_date_after_end_date_is_rejected(category_ids):
    with pytest.raises(ValidationError) as problem:
        transaction_service.get_transactions_for_period(date(2026, 9, 20), date(2026, 9, 10))

    assert "start date must be on or before" in str(problem.value)


def test_exported_csv_can_be_imported_again(category_ids):
    transaction_service.add_transaction("2026-09-10", "450.50", "expense", category_ids["Food"])
    transaction_service.add_transaction("2026-09-11", "60000", "income", category_ids["Other"])

    csv_text = transaction_service.export_transactions_to_csv(transaction_service.get_transactions())

    assert csv_text.splitlines()[0] == "date,category,amount,type"
    assert "2026-09-10,Food,450.50,expense" in csv_text

    result = transaction_service.import_transactions_from_csv(csv_text.encode("utf-8"))

    assert result["success"] is True
    assert result["imported_count"] == 2
    assert count_transactions() == 4


def test_export_of_a_category_with_a_comma_survives_a_round_trip(category_ids):
    comma_category = category_service.add_category("Food, Drinks")
    transaction_service.add_transaction("2026-09-10", "10", "expense", comma_category)

    csv_text = transaction_service.export_transactions_to_csv(transaction_service.get_transactions())
    result = transaction_service.import_transactions_from_csv(csv_text.encode("utf-8"))

    assert result["success"] is True


def test_bad_csv_file_imports_nothing(category_ids):

    bad_file = (
        "date,category,amount,type\n"
        "2026-09-01,Food,10,expense\n"
        "2026-09-02,Food,-10,expense\n"
        "2026-09-03,Rent,20,expense\n"
    ).encode("utf-8")

    result = transaction_service.import_transactions_from_csv(bad_file)

    assert result["success"] is False
    assert result["imported_count"] == 0
    assert result["errors"][0]["row"] == 3
    assert count_transactions() == 0


def test_import_never_creates_new_categories(category_ids):
    file_bytes = "date,category,amount,type\n2026-09-01,Holidays,10,expense\n".encode("utf-8")

    result = transaction_service.import_transactions_from_csv(file_bytes)

    assert result["success"] is False
    assert len(category_service.get_categories()) == 6


def test_database_level_import_is_all_or_nothing(category_ids):


    rows = [
        {"date": "2026-09-01", "amount_minor": 100, "type": "expense", "category_id": category_ids["Food"]},
        {"date": "2026-09-02", "amount_minor": 200, "type": "expense", "category_id": category_ids["Food"]},
        {"date": "2026-09-03", "amount_minor": 300, "type": "expense", "category_id": 9999},
    ]

    with pytest.raises(DatabaseError):
        transaction_repo.add_many_transactions(rows)

    assert count_transactions() == 0


def test_successful_import_reports_budget_alerts(category_ids):
    food = category_ids["Food"]
    budget_service.set_budget(food, "100")
    this_month = THIS_MONTH_DAY.isoformat()
    file_bytes = ("date,category,amount,type\n" + this_month + ",Food,500,expense\n").encode("utf-8")

    result = transaction_service.import_transactions_from_csv(file_bytes)

    assert result["success"] is True
    assert len(result["alerts"]) == 1


def test_the_sample_csv_shipped_with_the_project_is_valid(category_ids):
    sample_path = os.path.join(PROJECT_FOLDER, "sample_data", "sample_transactions.csv")
    with open(sample_path, "rb") as sample_file:
        file_bytes = sample_file.read()

    result = transaction_service.import_transactions_from_csv(file_bytes)

    assert result["success"] is True
    assert result["imported_count"] == 34


def test_database_failure_gives_a_friendly_error_not_a_crash(temp_database, monkeypatch, tmp_path):


    broken_path = str(tmp_path / "no_such_folder" / "broken.db")
    monkeypatch.setattr(database, "DATABASE_FILE", broken_path)

    with pytest.raises(DatabaseError) as problem:
        transaction_service.get_transactions()

    message = str(problem.value)
    assert "Unable to load" in message

    assert "sqlite" not in message.lower()
    assert "Traceback" not in message


def test_failed_save_shows_the_friendly_save_message(category_ids, monkeypatch, tmp_path):
    monkeypatch.setattr(database, "DATABASE_FILE", str(tmp_path / "missing_folder" / "x.db"))

    with pytest.raises(DatabaseError) as problem:
        transaction_repo.add_transaction("2026-09-20", 100, "expense", 1)

    assert "Unable to save the transaction" in str(problem.value)


def test_database_itself_refuses_bad_data(category_ids):


    with pytest.raises(DatabaseError):
        transaction_repo.add_transaction("2026-09-20", -5, "expense", category_ids["Food"])
    with pytest.raises(DatabaseError):
        transaction_repo.add_transaction("2026-09-20", 5, "refund", category_ids["Food"])
    with pytest.raises(DatabaseError):
        transaction_repo.add_transaction("not-a-date", 5, "expense", category_ids["Food"])

    assert count_transactions() == 0
