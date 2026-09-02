"""
04_data_analysis.py  –  CO4: Banking Data Exploration & Analysis
================================================================
Answers 9 required analytical questions using joins, grouping,
correlation, outlier analysis, and aggregation on cleaned data.
"""

import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')


import sqlite3
import pandas as pd
import numpy as np
from scipy import stats
import warnings
warnings.filterwarnings("ignore")

DB_PATH = "database/banking.db"

def section(title: str):
    print("\n" + "═"*70)
    print(f"  {title}")
    print("═"*70)

def load_data(conn):
    """Load all tables into DataFrames for in-memory analysis."""
    df_cust  = pd.read_sql("SELECT * FROM Customer", conn)
    df_acc   = pd.read_sql("SELECT * FROM Account",  conn)
    df_txn   = pd.read_sql("SELECT * FROM Txn",      conn)
    df_loan  = pd.read_sql("SELECT * FROM Loan",     conn)
    df_br    = pd.read_sql("SELECT * FROM Branch",   conn)
    return df_cust, df_acc, df_txn, df_loan, df_br

# ══════════════════════════════════════════════════════════════════════════════
# Q1 – Which branches have the highest number of customers?
# ══════════════════════════════════════════════════════════════════════════════
def q1_branch_customer_count(conn):
    section("Q1 – Branches with Highest Number of Customers")
    sql = """
        SELECT b.branch_name,
               COUNT(DISTINCT c.customer_id) AS customer_count
        FROM Branch b
        LEFT JOIN Customer c ON c.branch_id = b.branch_id
        GROUP BY b.branch_name
        ORDER BY customer_count DESC
    """
    df = pd.read_sql(sql, conn)
    print(df.to_string(index=False))
    print("\n  Insight: Top 3 branches by customer count are most resource-intensive.")
    return df

# ══════════════════════════════════════════════════════════════════════════════
# Q2 – Which account type has the highest transaction volume?
# ══════════════════════════════════════════════════════════════════════════════
def q2_account_type_txn_volume(conn):
    section("Q2 – Account Type with Highest Transaction Volume")
    sql = """
        SELECT a.account_type,
               COUNT(t.transaction_id)   AS txn_count,
               ROUND(SUM(t.amount), 2)   AS total_volume,
               ROUND(AVG(t.amount), 2)   AS avg_amount
        FROM Account a
        JOIN Txn t ON t.account_id = a.account_id
        GROUP BY a.account_type
        ORDER BY total_volume DESC
    """
    df = pd.read_sql(sql, conn)
    print(df.to_string(index=False))
    print("\n  Insight: The dominant account type drives the highest transaction throughput.")
    return df

# ══════════════════════════════════════════════════════════════════════════════
# Q3 – Which customers have unusually high transaction activity? (z-score)
# ══════════════════════════════════════════════════════════════════════════════
def q3_high_activity_customers(conn):
    section("Q3 – Customers with Unusually High Transaction Activity (z-score > 2)")
    sql = """
        SELECT c.customer_id, c.name,
               COUNT(t.transaction_id)  AS txn_count,
               ROUND(SUM(t.amount), 2)  AS total_amount
        FROM Customer c
        JOIN Account a ON a.customer_id = c.customer_id
        JOIN Txn     t ON t.account_id  = a.account_id
        GROUP BY c.customer_id, c.name
        ORDER BY txn_count DESC
    """
    df = pd.read_sql(sql, conn)
    df["txn_zscore"] = stats.zscore(df["txn_count"].fillna(0))
    df["amt_zscore"] = stats.zscore(df["total_amount"].fillna(0))
    high_activity = df[(df["txn_zscore"] > 2) | (df["amt_zscore"] > 2)].copy()
    high_activity = high_activity.sort_values("txn_zscore", ascending=False)
    print(f"\n  High-activity customers (z > 2):  {len(high_activity)}")
    print(high_activity[["customer_id","name","txn_count","total_amount","txn_zscore"]].to_string(index=False))
    print("\n  Insight: These customers may require enhanced KYC review or VIP service.")
    return high_activity, df

# ══════════════════════════════════════════════════════════════════════════════
# Q4 – What is the relationship between customer income and loan amount?
# ══════════════════════════════════════════════════════════════════════════════
def q4_income_vs_loan(conn):
    section("Q4 – Income vs. Loan Amount Correlation")
    sql = """
        SELECT c.customer_id, c.annual_income, AVG(l.loan_amount) AS avg_loan
        FROM Customer c
        JOIN Loan l ON l.customer_id = c.customer_id
        WHERE c.annual_income IS NOT NULL AND l.loan_amount IS NOT NULL
        GROUP BY c.customer_id, c.annual_income
    """
    df = pd.read_sql(sql, conn)
    if len(df) >= 2:
        r, p = stats.pearsonr(df["annual_income"], df["avg_loan"])
        print(f"\n  Pearson r = {r:.4f},  p-value = {p:.4e}")
        if abs(r) > 0.5:
            print(f"  → Strong {'positive' if r>0 else 'negative'} correlation.")
        elif abs(r) > 0.2:
            print(f"  → Moderate correlation.")
        else:
            print(f"  → Weak correlation.")
    print("\n  Insight: Correlation guides appropriate loan amount offers by income band.")
    return df

