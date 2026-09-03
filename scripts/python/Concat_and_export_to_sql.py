import pandas as pd
import glob
from sqlalchemy import create_engine
# Adjust the path/pattern to match where your cleaned files actually live
files = glob.glob(r"C:\Users\sidlu\Mauritius_Tourism_Analytics\data\processed\*_Tourist_Arrivals_Clean.csv")

#print(files)  # sanity check — should list all 8 yearly files

all_arrivals = pd.concat([pd.read_csv(f) for f in files], ignore_index=True)
print(all_arrivals.shape)
print(all_arrivals["Country"].nunique())

countries = (
    all_arrivals[["Country", "Continent"]]
    .drop_duplicates()
    .rename(columns={"Country": "Country_Name", "Continent": "Continent"})
    .reset_index(drop=True)
)
countries.head(10)


conn_str = (
    "mssql+pyodbc://SIDS_PC\\SQLEXPRESS/MauritiusTourism"
    "?driver=ODBC+Driver+17+for+SQL+Server"
    "&trusted_connection=yes"
)
engine = create_engine(conn_str)


#populating the table

dim_date_sql = pd.read_sql("SELECT Arrival_ID, Full_Date FROM Date_Dim", engine)
countries_sql = pd.read_sql("SELECT Country_ID, Country_Name FROM Countries", engine)

# Make sure Date is a proper datetime for matching against Full_Date
all_arrivals["Date"] = pd.to_datetime(all_arrivals["Date"])
dim_date_sql["Full_Date"] = pd.to_datetime(dim_date_sql["Full_Date"])

merged = all_arrivals.merge(
    dim_date_sql, left_on="Date", right_on="Full_Date", how="left"
).merge(
    countries_sql, left_on="Country", right_on="Country_Name", how="left"
)

# Check for any unmatched rows before loading — this is important
print(merged["Arrival_ID"].isna().sum())
print(merged["Country_ID"].isna().sum())

fact_arrivals = merged[["Arrival_ID", "Country_ID", "Air", "Sea"]].rename(
    columns={"Air": "Air_Arrivals", "Sea": "Sea_Arrivals"}
)

# fact_arrivals.to_sql("Arrivals_Fact", engine, if_exists="append", index=False)

#EARNINGS

# --- Combine your yearly earnings CSVs ---
earnings_files = glob.glob(r"C:\Users\sidlu\Mauritius_Tourism_Analytics\data\processed\*_Earnings_Clean.csv")
print(earnings_files)  # confirm all 8 years are picked up

all_earnings = pd.concat([pd.read_csv(f) for f in earnings_files], ignore_index=True)
print(all_earnings.shape)   # expect 96 rows (8 years x 12 months)

# --- Merge against Date_Dim to get Arrival_ID ---
all_earnings["Date"] = pd.to_datetime(all_earnings["Date"].astype(str).str.strip())

merged_earnings = all_earnings.merge(
    dim_date_sql, left_on="Date", right_on="Full_Date", how="left"
)

print(merged_earnings["Arrival_ID"].isna().sum())

# --- Build final table and load ---
income_dim = merged_earnings[["Arrival_ID", "Earnings"]].rename(
    columns={"Earnings": "Net_Income"}
)

# income_dim.to_sql("Income_Dim", engine, if_exists="append", index=False)

# --- EVENTS ---

events_df = pd.read_csv(r"C:\Users\sidlu\Mauritius_Tourism_Analytics\data\processed\Significant_Events.csv")
events_df["Event_Date"] = pd.to_datetime(events_df["Event_Date"])

# Merge against Date_Dim to get the matching Arrival_ID for each event's month
merged_events = events_df.merge(
    dim_date_sql, left_on=events_df["Event_Date"].dt.to_period("M").dt.to_timestamp(),
    right_on="Full_Date", how="left"
)

print(merged_events["Arrival_ID"].isna().sum())  # confirm every event matched a month

events_final = merged_events[["Arrival_ID", "Event_Date", "Event_Name"]]

# events_final.to_sql("Events", engine, if_exists="append", index=False)