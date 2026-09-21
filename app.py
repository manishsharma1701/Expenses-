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
        "Other",
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
        "Swiggy / Zomato",
        "Dining Out",
    ],
    "Groceries": [
        "Vegetables / Fruits",
        "Supermarket",
        "Milk / Daily Essentials",
    ],
    "Bills & Utilities": [
        "Mobile Recharge",
        "Wi-Fi",
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


# App UI
st.title("💸 Daily Expense Tracker")

with st.form("expense_form", clear_on_submit=True):
  col1, col2 = st.columns(2)
  with col1:
    amount = st.number_input("Amount (₹)", min_value=1.0, step=10.0, format="%.2f")
  with col2:
    category = st.selectbox("Category", list(CATEGORIES.keys()))

  sub_category = st.selectbox("Sub-Type", CATEGORIES[category])

  col3, col4 = st.columns(2)
  with col3:
    payment = st.selectbox(
        "Payment Mode", ["UPI", "Card", "Cash", "Net Banking"]
    )
  with col4:
    tx_date = st.date_input("Date", value=date.today())

  note = st.text_input("Note (Optional)", placeholder="e.g., Irani chai, metro")

  submitted = st.form_submit_button("➕ Add Expense", use_container_width=True)

  if submitted and amount > 0:
    df = load_data()
    new_entry = pd.DataFrame([{
        "Date": pd.to_datetime(tx_date),
        "Category": category,
        "Sub-Category": sub_category,
        "Amount": amount,
        "Payment": payment,
        "Note": note,
    }])
    df = pd.concat([df, new_entry], ignore_index=True)
    save_data(df)
    st.success(f"Added ₹{amount:.2f} under {sub_category}!")

# Data Display & Analytics
df = load_data()

if not df.empty:
  today = date.today()
  # Filter for current month
  current_month_df = df[
      (df["Date"].dt.year == today.year) & (df["Date"].dt.month == today.month)
  ]

  month_total = current_month_df["Amount"].sum()
  st.metric(
      label=f"Total Spent ({today.strftime('%B %Y')})",
      value=f"₹{month_total:,.2f}",
  )

  # Breakdown by Category
  st.subheader("Category Breakdown")
  cat_summary = (
      current_month_df.groupby("Category")["Amount"].sum().reset_index()
  )
  st.bar_chart(data=cat_summary, x="Category", y="Amount")

  # Recent Entries Table
  st.subheader("Recent Entries")
  display_df = df.sort_values(by="Date", ascending=False).copy()
  display_df["Date"] = display_df["Date"].dt.strftime("%Y-%m-%d")
  st.dataframe(display_df.head(20), use_container_width=True, hide_index=True)

  # Export CSV
  csv_data = df.to_csv(index=False).encode("utf-8")
  st.download_button(
      label="📥 Download All Data (CSV)",
      data=csv_data,
      file_name=f"expenses_{today}.csv",
      mime="text/csv",
      use_container_width=True,
  )
else:
  st.info("No expenses logged yet. Add your first entry above!")
      
