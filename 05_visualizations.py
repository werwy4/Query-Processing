"""
05_visualizations.py  –  CO5: Banking Data Visualizations
==========================================================
Creates 10 Matplotlib/Seaborn charts saved as PNG files,
each with a printed interpretation.
"""

import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')


import sqlite3
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")          # Non-interactive backend for file saving
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns
from scipy import stats
import warnings
warnings.filterwarnings("ignore")

DB_PATH    = "database/banking.db"
VIZ_DIR    = "visualizations/"

# ── Global style ─────────────────────────────────────────────────────────────
PALETTE    = ["#2563EB","#7C3AED","#059669","#DC2626","#D97706",
              "#0891B2","#BE185D","#65A30D","#EA580C","#6366F1"]
BG_COLOR   = "#0F172A"
GRID_COLOR = "#1E293B"
TEXT_COLOR = "#F1F5F9"
ACCENT     = "#38BDF8"

def apply_dark_style():
    plt.rcParams.update({
        "figure.facecolor":  BG_COLOR,
        "axes.facecolor":    GRID_COLOR,
        "axes.edgecolor":    "#334155",
        "axes.labelcolor":   TEXT_COLOR,
        "axes.titlecolor":   TEXT_COLOR,
        "xtick.color":       TEXT_COLOR,
        "ytick.color":       TEXT_COLOR,
        "text.color":        TEXT_COLOR,
        "grid.color":        "#1E3A5F",
        "grid.linestyle":    "--",
        "grid.alpha":        0.4,
        "font.family":       "DejaVu Sans",
        "font.size":         10,
        "axes.titlesize":    13,
        "axes.titleweight":  "bold",
        "legend.facecolor":  "#1E293B",
        "legend.edgecolor":  "#334155",
        "legend.labelcolor": TEXT_COLOR,
    })

def save(fig, name, interp):
    path = VIZ_DIR + name
    fig.savefig(path, dpi=150, bbox_inches="tight", facecolor=BG_COLOR)
    plt.close(fig)
    print(f"\n  ✔ Saved: {path}")
    print(f"  📌 Interpretation: {interp}")

# ══════════════════════════════════════════════════════════════════════════════
# Chart 1 – Customer Distribution by Branch (Horizontal Bar)
# ══════════════════════════════════════════════════════════════════════════════
def chart1_customer_by_branch(conn):
    df = pd.read_sql("""
        SELECT b.branch_name, COUNT(c.customer_id) AS customer_count
        FROM Branch b LEFT JOIN Customer c ON c.branch_id = b.branch_id
        GROUP BY b.branch_name ORDER BY customer_count DESC
    """, conn)

    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.barh(df["branch_name"], df["customer_count"],
                   color=PALETTE[:len(df)], edgecolor="none", height=0.65)
    ax.bar_label(bars, padding=4, color=TEXT_COLOR, fontsize=9)
    ax.set_xlabel("Number of Customers")
    ax.set_title("Customer Distribution by Branch")
    ax.invert_yaxis()
    ax.grid(axis="x")
    fig.tight_layout()
    save(fig, "01_customer_by_branch.png",
         "Branches with more customers need higher staffing levels and ATM capacity.")
    return df

# ══════════════════════════════════════════════════════════════════════════════
# Chart 2 – Account-Type Distribution (Donut Chart)
# ══════════════════════════════════════════════════════════════════════════════
def chart2_account_type_dist(conn):
    df = pd.read_sql("""
        SELECT account_type, COUNT(*) AS count FROM Account
        GROUP BY account_type ORDER BY count DESC
    """, conn)

    fig, ax = plt.subplots(figsize=(7, 7))
    pie_result = ax.pie(
        df["count"], labels=df["account_type"],
        colors=PALETTE[:len(df)],
        autopct="%1.1f%%", startangle=140,
        wedgeprops={"width": 0.55, "edgecolor": BG_COLOR, "linewidth": 2},
        textprops={"color": TEXT_COLOR},
    )
    autotexts = pie_result[2] if len(pie_result) > 2 else []
    for at in autotexts:
        at.set_fontsize(10); at.set_color(BG_COLOR); at.set_fontweight("bold")
    ax.set_title("Account-Type Distribution", pad=20)
    centre = plt.Circle((0,0), 0.35, color=BG_COLOR)
    ax.add_patch(centre)
    fig.tight_layout()
    save(fig, "02_account_type_distribution.png",
         "Savings accounts dominate, indicating a retail-heavy customer base.")
    return df

