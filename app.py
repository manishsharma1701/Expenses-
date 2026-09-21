from datetime import date, timedelta
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Expense Tracker", page_icon="💸", layout="centered")

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


def load_data():
  try:
    df = pd.read_csv(CSV_FILE)
    if "ID" not in df.columns:
      df.insert(0, "ID", range(1, len(df) + 1))
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
            "Note",
        ]
    )


def save_data(df):
  df.to_csv(CSV_FILE, index=False)


st.title("💸 Daily Expense Tracker")

# 1. Summary Metrics: Today, Yesterday, This Month
df = load_data()
today = date.today()
yesterday = today - timedelta(days=1)

today_total = 0.0
yesterday_total = 0.0
month_total = 0.0

if not df.empty:
  today_total = df[df["Date"] == today]["Amount"].sum()
  yesterday_total = df[df["Date"] == yesterday]["Amount"].sum()
  month_total = df[
      (pd.to_datetime(df["Date"]).dt.year == today.year)
      & (pd.to_datetime(df["Date"]).dt.month == today.month)
  ]["Amount"].sum()

m1, m2, m3 = st.columns(3)
m1.metric("Today", f"₹{today_total:,.0f}")
m2.metric("Yesterday", f"₹{yesterday_total:,.0f}")
m3.metric(f"{today.strftime('%b')} Total", f"₹{month_total:,.0f}")

st.divider()

# 2. Add Expense Form
st.subheader("Add New Entry")
col1, col2 = st.columns(2)
with col1:
  amount = st.number_input("Amount (₹)", min_value=0.0, step=10.0, format="%.2f")
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

note = st.text_input("Note (Optional)", placeholder="e.g., Irani chai, metro")

if st.button("➕ Add Expense", use_container_width=True, type="primary"):
  if amount <= 0:
    st.error("Please enter an amount greater than ₹0.")
  else:
    df = load_data()
    next_id = int(df["ID"].max() + 1) if not df.empty else 1
    new_entry = pd.DataFrame([{
        "ID": next_id,
        "Date": tx_date,
        "Category": selected_cat,
        "Sub-Category": sub_cat,
        "Amount": amount,
        "Payment": payment,
        "Note": note.strip(),
    }])
    df = pd.concat([df, new_entry], ignore_index=True)
    save_data(df)
    st.success(f"Added ₹{amount:.2f} to {sub_cat}!")
    st.rerun()

st.divider()

# 3. Recent Entries & Deletion
if not df.empty:
  st.subheader("Recent Entries")
  display_df = df.sort_values(by=["Date", "ID"], ascending=[False, False])
  st.dataframe(display_df.head(20), use_container_width=True, hide_index=True)

  # Delete section
  with st.expander("🗑️ Delete an Entry"):
    # Generate labels like: "ID: 4 | 2026-09-21 | ₹150.00 | Lunch"
    options_df = display_df.head(30)
    options = {
        f"ID: {row.ID} | {row.Date} | ₹{row.Amount:.0f} | {row['Sub-Category']}"
        + (f" ({row.Note})" if row.Note else ""): row.ID
        for _, row in options_df.iterrows()
    }

    selected_label = st.selectbox("Select entry to delete", list(options.keys()))
    if st.button("Delete Selected Entry", type="secondary"):
      id_to_delete = options[selected_label]
      df = df[df["ID"] != id_to_delete]
      save_data(df)
      st.warning(f"Deleted entry #{id_to_delete}")
      st.rerun()

  # Category breakdown chart for current month
  current_month_df = df[
      (pd.to_datetime(df["Date"]).dt.year == today.year)
      & (pd.to_datetime(df["Date"]).dt.month == today.month)
  ]
  if not current_month_df.empty:
    st.subheader(f"Spending by Category ({today.strftime('%B')})")
    cat_summary = (
        current_month_df.groupby("Category")["Amount"].sum().reset_index()
    )
    st.bar_chart(data=cat_summary, x="Category", y="Amount")

  # Download CSV
  csv_data = df.to_csv(index=False).encode("utf-8")
  st.download_button(
      label="📥 Export All to CSV",
      data=csv_data,
      file_name=f"expenses_{today}.csv",
      mime="text/csv",
      use_container_width=True,
  )
else:
  st.info("No records found. Start logging above!")
      
