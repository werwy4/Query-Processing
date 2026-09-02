"""
02_database_crud.py  –  CO2: Database Design & CRUD Operations
==============================================================
Designs and implements a relational SQLite database with:
  - 5 tables: Branch, Customer, Account, Transaction, Loan
  - Full CRUD operations
  - 12 meaningful banking SQL queries
"""

import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')


import sqlite3
import pandas as pd
import os

DB_PATH = "database/banking.db"

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 1 – Schema creation (DDL)
# ══════════════════════════════════════════════════════════════════════════════

DDL = """
-- ─── Branch ──────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS Branch (
    branch_id        TEXT PRIMARY KEY,
    branch_name      TEXT NOT NULL UNIQUE,
    city             TEXT,
    manager          TEXT,
    phone            TEXT,
    established_year INTEGER
);

-- ─── Customer ─────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS Customer (
    customer_id   TEXT PRIMARY KEY,
    name          TEXT NOT NULL,
    email         TEXT,
    phone         TEXT,
    dob           TEXT,
    gender        TEXT,
    city          TEXT,
    branch_id     TEXT REFERENCES Branch(branch_id),
    annual_income REAL,
    credit_score  INTEGER,
    join_date     TEXT
);

-- ─── Account ──────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS Account (
    account_id    TEXT PRIMARY KEY,
    customer_id   TEXT REFERENCES Customer(customer_id),
    account_no    TEXT NOT NULL,
    account_type  TEXT CHECK(account_type IN ('Savings','Current','Fixed Deposit','Recurring Deposit')),
    balance       REAL DEFAULT 0.0,
    open_date     TEXT,
    branch_id     TEXT REFERENCES Branch(branch_id),
    status        TEXT CHECK(status IN ('Active','Inactive','Closed'))
);

-- ─── Transaction ──────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS Txn (
    transaction_id   TEXT PRIMARY KEY,
    account_id       TEXT REFERENCES Account(account_id),
    transaction_type TEXT CHECK(transaction_type IN ('Deposit','Withdrawal','Transfer')),
    amount           REAL,
    transaction_date TEXT,
    description      TEXT,
    channel          TEXT
);

-- ─── Loan ─────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS Loan (
    loan_id        TEXT PRIMARY KEY,
    customer_id    TEXT REFERENCES Customer(customer_id),
    loan_category  TEXT,
    loan_amount    REAL,
    interest_rate  REAL,
    tenure_months  INTEGER,
    start_date     TEXT,
    status         TEXT CHECK(status IN ('Active','Closed','Defaulted'))
);
"""

def section(title: str):
    print("\n" + "═"*70)
    print(f"  {title}")
    print("═"*70)

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 2 – Table creation
# ══════════════════════════════════════════════════════════════════════════════

def create_tables(conn: sqlite3.Connection):
    section("CREATE TABLES")
    conn.executescript(DDL)
    conn.commit()
    # Verify
    cur = conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [r[0] for r in cur.fetchall()]
    print(f"  Tables created: {tables}")

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 3 – Bulk INSERT from cleaned DataFrames
# ══════════════════════════════════════════════════════════════════════════════

def insert_branches(conn, df_branches):
    df = df_branches[["branch_id","branch_name","city","manager","phone","established_year"]].copy()
    df.drop_duplicates(subset="branch_id", inplace=True)
    df.to_sql("Branch", conn, if_exists="append", index=False, method="multi")
    print(f"  ✔ Branch    – {len(df):,} rows inserted")

def insert_customers(conn, df_customers, branch_name_to_id):
    df = df_customers.copy()
    df["branch_id"] = df["branch_name_clean"].map(branch_name_to_id)
    cols = ["customer_id","name","email","phone","dob","gender","city",
            "branch_id","annual_income","credit_score","join_date"]
    # Only keep cols that exist
    cols = [c for c in cols if c in df.columns]
    df = df[cols].drop_duplicates(subset="customer_id")
    df["join_date"] = df["join_date"].astype(str)
    df.to_sql("Customer", conn, if_exists="append", index=False, method="multi")
    print(f"  ✔ Customer  – {len(df):,} rows inserted")

def insert_accounts(conn, df_accounts, branch_name_to_id):
    df = df_accounts.copy()
    df["branch_id"] = df["branch_name_clean"].map(branch_name_to_id)
    # Only keep customers that exist in DB
    cust_in_db = pd.read_sql("SELECT customer_id FROM Customer", conn)["customer_id"].tolist()
    df = df[df["customer_id"].isin(cust_in_db)]
    cols = ["account_id","customer_id","account_no","account_type",
            "balance","open_date","branch_id","status"]
    cols = [c for c in cols if c in df.columns]
    df = df[cols].drop_duplicates(subset="account_id")
    df["open_date"] = df["open_date"].astype(str)
    df.to_sql("Account", conn, if_exists="append", index=False, method="multi")
    print(f"  ✔ Account   – {len(df):,} rows inserted")

