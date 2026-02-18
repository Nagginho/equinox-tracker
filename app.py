import streamlit as st
import datetime
import json
import gspread
import pandas as pd
import altair as alt  # <--- NEW: Added for custom axis control
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
    st.write("Log your metrics below.")
    
    # 1. Date Input
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
            # Note: Ensure this URL points to your specific "Entry" sheet
            sheet = client.open_by_url("https://docs.google.com/spreadsheets/d/1YhYGFyAUNKByZ_fN1jDs3G1raBeB8MXko61DE3NtUTI").sheet1
            
            def tick_to_num(val): return 1 if val else 0
            w_val = weight if weight is not None else ""
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
                0, 
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
    st.write("Visualising your progress by Week, Month, and Year.")
    
    if st.checkbox("Load Historical Data"):
        try:
            client = get_connection()
            sh = client.open_by_url("https://docs.google.com/spreadsheets/d/1tZ48YYIPMz9algjc4blxoHcxaiwnVIli_bFZNZrVXfU")
            
            all_data_frames = []
            
            # 1. LOOP THROUGH ALL SHEETS
            worksheets = sh.worksheets()
            progress_text = st.empty()
            
            for ws in worksheets:
                # Attempt to extract year from sheet name (e.g., "2024")
                sheet_title = ws.title.strip()
                year_val = None
                
                if sheet_title.isdigit() and len(sheet_title) == 4:
                    year_val = int(sheet_title)
                else:
                    continue

                progress_text.text(f"Processing Year: {year_val}...")
                
                raw_data = ws.get_all_values()
                if len(raw_data) < 3:
                    continue
                
                # 2. HEADERS & DATA
                header_row = raw_data[1]
                data_rows = raw_data[2:]
                
                clean_headers = []
                seen_count = {}
                for h in header_row:
                    h = str(h).strip()
                    if not h: h = "Unknown"
                    if h in seen_count:
                        seen_count[h] += 1
                        h = f"{h}_{seen_count[h]}"
                    else:
                        seen_count[h] = 1
                    clean_headers.append(h)
                
                df_sheet = pd.DataFrame(data_rows, columns=clean_headers)
                
                # 3. CONVERT WEEK COLUMN TO DATE
                first_col_name = df_sheet.columns[0]
                df_sheet[first_col_name] = pd.to_numeric(df_sheet[first_col_name], errors='coerce')
                df_sheet = df_sheet.dropna(subset=[first_col_name])
                
                def get_date_from_week(week_num, year):
                    try:
                        return datetime.date.fromisocalendar(year, int(week_num), 1)
                    except:
                        return None

                df_sheet['Date'] = df_sheet[first_col_name].apply(lambda x: get_date_from_week(x, year_val))
                all_data_frames.append(df_sheet)
            
            progress_text.empty()
            
            if not all_data_frames:
                st.warning("No valid yearly data found (Tabs must be named '2023', '2024', etc).")
            else:
                # 4. COMBINE & PREPARE
                df = pd.concat(all_data_frames, ignore_index=True)
                df['Date'] = pd.to_datetime(df['Date'])
                df = df.dropna(subset=['Date']).sort_values('Date')
                
                for col in df.columns:
                    if col != 'Date':
                        df[col] = pd.to_numeric(df[col], errors='coerce')

                # --- FILTERS ---
                st.divider()
                st.subheader("⚙️ View Settings")
                
                time_view = st.radio(
                    "Group Data By:", 
                    ["Original (Weekly)", "Monthly Average", "Yearly Average"], 
                    horizontal=True
                )
                
                # Create plotting dataframe
                plot_df = df.set_index('Date').copy()
                
                if "Monthly" in time_view:
                    plot_df = plot_df.resample('ME').mean()
                elif "Yearly" in time_view:
                    plot_df = plot_df.resample('YE').mean()

                # --- VISUALIZATIONS ---
                
                # A. Weight Chart (CUSTOM AXIS [75, 90])
                weight_col = next((c for c in df.columns if 'weight' in c.lower()), None)
                if weight_col:
                    st.subheader("⚖️ Weight Trends")
                    
                    # Prepare data for Altair (Reset index to get Date as a column)
                    chart_data = plot_df[[weight_col]].dropna().reset_index()
                    
                    if not chart_data.empty:
                        # Define the custom chart
                        chart = alt.Chart(chart_data).mark_line(point=True).encode(
                            x=alt.X('Date', title='Date'),
                            y=alt.Y(weight_col, 
                                    scale=alt.Scale(domain=[75, 90]), # <--- FIXED DOMAIN
                                    title='Weight (kg)'),
                            tooltip=['Date', weight_col]
                        ).interactive()
                        
                        st.altair_chart(chart, use_container_width=True)
                    else:
                        st.info("No weight data available to plot.")
                
                # B. Habits Chart
                st.subheader("✅ Habit Consistency")
                
                habit_keywords = ['Veggie', 'Vitamin', 'Gym', 'Drink', 'Alcohol', 
                                'Water', 'Protein', 'Knee', 'Cycle', 'Read', 'Golf', 'Run']
                
                found_habits = []
                for kw in habit_keywords:
                    for col in df.columns:
                        if kw.lower() in col.lower() and col != weight_col and col != 'Date':
                            found_habits.append(col)
                found_habits = list(set(found_habits))
                
                if found_habits:
                    selected = st.multiselect("Select Habits:", found_habits, default=found_habits[:3])
                    if selected:
                        st.line_chart(plot_df[selected])
                else:
                    st.info("No habit columns found.")

        except Exception as e:
            st.warning("Could not load historical data.")
            st.error(f"Detailed Error: {e}")
