"""
app_streamlit.py – Streamlit Interactive Banking Analytics Dashboard
====================================================================
Alternative lightweight Python web UI for rapid data exploration.
To launch:
    streamlit run app_streamlit.py
"""

import streamlit as st
import pandas as pd
import sqlite3
import os
import glob
from PIL import Image

st.set_page_config(
    page_title="Banking Customer Analytics & Query System",
    page_icon="🏦",
    layout="wide"
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "database", "banking.db")

@st.cache_resource
def get_connection():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

st.title("🏦 Banking Customer Analytics & Query System")
st.markdown("DSA0504 Team Project • End-to-End Pipeline & Interactive Analytics UI")

# Sidebar
st.sidebar.header("Navigation")
menu = st.sidebar.radio("Select View", [
    "Dashboard Overview",
    "Database Browser & SQL Runner",
    "Data Quality Audit",
    "Visualization Gallery",
    "Executive Insights"
])

conn = get_connection()

if menu == "Dashboard Overview":
    st.subheader("📊 Key Banking Performance Indicators")
    
    col1, col2, col3, col4 = st.columns(4)
    
    cust_count = pd.read_sql("SELECT COUNT(*) FROM Customer", conn).iloc[0, 0]
    acc_count, total_bal = pd.read_sql("SELECT COUNT(*), SUM(balance) FROM Account", conn).iloc[0]
    txn_count, total_vol = pd.read_sql("SELECT COUNT(*), SUM(amount) FROM Txn", conn).iloc[0]
    loan_count, total_loan = pd.read_sql("SELECT COUNT(*), SUM(loan_amount) FROM Loan", conn).iloc[0]
    
    col1.metric("Total Customers", f"{cust_count:,}")
    col2.metric("Total Deposit Balance", f"₹{total_bal:,.2f}")
    col3.metric("Total Transactions Volume", f"₹{total_vol:,.2f}")
    col4.metric("Active Loan Portfolio", f"₹{total_loan:,.2f}")
    
    st.divider()
    
    st.subheader("📈 Quick Data Previews")
    tab1, tab2, tab3 = st.tabs(["Top Customers by Balance", "Loan Distribution", "Recent Outlier Txns"])
    
    with tab1:
        df_top = pd.read_sql("""
            SELECT c.customer_id, c.name, c.city, a.account_no, a.account_type, a.balance 
            FROM Customer c JOIN Account a ON c.customer_id = a.customer_id 
            ORDER BY a.balance DESC LIMIT 10
        """, conn)
        st.dataframe(df_top, use_container_width=True)
        
    with tab2:
        df_loans = pd.read_sql("""
            SELECT loan_category, COUNT(*) as loan_count, AVG(loan_amount) as avg_amount, SUM(loan_amount) as total_amount
            FROM Loan GROUP BY loan_category ORDER BY total_amount DESC
        """, conn)
        st.bar_chart(df_loans.set_index("loan_category")["total_amount"])
        
    with tab3:
        df_outliers = pd.read_sql("""
            SELECT t.transaction_id, c.name, t.transaction_type, t.amount, t.channel
            FROM Txn t JOIN Account a ON t.account_id = a.account_id
            JOIN Customer c ON a.customer_id = c.customer_id
            WHERE t.amount > 75000 ORDER BY t.amount DESC
        """, conn)
        st.dataframe(df_outliers, use_container_width=True)

elif menu == "Database Browser & SQL Runner":
    st.subheader("💻 Interactive SQL Console & Database Explorer")
    
    sql_query = st.text_area("Enter SQL Query", "SELECT * FROM Customer LIMIT 10;", height=100)
    if st.button("Run Query"):
        try:
            res = pd.read_sql(sql_query, conn)
            st.success(f"Query executed successfully! ({len(res)} rows returned)")
            st.dataframe(res, use_container_width=True)
        except Exception as e:
            st.error(f"SQL Execution Error: {e}")
            
    st.divider()
    st.subheader("📂 Browse Relational Tables")
    table_name = st.selectbox("Select Table", ["Customer", "Account", "Txn", "Loan", "Branch"])
    df_tbl = pd.read_sql(f"SELECT * FROM {table_name}", conn)
    st.dataframe(df_tbl, use_container_width=True)

elif menu == "Data Quality Audit":
    st.subheader("🧹 Data Cleaning & Quality Audit Metrics")
    report_file = os.path.join(BASE_DIR, "reports", "data_cleaning_report.md")
    if os.path.exists(report_file):
        with open(report_file, "r", encoding="utf-8") as f:
            st.markdown(f.read())
    else:
        st.warning("Data cleaning report file not found.")

elif menu == "Visualization Gallery":
    st.subheader("🎨 Generated Analytical Visualizations")
    viz_files = sorted(glob.glob(os.path.join(BASE_DIR, "visualizations", "*.png")))
    
    if not viz_files:
        st.info("No visualization charts found. Run main.py to generate charts.")
    else:
        cols = st.columns(2)
        for idx, viz in enumerate(viz_files):
            col = cols[idx % 2]
            img = Image.open(viz)
            col.image(img, caption=os.path.basename(viz), use_column_width=True)

elif menu == "Executive Insights":
    st.subheader("💡 Strategic Recommendations for Banking Operations")
    
    st.info("**1. Branch Capacity**: Powai & Bandra show highest customer load → Expand staff by 20% & add smart ATMs.")
    st.success("**2. High-Value VIP Retention**: 8 customers have z-score > 1.5 in transactions → Offer Priority Banking & Dedicated RMs.")
    st.warning("**3. Fraud Risk Alert**: 16 high-value transactions exceed ₹75,000 → Mandatory 2FA for amounts above ₹50k.")
    st.error("**4. Loan Default Mitigation**: Personal Loans exhibit highest demand and default rate → Tighten credit score cutoff to 700+.")
