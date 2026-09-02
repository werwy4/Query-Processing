# Banking Customer Data Management, Query Processing & Analytics System
**Course Project Report | Course Code: DSA0504**  
**Domain:** Financial Services & Retail Banking Analytics  

---

## 1. Executive Summary

Modern retail banking institutions manage massive volumes of heterogeneous data across disparate legacy systems—ranging from relational branch databases and JSON transaction streams to XML credit and loan logs. Inefficiencies in data integration, poor quality control, and unstandardised schemas often result in operational bottlenecks, inaccurate financial reporting, and heightened fraud risk.

This project delivers an end-to-end Python-based Data Wrangling, Relational Query Processing, and Business Intelligence pipeline. Designed to comply with all six Course Outcomes (CO1 to CO6), the system automates multi-source ingestion, enforces strict data cleaning standardisation (imputation, regex validation, fuzzy matching, and IQR outlier capping), models a 5-entity relational SQLite database, executes advanced analytical SQL queries, generates 10 graphical visualisations, and synthesises 6 strategic business insights.

### Key Performance Highlights:
- **Processed Datasets**: Ingested 5 heterogeneous sources (CSV, JSON, XML).
- **Data Quality Improvement**: Resolved **400+ data anomalies**, achieving **100% relational integrity** and zero unhandled nulls across clean datasets.
- **Database Architecture**: Implemented an indexed 5-table SQLite relational database (`Branch`, `Customer`, `Account`, `Transaction`, `Loan`).
- **Analytics & BI**: Executed 9 core analytical queries and generated 10 high-resolution charts.
- **Pipeline Execution**: Complete end-to-end execution finalized in **~6.5 seconds**.

---

## 2. System Architecture & Relational ER Model

The system follows a modular architecture separating raw ingestion, schema definitions, cleaning pipelines, query execution, visualization engines, and reporting modules.

```
                    ┌─────────────────────────────────────────┐
                    │ Raw Heterogeneous Data Sources          │
                    │ (.csv, .json, .xml)                     │
                    └────────────────────┬────────────────────┘
                                         │
                                         ▼
                    ┌─────────────────────────────────────────┐
                    │ CO1: Data Wrangling & Schema Parsing    │
                    └────────────────────┬────────────────────┘
                                         │
                                         ▼
                    ┌─────────────────────────────────────────┐
                    │ CO3: Data Cleaning & Standardisation    │
                    │ (RegEx, Fuzzy Matching, IQR Capping)    │
                    └────────────────────┬────────────────────┘
                                         │
                                         ▼
                    ┌─────────────────────────────────────────┐
                    │ CO2: SQLite Relational Database Engine  │
                    │ (Tables, Foreign Keys, CRUD, Indexing)  │
                    └────────────────────┬────────────────────┘
                                         │
                 ┌───────────────────────┴───────────────────────┐
                 ▼                                               ▼
┌─────────────────────────────────┐             ┌─────────────────────────────────┐
│ CO4: SQL EDA & Analytical Queries│             │ CO5: Graphical Visualization    │
└────────────────┬────────────────┘             └────────────────┬────────────────┘
                 │                                               │
                 └───────────────────────┬───────────────────────┘
                                         │
                                         ▼
                    ┌─────────────────────────────────────────┐
                    │ CO6: Strategic Insights & Decisions     │
                    └─────────────────────────────────────────┘
```

### Entity-Relationship Schema Overview

The relational structure models core retail banking operations across five primary entities:

1. **Branch (`Branch`)**: Stores branch master data (ID, name, region, manager, contact). Primary Key: `branch_id`.
2. **Customer (`Customer`)**: Stores demographic, contact, and credit score details. Foreign Key: `branch_id` → `Branch(branch_id)`.
3. **Account (`Account`)**: Stores customer bank account types, balances, and opening dates. Foreign Key: `customer_id` → `Customer(customer_id)`.
4. **Transaction (`Txn`)**: Captures high-frequency transactions (Deposit, Withdrawal, Transfer) across multiple channels. Foreign Key: `account_id` → `Account(account_id)`.
5. **Loan (`Loan`)**: Contains credit portfolio records (Personal, Home, Auto, Education, Business), interest rates, and loan statuses. Foreign Key: `customer_id` → `Customer(customer_id)`.

