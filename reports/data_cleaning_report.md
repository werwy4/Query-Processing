# Banking Data Quality Report

## Summary of Issues Found & Resolved

| Issue | Before | After | Fixed |
|-------|--------|-------|-------|
| Exact duplicate rows | 0 | 0 | 0 |
| Missing name (drop) | 8 | 0 | 8 |
| Missing email (imputed) | 10 | 0 | 10 |
| Invalid email format (corrected) | 0 | 0 | 0 |
| Invalid phone replaced | 0 | 0 | 0 |
| Inconsistent gender (normalised) | 38 | 0 | 38 |
| Negative annual_income (abs) | 4 | 0 | 4 |
| Missing annual_income (median impute) | 5 | 0 | 5 |
| Income outliers (capped at upper fence) | 5 | 0 | 5 |
| Missing credit_score (median impute) | 11 | 0 | 11 |
| Inconsistent branch names (fuzzy fixed) | 212 | 0 | 212 |
| Invalid account_no (regex drop) | 16 | 0 | 16 |
| Negative balance (abs) | 8 | 0 | 8 |
| Missing balance (median impute) | 9 | 0 | 9 |
| Invalid account_type (default 'Savings') | 0 | 0 | 0 |
| Invalid status (default 'Active') | 0 | 0 | 0 |
| Missing transaction_id (drop) | 11 | 0 | 11 |
| Duplicate transaction_id (keep first) | 0 | 0 | 0 |
| Negative amount (abs) | 21 | 0 | 21 |
| Missing amount (drop) | 22 | 0 | 22 |
| Zero amount (drop) | 0 | 0 | 0 |
| Transaction amount outliers (capped) | 20 | 0 | 20 |
| Invalid transaction_type (default 'Deposit') | 0 | 0 | 0 |
| Missing transaction_date (filled) | 23 | 0 | 23 |
| Negative loan_amount (abs) | 4 | 0 | 4 |
| Loan amount outliers (capped) | 3 | 0 | 3 |
| Missing interest_rate (median impute) | 11 | 0 | 11 |
| Invalid loan_category (default 'Personal Loan') | 0 | 0 | 0 |
| Invalid loan status (default 'Active') | 0 | 0 | 0 |

## Final Dataset Shapes
- Customers    : 212 rows × 12 cols
- Accounts     : 264 rows × 9 cols
- Transactions : 567 rows × 8 cols
- Loans        : 180 rows × 9 cols

## Techniques Applied
- **Duplicate Detection**: `DataFrame.duplicated()` + `drop_duplicates()`
- **Missing Value Imputation**: Median/mode fill, placeholder strings
- **RegEx Validation**: Account number (10-digit), email format
- **Fuzzy Matching**: `thefuzz.process.extractOne` for branch names (score ≥ 70)
- **Category Normalisation**: Lowercase-strip-map to canonical sets
- **Outlier Detection**: IQR × 3 method with capping
- **Negative Value Handling**: `abs()` correction for amounts/income
- **Date Parsing**: `pd.to_datetime(errors='coerce')` with fallback fill