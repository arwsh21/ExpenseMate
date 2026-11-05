from datetime import date

import streamlit as st

from exceptions import DatabaseError
from exceptions import ValidationError
from services import category_service
from services import money
from services import transaction_service
from services import validators
from ui import components


EARLIEST_DATE = date(validators.EARLIEST_YEAR, 1, 1)
LATEST_DATE = date(validators.LATEST_YEAR, 12, 31)

TYPE_CHOICES = ["Expense", "Income"]


def show_add_section(category_ids):
    st.subheader("Add a new transaction")


    form_version = st.session_state.get("add_form_version", 0)


    with st.form("add_transaction_form_" + str(form_version)):
        date_value = st.date_input(
            "Date",
            value=date.today(),
            min_value=EARLIEST_DATE,
            max_value=LATEST_DATE,
            format="YYYY-MM-DD",
            help="Future dates are allowed.",
        )
        amount_text = st.text_input(
            "Amount",
            placeholder="e.g. 450 or 450.50",
            help="A positive number with at most 2 decimal places.",
        )
        type_label = st.radio("Type", TYPE_CHOICES, horizontal=True)


        category_name = st.selectbox("Category", list(category_ids.keys()))

        submitted = st.form_submit_button("Save transaction", type="primary")


    if submitted:
        try:
            result = transaction_service.add_transaction(
                date_value,
                amount_text,
                type_label.lower(),
                category_ids[category_name],
            )
        except ValidationError as error:

            components.show_errors(error.messages)
            return


        st.session_state["add_form_version"] = form_version + 1
        components.set_flash_message("Transaction saved successfully.", result["alerts"])
        st.rerun()


def show_list_section():
    st.subheader("All transactions")

    sort_choice = st.radio(
        "Sort by date",
        ["Newest first", "Oldest first"],
        horizontal=True,
    )
    newest_first = (sort_choice == "Newest first")

    transactions = transaction_service.get_transactions(newest_first)

    st.caption(str(len(transactions)) + " transaction(s)")
    components.show_transactions_table(transactions)


def index_transactions(transactions):
    transactions_by_id = {}
    labels_by_id = {}

    for transaction in transactions:
        transactions_by_id[transaction["id"]] = transaction
        labels_by_id[transaction["id"]] = components.describe_transaction(transaction)

    return transactions_by_id, labels_by_id


def show_edit_section(category_ids):
    st.subheader("Edit a transaction")

    transactions = transaction_service.get_transactions(newest_first=True)
    if len(transactions) == 0:
        st.info("There are no transactions to edit yet.")
        return

    transactions_by_id, labels_by_id = index_transactions(transactions)


    selected_id = st.selectbox(
        "Choose the transaction to edit",
        list(labels_by_id.keys()),
        format_func=labels_by_id.get,
    )
    transaction = transactions_by_id[selected_id]

    category_names = list(category_ids.keys())
    id_text = str(selected_id)


    with st.form("edit_transaction_form_" + id_text):
        date_value = st.date_input(
            "Date",
            value=date.fromisoformat(transaction["date"]),
            min_value=EARLIEST_DATE,
            max_value=LATEST_DATE,
            format="YYYY-MM-DD",
            key="edit_date_" + id_text,
        )
        amount_text = st.text_input(
            "Amount",
            value=money.minor_to_text(transaction["amount_minor"]),
            key="edit_amount_" + id_text,
        )
        type_label = st.radio(
            "Type",
            TYPE_CHOICES,
            index=TYPE_CHOICES.index(transaction["type"].capitalize()),
            horizontal=True,
            key="edit_type_" + id_text,
        )
        category_name = st.selectbox(
            "Category",
            category_names,
            index=category_names.index(transaction["category_name"]),
            key="edit_category_" + id_text,
        )
        submitted = st.form_submit_button("Save changes", type="primary")

    if submitted:
        try:
            result = transaction_service.update_transaction(
                selected_id,
                date_value,
                amount_text,
                type_label.lower(),
                category_ids[category_name],
            )
        except ValidationError as error:
            components.show_errors(error.messages)
            return

        components.set_flash_message("Transaction updated successfully.", result["alerts"])
        st.rerun()