---

## 3. Data Ingestion & Wrangling (CO1)

The system handles multi-format data ingestion using native and open-source Python libraries:

- **CSV Ingestion**: Ingested `customers.csv`, `accounts.csv`, and `branches.csv` using `pandas.read_csv()`.
- **JSON Ingestion**: Parsed semi-structured `transactions.json` with nested channel attributes using `pandas.read_json()`.
- **XML Parsing**: Extracted tree-structured `loans.xml` using Python's `xml.etree.ElementTree` module and flattened nodes into tabular DataFrames.

### Raw Data Ingest Summary Table

| Source File | Format | Records Ingested | Key Anomaly Types Observed |
| :--- | :---: | :---: | :--- |
| `customers.csv` | CSV | 220 | Missing names, inconsistent branch spellings, negative incomes |
| `accounts.csv` | CSV | 280 | Invalid non-10-digit account numbers, missing balances |
| `transactions.json` | JSON | 600 | Missing transaction dates/IDs, negative amounts, outliers |
| `loans.xml` | XML | 187 | Negative loan amounts, missing interest rates, unstripped text |
| `branches.csv` | CSV | 10 | Case inconsistencies ("mumbai south" vs "Mumbai South") |

---

## 4. Data Cleaning Pipeline & Quality Report (CO3)

Data cleaning is orchestrated in `03_data_cleaning.py`. Every field undergoes strict validation before being passed into the relational database.

### Applied Cleaning Methodologies:
1. **RegEx Pattern Validation**: Enforced exact 10-digit numerical patterns (`^\d{10}$`) for account numbers; malformed accounts were purged.
2. **Fuzzy String Standardisation**: Branch names were normalized using Levenshtein distance similarity scoring via `thefuzz.process.extractOne()` against canonical branch names (similarity threshold $\ge 70$).
3. **Imputation Strategies**:
   - Continuous numerical features (`annual_income`, `credit_score`, `balance`, `interest_rate`) were imputed using the **median**.
   - Categorical missing items were imputed using **mode** or default canonical categories.
4. **Outlier Detection & Capping**: Applied non-parametric **Interquartile Range (IQR $\times 3.0$)** bounds to transaction amounts and loan amounts to cap extreme values without removing valid financial records.
5. **Sign Correction**: Corrected negative financial balances, transaction amounts, and incomes using absolute transformation `abs()`.

### Comprehensive Data Quality Audit Matrix

| Cleaning Issue / Anomaly | Pre-Clean Count | Post-Clean Count | Fixed Action Taken |
| :--- | :---: | :---: | :--- |
| Missing Customer Names | 8 | 0 | Dropped record |
| Missing Email Addresses | 10 | 0 | Imputed formatted placeholder |
| Inconsistent Gender Labels | 38 | 0 | Standardised to 'Male' / 'Female' / 'Other' |
| Negative Annual Incomes | 4 | 0 | Applied `abs()` transformation |
| Missing Annual Incomes | 5 | 0 | Imputed median income |
| Income Outliers | 5 | 0 | Capped at upper IQR fence |
| Missing Credit Scores | 11 | 0 | Imputed median credit score |
| Misspelled Branch Names | 212 | 0 | Fuzzy matched to canonical branch list |
| Invalid Account Numbers | 16 | 0 | Filtered out via RegEx pattern (`^\d{10}$`) |
| Negative Account Balances | 8 | 0 | Applied `abs()` transformation |
| Missing Account Balances | 9 | 0 | Imputed median account balance |
| Missing Transaction IDs | 11 | 0 | Dropped corrupt records |
| Negative Transaction Amounts | 21 | 0 | Applied `abs()` transformation |
| Missing Transaction Amounts | 22 | 0 | Dropped corrupt records |
| Transaction Outliers | 20 | 0 | Capped at upper IQR fence |
| Missing Transaction Dates | 23 | 0 | Imputed with standard timestamp fallback |
| Negative Loan Amounts | 4 | 0 | Applied `abs()` transformation |
| Loan Amount Outliers | 3 | 0 | Capped at upper IQR fence |
| Missing Interest Rates | 11 | 0 | Imputed median interest rate |

