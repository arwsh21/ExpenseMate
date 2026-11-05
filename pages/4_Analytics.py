from datetime import date

import pandas as pd
import streamlit as st

from exceptions import DatabaseError
from exceptions import ValidationError
from services import budget_calculator
from services import budget_service
from services import money
from services import savings_logic
from services import transaction_service
from services import validators
from ui import charts
from ui import components


EARLIEST_DATE = date(validators.EARLIEST_YEAR, 1, 1)
LATEST_DATE = date(validators.LATEST_YEAR, 12, 31)


def show_summary_tab():
    st.subheader("Financial summary")


    first_day, last_day = budget_calculator.get_month_range(date.today())

    start_column, end_column = st.columns(2)
    start_value = start_column.date_input(
        "Start date",
        value=date.fromisoformat(first_day),
        min_value=EARLIEST_DATE,
        max_value=LATEST_DATE,
        format="YYYY-MM-DD",
        key="summary_start_date",
    )
    end_value = end_column.date_input(
        "End date",
        value=date.fromisoformat(last_day),
        min_value=EARLIEST_DATE,
        max_value=LATEST_DATE,
        format="YYYY-MM-DD",
        key="summary_end_date",
    )

    try:
        transactions = transaction_service.get_transactions_for_period(start_value, end_value)
    except ValidationError as error:

        components.show_errors(error.messages)
        return

    totals = savings_logic.calculate_totals(transactions)

    card1, card2, card3 = st.columns(3)
    card1.metric("Total income", money.format_amount(totals["income_minor"]), border=True)
    card2.metric("Total expenses", money.format_amount(totals["expense_minor"]), border=True)
    card3.metric("Net balance", money.format_amount(totals["net_minor"]), border=True)

    st.caption(
        str(len(transactions)) + " transaction(s) between "
        + start_value.isoformat() + " and " + end_value.isoformat()
        + ". Net balance = total income - total expenses."
    )


def show_category_budget_tab():
    st.subheader("Budget, spent and remaining by category")

    status_list = budget_service.get_budget_status()

    if len(status_list) == 0:
        st.info("No budgets set yet. Set a monthly limit on the Budgets page to see this chart.")
        return

    figure = charts.create_budget_chart(status_list)
    st.pyplot(figure)

    components.show_budget_table(status_list)


def show_trend_tab():
    st.subheader("Income vs expenses over time")

    transactions = transaction_service.get_transactions(newest_first=False)
    monthly_summary = savings_logic.calculate_monthly_summary(transactions)

    if len(monthly_summary) == 0:
        st.info("Add some transactions to see your monthly income, expenses and savings.")
        return

    figure = charts.create_trend_chart(monthly_summary)
    st.pyplot(figure)


    rows = []
    for row in monthly_summary:
        rows.append({
            "Month": row["month"],
            "Income": row["income_minor"] / 100,
            "Expenses": row["expense_minor"] / 100,
            "Savings": row["savings_minor"] / 100,
        })
    table = pd.DataFrame(rows, columns=["Month", "Income", "Expenses", "Savings"])

    st.dataframe(
        table,
        hide_index=True,
        column_config={
            "Income": st.column_config.NumberColumn("Income", format="%.2f"),
            "Expenses": st.column_config.NumberColumn("Expenses", format="%.2f"),
            "Savings": st.column_config.NumberColumn("Savings", format="%.2f"),
        },
    )
    st.caption("Savings = income - expenses for the month. It is negative when expenses are higher than income.")


components.show_page_header(
    "Analytics",
    "See where your money goes and how much you save",
)

try:

    summary_tab, budget_tab, trend_tab = st.tabs(
        ["Financial summary", "Category budgets", "Income vs expenses"]
    )

    with summary_tab:
        show_summary_tab()
    with budget_tab:
        show_category_budget_tab()
    with trend_tab:
        show_trend_tab()
except DatabaseError as error:
    components.show_database_error(error)