# ══════════════════════════════════════════════════════════════════════════════
# Q5 – Which customers have multiple loans / accounts?
# ══════════════════════════════════════════════════════════════════════════════
def q5_multi_loan_account(conn):
    section("Q5 – Customers with Multiple Loans or Accounts")
    sql_loans = """
        SELECT c.customer_id, c.name,
               COUNT(DISTINCT l.loan_id)   AS loan_count,
               COUNT(DISTINCT a.account_id) AS account_count
        FROM Customer c
        LEFT JOIN Loan    l ON l.customer_id = c.customer_id
        LEFT JOIN Account a ON a.customer_id = c.customer_id
        GROUP BY c.customer_id, c.name
        HAVING loan_count >= 2 OR account_count >= 2
        ORDER BY loan_count DESC, account_count DESC
        LIMIT 15
    """
    df = pd.read_sql(sql_loans, conn)
    print(df.to_string(index=False))
    total_multi = len(df)
    print(f"\n  {total_multi} customers hold multiple loans and/or accounts.")
    print("  Insight: Multi-product customers are strong cross-sell candidates.")
    return df

# ══════════════════════════════════════════════════════════════════════════════
# Q6 – Which branches have the highest total deposits?
# ══════════════════════════════════════════════════════════════════════════════
def q6_branch_deposits(conn):
    section("Q6 – Branches with Highest Total Deposits")
    sql = """
        SELECT b.branch_name,
               ROUND(SUM(CASE WHEN t.transaction_type='Deposit'
                               THEN t.amount ELSE 0 END), 2) AS total_deposits,
               ROUND(SUM(CASE WHEN t.transaction_type='Withdrawal'
                               THEN t.amount ELSE 0 END), 2) AS total_withdrawals,
               COUNT(DISTINCT c.customer_id)                  AS customers
        FROM Branch b
        JOIN Customer c ON c.branch_id = b.branch_id
        JOIN Account  a ON a.customer_id = c.customer_id
        JOIN Txn      t ON t.account_id  = a.account_id
        GROUP BY b.branch_name
        ORDER BY total_deposits DESC
    """
    df = pd.read_sql(sql, conn)
    print(df.to_string(index=False))
    print("\n  Insight: High-deposit branches are liquidity anchors of the bank.")
    return df

# ══════════════════════════════════════════════════════════════════════════════
# Q7 – Monthly transaction trends
# ══════════════════════════════════════════════════════════════════════════════
def q7_monthly_trends(conn):
    section("Q7 – Monthly Transaction Trends (2023–2024)")
    sql = """
        SELECT SUBSTR(transaction_date, 1, 7)   AS month,
               transaction_type,
               COUNT(*)                          AS txn_count,
               ROUND(SUM(amount), 2)             AS total_amount
        FROM Txn
        WHERE transaction_date IS NOT NULL
          AND SUBSTR(transaction_date,1,4) IN ('2023','2024')
        GROUP BY month, transaction_type
        ORDER BY month, transaction_type
    """
    df = pd.read_sql(sql, conn)
    pivot = df.pivot_table(index="month", columns="transaction_type",
                           values="txn_count", aggfunc="sum", fill_value=0)
    print(pivot.to_string())
    print("\n  Insight: Identify peak months for staffing and liquidity management.")
    return df

# ══════════════════════════════════════════════════════════════════════════════
# Q8 – Which loan categories have the highest average loan amount?
# ══════════════════════════════════════════════════════════════════════════════
def q8_loan_categories(conn):
    section("Q8 – Loan Categories by Average Loan Amount")
    sql = """
        SELECT loan_category,
               COUNT(*)                         AS loan_count,
               ROUND(AVG(loan_amount), 2)        AS avg_amount,
               ROUND(MIN(loan_amount), 2)        AS min_amount,
               ROUND(MAX(loan_amount), 2)        AS max_amount,
               ROUND(SUM(loan_amount), 2)        AS total_amount
        FROM Loan
        GROUP BY loan_category
        ORDER BY avg_amount DESC
    """
    df = pd.read_sql(sql, conn)
    print(df.to_string(index=False))
    print("\n  Insight: High-average-loan categories need stronger credit risk controls.")
    return df

