import pandas as pd
import re

raw = pd.read_excel(r"C:\Users\sidlu\Mauritius_Tourism_Analytics\data\raw\2023 tourist arrivals\Tourist_M_Dec23_160224.xlsx", sheet_name="Table 2", header=None)
raw.iloc[3].name=None


year_row = raw.iloc[3, 1:].ffill()
year_row = year_row.apply(lambda x: re.match(r"\d+", str(x)).group() if pd.notna(x) else x)
month_row = raw.iloc[4, 1:].ffill()
type_row  = raw.iloc[5, 1:]

new_columns = ["Country"]
for y, m, t in zip(year_row, month_row, type_row):
    new_columns.append(f"{y}_{m}_{t}")

data = raw.iloc[5:129].copy()
data.columns = new_columns
data = data.reset_index(drop=True)

data["Country"] = data["Country"].astype(str).str.replace(r"\s*\d+$", "", regex=True).str.strip()

# Detect region header rows: they're written in ALL CAPS (e.g. "EUROPE"), unlike country names
continents = {"AFRICA", "AMERICA", "ASIA", "EUROPE", "OCEANIA"}
is_region_header = data["Country"].isin(continents)

# Carry the most recent continent header down to its country rows.
data["Continent"] = data["Country"].where(is_region_header).ffill()

# Remove the actual continent header rows.
data = data[~is_region_header].copy()

long_df = data.melt(
    id_vars=["Country", "Continent"],
    var_name="Year_Month_Type",
    value_name="value"
)

long_df[["Year", "Month", "Type"]] = long_df[
    "Year_Month_Type"
].str.rsplit("_", n=2, expand=True)
long_df = long_df.drop(columns="Year_Month_Type")

long_df = long_df[
    (long_df["Year"] == "2023") &
    (long_df["Month"] != "Jan-Dec")
]

tidy = long_df.pivot_table(
    index=["Continent", "Country", "Year", "Month"],
    columns="Type",
    values="value",
    aggfunc="first"
).reset_index()
tidy.columns.name = None

tidy["Date"] = pd.to_datetime(
    tidy["Year"] + "-" + tidy["Month"],
    format="%Y-%b"
)

print((tidy["Air"] + tidy["Sea"] == tidy["Total"]).all())

tidy = tidy.sort_values(
    ["Continent", "Country", "Date"]
).reset_index(drop=True)

tidy = tidy[tidy["Country"].notna()]
tidy = tidy[~tidy["Country"].str.contains("IOC 3 countries", na=False)]
tidy = tidy[~tidy["Country"].str.contains("MIDDLE EAST", na=False)]
tidy = tidy[~tidy["Country"].str.contains("CIS 2 countries", na=False)]
tidy = tidy[~tidy["Country"].str.contains("All countries", na=False)]
tidy = tidy[~tidy["Country"].str.contains("Others", na=False)]

tidy.to_csv(
    r"C:\Users\sidlu\Mauritius_Tourism_Analytics\data\processed\2023_Tourist_Arrivals_Clean.CSV",
    index=False
)