### Final Clean Dataset Shapes
- **Customers**: 212 rows $\times$ 12 columns
- **Accounts**: 264 rows $\times$ 9 columns
- **Transactions**: 567 rows $\times$ 8 columns
- **Loans**: 180 rows $\times$ 9 columns

---

## 5. Database Design & SQL Operations (CO2)

The clean records are loaded into an SQLite database (`database/banking.db`) defined in `02_database_crud.py`.

### Schema Definition & Indexing SQL
```sql
CREATE TABLE IF NOT EXISTS Branch (
    branch_id TEXT PRIMARY KEY,
    branch_name TEXT NOT NULL,
    city TEXT NOT NULL,
    manager TEXT,
    contact_phone TEXT
);

CREATE TABLE IF NOT EXISTS Customer (
    customer_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT,
    phone TEXT,
    gender TEXT,
    dob DATE,
    city TEXT,
    annual_income REAL,
    credit_score INTEGER,
    branch_id TEXT,
    FOREIGN KEY (branch_id) REFERENCES Branch(branch_id)
);

CREATE TABLE IF NOT EXISTS Account (
    account_id TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL,
    account_number TEXT UNIQUE NOT NULL,
    account_type TEXT NOT NULL,
    balance REAL DEFAULT 0.0,
    currency TEXT DEFAULT 'INR',
    status TEXT DEFAULT 'Active',
    opened_date DATE,
    FOREIGN KEY (customer_id) REFERENCES Customer(customer_id)
);

CREATE TABLE IF NOT EXISTS Txn (
    transaction_id TEXT PRIMARY KEY,
    account_id TEXT NOT NULL,
    transaction_type TEXT NOT NULL,
    amount REAL NOT NULL,
    transaction_date TIMESTAMP NOT NULL,
    channel TEXT,
    status TEXT DEFAULT 'Completed',
    FOREIGN KEY (account_id) REFERENCES Account(account_id)
);

CREATE TABLE IF NOT EXISTS Loan (
    loan_id TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL,
    loan_category TEXT NOT NULL,
    loan_amount REAL NOT NULL,
    interest_rate REAL NOT NULL,
    tenure_months INTEGER NOT NULL,
    start_date DATE,
    status TEXT DEFAULT 'Active',
    FOREIGN KEY (customer_id) REFERENCES Customer(customer_id)
);

-- Performance Indexes
CREATE INDEX IF NOT EXISTS idx_cust_branch ON Customer(branch_id);
CREATE INDEX IF NOT EXISTS idx_acc_cust ON Account(customer_id);
CREATE INDEX IF NOT EXISTS idx_txn_acc ON Txn(account_id);
CREATE INDEX IF NOT EXISTS idx_loan_cust ON Loan(customer_id);
```

---

## 6. Exploratory Data Analysis & Analytical Findings (CO4)

Analytical queries in `04_data_analysis.py` evaluate performance metrics across branches, customer segments, and loan products.

### Q1. Branch Customer Load
**Top Branches by Customer Count:**
1. **Juhu Branch**: 27 customers
2. **Thane Branch**: 26 customers
3. **Bandra Branch**: 25 customers
4. **Borivali Branch**: 25 customers
5. **Malad Branch**: 23 customers

### Q2. Transaction Volume by Account Type

| Account Type | Total Transactions | Total Volume (₹) | Avg Transaction (₹) |
| :--- | :---: | :---: | :---: |
| **Savings Account** | 224 | ₹11,351,200.45 | ₹50,675.00 |
| **Current Account** | 185 | ₹9,842,110.10 | ₹53,200.59 |
| **Salary Account** | 158 | ₹7,412,300.20 | ₹46,913.29 |

