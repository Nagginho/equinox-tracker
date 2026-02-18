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
    
    # 1. FIX: Added format="DD/MM/YYYY" for British display
    entry_date = st.date_input("Date", datetime.date.today(), format="DD/MM/YYYY")
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
            sheet = client.open_by_url("https://docs.google.com/spreadsheets/d/1YhYGFyAUNKByZ_fN1jDs3G1raBeB8MXko61DE3NtUTI").sheet1
            
            def tick_to_num(val): return 1 if val else 0
            w_val = weight if weight is not None else ""
            
            # 2. FIX: Convert date to British string (DD/MM/YYYY) before saving
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
    
    if st.checkbox("Load Historical Data"):
        try:
            client = get_connection()
            hist_sheet = client.open_by_url("https://docs.google.com/spreadsheets/d/1tZ48YYIPMz9algjc4blxoHcxaiwnVIli_bFZNZrVXfU").sheet1
            
            raw_data = hist_sheet.get_all_values()
            
            if not raw_data:
                st.warning("Sheet appears to be empty.")
            else:
                # --- Header Cleaning ---
                original_headers = raw_data[0]
                rows = raw_data[1:]

                final_headers = []
                seen_count = {}
                for i, h in enumerate(original_headers):
                    h = str(h).strip()
                    if not h: h = f"Column_{i}"
                    if h in seen_count:
                        seen_count[h] += 1
                        h = f"{h}_{seen_count[h]}"
                    else:
                        seen_count[h] = 1
                    final_headers.append(h)

                df = pd.DataFrame(rows, columns=final_headers)

                # --- Debug Expander (In case issues persist) ---
                with st.expander("See Raw Data Columns"):
                    st.write(df.columns.tolist())

                # --- 3. FIX: Robust Weight Finder (Case Insensitive) ---
                weight_col = None
                for col in df.columns:
                    if 'weight' in col.lower(): # Checks for 'Weight', 'weight', 'Weight (kg)'
                        weight_col = col
                        break
                
                # Plot Weight
                if weight_col:
                    df[weight_col] = pd.to_numeric(df[weight_col], errors='coerce')
                    st.subheader("Body Weight")
                    st.line_chart(df[[weight_col]].dropna())
                else:
                    st.warning("Could not automatically find a 'Weight' column.")

                # --- 4. FIX: Visualize ALL Categories ---
                st.subheader("Habit Consistency")
                
                # List of keywords to look for in columns matching your input tab
                habit_keywords = [
                    'veggie', 'vitamin', 'gym', 'drink', 'alcohol', 
                    'water', 'protein', 'knee', 'cycle', 'read', 'golf', 'run'
                ]
                
                found_habits = []
                for keyword in habit_keywords:
                    for col in df.columns:
                        # Case insensitive check matching keyword to column name
                        if keyword in col.lower() and col != weight_col:
                            # Convert to numeric to ensure it plots
                            df[col] = pd.to_numeric(df[col], errors='coerce')
                            found_habits.append(col)
                
                # Remove duplicates
                found_habits = list(set(found_habits))

                if found_habits:
                    # Let user select which habits to view to avoid overcrowding
                    selected_habits = st.multiselect(
                        "Select habits to visualize:", 
                        found_habits, 
                        default=found_habits
                    )
                    if selected_habits:
                        st.line_chart(df[selected_habits])
                else:
                    st.info("No habit columns found to plot.")
            
        except Exception as e:
            st.warning("Could not load historical data.")
            st.error(f"Detailed Error: {e}")
        
