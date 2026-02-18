import streamlit as st
import datetime
import json
import gspread
import pandas as pd
from google.oauth2.service_account import Credentials

# App Title
st.set_page_config(page_title="Equinox", page_icon="📈")
st.title("Equinox: Life Dashboard")

# ---------------------------------------------------------
# AUTHENTICATION & CONNECTION FUNCTION
# ---------------------------------------------------------
# We cache this so the app doesn't reload the database every time you click a button
@st.cache_resource
def get_connection():
    key_dict = json.loads(st.secrets["google_key"])
    creds = Credentials.from_service_account_info(
        key_dict, 
        scopes=["https://www.googleapis.com/auth/spreadsheets"]
    )
    client = gspread.authorize(creds)
    return client

# ---------------------------------------------------------
# TABS
# ---------------------------------------------------------
tab_log, tab_dash = st.tabs(["📝 Log Entry", "📊 Dashboard"])

# ---------------------------------------------------------
# TAB 1: LOG ENTRY (Daily Input)
# ---------------------------------------------------------
with tab_log:
    st.header("Daily Log")
    entry_date = st.date_input("Date", datetime.date.today())
    st.divider()

    st.subheader("Body & Diet")
    weight = st.number_input("Weight (kg) - Optional", value=None, placeholder="e.g. 81.6")
    veggie_meals = st.radio("Vegetarian Meals Today", options=[0, 1, 2, 3], horizontal=True)
    st.divider()

    st.subheader("Habits")
    col1, col2 = st.columns(2)
    with col1:
        vitamins = st.checkbox("Vitamins")
        no_drink = st.checkbox("No Alcohol")
        water = st.checkbox("Water (6+)")
        protein = st.checkbox("Protein Target")
    with col2:
        gym = st.checkbox("Gym")
        knee_exercise = st.checkbox("Exercise Knee")
        cycle = st.checkbox("Cycle")
        read = st.checkbox("Read / Edu")

    if st.button("Save Daily Entry"):
        try:
            client = get_connection()
            # PASTE YOUR NEW DAILY SHEET LINK HERE
            sheet = client.open_by_url("https://docs.google.com/spreadsheets/d/1YhYGFyAUNKByZ_fN1jDs3G1raBeB8MXko61DE3NtUTI/edit?usp=drivesdk").sheet1
            
            def tick_to_num(val): return 1 if val else 0
            w_val = weight if weight is not None else ""
            
            row = [str(entry_date), w_val, veggie_meals, tick_to_num(vitamins), 
                   tick_to_num(no_drink), tick_to_num(water), tick_to_num(protein), 
                   tick_to_num(cycle), tick_to_num(knee_exercise), tick_to_num(gym), 
                   0, tick_to_num(read)] # 0 placeholder for Golf/Other if needed
            
            sheet.append_row(row)
            st.success("Saved!")
        except Exception as e:
            st.error(f"Error: {e}")

# ---------------------------------------------------------
# TAB 2: DASHBOARD (Historical Insights)
# ---------------------------------------------------------
with tab_dash:
    st.header("Historical Trends")
    
    # Load Data Button (Save data by not loading automatically)
    if st.checkbox("Load Historical Data"):
        try:
            client = get_connection()
            # PASTE YOUR OLD HISTORICAL SHEET LINK HERE
            hist_sheet = client.open_by_url("https://docs.google.com/spreadsheets/d/1tZ48YYIPMz9algjc4blxoHcxaiwnVIli_bFZNZrVXfU/edit?usp=drivesdk").sheet1
            
            # 1. Get all data
            data = hist_sheet.get_all_records()
            df = pd.DataFrame(data)

            # 2. CLEANING: The magic step
            # We filter out rows where 'Week' is not a number (removes '2025', 'Average' etc)
            # This handles the structure seen in your PDF
            if 'Week' in df.columns:
                df = df[pd.to_numeric(df['Week'], errors='coerce').notnull()]
            
            # Convert Weight to numbers, treating "N/A" as NaN (empty)
            if 'Weight' in df.columns:
                df['Weight'] = pd.to_numeric(df['Weight'], errors='coerce')

            # 3. VISUALISATION
            st.subheader("Weight Trend (All Time)")
            # Simple line chart of the Weight column
            st.line_chart(df[['Weight']].dropna())

            # 4. Habit Consistency
            st.subheader("Habit Consistency (Weekly Counts)")
            # Let's try to plot 'Veggie' or 'Vitamins' if they exist
            habits_to_plot = []
            if 'Veggie' in df.columns: habits_to_plot.append('Veggie')
            if 'Vitamins' in df.columns: habits_to_plot.append('Vitamins')
            if 'Gym' in df.columns: habits_to_plot.append('Gym')
            
            if habits_to_plot:
                st.bar_chart(df[habits_to_plot])
            
        except Exception as e:
            st.warning("Could not load data. Check your sheet link!")
            st.error(e)
