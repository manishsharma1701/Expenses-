import calendar
from datetime import date, timedelta
import re
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="TrackWise Pro",
    page_icon="⚡",
    layout="wide" if st.session_state.get("is_wide", False) else "centered",
)

CSV_FILE = "expenses.csv"

CATEGORIES = {
    "Home Travel": [
        "Train Fare",
        "Flight Fare",
        "Bus Fare",
        "Auto to Station/Airport",
        "Cab/Taxi",
        "Other Travel",
    ],
    "Office Commute": [
        "Auto Fare",
        "Metro Fare",
        "Cab/Rideshare",
        "Fuel/Petrol",
        "Bus Fare",
    ],
    "Chai & Snacks": ["Tea / Chai", "Coffee", "Evening Snacks", "Juice / Bakery"],
    "Meals & Dining": [
        "Lunch",
        "Dinner",
        "Breakfast",
        "Swiggy / Zomato Order",
        "Dining Out",
    ],
    "Groceries": [
        "Vegetables / Fruits",
        "Supermarket",
        "Milk / Daily Essentials",
    ],
    "Bills & Utilities": [
        "Mobile Recharge",
        "Wi-Fi / Broadband",
        "Electricity",
        "Subscriptions",
    ],
    "Shopping & Misc": [
        "Clothing / Shoes",
        "Electronics",
        "Personal Care",
        "Miscellaneous",
    ],
}

TRIP_TAGS = [
    "None",
    "Home Trip (Train/Flight)",
    "Office Commute",
    "Weekend Outing",
    "Vacation",
]

# -------------------------------------------------------------
# Storage Engine (Google Sheets if available, fallback to CSV)
# -------------------------------------------------------------


def get_connection():
  try:
    from streamlit_gsheets import GSheetsConnection

    conn = st.connection("gsheets", type=GSheetsConnection)
    return conn
  except Exception:
    return None


def load_data():
  conn = get_connection()
  if conn:
    try:
      df = conn.read(ttl="0s")
      if df is not None and not df.empty:
        if "ID" not in df.columns:
          df.insert(0, "ID", range(1, len(df) + 1))
        df["Date"] = pd.to_datetime(df["Date"]).dt.date
        return df
    except Exception:
      pass

  # Fallback to local CSV
  try:
    df = pd.read_csv(CSV_FILE)
    if "ID" not in df.columns:
      df.insert(0, "ID", range(1, len(df) + 1))
    if "Trip" not in df.columns:
      df["Trip"] = "None"
    df["Date"] = pd.to_datetime(df["Date"]).dt.date
    return df
  except (FileNotFoundError, pd.errors.EmptyDataError):
    return pd.DataFrame(
        columns=[
            "ID",
            "Date",
            "Category",
            "Sub-Category",
            "Amount",
            "Payment",
            "Trip",
            "Note",
        ]
    )


def save_data(df):
  conn = get_connection()
  if conn:
    try:
      conn.update(data=df)
      return
    except Exception:
      pass
  df.to_csv(CSV_FILE, index=False)


def append_entry(
    amount, category, sub_cat, payment, tx_date, trip="None", note=""
):
  df = load_data()
  next_id = int(df["ID"].max() + 1) if not df.empty and "ID" in df.columns else 1
  new_row = pd.DataFrame([{
      "ID": next_id,
      "Date": tx_date,
      "Category": category,
      "Sub-Category": sub_cat,
      "Amount": float(amount),
      "Payment": payment,
      "Trip": trip,
      "Note": note.strip(),
  }])
  df = pd.concat([df, new_row], ignore_index=True)
  save_data(df)


# -------------------------------------------------------------
# UI Header & Quick Log Bar
# -------------------------------------------------------------
st.title("⚡ TrackWise Pro")

# 1-Tap Quick Action Buttons
st.markdown("##### ⚡ Quick Log (1-Tap)")
q1, q2, q3, q4 = st.columns(4)
today = date.today()

with q1:
  if st.button("☕ Chai ₹15", use_container_width=True):
    append_entry(
        15, "Chai & Snacks", "Tea / Chai", "UPI", today, note="Quick Chai"
    )
    st.toast("Logged ₹15 for Chai!", icon="☕")
    st.rerun()

with q2:
  if st.button("☕ Coffee ₹25", use_container_width=True):
    append_entry(
        25, "Chai & Snacks", "Coffee", "UPI", today, note="Quick Coffee"
    )
    st.toast("Logged ₹25 for Coffee!", icon="☕")
    st.rerun()

with q3:
  if st.button("🛺 Auto ₹50", use_container_width=True):
    append_entry(
        50,
        "Office Commute",
        "Auto Fare",
        "UPI",
        today,
        trip="Office Commute",
        note="Quick Auto",
    )
    st.toast("Logged ₹50 for Auto Fare!", icon="🛺")
    st.rerun()

