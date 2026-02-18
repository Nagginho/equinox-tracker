import streamlit as st
import datetime
import json
import gspread
import pandas as pd
from google.oauth2.service_account import Credentials

# ---------------------------------------------------------
# CONFIGURATION & SETUP
# ---------------------------------------------------------
st.set_page_config(page_title="Equinox", page_icon="📈", layout="centered")
st.title("Equinox: Life Dashboard")

# ---------------------------------------------------------
# AUTHENTICATION FUNCTION
# ---------------------------------------------------------
@st.cache_resource
def get_connection():
    """Authenticates with Google Sheets using Streamlit Secrets."""
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
    st.write("Log your metrics below. It takes less than 10 seconds.")
    
    # 1. Date Input (British Format Display)
    entry_date = st.date_input("Date", datetime.date.today(), format="DD/MM/YYYY")
    st.divider()

    # --- INPUT FORM ---
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

    # --- SAVE ACTION ---
    if st.button("Save Daily Entry"):
        try:
            client = get_connection()
            # LINK TO ENTRY SHEET
            sheet = client.open_by_url("https://docs.google.com/spreadsheets/d/1YhYGFyAUNKByZ_fN1jDs3G1raBeB8MXko61DE3NtUTI").sheet1
            
            # Helper: Convert Checkbox to 1/0
            def tick_to_num(val): return 1 if val else 0
            
            # Helper: Handle weight
            w_val = weight if weight is not None else ""
            
            # Helper: Format date to British string (DD/MM/YYYY)
            formatted_date = entry_date.strftime("%d/%m/%Y")
            
            row = [
                formatted_date, 
                w_val, 
                veggie_meals, 
                tick_to_num(vitamins), 
                tick_to_num(no_drink), 
                tick_to_num(water), 
                tick_to_num(protein), 
                tick_to_num(cycle), 
                tick_to_num(knee_exercise), 
                tick_to_num(gym), 
                0, # Placeholder
                tick_to_num(read)
            ]
            
            sheet.append_row(row)
            st.success(f"Entry for {formatted_date} saved successfully!")
            
        except Exception as e:
            st.error(f"Error saving data: {e}")

# ---------------------------------------------------------
# TAB 2: DASHBOARD (Historical Insights)
# ---------------------------------------------------------
with tab_dash:
    st.header("Historical Trends")
    st.write("Visualising your progress over the years.")
    
    if st.checkbox("Load Historical Data"):
        try:
            client = get_connection()
            # LINK TO HISTORICAL DATA SHEET
            hist_sheet = client.open_by_url("https://docs.google.com/spreadsheets/d/1tZ48YYIPMz9algjc4blxoHcxaiwnVIli_bFZNZrVXfU").sheet1
            
            # 1. GET ALL DATA
            raw_data = hist_sheet.get_all_values()
            
            if len(raw_data) < 3:
                st.warning("Sheet appears to be empty or missing data rows.")
            else:
                # 2. PARSE HEADERS CORRECTLY
                # Row 0 = Categories -> Ignore
                # Row 1 = Actual Headers -> Use this
                header_row = raw_data[1] 
                data_rows = raw_data[2:]

                # 3. CLEAN HEADERS
                final_headers = []
                seen_count = {}

                for i, h in enumerate(header_row):
                    h = str(h).strip()
                    if not h: h = f"Column_{i}"
                    if h in seen_count:
                        seen_count[h] += 1
                        h = f"{h}_{seen_count[h]}"
                    else:
                        seen_count[h] = 1
                    final_headers.append(h)

                # 4. CREATE DATAFRAME
                df = pd.DataFrame(data_rows, columns=final_headers)

                # 5. CONVERT TO NUMBERS
                for col in df.columns:
                    if "Date" not in col and "Note" not in col:
                        df[col] = pd.to_numeric(df[col], errors='coerce')

                # 6. PLOT WEIGHT
                weight_col = None
                for col in df.columns:
                    if 'weight' in col.lower():
                        weight_col = col
                        break
                
                if weight_col:
                    st.subheader("Body Weight")
                    st.line_chart(df[[weight_col]].dropna())
                else:
                    st.warning("Could not automatically find a 'Weight' column.")

                # 7. PLOT HABITS
                st.subheader("Habit Consistency")
                
                search_terms = ['Veggie', 'Vitamin', 'Gym', 'Drink', 'Alcohol', 
                                'Water', 'Protein', 'Knee', 'Cycle', 'Read', 'Golf', 'Run']
                
                found_habits = []
                for term in search_terms:
                    for col in df.columns:
                        if term.lower() in col.lower() and col != weight_col:
                            found_habits.append(col)
                
                found_habits = list(set(found_habits))

                if found_habits:
                    options = st.multiselect("Select Habits:", found_habits, default=found_habits)
                    if options:
                        st.line_chart(df[options])
                else:
                    st.info("No habit columns found.")
            
        except Exception as e:
            st.warning("Could not load historical data.")
            st.error(f"Detailed Error: {e}")
