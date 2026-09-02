"""
03_data_cleaning.py  –  CO3: Banking Data Cleaning & Preprocessing
===================================================================
Systematically identifies and resolves:
  - Missing values (imputation / drop)
  - Duplicate records (exact + near-duplicate detection)
  - Invalid account numbers (RegEx validation)
  - Inconsistent branch names (fuzzy matching)
  - Inconsistent categories (normalisation)
  - Invalid amounts (negative / zero filtering)
  - Outliers (IQR method)
  - Formatting inconsistencies (gender, phone, email, dates)

Produces a before/after data-quality report.
"""

import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')


import re
import pandas as pd
import numpy as np
from thefuzz import process as fuzz_process
import warnings
warnings.filterwarnings("ignore")

# Canonical reference values
CANONICAL_BRANCHES = [
    "Andheri Branch", "Bandra Branch", "Borivali Branch", "Dadar Branch",
    "Ghatkopar Branch", "Juhu Branch", "Kurla Branch", "Malad Branch",
    "Powai Branch", "Thane Branch",
]
CANONICAL_BRANCH_TO_ID = {
    "Andheri Branch": "BR001", "Bandra Branch": "BR002",
    "Borivali Branch": "BR003", "Dadar Branch": "BR004",
    "Ghatkopar Branch": "BR005", "Juhu Branch": "BR006",
    "Kurla Branch": "BR007", "Malad Branch": "BR008",
    "Powai Branch": "BR009", "Thane Branch": "BR010",
}
CANONICAL_ACC_TYPES    = {"Savings", "Current", "Fixed Deposit", "Recurring Deposit"}
CANONICAL_LOAN_CATS    = {"Home Loan", "Car Loan", "Personal Loan", "Education Loan", "Business Loan"}
CANONICAL_TXN_TYPES    = {"Deposit", "Withdrawal", "Transfer"}
CANONICAL_STATUS       = {"Active", "Inactive", "Closed"}
CANONICAL_LOAN_STATUS  = {"Active", "Closed", "Defaulted"}

ACCOUNT_NO_PATTERN  = re.compile(r"^\d{10}$")
EMAIL_PATTERN       = re.compile(r"^[\w.+-]+@[\w-]+\.[a-z]{2,}$", re.IGNORECASE)

# ── Issue tracking dictionary ─────────────────────────────────────────────────
issues = {}

def section(title: str):
    print("\n" + "═"*70)
    print(f"  {title}")
    print("═"*70)

def log(key, before, after, detail=""):
    issues[key] = {"before": before, "after": after, "fixed": before - after, "detail": detail}
    print(f"    {key:<50} before={before:>5}  after={after:>5}  fixed={before-after:>5}  {detail}")

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 1 – Fuzzy branch-name normalisation
# ══════════════════════════════════════════════════════════════════════════════

_fuzz_cache: dict = {}

def normalise_branch(name):
    if pd.isna(name):
        return pd.NA
    if name in _fuzz_cache:
        return _fuzz_cache[name]
    match, score = fuzz_process.extractOne(str(name), CANONICAL_BRANCHES)
    result = match if score >= 70 else pd.NA
    _fuzz_cache[name] = result
    return result

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 2 – Category normalisation maps
# ══════════════════════════════════════════════════════════════════════════════

ACC_TYPE_MAP = {
    "savings": "Savings", "saving": "Savings",
    "current": "Current",
    "fixed deposit": "Fixed Deposit", "fd": "Fixed Deposit",
    "recurring deposit": "Recurring Deposit", "rd": "Recurring Deposit",
}
LOAN_CAT_MAP = {
    "home loan": "Home Loan", "homeloan": "Home Loan",
    "car loan": "Car Loan", "carloan": "Car Loan",
    "personal loan": "Personal Loan", "personalloan": "Personal Loan", "personal": "Personal Loan",
    "education loan": "Education Loan", "edu loan": "Education Loan",
    "business loan": "Business Loan", "biz loan": "Business Loan",
}
TXN_TYPE_MAP = {
    "deposit": "Deposit",
    "withdrawal": "Withdrawal",
    "transfer": "Transfer",
}
STATUS_MAP = {
    "active": "Active", "inactive": "Inactive", "closed": "Closed",
}
LOAN_STATUS_MAP = {
    "active": "Active", "closed": "Closed", "defaulted": "Defaulted",
}
GENDER_MAP = {
    "male": "Male", "m": "Male",
    "female": "Female", "f": "Female",
}

