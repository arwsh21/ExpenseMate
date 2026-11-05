import pandas as pd
import streamlit as st

from services import money


APP_NAME = "ExpenseMate"
APP_TAGLINE = "Your personal income and expense tracker"


BRANDING_CSS = """
<style>
.bbb-banner {
    background: linear-gradient(135deg, #0F766E 0%, #4338CA 100%);
    padding: 1.4rem 1.7rem;
    border-radius: 14px;
    margin-bottom: 1.3rem;
}
.bbb-banner h1 {
    color: #FFFFFF;
    font-size: 1.9rem;
    font-weight: 800;
    letter-spacing: 0.4px;
    line-height: 1.2;
    margin: 0;
    padding: 0;
}
.bbb-banner p {
    color: #D5F5F0;
    font-size: 1rem;
    margin: 0.4rem 0 0 0;
}
.bbb-eyebrow {
    color: #99F6E4;
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 1.6px;
    margin-bottom: 0.3rem;
}
.bbb-brand {
    border-left: 4px solid #0F766E;
    padding: 0.2rem 0 0.2rem 0.75rem;
    margin-bottom: 0.5rem;
}
.bbb-brand-name {
    color: #0F766E;
    font-size: 1.05rem;
    font-weight: 800;
    letter-spacing: 0.8px;
}
.bbb-brand-tag {
    color: #64748B;
    font-size: 0.8rem;
}
</style>
"""


def apply_branding():
    st.markdown(BRANDING_CSS, unsafe_allow_html=True)


def show_sidebar_brand():
    html = (
        '<div class="bbb-brand">'
        '<div class="bbb-brand-name">' + APP_NAME + '</div>'
        '<div class="bbb-brand-tag">' + APP_TAGLINE + '</div>'
        '</div>'
    )
    st.sidebar.markdown(html, unsafe_allow_html=True)


def show_page_header(title, subtitle):
    eyebrow = ""
    if title != APP_NAME:
        eyebrow = '<div class="bbb-eyebrow">' + APP_NAME + '</div>'

    html = (
        '<div class="bbb-banner">'
        + eyebrow
        + '<h1>' + title + '</h1>'
        + '<p>' + subtitle + '</p>'
        '</div>'
    )
    st.markdown(html, unsafe_allow_html=True)


def show_success(message):
    st.success(message)


def show_errors(messages):
    for message in messages:
        st.error(message)


def show_database_error(error):
    st.error(str(error))


def show_alerts(alerts):
    for alert in alerts:
        st.warning(alert)


def set_flash_message(message, alerts):
    st.session_state["flash_message"] = message
    st.session_state["flash_alerts"] = alerts


def show_flash_message():
    if "flash_message" in st.session_state:
        message = st.session_state["flash_message"]
        alerts = st.session_state["flash_alerts"]


        del st.session_state["flash_message"]
        del st.session_state["flash_alerts"]

        show_success(message)
        show_alerts(alerts)


def transactions_to_dataframe(transactions):
    rows = []
    for transaction in transactions:
        rows.append({
            "Date": transaction["date"],
            "Category": transaction["category_name"],
            "Type": transaction["type"].capitalize(),
            "Amount": transaction["amount_minor"] / 100,
        })
    return pd.DataFrame(rows, columns=["Date", "Category", "Type", "Amount"])


def show_transactions_table(transactions):
    if len(transactions) == 0:
        st.info("No transactions to show yet.")
        return

    table = transactions_to_dataframe(transactions)


    st.dataframe(
        table,
        hide_index=True,
        column_config={"Amount": st.column_config.NumberColumn("Amount", format="%.2f")},
    )


def budget_status_to_dataframe(status_list):
    rows = []
    for status in status_list:
        if status["over_budget"]:
            state = "Over budget"
        else:
            state = "Within budget"

        rows.append({
            "Category": status["category_name"],
            "Budget": status["limit_minor"] / 100,
            "Spent": status["spent_minor"] / 100,
            "Remaining": status["remaining_minor"] / 100,
            "Used": status["percent_used"],
            "Status": state,
        })
    return pd.DataFrame(rows, columns=["Category", "Budget", "Spent", "Remaining", "Used", "Status"])


def show_budget_table(status_list):
    table = budget_status_to_dataframe(status_list)

    st.dataframe(
        table,
        hide_index=True,
        column_config={
            "Budget": st.column_config.NumberColumn("Budget", format="%.2f"),
            "Spent": st.column_config.NumberColumn("Spent", format="%.2f"),
            "Remaining": st.column_config.NumberColumn("Remaining", format="%.2f"),
            "Used": st.column_config.NumberColumn("Used", format="%d%%"),
        },
    )


def show_budget_progress(status_list):
    for status in status_list:
        used = status["percent_used"]
        bar_value = used
        if bar_value > 100:
            bar_value = 100

        if status["over_budget"]:
            state = "  -  OVER BUDGET"
        else:
            state = ""

        label = (
            status["category_name"] + ": "
            + money.format_amount(status["spent_minor"]) + " of "
            + money.format_amount(status["limit_minor"]) + " (" + str(used) + "%)" + state
        )
        st.progress(bar_value, text=label)


def describe_transaction(transaction):
    return (
        "#" + str(transaction["id"]) + "  |  " + transaction["date"] + "  |  "
        + transaction["type"].capitalize() + "  |  " + transaction["category_name"]
        + "  |  " + money.format_amount(transaction["amount_minor"])
    )