with q4:
  if st.button("🍱 Lunch ₹120", use_container_width=True):
    append_entry(
        120, "Meals & Dining", "Lunch", "UPI", today, note="Quick Lunch"
    )
    st.toast("Logged ₹120 for Lunch!", icon="🍱")
    st.rerun()

st.divider()

# -------------------------------------------------------------
# Metrics & Run-Rate Engine
# -------------------------------------------------------------
df = load_data()
yesterday = today - timedelta(days=1)

today_spend = 0.0
yesterday_spend = 0.0
month_spend = 0.0

if not df.empty:
  today_spend = df[df["Date"] == today]["Amount"].sum()
  yesterday_spend = df[df["Date"] == yesterday]["Amount"].sum()

  current_month_mask = (pd.to_datetime(df["Date"]).dt.year == today.year) & (
      pd.to_datetime(df["Date"]).dt.month == today.month
  )
  month_df = df[current_month_mask]
  month_spend = month_df["Amount"].sum()
else:
  month_df = pd.DataFrame()

# Days calculation for burn rate
days_in_month = calendar.monthrange(today.year, today.month)[1]
days_passed = today.day
daily_burn_rate = (month_spend / days_passed) if days_passed > 0 else 0.0
projected_month_end = daily_burn_rate * days_in_month

# Top Metric Cards
m1, m2, m3 = st.columns(3)
m1.metric("Today", f"₹{today_spend:,.0f}")
m2.metric("Yesterday", f"₹{yesterday_spend:,.0f}")
m3.metric(f"{today.strftime('%b')} Total", f"₹{month_spend:,.0f}")

# Monthly Burn Alert Banner
with st.expander("📊 Burn-Rate & Budget Projection", expanded=True):
  b_col1, b_col2, b_col3 = st.columns(3)
  b_col1.metric("Daily Avg Burn", f"₹{daily_burn_rate:,.0f}/day")
  b_col2.metric("Projected Month End", f"₹{projected_month_end:,.0f}")
  monthly_budget = b_col3.number_input(
      "Monthly Budget (₹)", value=25000, step=1000
  )

  if projected_month_end > monthly_budget:
    st.warning(
        f"⚠️ **Pace Alert:** At ₹{daily_burn_rate:,.0f}/day, you are on track to overshoot your ₹{monthly_budget:,.0f} budget by ₹{projected_month_end - monthly_budget:,.0f}."
    )
  else:
    st.success(
        f"✅ **On Track:** Projected to save ₹{monthly_budget - projected_month_end:,.0f} below your budget."
    )

st.divider()

# -------------------------------------------------------------
# Main Navigation Tabs
# -------------------------------------------------------------
tab_add, tab_trips, tab_parser, tab_manage = st.tabs(
    ["➕ Manual Log", "✈️ Trip Aggregator", "📥 Bank / SMS Parser", "📋 History"]
)

# --- TAB 1: Manual Log ---
with tab_add:
  col1, col2 = st.columns(2)
  with col1:
    amount = st.number_input(
        "Amount (₹)", min_value=0.0, step=10.0, format="%.2f"
    )
  with col2:
    selected_cat = st.selectbox("Category", list(CATEGORIES.keys()))

  sub_options = CATEGORIES[selected_cat]
  sub_cat = st.selectbox("Sub-Type", sub_options)

  col3, col4 = st.columns(2)
  with col3:
    payment = st.selectbox(
        "Payment Mode", ["UPI", "Card", "Cash", "Net Banking"]
    )
  with col4:
    tx_date = st.date_input("Date", value=today)

  col5, col6 = st.columns(2)
  with col5:
    selected_trip = st.selectbox("Tag Trip / Purpose", TRIP_TAGS)
  with col6:
    note = st.text_input("Note", placeholder="e.g., IRCTC Tatkal, Auto to station")

  if st.button("Save Entry", type="primary", use_container_width=True):
    if amount <= 0:
      st.error("Please enter a valid amount.")
    else:
      append_entry(
          amount,
          selected_cat,
          sub_cat,
          payment,
          tx_date,
          selected_trip,
          note,
      )
      st.success(f"Recorded ₹{amount:.2f} under {sub_cat}!")
      st.rerun()

# --- TAB 2: Trip Cost Aggregator ---
with tab_trips:
  st.subheader("✈️ End-to-End Trip Expenses")
  st.caption(
      "See the true, combined cost of your home trips (train tickets, local"
      " autos, food on the way)."
  )

  if not df.empty and "Trip" in df.columns:
    trip_list = [t for t in df["Trip"].unique() if t != "None" and pd.notna(t)]
    if trip_list:
      chosen_trip = st.selectbox("Select Trip to Analyze", trip_list)
      trip_df = df[df["Trip"] == chosen_trip].sort_values(
          by="Date", ascending=False
      )

      total_trip_cost = trip_df["Amount"].sum()
      st.metric(f"Total Spent on '{chosen_trip}'", f"₹{total_trip_cost:,.2f}")

      # Visual split
      trip_cat_breakdown = (
          trip_df.groupby("Sub-Category")["Amount"].sum().reset_index()
      )
      st.bar_chart(data=trip_cat_breakdown, x="Sub-Category", y="Amount")
      st.dataframe(trip_df, use_container_width=True, hide_index=True)
    else:
      st.info(
          "No trips tagged yet. Select 'Home Trip' in the trip dropdown when"
          " logging an expense."
      )
  else:
    st.info("No records available yet.")