### Q3. High-Activity Customers ($Z \ge 1.5$)
Identified **8 VIP / high-frequency customers** whose transaction volume significantly exceeds normal population distributions:
- **Nidhi Kala (`CUST00209`)**: 14 transactions, ₹382,628.33 total volume.
- **Triya Bora (`CUST00206`)**: 10 transactions, ₹282,737.26 total volume.
- **Wridesh Handa (`CUST00113`)**: 10 transactions, ₹246,520.98 total volume.

### Q4. Income vs. Loan Amount Relationship
- **Pearson Correlation Coefficient**: $r = 0.0894$ ($p = 0.333$).
- **Finding**: Indicates a weak linear correlation, suggesting that loan approvals are influenced by parameters beyond raw income (e.g., credit score, collateral).

### Q5. Multi-Product Holding Analysis
- **Finding**: 42 customers hold 2+ accounts or loans simultaneously, representing the primary segment for cross-selling.

### Q6. Branch Liquidity & Deposit vs. Withdrawal Ratios

| Branch Name | Deposits (₹ M) | Withdrawals (₹ M) | Net Flow (₹ M) | Withdrawal/Deposit Ratio |
| :--- | :---: | :---: | :---: | :---: |
| **Powai Branch** | ₹0.23 M | ₹0.81 M | **-₹0.58 M** | **3.52** |
| **Andheri Branch** | ₹0.26 M | ₹0.40 M | **-₹0.14 M** | **1.54** |
| **Ghatkopar Branch**| ₹0.31 M | ₹0.45 M | **-₹0.14 M** | **1.45** |
| **Thane Branch** | ₹0.72 M | ₹0.52 M | **+₹0.20 M** | **0.72** |
| **Malad Branch** | ₹0.53 M | ₹0.39 M | **+₹0.14 M** | **0.74** |

### Q7. Loan Portfolio & Risk Performance

| Loan Category | Loan Count | Avg Loan (₹ Lakh) | Total Volume (₹ Cr) | Default Count |
| :--- | :---: | :---: | :---: | :---: |
| **Personal Loan** | 43 | ₹28.15 L | ₹12.10 Cr | **7** |
| **Education Loan**| 39 | ₹23.57 L | ₹9.19 Cr | 4 |
| **Home Loan** | 33 | ₹27.31 L | ₹9.01 Cr | 2 |
| **Car Loan** | 32 | ₹22.72 L | ₹7.27 Cr | 3 |
| **Business Loan** | 29 | ₹26.62 L | ₹7.72 Cr | 5 |

---

## 7. Data Visualization Suite (CO5)

The pipeline generates 10 high-resolution charts in `visualizations/`:

1. `01_customer_distribution_by_branch.png`: Bar chart highlighting branch customer footprint.
2. `02_account_type_distribution.png`: Pie chart illustrating account composition.
3. `03_monthly_transaction_trends.png`: Multi-line time series chart showing monthly deposits vs withdrawals.
4. `04_deposit_vs_withdrawal_comparison.png`: Grouped bar chart depicting net flows per branch.
5. `05_loan_distribution_by_category.png`: Bar chart of loan distribution.
6. `06_branch_transaction_volume.png`: Horizontal bar chart of total financial throughput.
7. `07_income_vs_loan_scatter.png`: Scatter plot with ordinary least squares (OLS) trendline.
8. `08_transaction_amount_distribution.png`: Combined Histogram and Kernel Density Estimation (KDE) plot.
9. `09_correlation_heatmap.png`: Correlation matrix heatmap across numeric features (`income`, `credit_score`, `balance`, `loan_amount`).
10. `10_outlier_boxplot.png`: Box plot visualizing IQR outlier distribution.

---

## 10. Conclusion

The Banking Customer Data Management, Query Processing & Analytics System provides a complete framework for financial data integration and business intelligence. By eliminating data quality anomalies, establishing relational schema integrity, and extracting data-driven insights, the platform equips financial stakeholders with the tools needed to optimize branch performance, manage credit risk, and enhance customer retention.
