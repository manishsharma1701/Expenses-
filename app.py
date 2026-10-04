# =============================================================
# PATCH 1 of 2
# REPLACE everything from the "Storage Engine" comment header
# down to and including append_entry() with this block.
# (Imports, CATEGORIES, TRIP_TAGS and everything below stay as is.)
# =============================================================

COLUMNS = [
    "ID", "Date", "Category", "Sub-Category",
    "Amount", "Payment", "Trip", "Note",
]


def get_connection():
  """Returns a Google Sheets connection, or None if not configured."""
  try:
    from streamlit_gsheets import GSheetsConnection

    return st.connection("gsheets", type=GSheetsConnection)
  except Exception:
    return None


def _normalize(df):
  """Makes any loaded table match the expected schema and types."""
  df = df.copy()
  for c in COLUMNS:
    if c not in df.columns:
      df[c] = "None" if c == "Trip" else ("" if c != "ID" else None)
  df = df[COLUMNS]
  df["Date"] = pd.to_datetime(df["Date"], errors="coerce").dt.date
  df = df[df["Date"].notna()]  # drops blank / junk rows
  df["Amount"] = pd.to_numeric(df["Amount"], errors="coerce").fillna(0.0)
  df["Trip"] = df["Trip"].fillna("None").replace("", "None")
  df["Note"] = df["Note"].fillna("").astype(str)
  ids = pd.to_numeric(df["ID"], errors="coerce")
  if ids.isna().any() or ids.duplicated().any():
    df["ID"] = range(1, len(df) + 1)
  else:
    df["ID"] = ids.astype(int)
  return df.reset_index(drop=True)


def load_data():
  conn = get_connection()
  if conn:
    try:
      raw = conn.read(ttl="0s")
      if raw is None:
        raw = pd.DataFrame(columns=COLUMNS)
      st.session_state["storage_mode"] = "gsheets"
      return _normalize(raw)
    except Exception as e:
      # Sheets is configured but unreachable. Stop instead of silently
      # falling back, otherwise the next save would overwrite the sheet.
      st.error(f"Could not read Google Sheet: {e}")
      st.stop()

  st.session_state["storage_mode"] = "csv"
  try:
    return _normalize(pd.read_csv(CSV_FILE))
  except (FileNotFoundError, pd.errors.EmptyDataError):
    return _normalize(pd.DataFrame(columns=COLUMNS))


def save_data(df):
  out = df[COLUMNS].copy()
  out["Date"] = out["Date"].astype(str)  # ISO strings are safe for Sheets

  # Always keep a local CSV copy as a secondary backup
  try:
    out.to_csv(CSV_FILE, index=False)
  except Exception:
    pass

  conn = get_connection()
  if conn:
    try:
      conn.update(data=out)
    except Exception as e:
      st.error(f"Save to Google Sheet FAILED: {e}")
      st.stop()


def append_entry(
    amount, category, sub_cat, payment, tx_date, trip="None", note=""
):
  df = load_data()
  next_id = int(df["ID"].max() + 1) if not df.empty else 1
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


# =============================================================
# PATCH 2 of 2
# ADD this right after:  st.title("⚡ TrackWise Pro")
# =============================================================

with st.sidebar:
  st.subheader("💾 Data & Backup")
  _data = load_data()  # also sets st.session_state["storage_mode"]
  if st.session_state.get("storage_mode") == "gsheets":
    st.success("Saving to Google Sheets (persistent)")
  else:
    st.warning(
        "Saving to a local CSV only. On hosted apps this can be wiped on"
        " reboot. Download a backup below or connect Google Sheets."
    )

  st.download_button(
      "⬇️ Download backup (CSV)",
      data=_data.to_csv(index=False).encode("utf-8"),
      file_name=f"trackwise_backup_{date.today().isoformat()}.csv",
      mime="text/csv",
      use_container_width=True,
  )

  _up = st.file_uploader("Restore from backup CSV", type=["csv"])
  if _up is not None and st.button("♻️ Merge backup into data"):
    try:
      _incoming = _normalize(pd.read_csv(_up))
      _merged = pd.concat([_data, _incoming], ignore_index=True)
      _merged = _merged.drop_duplicates(
          subset=[c for c in COLUMNS if c != "ID"]
      ).reset_index(drop=True)
      _merged["ID"] = range(1, len(_merged) + 1)
      save_data(_merged)
      st.success(f"Restored. {len(_merged)} records total.")
      st.rerun()
    except Exception as e:
      st.error(f"Restore failed: {e}")
        
