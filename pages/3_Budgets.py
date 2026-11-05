from datetime import date

import streamlit as st

from exceptions import DatabaseError
from exceptions import ValidationError
from services import budget_service
from services import category_service
from ui import components


def show_budget_form(category_ids):
    st.subheader("Set a monthly budget limit")
    st.caption("Setting a limit for a category that already has one replaces the old limit.")

    form_version = st.session_state.get("budget_form_version", 0)

    with st.form("budget_form_" + str(form_version)):
        category_name = st.selectbox("Category", list(category_ids.keys()))
        limit_text = st.text_input(
            "Monthly budget limit",
            placeholder="e.g. 5000",
            help="A positive number with at most 2 decimal places.",
        )
        submitted = st.form_submit_button("Save budget", type="primary")

    if submitted:
        try:
            budget_service.set_budget(category_ids[category_name], limit_text)
        except ValidationError as error:
            components.show_errors(error.messages)
            return

        st.session_state["budget_form_version"] = form_version + 1


        components.set_flash_message("Budget for '" + category_name + "' saved successfully.", [])
        st.rerun()


def show_budget_status():
    st.subheader("This month: " + date.today().strftime("%B %Y"))

    status_list = budget_service.get_budget_status()

    if len(status_list) == 0:
        st.info("No budgets set yet. Use the form above to set a monthly limit for a category.")
        return

    components.show_alerts(budget_service.get_budget_alerts(status_list))
    components.show_budget_table(status_list)
    st.caption("Only expenses count as spent. A negative remaining amount means the budget was exceeded.")


components.show_page_header(
    "Budgets",
    "Set monthly limits and keep an eye on your spending",
)
components.show_flash_message()

try:
    category_ids = {}
    for category in category_service.get_categories():
        category_ids[category["name"]] = category["id"]

    show_budget_form(category_ids)
    show_budget_status()
except DatabaseError as error:
    components.show_database_error(error)
