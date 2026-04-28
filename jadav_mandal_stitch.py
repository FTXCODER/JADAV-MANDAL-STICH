import streamlit as st
import pandas as pd
import gspread
import json
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import pytz

# ---------------- PAGE CONFIG ---------------- #
st.set_page_config(page_title="Task Panel", layout="wide")

# ---------------- AUTH ---------------- #
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

# Load credentials from Streamlit Secrets
creds_dict = json.loads(st.secrets["GOOGLE_CREDENTIALS"])

creds = ServiceAccountCredentials.from_json_keyfile_dict(
    creds_dict, scope
)

client = gspread.authorize(creds)

# ---------------- SHEETS ---------------- #
SPREADSHEET_NAME = "YOUR FILE NAME"   # 👈 change this

dashboard_sheet = client.open(SPREADSHEET_NAME).worksheet("DOER DASHBOARD")
update_sheet = client.open(SPREADSHEET_NAME).worksheet("TASK UPDATE")

# ---------------- LOAD DATA ---------------- #
data = pd.DataFrame(dashboard_sheet.get_all_records())

# Apply FILTER logic
filtered = data[
    (data["E"] != "") &
    (data["C"] == "Jadav Mandal")
]

# Select required columns
filtered = filtered[["A", "H", "I", "J", "K", "L"]]

# ---------------- LOAD SUBMITTED DATA ---------------- #
update_data = pd.DataFrame(update_sheet.get_all_records())

submitted_ids = set()
if not update_data.empty:
    # Column B contains original Column A values
    submitted_ids = set(update_data.iloc[:, 1].astype(str))

# ---------------- SESSION STATE ---------------- #
if "submitted_local" not in st.session_state:
    st.session_state.submitted_local = set()

# ---------------- UI ---------------- #
st.title("📋 Jadav Mandal Task Panel")

# Styling for green button
st.markdown("""
<style>
.green-btn button {
    background-color: #28a745 !important;
    color: white !important;
}
</style>
""", unsafe_allow_html=True)

# ---------------- DISPLAY TABLE ---------------- #
for index, row in filtered.iterrows():

    task_id = str(row["A"])

    col1, col2, col3, col4, col5, col6, col7 = st.columns(7)

    col1.write(row["A"])
    col2.write(row["H"])
    col3.write(row["I"])
    col4.write(row["J"])
    col5.write(row["K"])
    col6.write(row["L"])

    already_done = (
        task_id in submitted_ids or
        task_id in st.session_state.submitted_local
    )

    # ---------------- GREEN BUTTON ---------------- #
    if already_done:
        with col7:
            st.markdown('<div class="green-btn">', unsafe_allow_html=True)
            st.button("SUBMITTED", key=f"done_{index}", disabled=True)
            st.markdown('</div>', unsafe_allow_html=True)

    # ---------------- SUBMIT BUTTON ---------------- #
    else:
        if col7.button("SUBMIT", key=f"submit_{index}"):

            tz = pytz.timezone('Asia/Kolkata')
            timestamp = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")

            update_sheet.append_row([
                timestamp,      # Column A
                row["A"],       # Column B
                row["L"],       # Column C
                "YES"           # Column D
            ])

            # Update local state (instant UI update)
            st.session_state.submitted_local.add(task_id)

            st.success(f"✅ Submitted for Task {row['A']}")

            st.rerun()