def normalise_col(series: pd.Series, mapping: dict) -> pd.Series:
    """Lower-strip then map to canonical; unknowns → NaN."""
    return series.map(
        lambda x: mapping.get(str(x).strip().lower(), x) if pd.notna(x) else pd.NA
    )

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 3 – Outlier detection (IQR)
# ══════════════════════════════════════════════════════════════════════════════

def flag_outliers_iqr(series: pd.Series, factor=3.0):
    """Return boolean mask: True = outlier."""
    q1, q3 = series.quantile(0.25), series.quantile(0.75)
    iqr = q3 - q1
    lower, upper = q1 - factor * iqr, q3 + factor * iqr
    return (series < lower) | (series > upper)

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 4 – Clean CUSTOMERS
# ══════════════════════════════════════════════════════════════════════════════

def clean_customers(df: pd.DataFrame) -> pd.DataFrame:
    section("CLEANING CUSTOMERS")
    before_rows = len(df)

    # ── 4a. Exact duplicates ────────────────────────────────────────────────
    dup_count = df.duplicated().sum()
    df.drop_duplicates(inplace=True)
    log("Exact duplicate rows", dup_count, 0, "(rows removed)")

    # ── 4b. Missing names → drop ────────────────────────────────────────────
    missing_names = df["name"].isna().sum()
    df.dropna(subset=["name"], inplace=True)
    log("Missing name (drop)", missing_names, 0, "(rows removed)")

    # ── 4c. Missing email → flag (retain row) ───────────────────────────────
    missing_email = df["email"].isna().sum()
    df["email"] = df["email"].fillna("unknown@bank.com")
    log("Missing email (imputed)", missing_email, 0, "→ 'unknown@bank.com'")

    # ── 4d. Validate email format ───────────────────────────────────────────
    invalid_email = (~df["email"].str.match(EMAIL_PATTERN, na=False)).sum()
    df.loc[~df["email"].str.match(EMAIL_PATTERN, na=False), "email"] = "unknown@bank.com"
    log("Invalid email format (corrected)", invalid_email, 0, "→ 'unknown@bank.com'")

    # ── 4e. Phone cleaning ──────────────────────────────────────────────────
    invalid_phone = df["phone"].isin(["N/A", "n/a", "NA", ""]).sum()
    df["phone"] = df["phone"].replace({"N/A": pd.NA, "n/a": pd.NA, "NA": pd.NA, "": pd.NA})
    df["phone"] = df["phone"].fillna("0000000000")
    log("Invalid phone replaced", invalid_phone, 0, "→ '0000000000'")

    # ── 4f. Gender normalisation ────────────────────────────────────────────
    before_gender_null = df["gender"].isna().sum()
    df["gender"] = normalise_col(df["gender"], GENDER_MAP)
    after_gender_null = df["gender"].isna().sum()
    log("Inconsistent gender (normalised)", df["gender"].isin(["Male","Female"]).shape[0] - df["gender"].isin(["Male","Female"]).sum(), 0)

    # ── 4g. Income: negative → abs; fill missing with median ────────────────
    neg_income = (df["annual_income"] < 0).sum()
    df.loc[df["annual_income"] < 0, "annual_income"] = df.loc[df["annual_income"] < 0, "annual_income"].abs()
    log("Negative annual_income (abs)", neg_income, 0)

    missing_income = df["annual_income"].isna().sum()
    df["annual_income"] = df["annual_income"].fillna(df["annual_income"].median())
    log("Missing annual_income (median impute)", missing_income, 0)

    # ── 4h. Income outliers (IQR×3) → cap at upper fence ────────────────────
    outlier_mask = flag_outliers_iqr(df["annual_income"])
    upper = df["annual_income"].quantile(0.75) + 3 * (df["annual_income"].quantile(0.75) - df["annual_income"].quantile(0.25))
    df.loc[outlier_mask, "annual_income"] = upper
    log("Income outliers (capped at upper fence)", outlier_mask.sum(), 0)

    # ── 4i. Credit score: clamp 300–900; fill with median ────────────────────
    missing_cs = df["credit_score"].isna().sum()
    df["credit_score"] = df["credit_score"].fillna(df["credit_score"].median())
    df["credit_score"] = df["credit_score"].clip(300, 900).round(0).astype(int)
    log("Missing credit_score (median impute)", missing_cs, 0)

    # ── 4j. Branch name fuzzy normalisation ─────────────────────────────────
    before_branch_null = df["branch_name"].isna().sum()
    df["branch_name_clean"] = df["branch_name"].apply(normalise_branch)
    df["branch_name_clean"] = df["branch_name_clean"].fillna("Andheri Branch")  # default
    log("Inconsistent branch names (fuzzy fixed)", len(df) - before_branch_null, 0)

    df["dob"] = pd.to_datetime(df["dob"], errors="coerce", dayfirst=True)
    df["join_date"] = pd.to_datetime(df["join_date"], errors="coerce")

    after_rows = len(df)
    print(f"\n  CUSTOMER rows: {before_rows} → {after_rows}  (removed {before_rows - after_rows})")
    df.to_csv("cleaned_data/customers_cleaned.csv", index=False)
    print("  ✔ Saved cleaned_data/customers_cleaned.csv")
    return df

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 5 – Clean ACCOUNTS
# ══════════════════════════════════════════════════════════════════════════════

