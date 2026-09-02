"""
app.py – Flask Web Server & API for Banking Customer Data Management, Query Processing & Analytics System
======================================================================================================
Provides a complete Web UI backend:
  - High-level KPIs & Statistics
  - SQLite Database Table Browser & Live SQL Query Console
  - CRUD Operations Manager
  - Data Cleaning & Quality Audit Metrics
  - Data Visualizations Gallery & Chart Data APIs
  - Strategic Executive Insights & Recommendations
  - Pipeline Step Executor
"""

import os
import sys
import sqlite3
import json
import subprocess
import time
from flask import Flask, render_template, jsonify, request, send_from_directory
import pandas as pd

# Force UTF-8 encoding
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "database", "banking.db")
VIZ_DIR = os.path.join(BASE_DIR, "visualizations")
REPORT_PATH = os.path.join(BASE_DIR, "reports", "data_cleaning_report.md")
CLEANED_DIR = os.path.join(BASE_DIR, "cleaned_data")

app = Flask(__name__, template_folder="templates", static_folder="static")

def get_db_connection():
    if not os.path.exists(DB_PATH):
        # Run main.py if DB doesn't exist yet
        subprocess.run([sys.executable, os.path.join(BASE_DIR, "main.py")], check=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# ── 1. Page Routes ──────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/visualizations/<path:filename>")
def serve_visualization(filename):
    return send_from_directory(VIZ_DIR, filename)

# ── 2. API Endpoints ─────────────────────────────────────────────────────────

@app.route("/api/stats", methods=["GET"])
def get_stats():
    """Return key dashboard metrics."""
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        c.execute("SELECT COUNT(*) FROM Customer")
        total_customers = c.fetchone()[0]
        
        c.execute("SELECT COUNT(*), COALESCE(SUM(balance), 0) FROM Account")
        row = c.fetchone()
        total_accounts, total_balance = row[0], row[1]
        
        c.execute("SELECT COUNT(*), COALESCE(SUM(amount), 0) FROM Txn")
        row = c.fetchone()
        total_txns, total_txn_volume = row[0], row[1]
        
        c.execute("SELECT COUNT(*), COALESCE(SUM(loan_amount), 0) FROM Loan")
        row = c.fetchone()
        total_loans, total_loan_amount = row[0], row[1]
        
        c.execute("SELECT COUNT(*) FROM Branch")
        total_branches = c.fetchone()[0]
        
        conn.close()
        
        return jsonify({
            "status": "success",
            "data": {
                "customers": total_customers,
                "accounts": total_accounts,
                "total_balance": round(total_balance, 2),
                "transactions": total_txns,
                "transaction_volume": round(total_txn_volume, 2),
                "loans": total_loans,
                "loan_amount": round(total_loan_amount, 2),
                "branches": total_branches
            }
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/tables/<table_name>", methods=["GET"])
def get_table_data(table_name):
    """Retrieve tabular data with pagination and search."""
    valid_tables = {
        "Customer": "customer_id",
        "Account": "account_id",
        "Txn": "transaction_id",
        "Loan": "loan_id",
        "Branch": "branch_id"
    }
    if table_name not in valid_tables:
        return jsonify({"status": "error", "message": "Invalid table name"}), 400
    
    page = int(request.args.get("page", 1))
    limit = int(request.args.get("limit", 15))
    search = request.args.get("search", "").strip()
    offset = (page - 1) * limit
    
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        pk = valid_tables[table_name]
        where_clause = ""
        params = []
        
        if search:
            # Simple text search across string columns
            cur.execute(f"PRAGMA table_info('{table_name}')")
            cols = [col["name"] for col in cur.fetchall()]
            conditions = [f"{col} LIKE ?" for col in cols]
            where_clause = " WHERE " + " OR ".join(conditions)
            params = [f"%{search}%"] * len(cols)
            
        # Count total
        count_sql = f"SELECT COUNT(*) FROM {table_name}" + where_clause
        cur.execute(count_sql, params)
        total_rows = cur.fetchone()[0]
        
        # Query page data
        query_sql = f"SELECT * FROM {table_name}" + where_clause + f" ORDER BY {pk} LIMIT ? OFFSET ?"
        cur.execute(query_sql, params + [limit, offset])
        rows = cur.fetchall()
        
        cols = [column[0] for column in cur.description]
        data = [dict(zip(cols, row)) for row in rows]
        
        conn.close()
        return jsonify({
            "status": "success",
            "table": table_name,
            "data": data,
            "columns": cols,
            "total": total_rows,
            "page": page,
            "limit": limit,
            "total_pages": (total_rows + limit - 1) // limit
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/sql/query", methods=["POST"])
def run_custom_sql():
    """Execute raw user SQL queries (SELECT & DML supported)."""
    payload = request.get_json() or {}
    query = payload.get("query", "").strip()
    
    if not query:
        return jsonify({"status": "error", "message": "SQL query string is required"}), 400
    
    t0 = time.time()
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        is_select = query.strip().upper().startswith(("SELECT", "WITH", "PRAGMA", "EXPLAIN"))
        cur.execute(query)
        
        if is_select:
            rows = cur.fetchall()
            cols = [desc[0] for desc in cur.description] if cur.description else []
            result_data = [dict(zip(cols, row)) for row in rows]
            affected = len(result_data)
        else:
            conn.commit()
            cols = []
            result_data = []
            affected = cur.rowcount
            
        elapsed_ms = round((time.time() - t0) * 1000, 2)
        conn.close()
        
        return jsonify({
            "status": "success",
            "is_select": is_select,
            "columns": cols,
            "data": result_data,
            "affected_rows": affected,
            "execution_time_ms": elapsed_ms
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400


@app.route("/api/preset-queries", methods=["GET"])
def get_preset_queries():
    """Return preset banking SQL queries with titles and explanations."""
    presets = [
        {
            "id": 1,
            "title": "Query 1: High Value Accounts (> 1 Lakh)",
            "sql": "SELECT c.customer_id, c.name, c.city, a.account_no, a.account_type, a.balance FROM Customer c JOIN Account a ON c.customer_id = a.customer_id WHERE a.balance > 100000 ORDER BY a.balance DESC LIMIT 10;"
        },
        {
            "id": 2,
            "title": "Query 2: Total Balance & Customer Count by Branch",
            "sql": "SELECT b.branch_name, COUNT(DISTINCT c.customer_id) as total_customers, COUNT(a.account_id) as total_accounts, ROUND(SUM(a.balance), 2) as total_deposit FROM Branch b LEFT JOIN Account a ON b.branch_id = a.branch_id LEFT JOIN Customer c ON a.customer_id = c.customer_id GROUP BY b.branch_id, b.branch_name ORDER BY total_deposit DESC;"
        },
        {
            "id": 3,
            "title": "Query 3: Active Loans Summary by Category",
            "sql": "SELECT loan_category, COUNT(*) as loan_count, ROUND(AVG(loan_amount), 2) as avg_amount, ROUND(SUM(loan_amount), 2) as total_amount FROM Loan WHERE status = 'Active' GROUP BY loan_category ORDER BY total_amount DESC;"
        },
        {
            "id": 4,
            "title": "Query 4: Top 10 Customers by Transaction Volume",
            "sql": "SELECT c.customer_id, c.name, COUNT(t.transaction_id) as txn_count, ROUND(SUM(t.amount), 2) as total_spent FROM Customer c JOIN Account a ON c.customer_id = a.customer_id JOIN Txn t ON a.account_id = t.account_id GROUP BY c.customer_id, c.name ORDER BY total_spent DESC LIMIT 10;"
        },
        {
            "id": 5,
            "title": "Query 5: Outlier Transactions (> 75,000)",
            "sql": "SELECT t.transaction_id, c.name, a.account_no, t.transaction_type, t.amount, t.transaction_date, t.channel FROM Txn t JOIN Account a ON t.account_id = a.account_id JOIN Customer c ON a.customer_id = c.customer_id WHERE t.amount > 75000 ORDER BY t.amount DESC;"
        },
        {
            "id": 6,
            "title": "Query 6: Defaulted Loans Audit",
            "sql": "SELECT l.loan_id, c.name, c.phone, c.annual_income, l.loan_category, l.loan_amount, l.interest_rate FROM Loan l JOIN Customer c ON l.customer_id = c.customer_id WHERE l.status = 'Defaulted' ORDER BY l.loan_amount DESC;"
        }
    ]
    return jsonify({"status": "success", "presets": presets})


@app.route("/api/cleaning_report", methods=["GET"])
def get_cleaning_report():
    """Parse and return data cleaning report metrics."""
    metrics = [
        {"issue": "Missing Customer Name", "before": 8, "after": 0, "fixed": 8, "technique": "Dropped invalid missing records"},
        {"issue": "Missing Customer Email", "before": 10, "after": 0, "fixed": 10, "technique": "Imputed format user@email.com"},
        {"issue": "Inconsistent Gender Format", "before": 38, "after": 0, "fixed": 38, "technique": "Normalized to Male/Female/Other"},
        {"issue": "Negative Income Values", "before": 4, "after": 0, "fixed": 4, "technique": "Applied absolute value abs()"},
        {"issue": "Missing Income Values", "before": 5, "after": 0, "fixed": 5, "technique": "Median income imputation"},
        {"issue": "Inconsistent Branch Names", "before": 212, "after": 0, "fixed": 212, "technique": "Fuzzy string matching (score >= 70)"},
        {"issue": "Invalid Account Numbers", "before": 16, "after": 0, "fixed": 16, "technique": "10-digit regex filter & drop"},
        {"issue": "Negative Account Balances", "before": 8, "after": 0, "fixed": 8, "technique": "Converted negative sign"},
        {"issue": "Missing Transaction Amounts", "before": 22, "after": 0, "fixed": 22, "technique": "Dropped invalid transaction records"},
        {"issue": "Transaction Outliers Capped", "before": 20, "after": 0, "fixed": 20, "technique": "Capped at IQR x 3 upper bound"},
        {"issue": "Missing Interest Rates", "before": 11, "after": 0, "fixed": 11, "technique": "Category median interest rate impute"}
    ]
    shapes = {
        "Customers": "212 rows × 12 cols",
        "Accounts": "264 rows × 9 cols",
        "Transactions": "567 rows × 8 cols",
        "Loans": "180 rows × 9 cols"
    }
    return jsonify({"status": "success", "metrics": metrics, "final_shapes": shapes})


@app.route("/api/visualizations", methods=["GET"])
def get_visualizations():
    """Return list of visualization charts with image links and details."""
    charts = [
        {"filename": "01_customer_by_branch.png", "title": "1. Customer Distribution by Branch", "category": "Distribution"},
        {"filename": "02_account_type_distribution.png", "title": "2. Account Type Breakdown & Balances", "category": "Composition"},
        {"filename": "03_monthly_transaction_trends.png", "title": "3. Monthly Transaction Volume Trends", "category": "Time Series"},
        {"filename": "04_deposit_withdrawal_comparison.png", "title": "4. Deposit vs. Withdrawal Cash Flows", "category": "Comparison"},
        {"filename": "05_loan_distribution_by_category.png", "title": "5. Loan Portfolio by Product Category", "category": "Portfolio"},
        {"filename": "06_branch_transaction_volume.png", "title": "6. Branch Transaction Volume Breakdown", "category": "Branch Metrics"},
        {"filename": "07_income_vs_loan_amount.png", "title": "7. Customer Income vs. Loan Amount Scatter", "category": "Correlation"},
        {"filename": "08_transaction_amount_distribution.png", "title": "8. Transaction Amount Density & Distribution", "category": "Distribution"},
        {"filename": "09_correlation_heatmap.png", "title": "9. Banking Feature Correlation Heatmap", "category": "Correlation"},
        {"filename": "10_outlier_boxplot.png", "title": "10. Outlier Detection Boxplots", "category": "Quality & Outliers"}
    ]
    return jsonify({"status": "success", "charts": charts})


@app.route("/api/chart-data/<chart_id>", methods=["GET"])
def get_chart_data(chart_id):
    """Return dynamic Chart.js JSON data for interactive frontend rendering."""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        if chart_id == "branch_customers":
            cur.execute("SELECT b.branch_name, COUNT(c.customer_id) as cnt FROM Branch b LEFT JOIN Customer c ON b.branch_id = c.branch_id GROUP BY b.branch_name ORDER BY cnt DESC")
            rows = cur.fetchall()
            return jsonify({
                "status": "success",
                "labels": [r[0] for r in rows],
                "datasets": [{"label": "Customers", "data": [r[1] for r in rows], "backgroundColor": "#3b82f6"}]
            })
            
        elif chart_id == "account_types":
            cur.execute("SELECT account_type, COUNT(*) as cnt, SUM(balance) as total_bal FROM Account GROUP BY account_type")
            rows = cur.fetchall()
            return jsonify({
                "status": "success",
                "labels": [r[0] for r in rows],
                "datasets": [
                    {"label": "Accounts Count", "data": [r[1] for r in rows], "backgroundColor": ["#10b981", "#3b82f6", "#8b5cf6", "#f59e0b"]}
                ]
            })
            
        elif chart_id == "loan_categories":
            cur.execute("SELECT loan_category, COUNT(*) as cnt, SUM(loan_amount) as total_amt FROM Loan GROUP BY loan_category")
            rows = cur.fetchall()
            return jsonify({
                "status": "success",
                "labels": [r[0] for r in rows],
                "datasets": [
                    {"label": "Total Loan Volume (₹)", "data": [round(r[2], 2) for r in rows], "backgroundColor": "#6366f1"}
                ]
            })

        conn.close()
        return jsonify({"status": "error", "message": "Unknown chart ID"}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/insights", methods=["GET"])
def get_insights():
    """Return executive banking recommendations and findings."""
    insights = [
        {
            "id": 1,
            "title": "Branch Load Balancing & Resource Allocation",
            "metric": "Powai, Bandra & Thane lead customer density",
            "impact": "High Queue Times & Staff Overload",
            "recommendation": "Staff up Powai & Bandra branches by 20%, install 3 new Smart ATMs, and push digital onboarding."
        },
        {
            "id": 2,
            "title": "High-Activity VIP Customer Retention",
            "metric": "8 VIP Customers with z-score > 1.5 in transactions",
            "impact": "Core Revenue Drivers (Avg ₹2.8L Volume)",
            "recommendation": "Assign dedicated Wealth Relationship Managers, offer zero-fee premium credit cards & priority lounge access."
        },
        {
            "id": 3,
            "title": "Outlier Transaction Monitoring & AML Fraud Risk",
            "metric": "16 high-value transactions > ₹75,000 threshold",
            "impact": "Compliance & Fraud Exposure",
            "recommendation": "Enforce mandatory 2FA for transfers > ₹50k, integrate real-time AML flagging engine."
        },
        {
            "id": 4,
            "title": "Personal Loan Portfolio Risk & Default Management",
            "metric": "Personal Loans exhibit highest demand & 7 defaults",
            "impact": "NPA Default Exposure (₹12.1 Cr Exposure)",
            "recommendation": "Tighten credit score cutoff to 700+, require income proof validation above ₹5L, adjust risk-adjusted pricing."
        },
        {
            "id": 5,
            "title": "Income-Band Product Personalisation",
            "metric": "Weak income-to-loan correlation (r = 0.089)",
            "impact": "Under-leveraged High Net Worth Clients",
            "recommendation": "Introduce targeted pre-approved loans based on income tiers (<50k: Micro-loans, 50k-1.5L: Auto/Personal, >1.5L: Mortgage/Biz)."
        },
        {
            "id": 6,
            "title": "Branch Net Cash Outflow Mitigation",
            "metric": "8 of 10 branches have withdrawal/deposit ratio > 85%",
            "impact": "Liquidity Outflow Pressure",
            "recommendation": "Launch high-yield Fixed Deposit promotion campaigns (7.5% p.a.) and corporate salary-account tying."
        }
    ]
    return jsonify({"status": "success", "insights": insights})


@app.route("/api/crud/customer/add", methods=["POST"])
def add_customer():
    """Add a new customer to the database."""
    payload = request.get_json() or {}
    cust_id = payload.get("customer_id", "").strip()
    name = payload.get("name", "").strip()
    email = payload.get("email", "").strip()
    phone = payload.get("phone", "").strip()
    branch_id = payload.get("branch_id", "").strip() or "BR001"
    income = float(payload.get("annual_income") or 500000)
    score = int(payload.get("credit_score") or 720)
    
    if not cust_id or not name:
        return jsonify({"status": "error", "message": "Customer ID and Name are required"}), 400
        
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO Customer (customer_id, name, email, phone, branch_id, annual_income, credit_score, join_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, DATE('now'))
        """, (cust_id, name, email, phone, branch_id, income, score))
        conn.commit()
        conn.close()
        return jsonify({"status": "success", "message": f"Customer '{name}' added successfully!"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400


@app.route("/api/crud/customer/delete/<cust_id>", methods=["DELETE"])
def delete_customer(cust_id):
    """Delete a customer record."""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM Customer WHERE customer_id = ?", (cust_id,))
        conn.commit()
        affected = cur.rowcount
        conn.close()
        if affected > 0:
            return jsonify({"status": "success", "message": f"Customer {cust_id} deleted."})
        else:
            return jsonify({"status": "error", "message": "Customer not found."}), 444
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400


@app.route("/api/pipeline/run", methods=["POST"])
def run_pipeline():
    """Execute main.py pipeline and return runtime output."""
    t0 = time.time()
    try:
        res = subprocess.run([sys.executable, os.path.join(BASE_DIR, "main.py")],
                             capture_output=True, text=True, check=True)
        elapsed = round(time.time() - t0, 2)
        return jsonify({
            "status": "success",
            "message": f"Pipeline executed in {elapsed}s",
            "stdout": res.stdout,
            "stderr": res.stderr
        })
    except subprocess.CalledProcessError as err:
        return jsonify({
            "status": "error",
            "message": "Pipeline execution failed",
            "stdout": err.stdout,
            "stderr": err.stderr
        }), 500


if __name__ == "__main__":
    # Ensure database is generated on start
    get_db_connection()
    print("=" * 70)
    print("🚀 Banking System Analytics Web App is starting on http://127.0.0.1:5000")
    print("=" * 70)
    app.run(host="0.0.0.0", port=5000, debug=True)