# ══════════════════════════════════════════════════════════════════════════════
# Q9 – Correlation between numeric attributes
# ══════════════════════════════════════════════════════════════════════════════
def q9_correlation_analysis(conn):
    section("Q9 – Correlation Analysis (Numeric Attributes)")
    cust  = pd.read_sql("SELECT customer_id, annual_income, credit_score FROM Customer", conn)
    loans = pd.read_sql("""
        SELECT customer_id,
               AVG(loan_amount)   AS avg_loan_amount,
               AVG(interest_rate) AS avg_interest_rate,
               COUNT(loan_id)     AS loan_count
        FROM Loan GROUP BY customer_id
    """, conn)
    accs  = pd.read_sql("""
        SELECT customer_id,
               AVG(balance) AS avg_balance,
               COUNT(account_id) AS account_count
        FROM Account GROUP BY customer_id
    """, conn)

    merged = cust.merge(loans, on="customer_id", how="left") \
                 .merge(accs,  on="customer_id", how="left")

    numeric_cols = ["annual_income","credit_score","avg_loan_amount",
                    "avg_interest_rate","loan_count","avg_balance","account_count"]
    numeric_cols = [c for c in numeric_cols if c in merged.columns]
    corr = merged[numeric_cols].corr().round(3)

    print("\n  Correlation Matrix:")
    print(corr.to_string())
    print("\n  Key observations:")
    print("   • annual_income ↔ avg_loan_amount  :", f"{corr.loc['annual_income','avg_loan_amount']:.3f}" if 'avg_loan_amount' in corr else "N/A")
    print("   • credit_score ↔ avg_interest_rate :", f"{corr.loc['credit_score','avg_interest_rate']:.3f}" if 'avg_interest_rate' in corr else "N/A")
    print("   • avg_balance  ↔ avg_loan_amount   :", f"{corr.loc['avg_balance','avg_loan_amount']:.3f}" if 'avg_loan_amount' in corr and 'avg_balance' in corr else "N/A")
    print("\n  Insight: Correlated attributes can feed a credit-scoring or loan-approval model.")
    return corr, merged

# ══════════════════════════════════════════════════════════════════════════════
# Q10 – Transaction / Loan Outliers (IQR)
# ══════════════════════════════════════════════════════════════════════════════
def q10_outlier_analysis(conn):
    section("Q10 – Significant Transaction & Loan Outliers")
    df_txn  = pd.read_sql("SELECT * FROM Txn",  conn)
    df_loan = pd.read_sql("SELECT * FROM Loan", conn)

    def iqr_bounds(series):
        q1, q3 = series.quantile(0.25), series.quantile(0.75)
        iqr = q3 - q1
        return q1 - 1.5*iqr, q3 + 1.5*iqr

    t_lo, t_hi = iqr_bounds(df_txn["amount"])
    txn_out = df_txn[(df_txn["amount"] < t_lo) | (df_txn["amount"] > t_hi)]
    print(f"\n  Transaction outliers  (IQR×1.5): {len(txn_out):,}  "
          f"| range [{t_lo:,.0f} – {t_hi:,.0f}]")
    print(txn_out[["transaction_id","account_id","transaction_type","amount"]].head(8).to_string(index=False))

    l_lo, l_hi = iqr_bounds(df_loan["loan_amount"])
    loan_out = df_loan[(df_loan["loan_amount"] < l_lo) | (df_loan["loan_amount"] > l_hi)]
    print(f"\n  Loan amount outliers  (IQR×1.5): {len(loan_out):,}  "
          f"| range [{l_lo:,.0f} – {l_hi:,.0f}]")
    print(loan_out[["loan_id","customer_id","loan_category","loan_amount"]].head(8).to_string(index=False))

    print("\n  Insight: Outlier transactions should trigger fraud-detection workflows.")
    return txn_out, loan_out

# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════

def run_analysis():
    print("\n" + "╔" + "═"*68 + "╗")
    print("║   CO4 – DATA EXPLORATION & ANALYSIS" + " "*31 + "║")
    print("╚" + "═"*68 + "╝")

    conn = sqlite3.connect(DB_PATH)

    results = {}
    results["q1"]  = q1_branch_customer_count(conn)
    results["q2"]  = q2_account_type_txn_volume(conn)
    results["q3_high"], results["q3_all"] = q3_high_activity_customers(conn)
    results["q4"]  = q4_income_vs_loan(conn)
    results["q5"]  = q5_multi_loan_account(conn)
    results["q6"]  = q6_branch_deposits(conn)
    results["q7"]  = q7_monthly_trends(conn)
    results["q8"]  = q8_loan_categories(conn)
    results["q9_corr"], results["q9_merged"] = q9_correlation_analysis(conn)
    results["q10_txn"], results["q10_loan"]  = q10_outlier_analysis(conn)

    conn.close()
    print("\n  ✔ CO4 – Data Analysis complete.\n")
    return results


if __name__ == "__main__":
    run_analysis()