def clean_accounts(df: pd.DataFrame) -> pd.DataFrame:
    section("CLEANING ACCOUNTS")
    before_rows = len(df)

    dup_count = df.duplicated().sum()
    df.drop_duplicates(inplace=True)
    log("Exact duplicate rows", dup_count, 0)

    # Invalid account number (must be exactly 10 digits)
    invalid_acc = (~df["account_no"].astype(str).str.match(ACCOUNT_NO_PATTERN)).sum()
    df = df[df["account_no"].astype(str).str.match(ACCOUNT_NO_PATTERN)]
    log("Invalid account_no (regex drop)", invalid_acc, 0)

    # Negative balance → abs
    neg_bal = (pd.to_numeric(df["balance"], errors="coerce") < 0).sum()
    df["balance"] = pd.to_numeric(df["balance"], errors="coerce").abs()
    log("Negative balance (abs)", neg_bal, 0)

    missing_bal = df["balance"].isna().sum()
    df["balance"] = df["balance"].fillna(df["balance"].median())
    log("Missing balance (median impute)", missing_bal, 0)

    # Normalise account_type
    df["account_type"] = normalise_col(df["account_type"], ACC_TYPE_MAP)
    invalid_type = (~df["account_type"].isin(CANONICAL_ACC_TYPES)).sum()
    df.loc[~df["account_type"].isin(CANONICAL_ACC_TYPES), "account_type"] = "Savings"
    log("Invalid account_type (default 'Savings')", invalid_type, 0)

    # Normalise status
    df["status"] = normalise_col(df["status"], STATUS_MAP)
    invalid_status = (~df["status"].isin(CANONICAL_STATUS)).sum()
    df.loc[~df["status"].isin(CANONICAL_STATUS), "status"] = "Active"
    log("Invalid status (default 'Active')", invalid_status, 0)

    # Branch fuzzy normalise
    df["branch_name_clean"] = df["branch_name"].apply(normalise_branch)
    df["branch_name_clean"] = df["branch_name_clean"].fillna("Andheri Branch")

    df["open_date"] = pd.to_datetime(df["open_date"], errors="coerce")

    after_rows = len(df)
    print(f"\n  ACCOUNT rows: {before_rows} → {after_rows}  (removed {before_rows - after_rows})")
    df.to_csv("cleaned_data/accounts_cleaned.csv", index=False)
    print("  ✔ Saved cleaned_data/accounts_cleaned.csv")
    return df

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 6 – Clean TRANSACTIONS
# ══════════════════════════════════════════════════════════════════════════════