# ══════════════════════════════════════════════════════════════════════════════
# Chart 3 – Monthly Transaction Trends (Multi-Line)
# ══════════════════════════════════════════════════════════════════════════════
def chart3_monthly_trends(conn):
    df = pd.read_sql("""
        SELECT SUBSTR(transaction_date,1,7) AS month,
               transaction_type, COUNT(*) AS txn_count
        FROM Txn
        WHERE transaction_date IS NOT NULL
          AND SUBSTR(transaction_date,1,4) IN ('2023','2024')
        GROUP BY month, transaction_type
        ORDER BY month
    """, conn)

    pivot = df.pivot_table(index="month", columns="transaction_type",
                           values="txn_count", fill_value=0)

    fig, ax = plt.subplots(figsize=(14, 5))
    for i, col in enumerate(pivot.columns):
        ax.plot(pivot.index, pivot[col], marker="o", linewidth=2.2,
                color=PALETTE[i], label=col, markersize=5)

    ax.set_xlabel("Month"); ax.set_ylabel("Transaction Count")
    ax.set_title("Monthly Transaction Trends (2023–2024)")
    ax.legend(); ax.grid(True)
    ax.tick_params(axis="x", rotation=45)
    fig.tight_layout()
    save(fig, "03_monthly_transaction_trends.png",
         "Peaks in certain months indicate seasonal demand; plan liquidity accordingly.")
    return pivot

# ══════════════════════════════════════════════════════════════════════════════
# Chart 4 – Deposit vs Withdrawal by Branch (Grouped Bar)
# ══════════════════════════════════════════════════════════════════════════════
def chart4_deposit_withdrawal(conn):
    df = pd.read_sql("""
        SELECT b.branch_name,
               ROUND(SUM(CASE WHEN t.transaction_type='Deposit'
                              THEN t.amount ELSE 0 END)/1e6,2) AS deposits_M,
               ROUND(SUM(CASE WHEN t.transaction_type='Withdrawal'
                              THEN t.amount ELSE 0 END)/1e6,2) AS withdrawals_M
        FROM Branch b
        JOIN Customer c ON c.branch_id = b.branch_id
        JOIN Account  a ON a.customer_id = c.customer_id
        JOIN Txn      t ON t.account_id = a.account_id
        GROUP BY b.branch_name ORDER BY deposits_M DESC
    """, conn)

    x = np.arange(len(df))
    width = 0.38
    fig, ax = plt.subplots(figsize=(13, 6))
    b1 = ax.bar(x - width/2, df["deposits_M"],    width, label="Deposits",    color=PALETTE[2], alpha=0.9)
    b2 = ax.bar(x + width/2, df["withdrawals_M"], width, label="Withdrawals", color=PALETTE[3], alpha=0.9)
    ax.bar_label(b1, fmt="%.1f", padding=3, color=TEXT_COLOR, fontsize=8)
    ax.bar_label(b2, fmt="%.1f", padding=3, color=TEXT_COLOR, fontsize=8)
    ax.set_xticks(x); ax.set_xticklabels(df["branch_name"], rotation=30, ha="right")
    ax.set_ylabel("Amount (₹ Millions)"); ax.set_title("Branch-wise Deposit vs Withdrawal (₹ M)")
    ax.legend(); ax.grid(axis="y")
    fig.tight_layout()
    save(fig, "04_deposit_withdrawal_comparison.png",
         "Branches where withdrawals approach deposits may need liquidity injections.")
    return df

