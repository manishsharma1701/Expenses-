from datetime import date
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
    df["Date"] = pd.to_datetime(df["Date"])
    return df
  except (FileNotFoundError, pd.errors.EmptyDataError):
    return pd.DataFrame(
        columns=[
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

# 1. Main Category & Amount (Outside st.form so selecting triggers an instant re-render)
col1, col2 = st.columns(2)
with col1:
  amount = st.number_input("Amount (₹)", min_value=0.0, step=10.0, format="%.2f")
with col2:
  selected_cat = st.selectbox("Category", list(CATEGORIES.keys()))

# 2. Sub-Category dynamically matches the selected category immediately
sub_options = CATEGORIES[selected_cat]
sub_cat = st.selectbox("Sub-Type", sub_options)

# 3. Payment Mode & Date
col3, col4 = st.columns(2)
with col3:
  payment = st.selectbox(
      "Payment Mode", ["UPI", "Card", "Cash", "Net Banking"]
  )
with col4:
  tx_date = st.date_input("Date", value=date.today())

note = st.text_input("Note (Optional)", placeholder="e.g., Irani chai, metro")

# 4. Save Button
if st.button("➕ Add Expense", use_container_width=True, type="primary"):
  if amount <= 0:
    st.error("Please enter an amount greater than ₹0.")
  else:
    df = load_data()
    new_entry = pd.DataFrame([{
        "Date": pd.to_datetime(tx_date),
        "Category": selected_cat,
        "Sub-Category": sub_cat,
        "Amount": amount,
        "Payment": payment,
        "Note": note.strip(),
    }])
    df = pd.concat([df, new_entry], ignore_index=True)
    save_data(df)
    st.success(f"Added ₹{amount:.2f} under {selected_cat} → {sub_cat}!")
    st.rerun()

st.divider()

# Dashboard & Summaries
df = load_data()

if not df.empty:
  today = date.today()
  current_month_df = df[
      (df["Date"].dt.year == today.year) & (df["Date"].dt.month == today.month)
  ]

  month_total = current_month_df["Amount"].sum()
  st.metric(
      label=f"Total Spent ({today.strftime('%B %Y')})",
      value=f"₹{month_total:,.2f}",
  )

  # Breakdown by category
  if not current_month_df.empty:
    st.subheader("Category Breakdown (This Month)")
    cat_summary = (
        current_month_df.groupby("Category")["Amount"].sum().reset_index()
    )
    st.bar_chart(data=cat_summary, x="Category", y="Amount")

  # Recent Log Table
  st.subheader("Recent Entries")
  display_df = df.sort_values(by="Date", ascending=False).copy()
  display_df["Date"] = display_df["Date"].dt.strftime("%Y-%m-%d")
  st.dataframe(display_df.head(25), use_container_width=True, hide_index=True)

  # CSV Download
  csv_data = df.to_csv(index=False).encode("utf-8")
  st.download_button(
      label="📥 Export All Data (CSV)",
      data=csv_data,
      file_name=f"expenses_{today}.csv",
      mime="text/csv",
      use_container_width=True,
  )
else:
  st.info("No expenses recorded yet. Add your first entry above.")
    