def insert_transactions(conn, df_transactions):
    df = df_transactions.copy()
    acc_in_db = pd.read_sql("SELECT account_id FROM Account", conn)["account_id"].tolist()
    df = df[df["account_id"].isin(acc_in_db)]
    cols = ["transaction_id","account_id","transaction_type","amount",
            "transaction_date","description","channel"]
    cols = [c for c in cols if c in df.columns]
    df = df[cols].drop_duplicates(subset="transaction_id")
    df["transaction_date"] = df["transaction_date"].astype(str)
    df.to_sql("Txn", conn, if_exists="append", index=False, method="multi")
    print(f"  ✔ Txn       – {len(df):,} rows inserted")

def insert_loans(conn, df_loans):
    df = df_loans.copy()
    cust_in_db = pd.read_sql("SELECT customer_id FROM Customer", conn)["customer_id"].tolist()
    df = df[df["customer_id"].isin(cust_in_db)]
    cols = ["loan_id","customer_id","loan_category","loan_amount",
            "interest_rate","tenure_months","start_date","status"]
    cols = [c for c in cols if c in df.columns]
    df = df[cols].drop_duplicates(subset="loan_id")
    df["start_date"] = df["start_date"].astype(str)
    df.to_sql("Loan", conn, if_exists="append", index=False, method="multi")
    print(f"  ✔ Loan      – {len(df):,} rows inserted")

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 4 – CRUD demonstrations
# ══════════════════════════════════════════════════════════════════════════════

def demo_crud(conn):
    section("CRUD OPERATIONS DEMO")

    # ── CREATE (single row insert) ───────────────────────────────────────────
    print("\n  [CREATE] Inserting a new test customer…")
    conn.execute("""
        INSERT OR IGNORE INTO Customer
          (customer_id, name, email, phone, gender, city, branch_id,
           annual_income, credit_score, join_date)
        VALUES
          ('CUST99999','Test Customer','test@bank.com','9876543210',
           'Male','Mumbai','BR001',750000,820,'2024-01-01')
    """)
    conn.commit()
    print("    ✔ Customer CUST99999 inserted.")

    # ── READ ─────────────────────────────────────────────────────────────────
    print("\n  [READ] Fetching customer CUST99999…")
    df = pd.read_sql("SELECT * FROM Customer WHERE customer_id='CUST99999'", conn)
    print(df.to_string(index=False))

    # ── UPDATE ───────────────────────────────────────────────────────────────
    print("\n  [UPDATE] Updating credit score for CUST99999…")
    conn.execute("""
        UPDATE Customer SET credit_score=850, annual_income=800000
        WHERE customer_id='CUST99999'
    """)
    conn.commit()
    df = pd.read_sql("SELECT customer_id,name,credit_score,annual_income FROM Customer WHERE customer_id='CUST99999'", conn)
    print(df.to_string(index=False))
    print("    ✔ Credit score updated to 850.")

    # ── DELETE ───────────────────────────────────────────────────────────────
    print("\n  [DELETE] Removing test customer CUST99999…")
    conn.execute("DELETE FROM Customer WHERE customer_id='CUST99999'")
    conn.commit()
    count = conn.execute("SELECT COUNT(*) FROM Customer WHERE customer_id='CUST99999'").fetchone()[0]
    print(f"    ✔ Deleted. Rows remaining with that ID: {count}")

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 5 – Meaningful SQL queries
# ══════════════════════════════════════════════════════════════════════════════

