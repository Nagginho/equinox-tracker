import json
import gspread
from google.oauth2.service_account import Credentials

# ... [Keep all the previous dashboard code for Date, Weight, Veggie Meals, and Habit tick boxes] ...

# 5. Submit Button and Google Sheets Connection
if st.button("Save Daily Entry"):
    try:
        # Load the secure key from Streamlit's vault
        key_dict = json.loads(st.secrets["google_key"])
        creds = Credentials.from_service_account_info(
            key_dict, 
            scopes=["https://www.googleapis.com/auth/spreadsheets"]
        )
        client = gspread.authorize(creds)
        
        # Connect to your specific spreadsheet (Replace with your actual link!)
        sheet = client.open_by_url("PASTE_YOUR_GOOGLE_SHEET_LINK_HERE").sheet1
        
        # Turn tick boxes into 1s and 0s
        def tick_to_number(tick_value):
            return 1 if tick_value else 0
            
        # Handle the optional weight
        weight_entry = weight if weight is not None else ""
        
        # Package the day's data into a single row
        new_row = [
            str(entry_date),              # Date
            weight_entry,                 # Weight (or blank)
            veggie_meals,                 # Veggie Meals (0 to 3)
            tick_to_number(vitamins),
            tick_to_number(no_drink),
            tick_to_number(water),
            tick_to_number(protein),
            tick_to_number(cycle),
            tick_to_number(knee_exercise),
            tick_to_number(gym),
            tick_to_number(golf),
            tick_to_number(read)
        ]
        
        # Send it to Google Sheets!
        sheet.append_row(new_row)
        st.success("Entry saved successfully! Great job today.")
        
    except Exception as e:
        st.error("Oops! Something went wrong connecting to the sheet. Please check your link and secrets.")
