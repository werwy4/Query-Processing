"""
06_insights.py  –  Banking Insights & Recommendations
======================================================
Derives 6 actionable banking insights from the processed data
and prints a structured report.
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

DB_PATH = "database/banking.db"

def section(title):
    print("\n" + "═"*70)
    print(f"  {title}")
    print("═"*70)

def run_insights():
    print("\n" + "╔" + "═"*68 + "╗")
    print("║   BANKING INSIGHTS & RECOMMENDATIONS" + " "*30 + "║")
    print("╚" + "═"*68 + "╝")

    conn = sqlite3.connect(DB_PATH)

    # ── Insight 1: Branches needing additional resources ─────────────────────
    section("INSIGHT 1 – Branches Requiring Additional Banking Resources")
    df = pd.read_sql("""
        SELECT b.branch_name,
               COUNT(DISTINCT c.customer_id)   AS customers,
               COUNT(DISTINCT t.transaction_id) AS transactions,
               ROUND(SUM(t.amount)/1e6, 2)      AS volume_M
        FROM Branch b
        JOIN Customer c ON c.branch_id = b.branch_id
        JOIN Account  a ON a.customer_id = c.customer_id
        JOIN Txn      t ON t.account_id  = a.account_id
        GROUP BY b.branch_name ORDER BY customers DESC
    """, conn)
    high_load = df[df["customers"] > df["customers"].quantile(0.7)]
    print(high_load.to_string(index=False))
    print(f"""
  RECOMMENDATION:
  ► Branches '{high_load['branch_name'].iloc[0]}' and '{high_load['branch_name'].iloc[1] if len(high_load)>1 else "N/A"}'
    exceed the 70th-percentile customer load.
  ► Allocate 2+ additional tellers, expand ATM capacity, and consider
    opening satellite offices to reduce congestion.
    """)

    # ── Insight 2: High-activity customer segments ────────────────────────────
    section("INSIGHT 2 – Customer Segments with High Transaction Activity")
    df2 = pd.read_sql("""
        SELECT c.customer_id, c.name, c.annual_income, c.credit_score,
               COUNT(t.transaction_id) AS txn_count,
               ROUND(SUM(t.amount),2)  AS total_txn_amount
        FROM Customer c
        JOIN Account a ON a.customer_id = c.customer_id
        JOIN Txn     t ON t.account_id  = a.account_id
        GROUP BY c.customer_id
    """, conn)
    df2["z"] = stats.zscore(df2["txn_count"].fillna(0))
    vip = df2[df2["z"] > 1.5].sort_values("total_txn_amount", ascending=False)
    print(f"  High-activity customers (z > 1.5): {len(vip)}")
    print(vip[["customer_id","name","annual_income","txn_count","total_txn_amount"]].head(8).to_string(index=False))
    print(f"""
  RECOMMENDATION:
  ► {len(vip)} customers show significantly above-average transaction volumes.
  ► Offer them Priority Banking / Wealth Management services and dedicated
    relationship managers to improve retention and cross-sell.
    """)

    # ── Insight 3: Unusual / suspicious transaction patterns ──────────────────
    section("INSIGHT 3 – Unusual Transaction Patterns (Fraud Risk)")
    df3 = pd.read_sql("""
        SELECT t.transaction_id, t.account_id, t.transaction_type,
               t.amount, t.transaction_date, t.channel
        FROM Txn t
        WHERE t.amount IS NOT NULL
        ORDER BY t.amount DESC
    """, conn)
    q3 = df3["amount"].quantile(0.75)
    iqr = q3 - df3["amount"].quantile(0.25)
    suspicious = df3[df3["amount"] > q3 + 3*iqr]
    print(f"  Suspicious high-value transactions (IQR×3): {len(suspicious)}")
    print(suspicious[["transaction_id","account_id","transaction_type","amount","channel"]].head(10).to_string(index=False))
    print(f"""
  RECOMMENDATION:
  ► {len(suspicious)} transactions exceed the IQR×3 threshold and should be
    automatically flagged for AML/fraud review.
  ► Implement real-time transaction monitoring with alerts for amounts
    above ₹{q3+3*iqr:,.0f} and require second-factor authentication.
    """)

    # ── Insight 4: Loan categories with high demand ───────────────────────────
    section("INSIGHT 4 – Loan Categories with High Demand & Risk Exposure")
    df4 = pd.read_sql("""
        SELECT loan_category,
               COUNT(*)                      AS loan_count,
               ROUND(AVG(loan_amount)/1e5,2) AS avg_lakh,
               ROUND(SUM(loan_amount)/1e7,2) AS total_crore,
               SUM(CASE WHEN status='Defaulted' THEN 1 ELSE 0 END) AS defaults
        FROM Loan GROUP BY loan_category ORDER BY loan_count DESC
    """, conn)
    print(df4.to_string(index=False))
    top_cat = df4.iloc[0]["loan_category"]
    default_cat = df4.sort_values("defaults", ascending=False).iloc[0]["loan_category"]
    print(f"""
  RECOMMENDATION:
  ► '{top_cat}' has the highest demand — increase dedicated loan officers.
  ► '{default_cat}' has the most defaults — tighten credit scoring thresholds
    and require collateral documentation for approvals above ₹10 lakh.
    """)

    # ── Insight 5: Income–loan correlation for product design ─────────────────
    section("INSIGHT 5 – Income–Loan Relationship for Product Personalisation")
    df5 = pd.read_sql("""
        SELECT c.annual_income, AVG(l.loan_amount) avg_loan
        FROM Customer c JOIN Loan l ON l.customer_id = c.customer_id
        WHERE c.annual_income IS NOT NULL AND l.loan_amount IS NOT NULL
        GROUP BY c.customer_id, c.annual_income
    """, conn)
    r, p = stats.pearsonr(df5["annual_income"], df5["avg_loan"])
    # Income bands
    df5["income_band"] = pd.cut(df5["annual_income"],
        bins=[0, 50000, 150000, 500000, np.inf],
        labels=["<50K","50K–1.5L","1.5L–5L",">5L"])
    band_summary = df5.groupby("income_band", observed=True)["avg_loan"].agg(["mean","count"])
    print(f"  Pearson r = {r:.4f}, p = {p:.2e}")
    print(band_summary.to_string())
    print(f"""
  RECOMMENDATION:
  ► Pearson r = {r:.3f} confirms {'a meaningful' if abs(r)>0.2 else 'a weak'} positive income–loan relationship.
  ► Design income-band-specific loan products:
      • <₹50K  → micro/personal loans ≤ ₹2L
      • ₹50K–1.5L → personal/car loans ₹2L–₹10L
      • >₹1.5L → home/business loans ≥ ₹10L
  ► Use credit score as a secondary gate to reduce default risk.
    """)

    # ── Insight 6: Branch deposit health ─────────────────────────────────────
    section("INSIGHT 6 – Branch Deposit Health & Net Cash Flow")
    df6 = pd.read_sql("""
        SELECT b.branch_name,
               ROUND(SUM(CASE WHEN t.transaction_type='Deposit'    THEN t.amount ELSE 0 END)/1e6,2) AS dep_M,
               ROUND(SUM(CASE WHEN t.transaction_type='Withdrawal' THEN t.amount ELSE 0 END)/1e6,2) AS wdl_M
        FROM Branch b
        JOIN Customer c ON c.branch_id = b.branch_id
        JOIN Account  a ON a.customer_id = c.customer_id
        JOIN Txn      t ON t.account_id = a.account_id
        GROUP BY b.branch_name
    """, conn)
    df6["net_flow_M"] = df6["dep_M"] - df6["wdl_M"]
    df6["ratio"] = (df6["wdl_M"] / df6["dep_M"]).round(3)
    at_risk = df6[df6["ratio"] > 0.85]
    print(df6.sort_values("net_flow_M").to_string(index=False))
    print(f"""
  RECOMMENDATION:
  ► {len(at_risk)} branch(es) have a withdrawal/deposit ratio > 85% — indicating
    net outflow pressure.
  ► Introduce fixed-deposit promotion campaigns and salary-account tie-ups
    in these branches to rebuild deposit buffers.
    """)

    conn.close()

    summary = """
╔══════════════════════════════════════════════════════════════════════╗
║              SUMMARY OF 6 BANKING INSIGHTS                          ║
╠══════════════════════════════════════════════════════════════════════╣
║  1. Overloaded branches → staff up + expand ATMs                    ║
║  2. VIP customers (z>1.5) → priority banking products               ║
║  3. High-amount outlier transactions → AML / fraud alerts           ║
║  4. High-demand loan categories → more officers + tighter credit    ║
║  5. Income–loan correlation → personalised loan product tiers       ║
║  6. Net-outflow branches → FD promotion + salary-account drives     ║
╚══════════════════════════════════════════════════════════════════════╝
"""
    print(summary)
    print("  ✔ Insights complete.\n")


if __name__ == "__main__":
    run_insights()
