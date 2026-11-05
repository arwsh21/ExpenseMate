import pytest

from data import database
from services import category_service


@pytest.fixture
def temp_database(tmp_path, monkeypatch):
    test_file = str(tmp_path / "test_expensemate.db")


    monkeypatch.setattr(database, "DATABASE_FILE", test_file)


    database.initialize_database()
    return test_file


@pytest.fixture
def category_ids(temp_database):
    result = {}
    for category in category_service.get_categories():
        result[category["name"]] = category["id"]
    return result