# ══════════════════════════════════════════════════════════════════════════════
# Chart 5 – Loan Distribution by Category (Bar + Count annotation)
# ══════════════════════════════════════════════════════════════════════════════
def chart5_loan_distribution(conn):
    df = pd.read_sql("""
        SELECT loan_category,
               COUNT(*) AS loan_count,
               ROUND(AVG(loan_amount)/1e5, 2) AS avg_loan_lakh
        FROM Loan GROUP BY loan_category ORDER BY loan_count DESC
    """, conn)

    fig, ax1 = plt.subplots(figsize=(9, 5))
    bars = ax1.bar(df["loan_category"], df["loan_count"],
                   color=PALETTE[:len(df)], edgecolor="none", alpha=0.9)
    ax1.bar_label(bars, padding=3, color=TEXT_COLOR, fontsize=9)
    ax1.set_ylabel("Number of Loans"); ax1.set_xlabel("Loan Category")
    ax1.set_title("Loan Distribution by Category")

    ax2 = ax1.twinx()
    ax2.plot(df["loan_category"], df["avg_loan_lakh"], "o--",
             color=PALETTE[6], linewidth=2.2, markersize=8, label="Avg Loan (₹ Lakh)")
    ax2.set_ylabel("Avg Loan Amount (₹ Lakh)", color=PALETTE[6])
    ax2.tick_params(axis="y", labelcolor=PALETTE[6])
    ax2.legend(loc="upper right")
    ax1.grid(axis="y")
    fig.tight_layout()
    save(fig, "05_loan_distribution_by_category.png",
         "Home and Business loans carry the highest average values — key risk segments.")
    return df

# ══════════════════════════════════════════════════════════════════════════════
# Chart 6 – Branch-wise Transaction Volume (Stacked Bar)
# ══════════════════════════════════════════════════════════════════════════════
def chart6_branch_txn_volume(conn):
    df = pd.read_sql("""
        SELECT b.branch_name, t.transaction_type,
               COUNT(t.transaction_id) AS txn_count
        FROM Branch b
        JOIN Customer c ON c.branch_id = b.branch_id
        JOIN Account  a ON a.customer_id = c.customer_id
        JOIN Txn      t ON t.account_id = a.account_id
        GROUP BY b.branch_name, t.transaction_type
        ORDER BY b.branch_name
    """, conn)

    pivot = df.pivot_table(index="branch_name", columns="transaction_type",
                           values="txn_count", fill_value=0)

    fig, ax = plt.subplots(figsize=(12, 6))
    bottom = np.zeros(len(pivot))
    for i, col in enumerate(pivot.columns):
        ax.bar(pivot.index, pivot[col], bottom=bottom,
               label=col, color=PALETTE[i], alpha=0.9)
        bottom += pivot[col].values

    ax.set_xlabel("Branch"); ax.set_ylabel("Transaction Count")
    ax.set_title("Branch-wise Transaction Volume (Stacked)")
    ax.legend(); ax.grid(axis="y")
    ax.tick_params(axis="x", rotation=35)
    fig.tight_layout()
    save(fig, "06_branch_transaction_volume.png",
         "Branches with disproportionately high withdrawals warrant cash-flow monitoring.")
    return pivot

