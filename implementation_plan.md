# Banking Customer Data Management, Query Processing & Analytics System

## Overview
A complete end-to-end Python banking data pipeline covering data wrangling, SQLite database CRUD, cleaning, analysis, and visualization — covering all 6 COs in the rubric.

---

## Project Structure

```
Team project/
├── datasets/                   # Raw datasets
│   ├── customers.csv
│   ├── accounts.csv
│   ├── transactions.json
│   ├── loans.xml
│   └── branches.csv
├── cleaned_data/               # Exported cleaned CSVs
│   ├── customers_cleaned.csv
│   ├── accounts_cleaned.csv
│   ├── transactions_cleaned.csv
│   └── loans_cleaned.csv
├── database/
│   └── banking.db              # SQLite database
├── visualizations/             # Saved PNG charts
│   └── *.png
├── reports/
│   └── data_cleaning_report.md
├── 01_data_wrangling.py        # CO1 – Load & understand datasets
├── 02_database_crud.py         # CO2 – Schema + CRUD + SQL queries
├── 03_data_cleaning.py         # CO3 – Cleaning pipeline
├── 04_data_analysis.py         # CO4 – EDA & analytical queries
├── 05_visualizations.py        # CO5 – Matplotlib/Pandas charts
├── 06_insights.py              # Insights & recommendations
├── main.py                     # Orchestrates all modules end-to-end
└── requirements.txt
```

---

## Proposed Changes

### Component 1 – Raw Datasets

#### [NEW] `datasets/customers.csv`
~200 rows with deliberate issues: missing names/emails, duplicates, inconsistent branch names.

#### [NEW] `datasets/accounts.csv`
Account records with invalid account numbers, inconsistent account types, missing balances.

#### [NEW] `datasets/transactions.json`
Transaction records in JSON with incorrect amounts, outliers, duplicate IDs.

#### [NEW] `datasets/loans.xml`
Loan records in XML with inconsistent loan categories, missing interest rates.

#### [NEW] `datasets/branches.csv`
Branch master data with inconsistent naming (e.g., "North Branch" vs "north branch").

---

### Component 2 – CO1: Data Wrangling (`01_data_wrangling.py`)
- Load CSV with `pandas.read_csv`
- Load JSON with `pandas.read_json`
- Load XML with `xml.etree.ElementTree` → DataFrame
- Print schema (dtypes, shape, head, null counts)
- Identify relationships between tables via foreign keys
- Output: structured summary report

---

### Component 3 – CO2: Database & CRUD (`02_database_crud.py`)
- SQLite database via `sqlite3`
- 5 tables: `Branch`, `Customer`, `Account`, `Transaction`, `Loan`
- Full CRUD: insert bulk records, select with filters, update records, delete stale records
- 10+ meaningful SQL queries (branch stats, top customers, etc.)

**ER Relationships:**
- Branch → Customer (1:N)
- Customer → Account (1:N)
- Account → Transaction (1:N)
- Customer → Loan (1:N)

---

### Component 4 – CO3: Data Cleaning (`03_data_cleaning.py`)
Techniques applied:
- **Missing values**: median/mode imputation, forward fill
- **Duplicates**: `df.duplicated()` detection and drop
- **Invalid account numbers**: RegEx validation (`^\d{10}$`)
- **Inconsistent branch names**: fuzzy matching (`thefuzz` library)
- **Inconsistent categories**: `.str.lower().str.strip()` normalization
- **Invalid amounts**: negative/zero transaction filtering
- **Outliers**: IQR method on transaction amounts and loan amounts
- **Formatting**: phone/email standardization with RegEx
- Before/after counts documented → `reports/data_cleaning_report.md`

---

### Component 5 – CO4: Data Analysis (`04_data_analysis.py`)
Analytical queries answering all 9 required questions:
1. Branches with highest customer count
2. Account type with highest transaction volume
3. Customers with unusually high transaction activity (z-score)
4. Income vs. loan amount relationship (Pearson correlation)
5. Customers with multiple loans/accounts
6. Branches with highest total deposits
7. Monthly transaction trends
8. Loan categories with highest average loan amount
9. Correlation matrix across numeric attributes
10. Outlier identification using IQR/z-score

---

### Component 6 – CO5: Visualizations (`05_visualizations.py`)
10 charts saved as PNG files:
1. Customer distribution by branch (bar chart)
2. Account-type distribution (pie chart)
3. Monthly transaction trends (line chart)
4. Deposit vs withdrawal comparison (grouped bar)
5. Loan distribution by category (bar chart)
6. Branch-wise transaction volume (horizontal bar)
7. Income vs loan amount (scatter plot with regression)
8. Transaction amount distribution (histogram + KDE)
9. Correlation heatmap (seaborn)
10. Outlier visualization (box plot)

Each chart has a title, labels, and printed interpretation.

---

### Component 7 – Insights (`06_insights.py`)
5+ actionable insights derived from data and visualizations.

---

### Component 8 – Orchestrator (`main.py`)
Runs all modules in sequence with timing and status logging.

---

## Open Questions

> [!IMPORTANT]
> **Dataset size**: Should the synthetic datasets have ~200 rows per table, or do you have actual data files to use? If you have real data, share them and I'll adapt the pipeline.

> [!IMPORTANT]
> **Database engine**: The plan uses **SQLite** (no installation needed). Should I switch to MySQL/PostgreSQL instead?

> [!NOTE]
> **Libraries**: The plan uses `pandas`, `matplotlib`, `seaborn`, `thefuzz`, `scipy`, `numpy`, `lxml`. I'll generate a `requirements.txt` and install them.

---

## Verification Plan

### Automated
- Run `main.py` end-to-end and confirm zero errors
- Verify all 5 tables are created and populated
- Verify all 10 charts are saved to `visualizations/`

### Manual
- Open `banking.db` with DB Browser for SQLite to inspect schema
- Review `reports/data_cleaning_report.md` for before/after counts
- Review saved PNGs for correctness
