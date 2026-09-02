"""
main.py  –  Banking Customer Data Management & Analytics System
===============================================================
Orchestrates the full end-to-end pipeline:
  Step 1 → Generate synthetic raw datasets
  Step 2 → CO1: Data Wrangling (CSV / JSON / XML)
  Step 3 → CO3: Data Cleaning & Preprocessing
  Step 4 → CO2: Database Design & CRUD Operations
  Step 5 → CO4: Data Exploration & Analysis
  Step 6 → CO5: Data Visualizations
  Step 7 → Insights & Recommendations
"""

import time
import traceback
import importlib.util
import sys
import os

# Force UTF-8 output on Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

def load_module(filename):
    """Load a Python module from a file path (supports numeric-prefixed names)."""
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)
    spec = importlib.util.spec_from_file_location(filename, path)
    mod  = importlib.util.module_from_spec(spec)
    sys.modules[filename] = mod
    spec.loader.exec_module(mod)
    return mod

BANNER = """
╔══════════════════════════════════════════════════════════════════════════╗
║     BANKING CUSTOMER DATA MANAGEMENT, QUERY PROCESSING &               ║
║     ANALYTICS SYSTEM  –  DSA0504 Team Project                          ║
╚══════════════════════════════════════════════════════════════════════════╝
"""

def run_step(step_num: int, name: str, fn, *args):
    """Run a pipeline step with timing and error handling."""
    print(f"\n{'─'*72}")
    print(f"  STEP {step_num}: {name}")
    print(f"{'─'*72}")
    t0 = time.time()
    try:
        result = fn(*args)
        elapsed = time.time() - t0
        print(f"\n  ✅  Step {step_num} completed in {elapsed:.1f}s")
        return result
    except Exception as exc:
        elapsed = time.time() - t0
        print(f"\n  ❌  Step {step_num} FAILED after {elapsed:.1f}s")
        traceback.print_exc()
        raise


def main():
    print(BANNER)
    total_start = time.time()

    # ── Step 1: Generate raw datasets ────────────────────────────────────────
    from generate_datasets import (
        gen_branches, gen_customers, gen_accounts, gen_transactions, gen_loans
    )
    def generate_all():
        gen_branches(); gen_customers(); gen_accounts()
        gen_transactions(); gen_loans()
    run_step(1, "Generate Synthetic Banking Datasets", generate_all)

    # ── Step 2: CO1 – Data Wrangling ─────────────────────────────────────────
    wrangling_mod = load_module("01_data_wrangling.py")
    wrangled = run_step(2, "CO1 – Data Wrangling (CSV / JSON / XML)", wrangling_mod.run_wrangling)
    df_customers, df_accounts, df_transactions, df_loans, df_branches = wrangled

    # ── Step 3: CO3 – Data Cleaning ──────────────────────────────────────────
    cleaning_mod = load_module("03_data_cleaning.py")
    cleaned = run_step(3, "CO3 – Data Cleaning & Preprocessing",
                       cleaning_mod.run_cleaning,
                       df_customers, df_accounts, df_transactions, df_loans, df_branches)
    df_cust_c, df_acc_c, df_txn_c, df_loan_c, df_br_c = cleaned

    # ── Step 4: CO2 – Database & CRUD ────────────────────────────────────────
    database_mod = load_module("02_database_crud.py")
    conn, query_results = run_step(4, "CO2 – Database Design & CRUD Operations",
                                   database_mod.run_database,
                                   df_cust_c, df_acc_c, df_txn_c, df_loan_c, df_br_c)
    conn.close()

    # ── Step 5: CO4 – Data Analysis ──────────────────────────────────────────
    analysis_mod = load_module("04_data_analysis.py")
    analysis_results = run_step(5, "CO4 – Data Exploration & Analysis", analysis_mod.run_analysis)

    # ── Step 6: CO5 – Visualizations ─────────────────────────────────────────
    viz_mod = load_module("05_visualizations.py")
    run_step(6, "CO5 – Data Visualizations", viz_mod.run_visualizations)

    # ── Step 7: Insights ─────────────────────────────────────────────────────
    insights_mod = load_module("06_insights.py")
    run_step(7, "Banking Insights & Recommendations", insights_mod.run_insights)

    # ── Final summary ─────────────────────────────────────────────────────────
    total = time.time() - total_start
    print(f"""
╔══════════════════════════════════════════════════════════════════════════╗
║   PIPELINE COMPLETE  –  Total time: {total:>6.1f}s                          ║
╠══════════════════════════════════════════════════════════════════════════╣
║   Outputs generated:                                                    ║
║   • datasets/          – 5 raw files (CSV / JSON / XML)                 ║
║   • cleaned_data/      – 4 cleaned CSV files                            ║
║   • database/banking.db – SQLite database (5 tables)                   ║
║   • reports/data_cleaning_report.md  – Quality report                  ║
║   • visualizations/    – 10 PNG charts                                  ║
╚══════════════════════════════════════════════════════════════════════════╝
""")


if __name__ == "__main__":
    main()