# ══════════════════════════════════════════════════════════════════════════════
# Chart 7 – Income vs. Loan Amount (Scatter + Regression)
# ══════════════════════════════════════════════════════════════════════════════
def chart7_income_vs_loan(conn):
    df = pd.read_sql("""
        SELECT c.annual_income, AVG(l.loan_amount) AS avg_loan
        FROM Customer c
        JOIN Loan l ON l.customer_id = c.customer_id
        WHERE c.annual_income IS NOT NULL AND l.loan_amount IS NOT NULL
        GROUP BY c.customer_id, c.annual_income
    """, conn)

    fig, ax = plt.subplots(figsize=(9, 6))
    ax.scatter(df["annual_income"]/1e3, df["avg_loan"]/1e5,
               alpha=0.55, color=PALETTE[0], edgecolors="none", s=50, label="Customer")

    # Regression line
    m, b, r, p, _ = stats.linregress(df["annual_income"], df["avg_loan"])
    x_line = np.linspace(df["annual_income"].min(), df["annual_income"].max(), 200)
    ax.plot(x_line/1e3, (m*x_line+b)/1e5, color=PALETTE[3],
            linewidth=2.2, label=f"Regression (r={r:.3f})")

    ax.set_xlabel("Annual Income (₹ Thousands)")
    ax.set_ylabel("Avg Loan Amount (₹ Lakh)")
    ax.set_title("Income vs. Average Loan Amount")
    ax.legend(); ax.grid(True)
    fig.tight_layout()
    save(fig, "07_income_vs_loan_amount.png",
         f"Pearson r={r:.3f}: customers with higher income tend to take larger loans, "
         f"guiding loan-limit policies.")
    return df

# ══════════════════════════════════════════════════════════════════════════════
# Chart 8 – Transaction Amount Distribution (Histogram + KDE)
# ══════════════════════════════════════════════════════════════════════════════
def chart8_txn_distribution(conn):
    df = pd.read_sql("SELECT amount FROM Txn WHERE amount IS NOT NULL", conn)
    amounts = df["amount"]

    fig, ax = plt.subplots(figsize=(10, 5))
    n, bins, patches = ax.hist(amounts, bins=60, color=PALETTE[1], alpha=0.7,
                                edgecolor="none", density=True, label="Frequency")
    # KDE
    kde_x = np.linspace(amounts.min(), amounts.max(), 400)
    kde   = stats.gaussian_kde(amounts)
    ax.plot(kde_x, kde(kde_x), color=PALETTE[4], linewidth=2.5, label="KDE")

    ax.axvline(amounts.mean(),   color=PALETTE[2], linestyle="--", linewidth=1.8, label=f"Mean ₹{amounts.mean():,.0f}")
    ax.axvline(amounts.median(), color=PALETTE[3], linestyle="-.", linewidth=1.8, label=f"Median ₹{amounts.median():,.0f}")

    ax.set_xlabel("Transaction Amount (₹)")
    ax.set_ylabel("Density"); ax.set_title("Transaction Amount Distribution")
    ax.legend(); ax.grid(axis="y")
    fig.tight_layout()
    save(fig, "08_transaction_amount_distribution.png",
         "Right-skewed distribution confirms most transactions are small-value; "
         "the long tail represents high-value outliers needing scrutiny.")
    return amounts

# ══════════════════════════════════════════════════════════════════════════════
# Chart 9 – Correlation Heatmap
# ══════════════════════════════════════════════════════════════════════════════
def chart9_correlation_heatmap(conn):
    cust  = pd.read_sql("SELECT customer_id, annual_income, credit_score FROM Customer", conn)
    loans = pd.read_sql("""
        SELECT customer_id, AVG(loan_amount) avg_loan, AVG(interest_rate) avg_ir,
               COUNT(loan_id) loan_count FROM Loan GROUP BY customer_id
    """, conn)
    accs = pd.read_sql("""
        SELECT customer_id, AVG(balance) avg_balance,
               COUNT(account_id) account_count FROM Account GROUP BY customer_id
    """, conn)
    merged = cust.merge(loans, on="customer_id", how="left") \
                 .merge(accs,  on="customer_id", how="left")

    numeric = ["annual_income","credit_score","avg_loan","avg_ir",
               "loan_count","avg_balance","account_count"]
    numeric = [c for c in numeric if c in merged.columns]
    corr = merged[numeric].corr()

    fig, ax = plt.subplots(figsize=(10, 8))
    mask = np.triu(np.ones_like(corr, dtype=bool))
    sns.heatmap(corr, mask=mask, annot=True, fmt=".2f", cmap="coolwarm",
                center=0, square=True, linewidths=0.5,
                cbar_kws={"shrink": 0.75}, ax=ax,
                annot_kws={"size": 9})
    ax.set_title("Correlation Heatmap – Key Banking Attributes")
    fig.tight_layout()
    save(fig, "09_correlation_heatmap.png",
         "Strong income–loan correlation validates income as a primary credit-limit driver.")
    return corr

