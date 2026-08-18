# Mauritius Tourism Analytics — Project Build Guide

**Stack:** Python → SQL Server → R → Power BI
**Goal:** An end-to-end pipeline (not just a dashboard) that shows raw government data going through cleaning, storage, statistical analysis, and visualization.

---

## Phase 0 — Environment Setup

Install these before touching data:

| Tool | What to install | Notes |
|---|---|---|
| **Python** | Python 3.11+, via [Anaconda](https://www.anaconda.com/download) or plain `pip` | Anaconda is easier if you don't want to manage envs manually |
| **SQL Server** | [SQL Server 2022 Developer Edition](https://www.microsoft.com/en-us/sql-server/sql-server-downloads) (free) | Developer edition has full features, free for non-production use |
| **SSMS** | [SQL Server Management Studio](https://learn.microsoft.com/en-us/sql/ssms/download-sql-server-management-studio-ssms) | GUI for managing SQL Server |
| **R** | [R 4.x](https://cran.r-project.org/) + [RStudio Desktop](https://posit.co/download/rstudio-desktop/) | |
| **Power BI** | [Power BI Desktop](https://www.microsoft.com/en-us/power-platform/products/power-bi/desktop) (free, Windows only) | |
| **Git** | [Git](https://git-scm.com/) + a GitHub account | For version control and your portfolio repo |
| **VS Code** | [VS Code](https://code.visualstudio.com/) | Optional but recommended as your main editor for Python/SQL |

Python packages to install (`pip install`):
```bash
pip install pandas numpy openpyxl xlrd requests sqlalchemy pyodbc python-dotenv matplotlib seaborn statsmodels jupyter
```

- `pandas`, `numpy` — data wrangling
- `openpyxl` / `xlrd` — reading `.xlsx` / older `.xls` files (Statistics Mauritius uses both)
- `sqlalchemy` + `pyodbc` — connecting Python to SQL Server
- `statsmodels` — seasonal decomposition / ARIMA forecasting
- `matplotlib`, `seaborn` — exploratory plots
- `jupyter` — for exploratory notebooks

You'll also need the **ODBC Driver 17 (or 18) for SQL Server** installed on your machine so `pyodbc` can connect — [download here](https://learn.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server).

R packages to install:
```r
install.packages(c("tidyverse", "readxl", "DBI", "odbc", "forecast", "lubridate", "janitor"))
```

---

## Phase 1 — Project Structure & Version Control

Set up your repo folder like this before you start:

```
mauritius-tourism-analytics/
│
├── data/
│   ├── raw/              # untouched downloaded files
│   └── processed/        # cleaned CSVs ready for SQL load
│
├── notebooks/             # Jupyter notebooks for EDA
├── scripts/
│   ├── python/            # cleaning + ETL scripts
│   └── r/                 # analysis scripts
│
├── sql/
│   ├── 01_create_schema.sql
│   ├── 02_create_tables.sql
│   └── 03_load_data.sql
│
├── powerbi/                # .pbix file
├── docs/                   # README, data dictionary, methodology notes
└── README.md
```

Initialize git now:
```bash
git init
git add .
git commit -m "Initial project structure"
```
Create the GitHub repo and push early — commit as you go, not just at the end. This shows a real development history, which matters more to people reviewing your portfolio than a single final commit.

---

## Phase 2 — Acquire the Data

Download these into `data/raw/`:

1. **Historical Data Series** (XLS) — long-run tourism indicators
2. **2–3 years of Monthly Tourist Arrivals**
3. **1–2 years of Tourism Digests** (XLSX) — arrivals by country, purpose, receipts, hotel occupancy
4. Optionally, the **Handbook of Statistical Data on Tourism** (PDF) if you want passenger-arrivals-by-mode-of-transport detail

Keep raw files untouched and named with their source date, e.g. `HS_Tourism_Yr25_220526.xls`. Never edit raw files by hand — all cleaning happens in code so it's reproducible.

---

## Phase 3 — Explore & Clean with Python

Do this in a Jupyter notebook first (`notebooks/01_explore.ipynb`), then move stable logic into a script (`scripts/python/clean_data.py`).

**3.1 Load and inspect**
```python
import pandas as pd

df = pd.read_excel("data/raw/HS_Tourism_Yr25_220526.xls", sheet_name=None)  # sheet_name=None loads all sheets as a dict
for name, sheet in df.items():
    print(name, sheet.shape)
```
Government Excel files are almost never analysis-ready — expect: merged header cells, multiple tables per sheet, footnotes embedded as rows, inconsistent date formats, and years as columns instead of rows (wide format). Budget real time for this step.

**3.2 Common cleaning tasks you'll likely hit**
- Drop title/footnote rows above and below the actual table
- Forward-fill merged header cells
- Reshape wide (years as columns) → long (one row per date) using `pd.melt()`
- Standardize country names (e.g. "United Kingdom" vs "U.K." vs "UK" across different files)
- Parse fortnightly/monthly labels into proper `datetime` objects
- Handle missing values consistently (don't silently drop — decide and document why)

**3.3 Target schema**
Aim to produce two or three clean, tidy CSVs in `data/processed/`:

- `tourist_arrivals.csv` — columns: `date`, `country_of_origin`, `arrivals`, `purpose_of_visit` (if available)
- `tourism_receipts.csv` — columns: `date`, `receipts_mur` (or per relevant currency)
- `hotel_statistics.csv` — columns: `date`, `bed_places`, `room_occupancy_rate`

Example melt pattern:
```python
long_df = wide_df.melt(
    id_vars=["country_of_origin"],
    var_name="month",
    value_name="arrivals"
)
```

Save with:
```python
long_df.to_csv("data/processed/tourist_arrivals.csv", index=False)
```

---

## Phase 4 — Design the SQL Server Schema

Open SSMS, connect to your local instance, and create a dedicated database.

**4.1 Create the database**
```sql
CREATE DATABASE MauritiusTourism;
GO
USE MauritiusTourism;
GO
```

**4.2 Star schema design**

Fact table + dimension tables — this is what makes the project look like real BI work rather than "one flat CSV imported":

```sql
-- Dimension: Date
CREATE TABLE dim_date (
    date_id INT PRIMARY KEY,
    full_date DATE NOT NULL,
    year INT,
    month INT,
    month_name VARCHAR(20),
    quarter INT
);

-- Dimension: Country
CREATE TABLE dim_country (
    country_id INT IDENTITY(1,1) PRIMARY KEY,
    country_name VARCHAR(100) NOT NULL UNIQUE,
    region VARCHAR(50)          -- e.g. Europe, Africa, Asia — you'll assign this yourself
);

-- Fact: Tourist Arrivals
CREATE TABLE fact_tourist_arrivals (
    arrival_id INT IDENTITY(1,1) PRIMARY KEY,
    date_id INT FOREIGN KEY REFERENCES dim_date(date_id),
    country_id INT FOREIGN KEY REFERENCES dim_country(country_id),
    arrivals INT,
    purpose_of_visit VARCHAR(50)
);

-- Fact: Tourism Receipts
CREATE TABLE fact_tourism_receipts (
    receipt_id INT IDENTITY(1,1) PRIMARY KEY,
    date_id INT FOREIGN KEY REFERENCES dim_date(date_id),
    receipts_mur DECIMAL(18,2)
);

-- Fact: Hotel Statistics
CREATE TABLE fact_hotel_stats (
    hotel_stat_id INT IDENTITY(1,1) PRIMARY KEY,
    date_id INT FOREIGN KEY REFERENCES dim_date(date_id),
    bed_places INT,
    room_occupancy_rate DECIMAL(5,2)
);
```

Save these as `sql/01_create_schema.sql` and `sql/02_create_tables.sql` in your repo.

---

## Phase 5 — Load Data from Python into SQL Server

Back in Python, connect via SQLAlchemy + pyodbc and push your cleaned CSVs in.

```python
from sqlalchemy import create_engine
import pandas as pd

# Connection string — adjust server name / auth method as needed
conn_str = (
    "mssql+pyodbc://localhost/MauritiusTourism"
    "?driver=ODBC+Driver+17+for+SQL+Server"
    "&trusted_connection=yes"
)
engine = create_engine(conn_str)

# Build dim_date first
dates = pd.date_range("2015-01-01", "2026-12-01", freq="MS")
dim_date = pd.DataFrame({
    "date_id": dates.strftime("%Y%m").astype(int),
    "full_date": dates,
    "year": dates.year,
    "month": dates.month,
    "month_name": dates.strftime("%B"),
    "quarter": dates.quarter
})
dim_date.to_sql("dim_date", engine, if_exists="append", index=False)

# Build dim_country from unique country names in your cleaned data
arrivals = pd.read_csv("data/processed/tourist_arrivals.csv")
countries = arrivals["country_of_origin"].drop_duplicates().to_frame(name="country_name")
countries.to_sql("dim_country", engine, if_exists="append", index=False)

# Then load fact table, mapping to the surrogate keys you just created
# (pull dim_date and dim_country back from SQL, merge on natural keys, then push fact table)
```

Do this for each fact table. Keep this logic in `scripts/python/load_to_sql.py` so the whole pipeline can be re-run end to end.

**Sanity check in SSMS** once loaded:
```sql
SELECT c.country_name, SUM(f.arrivals) AS total_arrivals
FROM fact_tourist_arrivals f
JOIN dim_country c ON f.country_id = c.country_id
GROUP BY c.country_name
ORDER BY total_arrivals DESC;
```

---

## Phase 6 — Analysis in R

Connect R directly to SQL Server rather than re-reading CSVs — this shows you can work across the stack, not just within one tool.

```r
library(DBI)
library(odbc)
library(tidyverse)
library(forecast)

con <- dbConnect(odbc(),
  Driver = "ODBC Driver 17 for SQL Server",
  Server = "localhost",
  Database = "MauritiusTourism",
  Trusted_Connection = "Yes"
)

arrivals <- dbGetQuery(con, "
  SELECT d.full_date, SUM(f.arrivals) AS total_arrivals
  FROM fact_tourist_arrivals f
  JOIN dim_date d ON f.date_id = d.date_id
  GROUP BY d.full_date
  ORDER BY d.full_date
")
```

**6.1 Seasonal decomposition**
```r
ts_arrivals <- ts(arrivals$total_arrivals, start = c(2015, 1), frequency = 12)
decomposed <- stl(ts_arrivals, s.window = "periodic")
plot(decomposed)
```

**6.2 Forecast next 12 months**
```r
fit <- auto.arima(ts_arrivals)
forecast_result <- forecast(fit, h = 12)
plot(forecast_result)

# Export forecast back out for Power BI or documentation
forecast_df <- as.data.frame(forecast_result)
write_csv(forecast_df, "data/processed/arrivals_forecast.csv")
```

**6.3 Optional: write the forecast back to SQL Server**
```r
dbWriteTable(con, "fact_arrivals_forecast", forecast_df, overwrite = TRUE)
```

This gives you a genuine narrative for the dashboard: "here's the historical pattern, here's the seasonal decomposition, here's a 12-month forecast" — much stronger than a static bar chart.

---

## Phase 7 — Build the Power BI Dashboard

**7.1 Connect Power BI directly to SQL Server**
`Get Data → SQL Server` → enter `localhost` and `MauritiusTourism` → choose **Import** mode (simpler for a portfolio project; DirectQuery is unnecessary here) → select your fact and dimension tables plus the forecast table.

**7.2 Build relationships**
Power BI should auto-detect the star schema relationships from your foreign keys. Verify in **Model view** that `dim_date`, `dim_country` connect properly to each fact table (one-to-many, single direction).

**7.3 Suggested pages**

- **Page 1 — Overview**: KPI cards (total arrivals YTD, YoY % change, total receipts), a line chart of arrivals over time, a map or bar chart of top source markets
- **Page 2 — Market Breakdown**: arrivals by country/region, a slicer for year, a table showing YoY growth by market
- **Page 3 — Seasonality & Forecast**: the seasonal pattern (bar chart by month), and your R-generated forecast plotted against historicals
- **Page 4 — Hotel & Receipts**: occupancy rate trend, receipts trend, and receipts-per-tourist calculated measure

**7.4 A few DAX measures worth adding**
```dax
Total Arrivals = SUM(fact_tourist_arrivals[arrivals])

YoY % Change =
VAR CurrentYear = [Total Arrivals]
VAR PriorYear = CALCULATE([Total Arrivals], SAMEPERIODLASTYEAR(dim_date[full_date]))
RETURN DIVIDE(CurrentYear - PriorYear, PriorYear)

Receipts per Tourist = DIVIDE(SUM(fact_tourism_receipts[receipts_mur]), [Total Arrivals])
```

**7.5 Polish**
Give it a consistent color theme (Mauritius flag colors work thematically — red, blue, yellow, green — but keep it subtle, not literal), clear titles, and a text box crediting Statistics Mauritius as the data source with the download date.

---

## Phase 8 — Package It for Your Portfolio

1. **README.md** — explain the project, the pipeline (Python → SQL Server → R → Power BI), a screenshot of the dashboard, and a link to a hosted version if possible
2. **Data dictionary** in `docs/` — document every column, source file, and any assumptions made during cleaning (e.g., how you handled a missing month)
3. **Publish the Power BI report** — if you have a free Power BI account, use **Publish to web** or share a `.pbix` + screenshots/GIF in the repo, since not everyone can open `.pbix` files
4. **Write a short blog post or LinkedIn post** walking through one interesting finding (e.g., "European arrivals recovered faster than Asian arrivals post-COVID") — this demonstrates communication skill, not just technical skill
5. Pin the repo on your GitHub profile and link it from your resume/LinkedIn

---

## Rough Time Budget

| Phase | Estimated time |
|---|---|
| Setup | 1–2 hours |
| Data acquisition | 1 hour |
| Python cleaning | 4–8 hours (this is usually the longest part) |
| SQL Server schema + load | 2–4 hours |
| R analysis | 2–3 hours |
| Power BI dashboard | 3–5 hours |
| Documentation/polish | 2–3 hours |

Total: roughly a focused week of evenings, or 2–3 full days.

---

## Next Steps

Once you've downloaded the actual files, the column structures will dictate some of the exact cleaning code above — the melt/reshape logic especially will need adjusting to match what's really in the spreadsheets. When you get there, share the raw structure (column names, a few sample rows) and the cleaning script can be tailored exactly to it rather than the generic pattern above.
