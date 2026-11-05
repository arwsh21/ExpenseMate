from datetime import date

import streamlit as st

from exceptions import DatabaseError
from services import budget_service
from services import money
from services import savings_logic
from services import transaction_service
from ui import components


components.show_page_header(
    components.APP_NAME,
    "Dashboard - your income, expenses and budgets at a glance",
)


try:
    month_transactions = transaction_service.get_current_month_transactions()
    status_list = budget_service.get_budget_status(month_transactions=month_transactions)
    all_transactions = transaction_service.get_transactions(newest_first=True)
except DatabaseError as error:
    components.show_database_error(error)
    st.stop()


alerts = budget_service.get_budget_alerts(status_list)
components.show_alerts(alerts)


st.subheader("This month: " + date.today().strftime("%B %Y"))

totals = savings_logic.calculate_totals(month_transactions)


categories_over_budget = 0
for status in status_list:
    if status["over_budget"]:
        categories_over_budget = categories_over_budget + 1


card1, card2, card3, card4 = st.columns(4)
card1.metric("Income", money.format_amount(totals["income_minor"]), border=True)
card2.metric("Expenses", money.format_amount(totals["expense_minor"]), border=True)
card3.metric("Net balance", money.format_amount(totals["net_minor"]), border=True)
card4.metric("Categories over budget", categories_over_budget, border=True)


left_column, right_column = st.columns([3, 2])

with left_column:
    st.subheader("Recent transactions")
    if len(all_transactions) == 0:
        st.info("You have not added any transactions yet. Open the Transactions page to add your first one.")
    else:

        components.show_transactions_table(all_transactions[0:5])

with right_column:
    st.subheader("Budget progress")
    if len(status_list) == 0:
        st.info("No budgets set yet. Open the Budgets page to set a monthly limit for a category.")
    else:
        components.show_budget_progress(status_list)