# ══════════════════════════════════════════════════════════════════════════════
# Chart 10 – Outlier Visualization (Box Plots)
# ══════════════════════════════════════════════════════════════════════════════
def chart10_outlier_boxplot(conn):
    df_txn  = pd.read_sql("SELECT amount, transaction_type FROM Txn  WHERE amount IS NOT NULL",  conn)
    df_loan = pd.read_sql("SELECT loan_amount, loan_category FROM Loan WHERE loan_amount IS NOT NULL", conn)

    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    # Box plot – transaction by type
    types = df_txn["transaction_type"].unique()
    data_txn = [df_txn[df_txn["transaction_type"]==t]["amount"].values for t in types]
    bp1 = axes[0].boxplot(data_txn, labels=types, patch_artist=True,
                           medianprops={"color": "white", "linewidth":2},
                           flierprops={"marker":"o","markerfacecolor":PALETTE[3],"markersize":4,"alpha":0.5})
    for patch, color in zip(bp1["boxes"], PALETTE):
        patch.set_facecolor(color); patch.set_alpha(0.75)
    axes[0].set_title("Transaction Amount Outliers by Type")
    axes[0].set_ylabel("Amount (₹)"); axes[0].grid(axis="y")

    # Box plot – loan by category
    cats = df_loan["loan_category"].unique()
    data_loan = [df_loan[df_loan["loan_category"]==c]["loan_amount"].values for c in cats]
    bp2 = axes[1].boxplot(data_loan, labels=cats, patch_artist=True,
                           medianprops={"color": "white", "linewidth":2},
                           flierprops={"marker":"o","markerfacecolor":PALETTE[3],"markersize":4,"alpha":0.5})
    for patch, color in zip(bp2["boxes"], PALETTE[2:]):
        patch.set_facecolor(color); patch.set_alpha(0.75)
    axes[1].set_title("Loan Amount Outliers by Category")
    axes[1].set_ylabel("Loan Amount (₹)"); axes[1].grid(axis="y")
    axes[1].tick_params(axis="x", rotation=20)

    fig.suptitle("Outlier Analysis – Transactions & Loans", fontsize=14, fontweight="bold")
    fig.tight_layout()
    save(fig, "10_outlier_boxplot.png",
         "Flier points above whiskers represent anomalous transactions/loans "
         "that require fraud or risk review.")

# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════

def run_visualizations():
    print("\n" + "╔" + "═"*68 + "╗")
    print("║   CO5 – DATA VISUALIZATIONS" + " "*40 + "║")
    print("╚" + "═"*68 + "╝")

    apply_dark_style()
    conn = sqlite3.connect(DB_PATH)

    chart1_customer_by_branch(conn)
    chart2_account_type_dist(conn)
    chart3_monthly_trends(conn)
    chart4_deposit_withdrawal(conn)
    chart5_loan_distribution(conn)
    chart6_branch_txn_volume(conn)
    chart7_income_vs_loan(conn)
    chart8_txn_distribution(conn)
    chart9_correlation_heatmap(conn)
    chart10_outlier_boxplot(conn)

    conn.close()
    print(f"\n  ✔ CO5 – All 10 charts saved to {VIZ_DIR}\n")


if __name__ == "__main__":
    run_visualizations()
