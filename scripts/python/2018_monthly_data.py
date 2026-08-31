import pandas as pd
import re

raw = pd.read_excel(
    r"C:\Users\sidlu\Mauritius_Tourism_Analytics\data\raw\2019 tourist arrivals\Tourist_M_Dec19.xls",
    sheet_name="Table 2", header=None
)
raw.iloc[3].name = None

# --- Build header rows ---
year_row  = raw.iloc[3, 1:].ffill()
month_row = raw.iloc[4, 1:].ffill().astype(str).str.strip()
type_row  = raw.iloc[5, 1:].astype(str).str.strip()

# --- Extract year safely: returns None (not a crash) for non-year cells like "% Change" ---
def extract_year(x):
    if pd.isna(x):
        return None
    match = re.match(r"\d+", str(x))
    return match.group() if match else None

year_clean = year_row.apply(extract_year)

# --- Keep only columns where a real year was found — drops the "% Change" block entirely ---
valid = year_clean.notna()
year_clean = year_clean[valid]
month_row  = month_row[valid]
type_row   = type_row[valid]

# --- Build column names from just the valid columns ---
new_columns = ["Country"]
for y, m, t in zip(year_clean, month_row, type_row):
    new_columns.append(f"{y}_{m}_{t}")

# --- Slice data rows, keeping only Country column + valid year/month/type columns ---
valid_col_positions = [0] + [i + 1 for i, keep in enumerate(valid) if keep]
data = raw.iloc[5:129, valid_col_positions].copy()
data.columns = new_columns
data = data.reset_index(drop=True)

data["Country"] = data["Country"].astype(str).str.replace(r"\s*\d+$", "", regex=True).str.strip()

# --- Continents (unchanged from your version) ---
continents = {"AFRICA", "AMERICA", "ASIA", "EUROPE", "OCEANIA"}
is_region_header = data["Country"].isin(continents)

data["Continent"] = data["Country"].where(is_region_header).ffill()
data = data[~is_region_header].copy()

long_df = data.melt(
    id_vars=["Country", "Continent"],
    var_name="Year_Month_Type",
    value_name="value"
)

long_df[["Year", "Month", "Type"]] = long_df["Year_Month_Type"].str.rsplit("_", n=2, expand=True)
long_df = long_df.drop(columns="Year_Month_Type")

long_df = long_df[
    (long_df["Year"] == "2018") &
    (long_df["Month"] != "Jan-Dec")
]

tidy = long_df.pivot_table(
    index=["Continent", "Country", "Year", "Month"],
    columns="Type",
    values="value",
    aggfunc="first"
).reset_index()
tidy.columns.name = None

tidy["Date"] = pd.to_datetime(tidy["Year"] + "-" + tidy["Month"], format="%Y-%b")

print((tidy["Air"] + tidy["Sea"] == tidy["Total"]).all())

tidy = tidy.sort_values(["Continent", "Country", "Date"]).reset_index(drop=True)

tidy = tidy[tidy["Country"].notna()]
tidy = tidy[~tidy["Country"].str.contains("IOC 3 countries", na=False)]
tidy = tidy[~tidy["Country"].str.contains("MIDDLE EAST", na=False)]
tidy = tidy[~tidy["Country"].str.contains("CIS 2 countries", na=False)]
tidy = tidy[~tidy["Country"].str.contains("All countries", na=False)]
tidy = tidy[~tidy["Country"].str.contains("Others", na=False)]

tidy.to_csv(
    r"C:\Users\sidlu\Mauritius_Tourism_Analytics\data\processed\2018_Tourist_Arrivals_Clean.CSV",
    index=False
)