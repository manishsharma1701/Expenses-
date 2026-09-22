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
    "home expenses": [
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
tab_add, tab_trips, tab_parser, tab_screenshot, tab_manage = st.tabs([
    "➕ Manual Log",
    "✈️ Trip Aggregator",
    "📥 SMS Parser",
    "📸 Screenshot Parser",
    "📋 History",
])

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

# # --- TAB 3: Automated SMS / Bank Text Parser ---
with tab_parser:
  st.subheader("📥 Paste SMS or Bank Narration")
  st.caption(
      "Paste any bank SMS (SBI, HDFC, ICICI, etc.) to extract amount, vendor,"
      " and category automatically."
  )

  sms_text = st.text_area(
      "Paste SMS Text",
      placeholder=(
          "Dear UPI user A/C X9343 debited by 50.00 on date 19Sep26 trf to JAY"
          " MALHAR SNACS..."
      ),
      height=90,
  )

  if st.button("Parse SMS Text"):
    if sms_text:
      # 1. Amount Extraction (handles "debited by 50.00", "Rs. 50", "INR 50", "paid 50.00")
      amt_match = re.search(
          r"(?:debited\s+by|Rs\.?|INR|paid)\s*[:\s]?\s*([\d,]+(?:\.\d{1,2})?)",
          sms_text,
          re.IGNORECASE,
      )

      # 2. Merchant / Receiver Extraction (handles "trf to ...", "to ...", "VPA ...")
      vendor_match = re.search(
          r"(?:trf\s+to|transferred\s+to|paid\s+to|to)\s+([A-Za-z0-9\s&]+?)(?=\s+(?:Refno|Ref|UPI|on|avl|bal|If|call)|$)",
          sms_text,
          re.IGNORECASE,
      )

      # 3. Date Extraction (e.g., "19Sep26" or "19-09-2026")
      parsed_date = today
      date_match = re.search(
          r"\b(\d{1,2}[A-Za-z]{3}\d{2,4})\b", sms_text, re.IGNORECASE
      )
      if date_match:
        try:
          parsed_date = pd.to_datetime(
              date_match.group(1), format="%d%b%y"
          ).date()
        except Exception:
          try:
            parsed_date = pd.to_datetime(date_match.group(1)).date()
          except Exception:
            parsed_date = today

      if amt_match:
        parsed_amt = float(amt_match.group(1).replace(",", ""))
        vendor_name = (
            vendor_match.group(1).strip()
            if vendor_match
            else "Unknown Merchant"
        )

        st.session_state["parsed_amt"] = parsed_amt
        st.session_state["parsed_date"] = parsed_date
        st.session_state["parsed_note"] = vendor_name

        # Smart Categorization Rules
        sms_upper = sms_text.upper()
        if any(
            k in sms_upper
            for k in [
                "SNAC",
                "SNACK",
                "TEA",
                "CHAI",
                "COFFEE",
                "CAFE",
                "BAKERY",
                "SWEETS",
            ]
        ):
          st.session_state["parsed_cat"] = "Chai & Snacks"
          st.session_state["parsed_sub"] = (
              "Evening Snacks"
              if "SNAC" in sms_upper
              else (
                  "Tea / Chai"
                  if "TEA" in sms_upper or "CHAI" in sms_upper
                  else "Coffee"
              )
          )
        elif any(
            k in sms_upper
            for k in [
                "SWIGGY",
                "ZOMATO",
                "FOOD",
                "RESTAURANT",
                "HOTEL",
                "BHOJANALAYA",
                "DHABA",
                "MESS",
            ]
        ):
          st.session_state["parsed_cat"] = "Meals & Dining"
          st.session_state["parsed_sub"] = (
              "Swiggy / Zomato Order"
              if ("SWIGGY" in sms_upper or "ZOMATO" in sms_upper)
              else "Dining Out"
          )
        elif any(
            k in sms_upper
            for k in [
                "IRCTC",
                "TRAIN",
                "RAILWAY",
                "MAKEMYTRIP",
                "FLIGHT",
                "AIRWAYS",
                "BUS",
                "REDBUS",
            ]
        ):
          st.session_state["parsed_cat"] = "Home Travel"
          st.session_state["parsed_sub"] = (
              "Train Fare"
              if "TRAIN" in sms_upper or "IRCTC" in sms_upper
              else "Bus Fare"
          )
        elif any(
            k in sms_upper
            for k in ["UBER", "OLA", "RAPIDO", "METRO", "NSRC", "AUTO"]
        ):
          st.session_state["parsed_cat"] = "Office Commute"
          st.session_state["parsed_sub"] = (
              "Metro Fare" if "METRO" in sms_upper else "Auto Fare"
          )
        elif any(
            k in sms_upper
            for k in [
                "BLINKIT",
                "ZEPTO",
                "INSTAMART",
                "BIGBASKET",
                "GROCERY",
                "SUPERMARKET",
                "PROVISION",
            ]
        ):
          st.session_state["parsed_cat"] = "Groceries"
          st.session_state["parsed_sub"] = "Supermarket"
        else:
          st.session_state["parsed_cat"] = "Shopping & Misc"
          st.session_state["parsed_sub"] = "Miscellaneous"

        st.success(
            f"Detected: ₹{parsed_amt:,.2f} to '{vendor_name}' on {parsed_date}"
        )
      else:
        st.error("Could not detect transaction amount from text.")

  if "parsed_amt" in st.session_state:
    st.write("Confirm Parsed Transaction:")
    p_col1, p_col2 = st.columns(2)
    p_amt = p_col1.number_input(
        "Amount (₹)", value=st.session_state.get("parsed_amt", 0.0)
    )
    p_cat = p_col2.selectbox(
        "Category",
        list(CATEGORIES.keys()),
        index=list(CATEGORIES.keys()).index(
            st.session_state.get("parsed_cat", "Chai & Snacks")
        ),
        key="parsed_cat_select",
    )

    p_col3, p_col4 = st.columns(2)
    p_sub = p_col3.selectbox(
        "Sub-Type", CATEGORIES[p_cat], key="parsed_sub_select"
    )
    p_date = p_col4.date_input(
        "Date", value=st.session_state.get("parsed_date", today)
    )

    p_col5, p_col6 = st.columns(2)
    p_mode = p_col5.selectbox(
        "Mode",
        ["UPI", "Card", "Cash", "Net Banking"],
        index=0,
        key="parsed_mode_select",
    )
    p_note = p_col6.text_input(
        "Note",
        value=st.session_state.get("parsed_note", ""),
        key="parsed_note_input",
    )

    if st.button(
        "➕ Confirm & Save Parsed Entry",
        type="primary",
        use_container_width=True,
    ):
      append_entry(
          p_amt,
          p_cat,
          p_sub,
          p_mode,
          p_date,
          trip="None",
          note=p_note,
      )
      del st.session_state["parsed_amt"]
      st.success(f"Saved ₹{p_amt:.2f} under {p_cat} → {p_sub}!")
      st.rerun()

from PIL import Image
import pytesseract
import calendar
from datetime import date
import re
import pandas as pd
from PIL import Image
import pytesseract
import streamlit as st

# --- TAB: Paytm History Screenshot Parser ---
with tab_screenshot:
  st.subheader("📸 Scan Paytm Transaction History")
  st.caption(
      "Upload screenshots showing Paytm's list of debit transactions with"
      " category tags."
  )

  uploaded_img = st.file_uploader(
      "Upload Paytm List Screenshot", type=["png", "jpg", "jpeg"]
  )

  if uploaded_img is not None:
    image = Image.open(uploaded_img)
    st.image(image, caption="Uploaded Screenshot", width=340)

    if st.button("🔍 Extract Transactions", type="primary"):
      with st.spinner("Parsing transactions and badges..."):
        # Configure Tesseract to capture layout cleanly
        custom_config = r"--oem 3 --psm 6"
        extracted_text = pytesseract.image_to_string(
            image, config=custom_config
        )

        lines = [
            line.strip()
            for line in extracted_text.split("\n")
            if len(line.strip()) > 1
        ]

        # Paytm UI noise to ignore
        noise_keywords = [
            "FROM",
            "SBI",
            "HDFC",
            "PAYTM",
            "PAYMENTS BANK",
            "STATEMENT",
            "FILTER",
            "SEARCH",
            "MONEY TRANSFER",
            "SUCCESSFUL",
            "DEBITED",
            "UPI",
            "PASSBOOK",
        ]

        # Map Paytm tags to your personal budget buckets
        paytm_cat_map = {
            "FOOD": ("Meals & Dining", "Lunch"),
            "SHOPPING": ("Shopping & Misc", "Clothing / Shoes"),
            "TRAVEL": ("Office Commute", "Auto Fare"),
            "GROCERIES": ("Groceries", "Supermarket"),
            "BILLS": ("Bills & Utilities", "Subscriptions"),
            "ENTERTAINMENT": ("Shopping & Misc", "Miscellaneous"),
        }

        detected_rows = []
        current_year = date.today().year

        # Scan line by line looking for amount markers like '- ₹15', '- ₹100', '₹45'
        for i, line in enumerate(lines):
          # Skip received money (+ sign)
          if "+" in line:
            continue

          # Match '- ₹15' or '- 15' or '₹ 100'
          amt_match = re.search(
              r"[-−]?\s*(?:₹|Rs\.?)\s*([\d,]+(?:\.\d{1,2})?)",
              line,
              re.IGNORECASE,
          )
          if not amt_match:
            # Fallback for plain debit values with dash: '- 45'
            amt_match = re.search(r"[-−]\s*([\d,]+(?:\.\d{1,2})?)", line)

          if amt_match:
            try:
              amount_val = float(amt_match.group(1).replace(",", ""))
              if (
                  amount_val <= 0 or amount_val > 100000
              ):  # Discard unrealistic or 0 amounts
                continue
            except Exception:
              continue

            # Look within surrounding lines (i-3 to i+3) for Merchant Name and Date
            surrounding_window = lines[max(0, i - 4) : min(len(lines), i + 4)]

            merchant_name = "UPI Payment"
            tx_date = date.today()
            detected_tag = None

            # 1. Look for Date: e.g. "18 Sep", "17 Sep, 07:38 PM"
            for w_line in surrounding_window:
              dt_search = re.search(
                  r"\b(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec))",
                  w_line,
                  re.IGNORECASE,
              )
              if dt_search:
                try:
                  date_str = f"{dt_search.group(1)} {current_year}"
                  tx_date = pd.to_datetime(
                      date_str, format="%d %b %Y"
                  ).date()
                  break
                except Exception:
                  pass

            # 2. Look for Paytm's built-in Category Tag (Food, Shopping, Travel, Groceries)
            for w_line in surrounding_window:
              tag_upper = w_line.strip().upper()
              for p_tag in paytm_cat_map:
                if p_tag in tag_upper and len(tag_upper) < 20:
                  detected_tag = p_tag
                  break
              if detected_tag:
                break

            # 3. Look for Merchant Name (text line that isn't an amount, date, or noise)
            for w_line in surrounding_window:
              clean = re.sub(
                  r"(?i)(paid to|to:|[-−]?\s*₹\s*[\d,]+|\b\d{1,2}\s+[A-Za-z]{3}\b)",
                  "",
                  w_line,
              ).strip()
              if (
                  len(clean) > 3
                  and not any(k in clean.upper() for k in noise_keywords)
                  and not re.search(r"\b\d{1,2}:\d{2}\b", clean)
              ):  # exclude times like 09:46 PM
                merchant_name = clean
                break

            # 4. Resolve Category: Prefer merchant name context over Paytm tag when specific
            m_upper = merchant_name.upper()
            if any(
                k in m_upper
                for k in [
                    "CHAHA",
                    "CHAI",
                    "TEA",
                    "SNAC",
                    "SNACKS",
                    "COFFEE",
                    "FUKREY",
                ]
            ):
              cat, sub = (
                  "Chai & Snacks",
                  (
                      "Evening Snacks"
                      if "SNAC" in m_upper
                      else "Tea / Chai"
                  ),
              )
            elif any(
                k in m_upper
                for k in ["AUTO", "METRO", "RAPIDO", "UBER", "OLA"]
            ):
              cat, sub = "Office Commute", "Auto Fare"
            elif any(
                k in m_upper
                for k in ["TRAIN", "IRCTC", "RAIL", "BUS", "FLIGHT"]
            ):
              cat, sub = "Home Travel", "Train Fare"
            elif any(k in m_upper for k in ["SUPER MARKET", "MART", "GROCERY"]):
              cat, sub = "Groceries", "Supermarket"
            elif detected_tag and detected_tag in paytm_cat_map:
              cat, sub = paytm_cat_map[detected_tag]
            else:
              cat, sub = "Shopping & Misc", "Miscellaneous"

            detected_rows.append({
                "Date": tx_date,
                "Category": cat,
                "Sub-Category": sub,
                "Amount": amount_val,
                "Payment": "UPI",
                "Trip": "None",
                "Note": merchant_name,
            })

        if detected_rows:
          # Deduplicate rows by Amount + Note + Date
          parsed_df = pd.DataFrame(detected_rows).drop_duplicates(
              subset=["Amount", "Note", "Date"]
          )
          st.session_state["paytm_extracted_df"] = parsed_df
          st.success(
              f"Successfully extracted {len(parsed_df)} transactions from"
              " image!"
          )
        else:
          st.error(
              "Could not locate clear debit amounts. Try zooming in slightly or"
              " taking a higher resolution screenshot."
          )

  # Interactive Table for Editing & Confirmation
  if "paytm_extracted_df" in st.session_state:
    st.markdown("##### ✏️ Verify Extracted Entries")
    st.caption(
        "Edit any misread merchant names or change categories directly in the"
        " table before saving:"
    )

    edited_df = st.data_editor(
        st.session_state["paytm_extracted_df"],
        num_rows="dynamic",
        use_container_width=True,
        hide_index=True,
    )

    c_save, c_clear = st.columns(2)
    with c_save:
      if st.button("💾 Save All to Expenses", type="primary"):
        df_master = load_data()
        next_id = (
            int(df_master["ID"].max() + 1)
            if not df_master.empty and "ID" in df_master.columns
            else 1
        )

        rows_to_save = []
        for _, row in edited_df.iterrows():
          rows_to_save.append({
              "ID": next_id,
              "Date": row["Date"],
              "Category": row["Category"],
              "Sub-Category": row["Sub-Category"],
              "Amount": float(row["Amount"]),
              "Payment": row["Payment"],
              "Trip": row.get("Trip", "None"),
              "Note": str(row["Note"]),
          })
          next_id += 1

        updated_df = pd.concat(
            [df_master, pd.DataFrame(rows_to_save)], ignore_index=True
        )
        save_data(updated_df)
        del st.session_state["paytm_extracted_df"]
        st.success(
            f"Saved {len(rows_to_save)} transactions directly to your tracker!"
        )
        st.rerun()

    with c_clear:
      if st.button("Clear / Cancel"):
        del st.session_state["paytm_extracted_df"]
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
