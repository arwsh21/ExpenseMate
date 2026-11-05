from datetime import date

import pandas as pd
import streamlit as st

from exceptions import DatabaseError
from exceptions import ValidationError
from services import budget_calculator
from services import transaction_service
from services import validators
from ui import components


EXPORT_FILE_NAME = "ExpenseMate_transactions.csv"

EXAMPLE_CSV = """date,category,amount,type
2026-09-01,Food,450,expense
2026-09-02,Other,50000,income"""


def show_export_section():
    st.subheader("Export transactions")


    all_transactions = transaction_service.get_transactions()
    if len(all_transactions) == 0:
        st.info("There are no transactions to export yet.")
        return


    scope_choice = st.radio(
        "Select export range",
        ["All transactions", "Current month only", "Custom date range"],
        horizontal=True,
        key="export_scope_radio",
    )

    transactions = []
    start_value = None
    end_value = None

    if scope_choice == "All transactions":
        transactions = transaction_service.get_transactions_for_export(scope="all")
        file_suffix = "all"
    elif scope_choice == "Current month only":
        transactions = transaction_service.get_transactions_for_export(scope="this_month")
        today = date.today()
        file_suffix = today.strftime("%Y-%m")
    else:
        first_day, last_day = budget_calculator.get_month_range(date.today())
        col1, col2 = st.columns(2)
        start_value = col1.date_input(
            "Start date",
            value=date.fromisoformat(first_day),
            min_value=date(validators.EARLIEST_YEAR, 1, 1),
            max_value=date(validators.LATEST_YEAR, 12, 31),
            format="YYYY-MM-DD",
            key="export_start_date",
        )
        end_value = col2.date_input(
            "End date",
            value=date.fromisoformat(last_day),
            min_value=date(validators.EARLIEST_YEAR, 1, 1),
            max_value=date(validators.LATEST_YEAR, 12, 31),
            format="YYYY-MM-DD",
            key="export_end_date",
        )

        try:
            transactions = transaction_service.get_transactions_for_export(
                scope="custom", start_value=start_value, end_value=end_value
            )
        except ValidationError as error:
            components.show_errors(error.messages)
            return

        file_suffix = f"{start_value.isoformat()}_to_{end_value.isoformat()}"

    if len(transactions) == 0:
        st.info("No transactions found for the selected export range.")
        return

    st.write(
        str(len(transactions)) + " transaction(s) will be exported. "
        "The file uses the same columns as the import format, so you can import it again later."
    )

    csv_text = transaction_service.export_transactions_to_csv(transactions)
    export_filename = f"ExpenseMate_transactions_{file_suffix}.csv"

    st.download_button(
        "Download transactions as CSV",
        data=csv_text,
        file_name=export_filename,
        mime="text/csv",
        type="primary",
    )


def show_import_section():
    st.subheader("Import transactions")


    with st.expander("Required CSV format"):
        st.write("The file must use exactly these columns, in this order:")
        st.code(EXAMPLE_CSV, language="text")
        st.markdown(
            "- **date**: written as YYYY-MM-DD\n"
            "- **category**: must match an existing category (spaces at the ends and upper/lower case are ignored)\n"
            "- **amount**: a positive number with at most 2 decimal places\n"
            "- **type**: `income` or `expense` in lowercase\n"
            "- The file must be UTF-8 text with no extra columns.\n"
            "- If **any** row is invalid, the whole file is rejected and nothing is imported."
        )


    uploader_version = st.session_state.get("uploader_version", 0)


    uploaded_file = st.file_uploader(
        "Choose a CSV file",
        type=["csv"],
        key="csv_uploader_" + str(uploader_version),
    )

    if uploaded_file is None:
        return


    if st.button("Import transactions", type="primary"):

        result = transaction_service.import_transactions_from_csv(uploaded_file.getvalue())

        if result["success"]:
            st.session_state["uploader_version"] = uploader_version + 1
            count = result["imported_count"]
            components.set_flash_message(
                "Imported " + str(count) + " transaction(s) successfully.",
                result["alerts"],
            )
            st.rerun()
        else:
            show_rejected_file(result["errors"])


def show_rejected_file(errors):
    st.error("The file was rejected and nothing was imported. Please fix the problems below and try again.")

    rows = []
    for error in errors:
        if error["row"] == 0:
            where = "Whole file"
        else:
            where = "Row " + str(error["row"])
        rows.append({"Where": where, "Problem": error["problem"]})

    st.caption(str(len(rows)) + " problem(s) found")
    st.dataframe(pd.DataFrame(rows, columns=["Where", "Problem"]), hide_index=True)


components.show_page_header(
    "Import / Export",
    "Back up your transactions or bring them in from a CSV file",
)
components.show_flash_message()

try:
    show_export_section()
    st.divider()
    show_import_section()
except DatabaseError as error:
    components.show_database_error(error)
