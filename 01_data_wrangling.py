"""
01_data_wrangling.py  –  CO1: Data Wrangling & Format Handling
================================================================
Loads CSV, JSON, and XML datasets, documents schema/structure,
identifies relationships, and performs initial wrangling.
"""

import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')


import pandas as pd
import json
import xml.etree.ElementTree as ET
import os

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 1 – Utility helpers
# ══════════════════════════════════════════════════════════════════════════════

def section(title: str):
    print("\n" + "═"*70)
    print(f"  {title}")
    print("═"*70)

def schema_report(df: pd.DataFrame, name: str):
    """Print a detailed schema/structure report for a DataFrame."""
    print(f"\n{'─'*50}")
    print(f" Dataset : {name}")
    print(f"{'─'*50}")
    print(f" Shape   : {df.shape[0]:,} rows × {df.shape[1]} columns")
    print(f"\n Column Details:")
    info = pd.DataFrame({
        "Column":    df.columns,
        "Dtype":     df.dtypes.values,
        "Non-Null":  df.notna().sum().values,
        "Null":      df.isna().sum().values,
        "Null %":    (df.isna().sum() / len(df) * 100).round(2).values,
        "Unique":    df.nunique().values,
        "Sample":    [str(df[c].dropna().iloc[0]) if df[c].notna().any() else "N/A"
                      for c in df.columns],
    })
    print(info.to_string(index=False))
    print(f"\n First 3 rows:")
    print(df.head(3).to_string(index=False))

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 2 – Load CSV files
# ══════════════════════════════════════════════════════════════════════════════

def load_csv_files():
    section("LOADING CSV FILES  (customers, accounts, branches)")

    # ── customers ────────────────────────────────────────────────────────────
    df_customers = pd.read_csv(
        "datasets/customers.csv",
        dtype={"credit_score": "object", "annual_income": "object"},
        low_memory=False,
    )
    schema_report(df_customers, "customers.csv")

    # ── accounts ─────────────────────────────────────────────────────────────
    df_accounts = pd.read_csv(
        "datasets/accounts.csv",
        dtype={"balance": "object"},
        low_memory=False,
    )
    schema_report(df_accounts, "accounts.csv")

    # ── branches ─────────────────────────────────────────────────────────────
    df_branches = pd.read_csv("datasets/branches.csv")
    schema_report(df_branches, "branches.csv")

    return df_customers, df_accounts, df_branches

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 3 – Load JSON file
# ══════════════════════════════════════════════════════════════════════════════

def load_json_file():
    section("LOADING JSON FILE  (transactions)")

    with open("datasets/transactions.json", "r", encoding="utf-8") as f:
        raw = json.load(f)

    # Normalize to flat DataFrame
    df_transactions = pd.json_normalize(raw)
    # Replace Python None → pd.NA
    df_transactions = df_transactions.where(df_transactions.notna())

    schema_report(df_transactions, "transactions.json")
    return df_transactions

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 4 – Load XML file
# ══════════════════════════════════════════════════════════════════════════════

def load_xml_file():
    section("LOADING XML FILE  (loans)")

    tree = ET.parse("datasets/loans.xml")
    root = tree.getroot()

    records = []
    for loan in root.findall("Loan"):
        record = {"loan_id": loan.get("id")}
        for child in loan:
            record[child.tag] = child.text
        records.append(record)

    df_loans = pd.DataFrame(records)
    # Convert numeric columns
    for col in ["loan_amount", "interest_rate", "tenure_months"]:
        df_loans[col] = pd.to_numeric(df_loans[col], errors="coerce")

    schema_report(df_loans, "loans.xml")
    return df_loans

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 5 – Relationship identification
# ══════════════════════════════════════════════════════════════════════════════

