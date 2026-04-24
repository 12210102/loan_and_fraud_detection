"""
=============================================================
STEP 1 — DATA CLEANING & PREPARATION
End-to-End Data Preparation Pipeline
Tool: Python (Pandas) — replacing Excel manual cleaning
=============================================================

What this script does:
  • Loads all 11 CSV files from the dataset
  • Removes duplicate rows
  • Handles missing / null values
  • Standardises date formats
  • Fixes inconsistent text formats
  • Creates derived features (Loan-to-Income Ratio, Txn Frequency)
  • Saves cleaned data to /cleaned/ folder and MySQL database

Run:  python 01_data_cleaning.py
"""

import os
import re
import pandas as pd
import numpy as np
from datetime import datetime

# -- Configuration ------------------------------------------
BASE_DIR   = os.path.join(os.path.dirname(__file__), 'uploaded to kaggle')
OUT_DIR    = os.path.join(os.path.dirname(__file__), 'cleaned')
os.makedirs(OUT_DIR, exist_ok=True)

USD_TO_INR = 84  # Conversion rate

# -- 1. Load all CSVs --------------------------------------─
print("=" * 60)
print("BANKGUARD — Step 1: Data Cleaning")
print("=" * 60)

def load(fname):
    path = os.path.join(BASE_DIR, fname)
    df   = pd.read_csv(path)
    print(f"  Loaded {fname:30s}  rows={len(df):>6,}  cols={df.shape[1]}")
    return df

customers         = load('customers.csv')
accounts          = load('accounts.csv')
loans             = load('loans.csv')
transactions      = load('transactions.csv')
branches          = load('branches.csv')
addresses         = load('addresses.csv')
account_statuses  = load('account_statuses.csv')
account_types     = load('account_types.csv')
loan_statuses     = load('loan_statuses.csv')
transaction_types = load('transaction_types.csv')
customer_types    = load('customer_types.csv')

print()

# -- 2. Audit raw data quality ------------------------------
print("-- Raw Data Quality Audit --")
for name, df in [('customers', customers), ('accounts', accounts),
                 ('loans', loans), ('transactions', transactions)]:
    nulls = df.isnull().sum().sum()
    dups  = df.duplicated().sum()
    print(f"  {name:15s}  nulls={nulls:5}  duplicates={dups:5}")
print()

# -- 3. Clean CUSTOMERS ------------------------------------
print("-- Cleaning customers --")
# Drop duplicates
before = len(customers)
customers.drop_duplicates(inplace=True)
print(f"  Removed {before - len(customers)} duplicate rows")

# Parse date of birth — mixed formats
customers['DateOfBirth'] = pd.to_datetime(
    customers['DateOfBirth'], errors='coerce'
).dt.normalize()

# Fill missing DateOfBirth with median year
median_year = customers['DateOfBirth'].dt.year.median()
customers['DateOfBirth'] = customers['DateOfBirth'].fillna(
    pd.Timestamp(f'{int(median_year)}-01-01')
)

# Standardise name casing
for col in ['FirstName', 'LastName']:
    if col in customers.columns:
        customers[col] = customers[col].str.strip().str.title()

# Ensure IDs are integers
for col in ['CustomerID', 'AddressID', 'CustomerTypeID']:
    customers[col] = pd.to_numeric(customers[col], errors='coerce').fillna(0).astype(int)

print(f"  Customers clean: {len(customers):,} rows")

# -- 4. Clean ACCOUNTS ------------------------------------
print("-- Cleaning accounts --")
before = len(accounts)
accounts.drop_duplicates(inplace=True)
print(f"  Removed {before - len(accounts)} duplicate rows")

accounts['OpeningDate'] = pd.to_datetime(accounts['OpeningDate'], errors='coerce').dt.normalize()
accounts['Balance']     = pd.to_numeric(accounts['Balance'], errors='coerce')

# Convert balance to INR
accounts['Balance_INR'] = (accounts['Balance'] * USD_TO_INR).round(2)

# Fill missing balance with account-type median
accounts['Balance_INR'] = accounts.groupby('AccountTypeID')['Balance_INR'].transform(
    lambda x: x.fillna(x.median())
)

for col in ['AccountID', 'CustomerID', 'AccountTypeID', 'AccountStatusID']:
    accounts[col] = pd.to_numeric(accounts[col], errors='coerce').fillna(0).astype(int)

# Remove future opening dates
today = pd.Timestamp.now()
future_mask = accounts['OpeningDate'] > today
print(f"  Found {future_mask.sum()} future OpeningDate values -> capped to today")
accounts.loc[future_mask, 'OpeningDate'] = today

print(f"  Accounts clean: {len(accounts):,} rows")

# -- 5. Clean LOANS ----------------------------------------
print("-- Cleaning loans --")
before = len(loans)
loans.drop_duplicates(inplace=True)
print(f"  Removed {before - len(loans)} duplicate rows")

loans['StartDate']        = pd.to_datetime(loans['StartDate'], errors='coerce').dt.normalize()
loans['EstimatedEndDate'] = pd.to_datetime(loans['EstimatedEndDate'], errors='coerce').dt.normalize()
loans['PrincipalAmount']  = pd.to_numeric(loans['PrincipalAmount'], errors='coerce')
loans['InterestRate']     = pd.to_numeric(loans['InterestRate'], errors='coerce')

# Convert principal to INR
loans['PrincipalAmount_INR'] = (loans['PrincipalAmount'] * USD_TO_INR).round(2)

# Clamp interest rate to realistic range [0.01, 0.30]
loans['InterestRate'] = loans['InterestRate'].clip(0.01, 0.30)