def show_delete_section():
    st.subheader("Delete transactions")

    transactions = transaction_service.get_transactions(newest_first=True)
    if len(transactions) == 0:
        st.info("There are no transactions to delete yet.")
        return

    transactions_by_id, labels_by_id = index_transactions(transactions)

    delete_mode = st.radio(
        "Choose deletion method",
        ["Single Transaction", "Checklist (Bulk Delete)", "Delete All Transactions"],
        horizontal=True,
        key="delete_mode_radio",
    )

    if delete_mode == "Checklist (Bulk Delete)":
        st.caption("Select multiple transactions to delete at once.")

        selected_ids = st.multiselect(
            "Select transactions to delete",
            options=list(labels_by_id.keys()),
            format_func=labels_by_id.get,
            key="bulk_delete_multiselect",
        )

        if len(selected_ids) > 0:
            st.write(f"**{len(selected_ids)}** transaction(s) selected:")
            selected_items = [transactions_by_id[item_id] for item_id in selected_ids]
            components.show_transactions_table(selected_items)

            pending_bulk = st.session_state.get("pending_bulk_delete", False)

            if not pending_bulk:
                if st.button(f"Delete Selected ({len(selected_ids)})", type="primary"):
                    st.session_state["pending_bulk_delete"] = True
                    st.rerun()
            else:
                st.warning(f"Are you sure you want to permanently delete these {len(selected_ids)} transaction(s)? This cannot be undone.")
                col_yes, col_no = st.columns(2)
                if col_yes.button("Yes, delete selected", type="primary", key="confirm_bulk_del"):
                    try:
                        result = transaction_service.delete_transactions_bulk(selected_ids)
                    except ValidationError as error:
                        components.show_errors(error.messages)
                        return

                    st.session_state["pending_bulk_delete"] = False
                    components.set_flash_message(f"Successfully deleted {result['deleted_count']} transaction(s).", result["alerts"])
                    st.rerun()

                if col_no.button("Cancel", key="cancel_bulk_del"):
                    st.session_state["pending_bulk_delete"] = False
                    st.rerun()
        else:
            st.info("Check one or more transactions above to enable bulk deletion.")

    elif delete_mode == "Single Transaction":
        selected_id = st.selectbox(
            "Choose the transaction to delete",
            list(labels_by_id.keys()),
            format_func=labels_by_id.get,
        )
        components.show_transactions_table([transactions_by_id[selected_id]])

        pending_id = st.session_state.get("pending_delete_id")
        if pending_id is not None and pending_id != selected_id:
            del st.session_state["pending_delete_id"]
            pending_id = None

        if st.button("Delete this transaction"):
            st.session_state["pending_delete_id"] = selected_id
            pending_id = selected_id

        if pending_id == selected_id:
            st.warning("Are you sure you want to permanently delete this transaction? This cannot be undone.")
            confirm_column, cancel_column = st.columns(2)

            if confirm_column.button("Yes, delete it", type="primary"):
                try:
                    result = transaction_service.delete_transaction(selected_id)
                except ValidationError as error:
                    components.show_errors(error.messages)
                    return

                del st.session_state["pending_delete_id"]
                components.set_flash_message("Transaction deleted.", result["alerts"])
                st.rerun()

            if cancel_column.button("Cancel"):
                del st.session_state["pending_delete_id"]
                st.rerun()

    else:

        st.error(f"DANGER ZONE: This will permanently delete all {len(transactions)} transaction(s) in the system.")
        pending_all = st.session_state.get("pending_delete_all", False)

        if not pending_all:
            if st.button("Delete ALL Transactions", type="primary"):
                st.session_state["pending_delete_all"] = True
                st.rerun()
        else:
            st.warning("CONFIRMATION REQUIRED: Are you sure you want to wipe ALL transactions? This action CANNOT be reversed.")
            c_yes, c_no = st.columns(2)
            if c_yes.button("Yes, wipe everything", type="primary", key="confirm_wipe_all"):
                result = transaction_service.delete_all_transactions()
                st.session_state["pending_delete_all"] = False
                components.set_flash_message(f"All {result['deleted_count']} transaction(s) were successfully deleted.", result["alerts"])
                st.rerun()

            if c_no.button("Cancel", key="cancel_wipe_all"):
                st.session_state["pending_delete_all"] = False
                st.rerun()


components.show_page_header(
    "Transactions",
    "Add, view, edit and delete your income and expenses",
)
components.show_flash_message()

try:
    categories = category_service.get_categories()


    category_ids = {}
    for category in categories:
        category_ids[category["name"]] = category["id"]


    section = st.radio(
        "What would you like to do?",
        ["Add Transaction", "All Transactions", "Edit Transaction", "Delete Transaction"],
        horizontal=True,
        key="transactions_section",
    )


    if section != "Delete Transaction" and "pending_delete_id" in st.session_state:
        del st.session_state["pending_delete_id"]

    if section == "Add Transaction":
        show_add_section(category_ids)
    elif section == "All Transactions":
        show_list_section()
    elif section == "Edit Transaction":
        show_edit_section(category_ids)
    else:
        show_delete_section()

except DatabaseError as error:

    components.show_database_error(error)
