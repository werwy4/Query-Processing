"""
generate_datasets.py
Generates synthetic raw banking datasets with intentional data quality issues:
 - customers.csv   (CSV)
 - accounts.csv    (CSV)
 - branches.csv    (CSV)
 - transactions.json (JSON)
 - loans.xml       (XML)
"""

import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')


import csv
import json
import random
import os
from datetime import datetime, timedelta
from faker import Faker

fake = Faker('en_IN')
random.seed(42)
Faker.seed(42)

os.makedirs("datasets", exist_ok=True)
os.makedirs("cleaned_data", exist_ok=True)
os.makedirs("database", exist_ok=True)
os.makedirs("visualizations", exist_ok=True)
os.makedirs("reports", exist_ok=True)

# ─── Master lists ────────────────────────────────────────────────────────────
BRANCH_IDS   = [f"BR{str(i).zfill(3)}" for i in range(1, 11)]
BRANCH_NAMES_CLEAN = [
    "Andheri Branch", "Bandra Branch", "Borivali Branch", "Dadar Branch",
    "Ghatkopar Branch", "Juhu Branch", "Kurla Branch", "Malad Branch",
    "Powai Branch", "Thane Branch",
]
# Dirty variants for branches (inconsistent naming)
BRANCH_NAME_VARIANTS = {
    "Andheri Branch": ["Andheri Branch", "andheri branch", "ANDHERI", "Andheri Br.", "Andheri"],
    "Bandra Branch":  ["Bandra Branch", "bandra branch", "BANDRA BR", "Bandra Br.", "Bandra"],
    "Borivali Branch":["Borivali Branch", "borivali branch", "BORIVALI", "Borivali Br"],
    "Dadar Branch":   ["Dadar Branch", "dadar branch", "DADAR", "Dadar Br.", "Dadar"],
    "Ghatkopar Branch":["Ghatkopar Branch", "ghatkopar branch", "GHATKOPAR", "Ghatkopar Br"],
    "Juhu Branch":    ["Juhu Branch", "juhu branch", "JUHU", "Juhu Br."],
    "Kurla Branch":   ["Kurla Branch", "kurla branch", "KURLA", "Kurla Br."],
    "Malad Branch":   ["Malad Branch", "malad branch", "MALAD", "Malad Br."],
    "Powai Branch":   ["Powai Branch", "powai branch", "POWAI", "Powai Br."],
    "Thane Branch":   ["Thane Branch", "thane branch", "THANE", "Thane Br."],
}

ACCOUNT_TYPES_CLEAN = ["Savings", "Current", "Fixed Deposit", "Recurring Deposit"]
ACCOUNT_TYPE_DIRTY  = ["Savings", "savings", "SAVINGS", "saving", "Current", "current",
                        "CURRENT", "Fixed Deposit", "fixed deposit", "FD",
                        "Recurring Deposit", "recurring deposit", "RD"]
LOAN_CATEGORIES_CLEAN = ["Home Loan", "Car Loan", "Personal Loan", "Education Loan", "Business Loan"]
LOAN_CAT_DIRTY = ["Home Loan", "home loan", "HOME LOAN", "HomeLoan",
                  "Car Loan", "car loan", "CAR LOAN", "CarLoan",
                  "Personal Loan", "personal loan", "PERSONAL", "PersonalLoan",
                  "Education Loan", "education loan", "EDU LOAN",
                  "Business Loan", "business loan", "BIZ LOAN"]