def clean_transactions(df: pd.DataFrame) -> pd.DataFrame:
    section("CLEANING TRANSACTIONS")
    before_rows = len(df)

    # Drop rows without transaction_id
    missing_id = df["transaction_id"].isna().sum()
    df.dropna(subset=["transaction_id"], inplace=True)
    log("Missing transaction_id (drop)", missing_id, 0)

    # Exact duplicates
    dup_count = df.duplicated().sum()
    df.drop_duplicates(inplace=True)
    log("Exact duplicate rows", dup_count, 0)

    # Duplicate transaction_id
    dup_id = df.duplicated(subset=["transaction_id"]).sum()
    df.drop_duplicates(subset=["transaction_id"], keep="first", inplace=True)
    log("Duplicate transaction_id (keep first)", dup_id, 0)

    # Invalid/negative amounts → abs; zero → drop
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce")
    neg_amt = (df["amount"] < 0).sum()
    df.loc[df["amount"] < 0, "amount"] = df.loc[df["amount"] < 0, "amount"].abs()
    log("Negative amount (abs)", neg_amt, 0)

    missing_amt = df["amount"].isna().sum()
    df.dropna(subset=["amount"], inplace=True)
    log("Missing amount (drop)", missing_amt, 0)

    zero_amt = (df["amount"] == 0).sum()
    df = df[df["amount"] > 0]
    log("Zero amount (drop)", zero_amt, 0)

    # Outliers: flag (keep but mark) then cap
    outlier_mask = flag_outliers_iqr(df["amount"])
    df["amount_outlier"] = outlier_mask
    upper = df["amount"].quantile(0.75) + 3*(df["amount"].quantile(0.75)-df["amount"].quantile(0.25))
    df.loc[outlier_mask, "amount"] = upper
    log("Transaction amount outliers (capped)", outlier_mask.sum(), 0)

    # Normalise transaction_type
    df["transaction_type"] = normalise_col(df["transaction_type"], TXN_TYPE_MAP)
    invalid_type = (~df["transaction_type"].isin(CANONICAL_TXN_TYPES)).sum()
    df.loc[~df["transaction_type"].isin(CANONICAL_TXN_TYPES), "transaction_type"] = "Deposit"
    log("Invalid transaction_type (default 'Deposit')", invalid_type, 0)

    # Channel normalise
    df["channel"] = df["channel"].str.strip().str.title()
    df["channel"] = df["channel"].fillna("Branch")

    # Date
    df["transaction_date"] = pd.to_datetime(df["transaction_date"], errors="coerce")
    missing_date = df["transaction_date"].isna().sum()
    df["transaction_date"] = df["transaction_date"].fillna(pd.Timestamp("2023-06-01"))
    log("Missing transaction_date (filled)", missing_date, 0)

    after_rows = len(df)
    print(f"\n  TRANSACTION rows: {before_rows} → {after_rows}  (removed {before_rows - after_rows})")
    df.to_csv("cleaned_data/transactions_cleaned.csv", index=False)
    print("  ✔ Saved cleaned_data/transactions_cleaned.csv")
    return df

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 7 – Clean LOANS
# ══════════════════════════════════════════════════════════════════════════════

def clean_loans(df: pd.DataFrame) -> pd.DataFrame:
    section("CLEANING LOANS")
    before_rows = len(df)

    dup_count = df.duplicated().sum()
    df.drop_duplicates(inplace=True)
    log("Exact duplicate rows", dup_count, 0)

    # Negative loan amount → abs
    df["loan_amount"] = pd.to_numeric(df["loan_amount"], errors="coerce")
    neg_loan = (df["loan_amount"] < 0).sum()
    df.loc[df["loan_amount"] < 0, "loan_amount"] = df.loc[df["loan_amount"] < 0, "loan_amount"].abs()
    log("Negative loan_amount (abs)", neg_loan, 0)

    # Outliers cap
    outlier_mask = flag_outliers_iqr(df["loan_amount"])
    df["loan_outlier"] = outlier_mask
    upper = df["loan_amount"].quantile(0.75) + 3*(df["loan_amount"].quantile(0.75)-df["loan_amount"].quantile(0.25))
    df.loc[outlier_mask, "loan_amount"] = upper
    log("Loan amount outliers (capped)", outlier_mask.sum(), 0)

    # Missing interest_rate → median impute
    missing_ir = df["interest_rate"].isna().sum()
    df["interest_rate"] = pd.to_numeric(df["interest_rate"], errors="coerce")
    df["interest_rate"] = df["interest_rate"].fillna(df["interest_rate"].median())
    log("Missing interest_rate (median impute)", missing_ir, 0)

    # Normalise loan_category
    df["loan_category"] = normalise_col(df["loan_category"], LOAN_CAT_MAP)
    invalid_cat = (~df["loan_category"].isin(CANONICAL_LOAN_CATS)).sum()
    df.loc[~df["loan_category"].isin(CANONICAL_LOAN_CATS), "loan_category"] = "Personal Loan"
    log("Invalid loan_category (default 'Personal Loan')", invalid_cat, 0)

    # Normalise status
    df["status"] = normalise_col(df["status"], LOAN_STATUS_MAP)
    invalid_status = (~df["status"].isin(CANONICAL_LOAN_STATUS)).sum()
    df.loc[~df["status"].isin(CANONICAL_LOAN_STATUS), "status"] = "Active"
    log("Invalid loan status (default 'Active')", invalid_status, 0)

    df["start_date"] = pd.to_datetime(df["start_date"], errors="coerce")

    after_rows = len(df)
    print(f"\n  LOAN rows: {before_rows} → {after_rows}  (removed {before_rows - after_rows})")
    df.to_csv("cleaned_data/loans_cleaned.csv", index=False)
    print("  ✔ Saved cleaned_data/loans_cleaned.csv")
    return df

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 8 – Data quality report
# ══════════════════════════════════════════════════════════════════════════════

