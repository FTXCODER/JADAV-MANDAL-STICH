import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import pytz

# ---------------- PAGE ---------------- #
st.set_page_config(page_title="Task Panel", layout="wide")

# ---------------- AUTH ---------------- #
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

# ✅ Directly use secrets (NO json.loads)
creds = ServiceAccountCredentials.from_json_keyfile_dict(
    st.secrets["GOOGLE_CREDENTIALS"], scope
)

client = gspread.authorize(creds)

# ---------------- SHEETS ---------------- #
SPREADSHEET_NAME = "YOUR FILE NAME"   # 👈 change this

dashboard_sheet = client.open(SPREADSHEET_NAME).worksheet("DOER DASHBOARD")
update_sheet = client.open(SPREADSHEET_NAME).worksheet("TASK UPDATE")

# ---------------- LOAD DATA ---------------- #
raw_data = dashboard_sheet.get_all_values()

# Fix duplicate headers
headers = raw_data[0]
unique_headers = []
seen = {}

for col in headers:
    if col in seen:
        seen[col] += 1
        unique_headers.append(f"{col}_{seen[col]}")
    else:
        seen[col] = 0
        unique_headers.append(col)

data = pd.DataFrame(raw_data[1:], columns=unique_headers)

# ---------------- FILTER ---------------- #
filtered = data[
    (data["PLANNED"] != "") &
    (data["DOER"] == "Jadav Mandal")
]

# ---------------- SELECT COLUMNS ---------------- #
filtered = filtered[
    [
        "JOB SERIES",
        "BUYER",
        "ITEM CODE",
        "CUT QUANTITY",
        "STEPKEY",
        "FULL UPDATE LINK"
    ]
]

# ---------------- LOAD SUBMITTED ---------------- #
update_data = pd.DataFrame(update_sheet.get_all_records())

submitted_ids = set()
if not update_data.empty:
    submitted_ids = set(update_data.iloc[:, 1].astype(str))

# ---------------- SESSION ---------------- #
if "submitted_local" not in st.session_state:
    st.session_state.submitted_local = set()

# ---------------- UI ---------------- #
st.title("📋 Jadav Mandal Task Panel")

# Green button style
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

    # Use unique ID
    task_id = str(row["JOB SERIES"]) + "_" + str(row["STEPKEY"])

    col1, col2, col3, col4, col5, col6, col7 = st.columns(7)

    col1.write(row["JOB SERIES"])
    col2.write(row["BUYER"])
    col3.write(row["ITEM CODE"])
    col4.write(row["CUT QUANTITY"])
    col5.write(row["STEPKEY"])

    # clickable link
    col6.markdown(f"[Open Link]({row['FULL UPDATE LINK']})")

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

    # ---------------- SUBMIT ---------------- #
    else:
        if col7.button("SUBMIT", key=f"submit_{index}"):

            tz = pytz.timezone('Asia/Kolkata')
            timestamp = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")

            update_sheet.append_row([
                timestamp,
                row["JOB SERIES"],
                row["FULL UPDATE LINK"],
                "YES"
            ])

            st.session_state.submitted_local.add(task_id)

            st.success(f"✅ Submitted for {row['JOB SERIES']}")

            st.rerun()