# --- TAB 3: Automated SMS / Bank Text Parser ---
with tab_parser:
  st.subheader("📥 Paste SMS or Bank Narration")
  st.caption(
      "Paste any bank SMS (HDFC, SBI, ICICI, etc.) to extract amount and vendor"
      " automatically."
  )

  sms_text = st.text_area(
      "Paste SMS Text",
      placeholder="e.g., Sent Rs. 180.00 from HDFC Bank to SWIGGY via UPI on 21-Sep-26...",
      height=80,
  )

  if st.button("Parse SMS Text"):
    if sms_text:
      # Regex pattern for Indian Bank SMS debits
      amt_match = re.search(
          r"(?:Rs\.?|INR)\s*([\d,]+(?:\.\d{1,2})?)", sms_text, re.IGNORECASE
      )
      if amt_match:
        parsed_amt = float(amt_match.group(1).replace(",", ""))
        st.session_state["parsed_amt"] = parsed_amt

        # Guess category based on keywords
        sms_upper = sms_text.upper()
        if any(
            k in sms_upper
            for k in ["SWIGGY", "ZOMATO", "FOOD", "RESTAURANT", "CAFE"]
        ):
          st.session_state["parsed_cat"] = "Meals & Dining"
          st.session_state["parsed_sub"] = "Swiggy / Zomato Order"
        elif any(
            k in sms_upper
            for k in ["IRCTC", "TRAIN", "RAILWAY", "MAKEMYTRIP", "FLIGHT"]
        ):
          st.session_state["parsed_cat"] = "Home Travel"
          st.session_state["parsed_sub"] = "Train Fare"
        elif any(k in sms_upper for k in ["UBER", "OLA", "RAPIDO", "METRO"]):
          st.session_state["parsed_cat"] = "Office Commute"
          st.session_state["parsed_sub"] = "Auto Fare"
        else:
          st.session_state["parsed_cat"] = "Shopping & Misc"
          st.session_state["parsed_sub"] = "Miscellaneous"

        st.success(f"Detected Amount: ₹{parsed_amt}")
      else:
        st.error("Could not detect transaction amount from text.")

  if "parsed_amt" in st.session_state:
    st.write("Confirm Parsed Transaction:")
    p_col1, p_col2 = st.columns(2)
    p_amt = p_col1.number_input(
        "Amount", value=st.session_state.get("parsed_amt", 0.0)
    )
    p_cat = p_col2.selectbox(
        "Category",
        list(CATEGORIES.keys()),
        index=list(CATEGORIES.keys()).index(
            st.session_state.get("parsed_cat", "Shopping & Misc")
        ),
    )
    p_sub = st.selectbox("Sub-Type", CATEGORIES[p_cat])

    if st.button("➕ Confirm & Save Parsed Entry", type="primary"):
      append_entry(
          p_amt,
          p_cat,
          p_sub,
          "UPI",
          today,
          note=f"Parsed: {sms_text[:30]}...",
      )
      del st.session_state["parsed_amt"]
      st.success("Entry added!")
      st.rerun()

# --- TAB 4: History & Data Management ---
with tab_manage:
  if not df.empty:
    st.subheader("📋 Logged Transactions")
    display_df = df.sort_values(by=["Date", "ID"], ascending=[False, False])
    st.dataframe(display_df, use_container_width=True, hide_index=True)

    st.markdown("##### 🗑️ Delete an Entry")
    options_df = display_df.head(25)
    del_options = {
        f"ID: {row.ID} | {row.Date} | ₹{row.Amount:.0f} | {row['Sub-Category']}"
        + (f" ({row.Note})" if row.Note else ""): row.ID
        for _, row in options_df.iterrows()
    }
    target_to_delete = st.selectbox("Choose entry to delete", list(del_options.keys()))

    if st.button("Delete Entry", type="secondary"):
      id_val = del_options[target_to_delete]
      df = df[df["ID"] != id_val]
      save_data(df)
      st.warning(f"Deleted record #{id_val}")
      st.rerun()

    # CSV Download
    csv_bytes = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        "📥 Export All Data (CSV)",
        data=csv_bytes,
        file_name=f"expenses_{today}.csv",
        mime="text/csv",
        use_container_width=True,
    )
  else:
    st.info("No records recorded yet.")
