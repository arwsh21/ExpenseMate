import pandas as pd
import streamlit as st

from exceptions import DatabaseError
from exceptions import ValidationError
from services import category_service
from ui import components


def show_create_form():
    st.subheader("Create a new category")


    form_version = st.session_state.get("add_category_form_version", 0)

    with st.form("add_category_form_" + str(form_version)):
        name = st.text_input(
            "Category name",
            placeholder="e.g. Groceries",
            help="The name must be new. Upper and lower case letters count as the same name.",
        )
        submitted = st.form_submit_button("Create category", type="primary")

    if submitted:
        try:
            category_service.add_category(name)
        except ValidationError as error:
            components.show_errors(error.messages)
            return

        st.session_state["add_category_form_version"] = form_version + 1
        components.set_flash_message("Category '" + name.strip() + "' created successfully.", [])
        st.rerun()


def show_category_list():
    st.subheader("All categories")

    categories = category_service.get_categories()

    rows = []
    for category in categories:
        rows.append({"Category": category["name"]})
    table = pd.DataFrame(rows, columns=["Category"])

    st.caption(str(len(categories)) + " categories. Food, Rent, Transport, Bills, Entertainment and Other are provided by default.")
    st.dataframe(table, hide_index=True)


components.show_page_header(
    "Categories",
    "Organise your transactions with your own categories",
)
components.show_flash_message()

try:
    show_create_form()
    show_category_list()
except DatabaseError as error:
    components.show_database_error(error)
