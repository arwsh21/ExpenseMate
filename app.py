import streamlit as st

from data import database
from exceptions import DatabaseError
from ui import components


st.set_page_config(
    page_title=components.APP_NAME,
    page_icon="💰",
    layout="wide",
)

components.apply_branding()


try:
    database.initialize_database()
except DatabaseError as error:
    components.show_database_error(error)
    st.stop()


pages = [
    st.Page("pages/0_Dashboard.py", title="Dashboard", icon="🏠", default=True),
    st.Page("pages/1_Transactions.py", title="Transactions", icon="💳"),
    st.Page("pages/2_Categories.py", title="Categories", icon="🏷️"),
    st.Page("pages/3_Budgets.py", title="Budgets", icon="🎯"),
    st.Page("pages/4_Analytics.py", title="Analytics", icon="📊"),
    st.Page("pages/5_Import_Export.py", title="Import / Export", icon="📁"),
]


current_page = st.navigation(pages)

components.show_sidebar_brand()


current_page.run()
