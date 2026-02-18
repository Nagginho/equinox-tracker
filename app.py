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
            # LINK TO NEW DATA ENTRY SHEET
            sheet = client.open_by_url("https://docs.google.com/spreadsheets/d/1YhYGFyAUNKByZ_fN1jDs3G1raBeB8MXko61DE3NtUTI").sheet1
            
            # Helper to convert True/False to 1/0
            def tick_to_num(val): return 1 if val else 0
            
            # Handle optional weight
            w_val = weight if weight is not None else ""
            
            # Prepare row data
            row = [
                str(entry_date), 
                w_val, 
                veggie_meals, 
                tick_to_num(vitamins), 
                tick_to_num(no_drink), 
                tick_to_num(water), 
                tick_to_num(protein), 
                tick_to_num(cycle), 
                tick_to_num(knee_exercise), 
                tick_to_num(gym), 
                0, # Placeholder for Golf if needed later
                tick_to_num(read)
            ]
            
            sheet.append_row(row)
            st.success("Entry saved successfully! Great job today.")
            
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
            
            # 1. Get ALL raw values (bypassing strict header checks)
            raw_data = hist_sheet.get_all_values()
            
            if not raw_data:
                st.warning("Sheet appears to be empty.")
            else:
                # 2. SEPARATE HEADERS & ROWS
                original_headers = raw_data[0]
                rows = raw_data[1:]

                # 3. CLEAN THE HEADERS (Fix duplicates/blanks)
                final_headers = []
                seen_count = {}

                for i, h in enumerate(original_headers):
                    h = str(h).strip()
                    if not h:
                        h = f"Column_{i}"
                    
                    if h in seen_count:
                        seen_count[h] += 1
                        h = f"{h}_{seen_count[h]}"
                    else:
                        seen_count[h] = 1
                    
                    final_headers.append(h)

                # 4. CREATE DATAFRAME
                df = pd.DataFrame(rows, columns=final_headers)

                # 5. DATA CLEANING & CONVERSION
                # Filter out summary rows (where 'Week' is not a number)
                if 'Week' in df.columns:
                    df = df[pd.to_numeric(df['Week'], errors='coerce').notnull()]
                
                # Intelligent Weight Column Finder
                target_weight_col = 'Weight'
                if target_weight_col not in df.columns:
                    # Look for any column containing "Weight"
                    for col in df.columns:
                        if 'Weight' in col:
                            target_weight_col = col
                            break
                
                # Plot Weight
                if target_weight_col in df.columns:
                    df[target_weight_col] = pd.to_numeric(df[target_weight_col], errors='coerce')
                    st.subheader("Weight Trend")
                    st.line_chart(df[[target_weight_col]].dropna())
                else:
                    st.warning("Could not automatically find a 'Weight' column.")

                # Plot Habits
                st.subheader("Habit Consistency")
                possible_habits = ['Veggie', 'Vitamins', 'Gym', 'No Drink', 'Golf', 'Read', 'Run', 'Tennis']
                found_habits = []

                for habit in possible_habits:
                    for col in df.columns:
                        if habit in col:
                            # force conversion to numeric so it plots
                            df[col] = pd.to_numeric(df[col], errors='coerce')
                            found_habits.append(col)
                
                found_habits = list(set(found_habits)) # Remove duplicates

                if found_habits:
                    st.bar_chart(df[found_habits])
                else:
                    st.info("No standard habit columns found to plot.")
            
        except Exception as e:
            st.warning("Could not load historical data.")
            st.error(f"Detailed Error: {e}")
