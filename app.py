import streamlit as st
import datetime

# App Title and Description
st.title("Equinox: Daily Tracker")
st.write("Log your daily metrics below. It takes less than 10 seconds.")

# 1. Date Input (Defaults to today)
entry_date = st.date_input("Date", datetime.date.today())

st.divider()

# 2. Optional Weight Input
st.subheader("Body & Diet")
# value=None makes the box empty by default, so it is totally optional
weight = st.number_input("Weight (kg) - Optional", value=None, placeholder="e.g. 81.6")

# 3. Veggie Meals (0 to 3 limit)
veggie_meals = st.radio("Vegetarian Meals Today", options=[0, 1, 2, 3], horizontal=True)

st.divider()

# 4. Daily Habits (Simple Tick Boxes)
st.subheader("Daily Habits")

# Splitting into two columns to make the app look neat on a screen
col1, col2 = st.columns(2)

with col1:
    vitamins = st.checkbox("Vitamins")
    no_drink = st.checkbox("No Alcohol")
    water = st.checkbox("Water (6+ Glasses)")
    protein = st.checkbox("Hit Protein Target")

with col2:
    gym = st.checkbox("Gym")
    knee_exercise = st.checkbox("Exercise Knee")
    cycle = st.checkbox("Cycle")
    golf = st.checkbox("Golf")
    read = st.checkbox("Education / Read")

st.divider()

# 5. Submit Button
if st.button("Save Daily Entry"):
    # The code to send this to your Google Sheet will go here next!
    st.success("Entry saved successfully! Great job today.")