QUERIES = {
    "Q1 – Branches with highest customer count": """
        SELECT b.branch_name, COUNT(c.customer_id) AS customer_count
        FROM Branch b
        LEFT JOIN Customer c ON c.branch_id = b.branch_id
        GROUP BY b.branch_name
        ORDER BY customer_count DESC
        LIMIT 10
    """,
    "Q2 – Account-type distribution": """
        SELECT account_type, COUNT(*) AS count, ROUND(AVG(balance),2) AS avg_balance
        FROM Account
        GROUP BY account_type
        ORDER BY count DESC
    """,
    "Q3 – Monthly transaction volume (2023–2024)": """
        SELECT SUBSTR(transaction_date,1,7) AS month,
               COUNT(*) AS txn_count,
               ROUND(SUM(amount),2) AS total_amount
        FROM Txn
        WHERE transaction_date IS NOT NULL
        GROUP BY month
        ORDER BY month
    """,
    "Q4 – Top 10 customers by total transaction amount": """
        SELECT c.customer_id, c.name,
               COUNT(t.transaction_id) AS txn_count,
               ROUND(SUM(t.amount),2) AS total_amount
        FROM Customer c
        JOIN Account a  ON a.customer_id = c.customer_id
        JOIN Txn    t   ON t.account_id  = a.account_id
        GROUP BY c.customer_id, c.name
        ORDER BY total_amount DESC
        LIMIT 10
    """,
    "Q5 – Loan category distribution with average amount": """
        SELECT loan_category,
               COUNT(*) AS loan_count,
               ROUND(AVG(loan_amount),2) AS avg_loan_amount,
               ROUND(SUM(loan_amount),2) AS total_loan_amount
        FROM Loan
        GROUP BY loan_category
        ORDER BY avg_loan_amount DESC
    """,
    "Q6 – Customers with multiple loans (≥2)": """
        SELECT c.customer_id, c.name, COUNT(l.loan_id) AS loan_count
        FROM Customer c
        JOIN Loan l ON l.customer_id = c.customer_id
        GROUP BY c.customer_id, c.name
        HAVING loan_count >= 2
        ORDER BY loan_count DESC
        LIMIT 10
    """,
    "Q7 – Branches with highest total deposits": """
        SELECT b.branch_name,
               ROUND(SUM(CASE WHEN t.transaction_type='Deposit' THEN t.amount ELSE 0 END),2) AS total_deposits,
               ROUND(SUM(CASE WHEN t.transaction_type='Withdrawal' THEN t.amount ELSE 0 END),2) AS total_withdrawals
        FROM Branch b
        JOIN Customer c ON c.branch_id = b.branch_id
        JOIN Account  a ON a.customer_id = c.customer_id
        JOIN Txn      t ON t.account_id  = a.account_id
        GROUP BY b.branch_name
        ORDER BY total_deposits DESC
    """,
    "Q8 – Income vs. loan amount (top 15 customers)": """
        SELECT c.customer_id, c.name,
               c.annual_income,
               ROUND(AVG(l.loan_amount),2) AS avg_loan_amount
        FROM Customer c
        JOIN Loan l ON l.customer_id = c.customer_id
        WHERE c.annual_income IS NOT NULL
        GROUP BY c.customer_id, c.name, c.annual_income
        ORDER BY c.annual_income DESC
        LIMIT 15
    """,
    "Q9 – Customers with multiple accounts": """
        SELECT c.customer_id, c.name, COUNT(a.account_id) AS account_count
        FROM Customer c
        JOIN Account a ON a.customer_id = c.customer_id
        GROUP BY c.customer_id, c.name
        HAVING account_count > 1
        ORDER BY account_count DESC
        LIMIT 10
    """,
    "Q10 – Account status breakdown per branch": """
        SELECT b.branch_name, a.status, COUNT(*) AS count
        FROM Branch b
        JOIN Customer c ON c.branch_id = b.branch_id
        JOIN Account  a ON a.customer_id = c.customer_id
        GROUP BY b.branch_name, a.status
        ORDER BY b.branch_name, a.status
    """,
    "Q11 – Defaulted loans with customer details": """
        SELECT c.customer_id, c.name, c.credit_score,
               l.loan_id, l.loan_category, l.loan_amount
        FROM Customer c
        JOIN Loan l ON l.customer_id = c.customer_id
        WHERE l.status = 'Defaulted'
        ORDER BY l.loan_amount DESC
        LIMIT 10
    """,
    "Q12 – Transaction channel usage": """
        SELECT channel, COUNT(*) AS txn_count,
               ROUND(SUM(amount),2) AS total_amount
        FROM Txn
        WHERE channel IS NOT NULL
        GROUP BY channel
        ORDER BY txn_count DESC
    """,
}

def run_sql_queries(conn):
    section("BANKING SQL QUERIES")
    results = {}
    for qname, sql in QUERIES.items():
        print(f"\n  ── {qname} ──")
        df = pd.read_sql(sql.strip(), conn)
        print(df.to_string(index=False))
        results[qname] = df
    return results

# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════

def run_database(df_customers, df_accounts, df_transactions, df_loans, df_branches):
    print("\n" + "╔" + "═"*68 + "╗")
    print("║   CO2 – DATABASE DESIGN & CRUD OPERATIONS" + " "*25 + "║")
    print("╚" + "═"*68 + "╝")

    # Remove old DB for fresh run
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")

    create_tables(conn)

    section("BULK DATA INSERTION")
    # Build branch_name → branch_id map from clean data
    branch_map = dict(zip(df_branches["branch_name"], df_branches["branch_id"]))

    insert_branches(conn, df_branches)
    insert_customers(conn, df_customers, branch_map)
    insert_accounts(conn, df_accounts, branch_map)
    insert_transactions(conn, df_transactions)
    insert_loans(conn, df_loans)

    demo_crud(conn)
    query_results = run_sql_queries(conn)

    print("\n  ✔ CO2 – Database & CRUD complete. DB saved at:", DB_PATH)
    return conn, query_results


if __name__ == "__main__":
    import importlib.util, sys, os
    def _load(f):
        p = os.path.join(os.path.dirname(os.path.abspath(__file__)), f)
        s = importlib.util.spec_from_file_location(f, p)
        m = importlib.util.module_from_spec(s)
        sys.modules[f] = m; s.loader.exec_module(m); return m
    dfs = _load("01_data_wrangling.py").run_wrangling()
    cleaned = _load("03_data_cleaning.py").run_cleaning(*dfs)
    run_database(*cleaned)