def identify_relationships(df_customers, df_accounts, df_transactions, df_loans, df_branches):
    section("RELATIONSHIP IDENTIFICATION")

    print("""
  Entity-Relationship Summary
  ────────────────────────────────────────────────────────────────────
  Branch    (branch_id  PK)  ──1:N──  Customer  (branch_name FK)
  Customer  (customer_id PK) ──1:N──  Account   (customer_id FK)
  Account   (account_id  PK) ──1:N──  Transaction(account_id FK)
  Customer  (customer_id PK) ──1:N──  Loan      (customer_id FK)
  ────────────────────────────────────────────────────────────────────
""")

    # Referential integrity checks
    cust_ids = set(df_customers["customer_id"].dropna())
    acc_ids  = set(df_accounts["account_id"].dropna())

    orphan_acc = df_accounts[~df_accounts["customer_id"].isin(cust_ids)]
    orphan_txn = df_transactions[~df_transactions["account_id"].isin(acc_ids)]
    orphan_loan = df_loans[~df_loans["customer_id"].isin(cust_ids)]

    print(f"  Accounts  with no matching Customer  : {len(orphan_acc):,}")
    print(f"  Transactions with no matching Account: {len(orphan_txn):,}")
    print(f"  Loans     with no matching Customer  : {len(orphan_loan):,}")

    print("\n  Cardinality checks:")
    accs_per_cust = df_accounts.groupby("customer_id").size()
    loans_per_cust = df_loans.groupby("customer_id").size()
    txns_per_acc   = df_transactions.groupby("account_id").size()

    print(f"    Accounts per Customer  – min:{accs_per_cust.min()}, "
          f"max:{accs_per_cust.max()}, avg:{accs_per_cust.mean():.2f}")
    print(f"    Loans    per Customer  – min:{loans_per_cust.min()}, "
          f"max:{loans_per_cust.max()}, avg:{loans_per_cust.mean():.2f}")
    print(f"    Txns     per Account   – min:{txns_per_acc.min()}, "
          f"max:{txns_per_acc.max()}, avg:{txns_per_acc.mean():.2f}")

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 6 – Initial wrangling operations
# ══════════════════════════════════════════════════════════════════════════════

def initial_wrangling(df_customers, df_accounts, df_transactions, df_loans):
    section("INITIAL WRANGLING OPERATIONS")

    # ── Strip leading/trailing whitespace from all string columns ────────────
    for df, name in [(df_customers, "customers"), (df_accounts, "accounts"),
                     (df_transactions, "transactions"), (df_loans, "loans")]:
        str_cols = df.select_dtypes(include="object").columns
        df[str_cols] = df[str_cols].apply(lambda c: c.str.strip() if c.dtype == "object" else c)
        print(f"  ✔ Whitespace stripped from {name}")

    # ── Replace empty strings with NaN ──────────────────────────────────────
    for df, name in [(df_customers, "customers"), (df_accounts, "accounts"),
                     (df_transactions, "transactions"), (df_loans, "loans")]:
        before = df.isna().sum().sum()
        df.replace("", pd.NA, inplace=True)
        after = df.isna().sum().sum()
        print(f"  ✔ Empty strings → NaN in {name}  (NaN count: {before} → {after})")

    # ── Date parsing ─────────────────────────────────────────────────────────
    df_customers["join_date"] = pd.to_datetime(df_customers["join_date"], errors="coerce")
    df_accounts["open_date"]  = pd.to_datetime(df_accounts["open_date"],  errors="coerce")
    df_transactions["transaction_date"] = pd.to_datetime(
        df_transactions["transaction_date"], errors="coerce")
    df_loans["start_date"] = pd.to_datetime(df_loans["start_date"], errors="coerce")
    print("  ✔ Date columns parsed to datetime")

    # ── Numeric coercion ─────────────────────────────────────────────────────
    df_customers["annual_income"] = pd.to_numeric(df_customers["annual_income"], errors="coerce")
    df_customers["credit_score"]  = pd.to_numeric(df_customers["credit_score"],  errors="coerce")
    df_accounts["balance"]        = pd.to_numeric(df_accounts["balance"],         errors="coerce")
    df_transactions["amount"]     = pd.to_numeric(df_transactions["amount"],      errors="coerce")
    print("  ✔ Numeric columns coerced")

    print("\n  Wrangling complete – DataFrames ready for cleaning pipeline.")
    return df_customers, df_accounts, df_transactions, df_loans

# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════

def run_wrangling():
    print("\n" + "╔" + "═"*68 + "╗")
    print("║   CO1 – DATA WRANGLING & FORMAT HANDLING" + " "*26 + "║")
    print("╚" + "═"*68 + "╝")

    df_customers, df_accounts, df_branches = load_csv_files()
    df_transactions = load_json_file()
    df_loans = load_xml_file()
    identify_relationships(df_customers, df_accounts, df_transactions, df_loans, df_branches)
    df_customers, df_accounts, df_transactions, df_loans = \
        initial_wrangling(df_customers, df_accounts, df_transactions, df_loans)

    print("\n  ✔ CO1 – Data Wrangling complete.\n")
    return df_customers, df_accounts, df_transactions, df_loans, df_branches


if __name__ == "__main__":
    run_wrangling()
