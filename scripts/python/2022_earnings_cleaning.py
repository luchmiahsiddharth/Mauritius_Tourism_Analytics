import pandas as pd
import re

raw = pd.read_excel(
    r"C:\Users\sidlu\Mauritius_Tourism_Analytics\data\raw\2023 tourist arrivals\Tourist_M_Dec23_160224.xlsx",
    sheet_name="Table 1", header=None
)

year_row  = raw.iloc[3, 1:].ffill()
month_row = raw.iloc[4, 1:].astype(str).str.strip()   # also strips whitespace, per your last fix

def extract_year(x):
    if pd.isna(x):
        return None
    match = re.match(r"\d+", str(x))
    return match.group() if match else None

year_clean = year_row.apply(extract_year)

# Keep only columns where a real year was found — drops the "% Change" block entirely
valid = year_clean.notna()
year_clean = year_clean[valid]
month_row  = month_row[valid]

# --- Find the earnings row, then keep only the valid (year/month) columns from it ---
earnings_row = raw[raw[0].astype(str).str.contains("Tourism earnings", na=False)]
earnings_values_full = earnings_row.iloc[0, 1:]
earnings_values = earnings_values_full[valid]

earnings_df = pd.DataFrame({
    "Year": year_clean.values,
    "Month": month_row.values,
    "Earnings": earnings_values.values
})

earnings_df["Earnings"] = earnings_df["Earnings"] * 1_000_000


earnings_df = earnings_df[(earnings_df["Year"] == "2022") & (earnings_df["Month"] != "Jan-Dec")]
earnings_df = earnings_df.reset_index(drop=True)

earnings_df["Date"] = pd.to_datetime(earnings_df["Year"] + "-" + earnings_df["Month"], format="%Y-%b")

earnings_df.to_csv(
    r"C:\Users\sidlu\Mauritius_Tourism_Analytics\data\processed\2022_Earnings_Clean.CSV",
    index=False
)

earnings_df