# ─── 1. branches.csv ─────────────────────────────────────────────────────────
def gen_branches():
    rows = []
    for bid, bname in zip(BRANCH_IDS, BRANCH_NAMES_CLEAN):
        rows.append({
            "branch_id": bid,
            "branch_name": bname,
            "city": bname.split()[0],
            "manager": fake.name(),
            "phone": fake.phone_number()[:15],
            "established_year": random.randint(1985, 2010),
        })
    with open("datasets/branches.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    print(f"  ✔ branches.csv  – {len(rows)} rows")

# ─── 2. customers.csv ────────────────────────────────────────────────────────
def gen_customers(n=220):
    rows = []
    cust_ids = [f"CUST{str(i).zfill(5)}" for i in range(1, n+1)]

    for i, cid in enumerate(cust_ids):
        branch_name_dirty = random.choice(
            BRANCH_NAME_VARIANTS[random.choice(BRANCH_NAMES_CLEAN)]
        )
        name  = fake.name()
        email = fake.email() if random.random() > 0.07 else ""          # 7% missing
        phone = fake.phone_number()[:15] if random.random() > 0.05 else ""
        dob   = fake.date_of_birth(minimum_age=21, maximum_age=70).strftime("%d-%m-%Y") \
                if random.random() > 0.04 else ""

        # Introduce some obviously bad phones
        if random.random() < 0.03:
            phone = "N/A"
        # Introduce income outliers (a few very rich, a few negative)
        income = round(random.uniform(15000, 200000), 2)
        if random.random() < 0.03:
            income = round(random.uniform(900000, 2000000), 2)   # outlier high
        if random.random() < 0.02:
            income = -abs(income)                                  # invalid negative

        rows.append({
            "customer_id":  cid,
            "name":         name if random.random() > 0.04 else "",   # 4% missing name
            "email":        email,
            "phone":        phone,
            "dob":          dob,
            "gender":       random.choice(["Male", "Female", "male", "female", "M", "F", ""]),
            "city":         fake.city() if random.random() > 0.05 else "",
            "branch_name":  branch_name_dirty,
            "annual_income": income if random.random() > 0.04 else "",
            "credit_score": random.randint(300, 900) if random.random() > 0.06 else "",
            "join_date":    fake.date_between(start_date="-10y", end_date="today").strftime("%Y-%m-%d"),
        })

    # Inject 15 duplicate rows (same customer repeated)
    duplicates = random.sample(rows, 15)
    rows.extend(duplicates)
    random.shuffle(rows)

    with open("datasets/customers.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    print(f"  ✔ customers.csv – {len(rows)} rows (incl. 15 duplicates)")

# ─── 3. accounts.csv ─────────────────────────────────────────────────────────
def gen_accounts(n=280):
    rows = []
    cust_ids = [f"CUST{str(i).zfill(5)}" for i in range(1, 221)]

    for i in range(1, n+1):
        cid = random.choice(cust_ids)
        # Some invalid account numbers (should be 10 digits)
        if random.random() < 0.05:
            acc_no = fake.bothify(text="???####")          # invalid format
        else:
            acc_no = fake.numerify(text="##########")      # valid 10-digit

        acc_type = random.choice(ACCOUNT_TYPE_DIRTY)
        balance  = round(random.uniform(500, 500000), 2)
        if random.random() < 0.04:
            balance = -abs(balance)                        # invalid negative balance

        rows.append({
            "account_id":   f"ACC{str(i).zfill(6)}",
            "customer_id":  cid,
            "account_no":   acc_no,
            "account_type": acc_type,
            "balance":      balance if random.random() > 0.05 else "",
            "open_date":    fake.date_between(start_date="-8y", end_date="today").strftime("%Y-%m-%d"),
            "branch_name":  random.choice(
                                BRANCH_NAME_VARIANTS[random.choice(BRANCH_NAMES_CLEAN)]
                            ),
            "status":       random.choice(["Active", "active", "ACTIVE", "Inactive", "inactive", "Closed"]),
        })

    with open("datasets/accounts.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    print(f"  ✔ accounts.csv  – {len(rows)} rows")

# ─── 4. transactions.json ────────────────────────────────────────────────────
def gen_transactions(n=600):
    acc_ids = [f"ACC{str(i).zfill(6)}" for i in range(1, 281)]
    records = []
    base_date = datetime(2023, 1, 1)

    for i in range(1, n+1):
        amount = round(random.uniform(100, 50000), 2)
        # Inject outliers
        if random.random() < 0.04:
            amount = round(random.uniform(200000, 1000000), 2)
        # Inject invalid amounts
        if random.random() < 0.03:
            amount = -abs(amount)

        txn_date = base_date + timedelta(days=random.randint(0, 730))
        records.append({
            "transaction_id":   f"TXN{str(i).zfill(7)}" if random.random() > 0.02 else None,
            "account_id":       random.choice(acc_ids),
            "transaction_type": random.choice(["Deposit", "Withdrawal", "deposit",
                                               "withdrawal", "DEPOSIT", "WITHDRAWAL",
                                               "Transfer", "transfer"]),
            "amount":           amount if random.random() > 0.04 else None,
            "transaction_date": txn_date.strftime("%Y-%m-%d") if random.random() > 0.03 else "",
            "description":      fake.sentence(nb_words=4) if random.random() > 0.1 else None,
            "channel":          random.choice(["ATM", "Online", "Branch", "Mobile", "atm", "online"]),
        })

    # Inject 20 duplicate transactions
    dupes = random.sample(records, 20)
    records.extend(dupes)
    random.shuffle(records)

    with open("datasets/transactions.json", "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2, default=str)
    print(f"  ✔ transactions.json – {len(records)} records (incl. 20 duplicates)")

# ─── 5. loans.xml ────────────────────────────────────────────────────────────
def gen_loans(n=180):
    cust_ids = [f"CUST{str(i).zfill(5)}" for i in range(1, 221)]
    lines = ['<?xml version="1.0" encoding="UTF-8"?>', "<Loans>"]

    for i in range(1, n+1):
        loan_amt = round(random.uniform(50000, 5000000), 2)
        if random.random() < 0.04:
            loan_amt = round(random.uniform(10000000, 50000000), 2)  # outlier
        if random.random() < 0.02:
            loan_amt = -abs(loan_amt)                                 # invalid

        cat = random.choice(LOAN_CAT_DIRTY)
        interest = round(random.uniform(6.5, 18.5), 2) if random.random() > 0.06 else ""
        tenure   = random.choice([12, 24, 36, 48, 60, 84, 120, 180, 240])
        start    = fake.date_between(start_date="-6y", end_date="-1y")
        status   = random.choice(["Active", "Closed", "Defaulted", "active", "closed", "ACTIVE"])
        cid      = random.choice(cust_ids)

        lines.append(f'  <Loan id="LOAN{str(i).zfill(6)}">')
        lines.append(f'    <customer_id>{cid}</customer_id>')
        lines.append(f'    <loan_category>{cat}</loan_category>')
        lines.append(f'    <loan_amount>{loan_amt}</loan_amount>')
        lines.append(f'    <interest_rate>{interest}</interest_rate>')
        lines.append(f'    <tenure_months>{tenure}</tenure_months>')
        lines.append(f'    <start_date>{start.strftime("%Y-%m-%d")}</start_date>')
        lines.append(f'    <status>{status}</status>')
        lines.append(f'  </Loan>')

    lines.append("</Loans>")
    with open("datasets/loans.xml", "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"  ✔ loans.xml      – {n} records")

# ─── Main ────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("Generating synthetic banking datasets …")
    gen_branches()
    gen_customers()
    gen_accounts()
    gen_transactions()
    gen_loans()
    print("\nAll datasets saved to datasets/")
