import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import pytz

# ---------------- AUTH ---------------- #
scope = ["https://spreadsheets.google.com/feeds",
         "https://www.googleapis.com/auth/drive"]

creds = ServiceAccountCredentials.from_json_keyfile_name(
    "credentials.json", scope
)
client = gspread.authorize(creds)

# ---------------- SHEETS ---------------- #
SPREADSHEET_NAME = "YOUR FILE NAME"

dashboard_sheet = client.open(SPREADSHEET_NAME).worksheet("DOER DASHBOARD")
update_sheet = client.open(SPREADSHEET_NAME).worksheet("TASK UPDATE")

# ---------------- LOAD DATA ---------------- #
data = pd.DataFrame(dashboard_sheet.get_all_records())

filtered = data[
    (data["E"] != "") &
    (data["C"] == "Jadav Mandal")
]

filtered = filtered[["A", "H", "I", "J", "K", "L"]]

# ---------------- LOAD ALREADY SUBMITTED ---------------- #
update_data = pd.DataFrame(update_sheet.get_all_records())

# Track submitted IDs (Column B = A value)
submitted_ids = set()
if not update_data.empty:
    submitted_ids = set(update_data.iloc[:, 1].astype(str))  # Column B

# ---------------- SESSION STATE ---------------- #
if "submitted_local" not in st.session_state:
    st.session_state.submitted_local = set()

st.title("Jadav Mandal Task Panel")

# ---------------- STYLE ---------------- #
st.markdown("""
<style>
.green-btn button {
    background-color: #28a745 !important;
    color: white !important;
}
</style>
""", unsafe_allow_html=True)

# ---------------- DISPLAY ---------------- #
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

    if already_done:
        with col7:
            st.markdown('<div class="green-btn">', unsafe_allow_html=True)
            st.button("SUBMITTED", key=f"done_{index}", disabled=True)
            st.markdown('</div>', unsafe_allow_html=True)
    else:
        if col7.button("SUBMIT", key=index):

            tz = pytz.timezone('Asia/Kolkata')
            timestamp = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")

            update_sheet.append_row([
                timestamp,
                row["A"],
                row["L"],
                "YES"
            ])

            # Store locally so UI updates instantly
            st.session_state.submitted_local.add(task_id)

            st.success(f"Submitted for {row['A']}")
            st.rerun()