# Fill missing interest rates with global mean
loans['InterestRate'] = loans['InterestRate'].fillna(loans['InterestRate'].mean())

for col in ['LoanID', 'AccountID', 'LoanStatusID']:
    loans[col] = pd.to_numeric(loans[col], errors='coerce').fillna(0).astype(int)

print(f"  Loans clean: {len(loans):,} rows")

# -- 6. Clean TRANSACTIONS --------------------------------
print("-- Cleaning transactions (50K rows) --")
before = len(transactions)
transactions.drop_duplicates(inplace=True)
print(f"  Removed {before - len(transactions)} duplicate rows")

transactions['TransactionDate'] = pd.to_datetime(
    transactions['TransactionDate'], errors='coerce'
)
transactions['Amount'] = pd.to_numeric(transactions['Amount'], errors='coerce')

# Convert amount to INR
transactions['Amount_INR'] = (transactions['Amount'] * USD_TO_INR).round(2)

# Remove or cap negative amounts
neg_mask = transactions['Amount_INR'] < 0
print(f"  Found {neg_mask.sum()} negative amounts -> set to 0")
transactions.loc[neg_mask, 'Amount_INR'] = 0

# Cap outliers using IQR
Q1 = transactions['Amount_INR'].quantile(0.01)
Q3 = transactions['Amount_INR'].quantile(0.99)
IQR = Q3 - Q1
upper = Q3 + 3 * IQR
outlier_mask = transactions['Amount_INR'] > upper
print(f"  Found {outlier_mask.sum()} outlier transactions (>Rs.{upper:,.0f}) -> capped")
transactions.loc[outlier_mask, 'Amount_INR'] = upper

# Remove future-dated transactions
future_tx = transactions['TransactionDate'] > today
print(f"  Found {future_tx.sum()} future-dated transactions -> removed")
transactions = transactions[~future_tx]

for col in ['TransactionID', 'AccountOriginID', 'AccountDestinationID', 'TransactionTypeID', 'BranchID']:
    transactions[col] = pd.to_numeric(transactions[col], errors='coerce').fillna(0).astype(int)

print(f"  Transactions clean: {len(transactions):,} rows")

# -- 7. Create DERIVED FEATURES ----------------------------─
print()
print("-- Creating Derived Features --")

# 7a. Loan-to-Balance Ratio (proxy for Loan-to-Income)
loan_account = loans.merge(accounts[['AccountID', 'Balance_INR']], on='AccountID', how='left')
loan_account['LoanToBalanceRatio'] = (
    loan_account['PrincipalAmount_INR'] / loan_account['Balance_INR'].replace(0, np.nan)
).round(4)
print(f"  LoanToBalanceRatio: min={loan_account['LoanToBalanceRatio'].min():.3f}  "
      f"max={loan_account['LoanToBalanceRatio'].max():.3f}  "
      f"mean={loan_account['LoanToBalanceRatio'].mean():.3f}")

# Save back to loans
loans['LoanToBalanceRatio'] = loan_account['LoanToBalanceRatio'].values

# 7b. Transaction Frequency per account (last 90 days)
cutoff = transactions['TransactionDate'].max() - pd.Timedelta(days=90)
recent_tx = transactions[transactions['TransactionDate'] >= cutoff]
tx_freq = recent_tx.groupby('AccountOriginID')['TransactionID'].count().reset_index()
tx_freq.columns = ['AccountID', 'TxnFrequency_90d']
accounts = accounts.merge(tx_freq, on='AccountID', how='left')
accounts['TxnFrequency_90d'] = accounts['TxnFrequency_90d'].fillna(0).astype(int)
print(f"  TxnFrequency_90d: mean={accounts['TxnFrequency_90d'].mean():.1f} txns")

# 7c. Average transaction amount per account
avg_amt = transactions.groupby('AccountOriginID')['Amount_INR'].mean().reset_index()
avg_amt.columns = ['AccountID', 'AvgTxnAmount_INR']
accounts = accounts.merge(avg_amt, on='AccountID', how='left')
accounts['AvgTxnAmount_INR'] = accounts['AvgTxnAmount_INR'].fillna(0).round(2)

# 7d. Is Overdue flag (target variable for ML)
loans['IsOverdue'] = (loans['LoanStatusID'] == 3).astype(int)
print(f"  IsOverdue (target): {loans['IsOverdue'].sum()} overdue out of {len(loans)} loans "
      f"({loans['IsOverdue'].mean()*100:.1f}%)")

# -- 8. Save cleaned data ----------------------------------─
print()
print("-- Saving cleaned files --")
save_map = {
    'customers_clean.csv':    customers,
    'accounts_clean.csv':     accounts,
    'loans_clean.csv':        loans,
    'transactions_clean.csv': transactions,
    'branches_clean.csv':     branches,
    'addresses_clean.csv':    addresses,
}
for fname, df in save_map.items():
    path = os.path.join(OUT_DIR, fname)
    df.to_csv(path, index=False)
    print(f"  Saved {fname:35s}  ({len(df):,} rows)")

# -- 9. Summary Report ------------------------------------─
print()
print("=" * 60)
print("CLEANING COMPLETE — SUMMARY")
print("=" * 60)
print(f"  Customers:    {len(customers):>6,} rows")
print(f"  Accounts:     {len(accounts):>6,} rows  (+ 3 derived features)")
print(f"  Loans:        {len(loans):>6,} rows  (+ 2 derived features)")
print(f"  Transactions: {len(transactions):>6,} rows  (+ INR conversion)")
print(f"  Cleaned data saved to: {OUT_DIR}")
print()
print("  Next step -> Run 02_eda_analysis.py")
