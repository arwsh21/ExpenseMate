from services import savings_logic


def make_transaction(date_text, amount_minor, type_text):
    return {"date": date_text, "amount_minor": amount_minor, "type": type_text}


def test_totals_for_income_and_expenses():

    transactions = [
        make_transaction("2026-09-01", 5000000, "income"),
        make_transaction("2026-09-02", 2000000, "expense"),
        make_transaction("2026-09-03", 500000, "expense"),
    ]

    totals = savings_logic.calculate_totals(transactions)

    assert totals["income_minor"] == 5000000
    assert totals["expense_minor"] == 2500000
    assert totals["net_minor"] == 2500000


def test_totals_are_zero_for_an_empty_list():
    totals = savings_logic.calculate_totals([])

    assert totals == {"income_minor": 0, "expense_minor": 0, "net_minor": 0}


def test_net_balance_is_negative_when_expenses_are_higher():
    transactions = [
        make_transaction("2026-09-01", 1000, "income"),
        make_transaction("2026-09-02", 4000, "expense"),
    ]

    assert savings_logic.calculate_totals(transactions)["net_minor"] == -3000


def test_savings_is_income_minus_expenses():
    assert savings_logic.calculate_savings(60000, 45000) == 15000


def test_savings_can_be_negative():
    assert savings_logic.calculate_savings(1000, 4000) == -3000


def test_monthly_summary_of_no_transactions_is_empty():
    assert savings_logic.calculate_monthly_summary([]) == []


def test_monthly_summary_for_a_single_month():
    transactions = [
        make_transaction("2026-09-01", 60000, "income"),
        make_transaction("2026-09-15", 20000, "expense"),
        make_transaction("2026-09-20", 10000, "expense"),
    ]

    summary = savings_logic.calculate_monthly_summary(transactions)

    assert summary == [{
        "month": "2026-09",
        "income_minor": 60000,
        "expense_minor": 30000,
        "savings_minor": 30000,
    }]


def test_empty_months_between_first_and_last_are_zero():


    transactions = [
        make_transaction("2026-06-10", 1000, "income"),
        make_transaction("2026-09-10", 400, "expense"),
    ]

    summary = savings_logic.calculate_monthly_summary(transactions)

    months = []
    for row in summary:
        months.append(row["month"])
    assert months == ["2026-06", "2026-07", "2026-08", "2026-09"]


    assert summary[1]["income_minor"] == 0
    assert summary[1]["expense_minor"] == 0
    assert summary[1]["savings_minor"] == 0
    assert summary[2]["savings_minor"] == 0


    assert summary[3]["savings_minor"] == -400


def test_monthly_summary_crosses_the_new_year():
    transactions = [
        make_transaction("2026-11-05", 100, "income"),
        make_transaction("2027-02-05", 100, "income"),
    ]

    summary = savings_logic.calculate_monthly_summary(transactions)

    months = []
    for row in summary:
        months.append(row["month"])
    assert months == ["2026-11", "2026-12", "2027-01", "2027-02"]


def test_monthly_summary_works_when_input_is_not_sorted():

    transactions = [
        make_transaction("2026-08-20", 300, "expense"),
        make_transaction("2026-06-02", 900, "income"),
        make_transaction("2026-07-11", 100, "expense"),
    ]

    summary = savings_logic.calculate_monthly_summary(transactions)

    assert summary[0]["month"] == "2026-06"
    assert summary[-1]["month"] == "2026-08"
    assert len(summary) == 3


def test_negative_savings_month():
    transactions = [
        make_transaction("2026-08-01", 6000000, "income"),
        make_transaction("2026-08-26", 8000000, "expense"),
    ]

    summary = savings_logic.calculate_monthly_summary(transactions)

    assert summary[0]["savings_minor"] == -2000000
