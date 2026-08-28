import pandas as pd
import re

raw = pd.read_excel(r"C:\Users\sidlu\Mauritius_Tourism_Analytics\data\raw\2023 tourist arrivals\Tourist_M_Dec23_160224.xlsx",
                    sheet_name="Table 1", header=None)

year_row = raw.iloc[3, 1:].ffill()
year_row = year_row.apply(lambda x: re.match(
    r"\d+", str(x)).group() if pd.notna(x) else x)
month_row = raw.iloc[4, 1:]

earnings_row = raw[raw[0].astype(str).str.contains(
    "Tourism earnings", na=False)]
earnings_values = earnings_row.iloc[0, 1:]  # drop the label in column 0

earnings_df = pd.DataFrame({
    "Year": year_row.values,
    "Month": month_row.values,
    "Earnings": earnings_values.values
})

earnings_df["Earnings"] = earnings_df["Earnings"] * 1_000_000

earnings_df = earnings_df[(earnings_df["Year"] == "2023") & (
    earnings_df["Month"] != "Jan-Dec")]
earnings_df = earnings_df.reset_index(drop=True)
earnings_df["Date"] = pd.to_datetime(
    earnings_df["Year"] + "-" + earnings_df["Month"], format="%Y-%b")

earnings_df.to_csv(
    "C:\\Users\\sidlu\\Mauritius_Tourism_Analytics\\data\\processed\\2023_Earnings_Clean.CSV", index=False)

earnings_df