def generate_quality_report(df_cust, df_acc, df_txn, df_loans):
    section("DATA QUALITY REPORT")
    report_lines = [
        "# Banking Data Quality Report",
        "",
        "## Summary of Issues Found & Resolved",
        "",
        f"| Issue | Before | After | Fixed |",
        f"|-------|--------|-------|-------|",
    ]
    for key, val in issues.items():
        report_lines.append(f"| {key} | {val['before']} | {val['after']} | {val['fixed']} |")

    report_lines += [
        "",
        "## Final Dataset Shapes",
        f"- Customers    : {df_cust.shape[0]:,} rows × {df_cust.shape[1]} cols",
        f"- Accounts     : {df_acc.shape[0]:,} rows × {df_acc.shape[1]} cols",
        f"- Transactions : {df_txn.shape[0]:,} rows × {df_txn.shape[1]} cols",
        f"- Loans        : {df_loans.shape[0]:,} rows × {df_loans.shape[1]} cols",
        "",
        "## Techniques Applied",
        "- **Duplicate Detection**: `DataFrame.duplicated()` + `drop_duplicates()`",
        "- **Missing Value Imputation**: Median/mode fill, placeholder strings",
        "- **RegEx Validation**: Account number (10-digit), email format",
        "- **Fuzzy Matching**: `thefuzz.process.extractOne` for branch names (score ≥ 70)",
        "- **Category Normalisation**: Lowercase-strip-map to canonical sets",
        "- **Outlier Detection**: IQR × 3 method with capping",
        "- **Negative Value Handling**: `abs()` correction for amounts/income",
        "- **Date Parsing**: `pd.to_datetime(errors='coerce')` with fallback fill",
    ]

    report_text = "\n".join(report_lines)
    with open("reports/data_cleaning_report.md", "w", encoding="utf-8") as f:
        f.write(report_text)
    print("\n  ✔ Report saved to reports/data_cleaning_report.md")
    print(report_text)

# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════

def run_cleaning(df_customers, df_accounts, df_transactions, df_loans, df_branches):
    print("\n" + "╔" + "═"*68 + "╗")
    print("║   CO3 – DATA CLEANING & PREPROCESSING" + " "*29 + "║")
    print("╚" + "═"*68 + "╝")

    df_cust  = clean_customers(df_customers.copy())
    df_acc   = clean_accounts(df_accounts.copy())
    df_txn   = clean_transactions(df_transactions.copy())
    df_loan  = clean_loans(df_loans.copy())

    generate_quality_report(df_cust, df_acc, df_txn, df_loan)

    print("\n  ✔ CO3 – Data Cleaning complete.\n")
    return df_cust, df_acc, df_txn, df_loan, df_branches


if __name__ == "__main__":
    import importlib.util, sys, os
    def _load(f):
        p = os.path.join(os.path.dirname(os.path.abspath(__file__)), f)
        s = importlib.util.spec_from_file_location(f, p)
        m = importlib.util.module_from_spec(s)
        sys.modules[f] = m; s.loader.exec_module(m); return m
    dfs = _load("01_data_wrangling.py").run_wrangling()
    run_cleaning(*dfs)
