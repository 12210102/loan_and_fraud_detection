"""
=============================================================
STEP 2 — EXPLORATORY DATA ANALYSIS (EDA)
Exploratory Analytics & Statistical Understanding
=============================================================

What this script does:
  • Loads cleaned data from /cleaned/ folder
  • Prints statistical summaries
  • Analyses customer/account/loan/transaction distributions
  • Saves EDA charts to /reports/eda_charts/
  • Generates a text-based EDA report

Run:  python 02_eda_analysis.py
"""

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import seaborn as sns
from matplotlib.ticker import FuncFormatter

# -- Config ------------------------------------------------─
CLEAN_DIR = os.path.join(os.path.dirname(__file__), 'cleaned')
CHART_DIR = os.path.join(os.path.dirname(__file__), 'reports', 'eda_charts')
os.makedirs(CHART_DIR, exist_ok=True)

# Dark theme to match dashboard
plt.style.use('dark_background')
COLORS = ['#6366f1', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#3b82f6', '#06b6d4']
sns.set_palette(COLORS)

def inr_fmt(x, pos=None):
    if x >= 1e7:  return f'Rs.{x/1e7:.1f}Cr'
    if x >= 1e5:  return f'Rs.{x/1e5:.1f}L'
    return f'Rs.{x:,.0f}'

# -- Load cleaned data --------------------------------------─
print("=" * 60)
print("BANKGUARD — Step 2: EDA")
print("=" * 60)

customers    = pd.read_csv(os.path.join(CLEAN_DIR, 'customers_clean.csv'))
accounts     = pd.read_csv(os.path.join(CLEAN_DIR, 'accounts_clean.csv'))
loans        = pd.read_csv(os.path.join(CLEAN_DIR, 'loans_clean.csv'))
transactions = pd.read_csv(os.path.join(CLEAN_DIR, 'transactions_clean.csv'),
                           parse_dates=['TransactionDate'])

# Reference tables (from original)
BASE_DIR = os.path.join(os.path.dirname(__file__), 'uploaded to kaggle')
acc_types  = pd.read_csv(os.path.join(BASE_DIR, 'account_types.csv'))
loan_stat  = pd.read_csv(os.path.join(BASE_DIR, 'loan_statuses.csv'))
tx_types   = pd.read_csv(os.path.join(BASE_DIR, 'transaction_types.csv'))
cust_types = pd.read_csv(os.path.join(BASE_DIR, 'customer_types.csv'))

# -- 1. Summary Statistics ----------------------------------
print("\n-- CUSTOMER SUMMARY --")
print(f"  Total customers          : {len(customers):,}")
print(f"  Unique customer types    : {customers['CustomerTypeID'].nunique()}")

print("\n-- ACCOUNT SUMMARY --")
print(f"  Total accounts           : {len(accounts):,}")
print(f"  Total Balance (INR)      : Rs.{accounts['Balance_INR'].sum():,.0f}")
print(f"  Avg Balance (INR)        : Rs.{accounts['Balance_INR'].mean():,.0f}")
print(f"  Median Balance (INR)     : Rs.{accounts['Balance_INR'].median():,.0f}")
print(f"  Max Balance (INR)        : Rs.{accounts['Balance_INR'].max():,.0f}")

print("\n-- LOAN SUMMARY --")
print(f"  Total loans              : {len(loans):,}")
print(f"  Total Principal (INR)    : Rs.{loans['PrincipalAmount_INR'].sum():,.0f}")
print(f"  Avg Interest Rate        : {loans['InterestRate'].mean()*100:.2f}%")
print(f"  Overdue loans            : {loans['IsOverdue'].sum()} ({loans['IsOverdue'].mean()*100:.1f}%)")

print("\n-- TRANSACTION SUMMARY --")
print(f"  Total transactions       : {len(transactions):,}")
print(f"  Total Volume (INR)       : Rs.{transactions['Amount_INR'].sum():,.0f}")
print(f"  Avg Txn Amount (INR)     : Rs.{transactions['Amount_INR'].mean():,.0f}")
print(f"  Date range               : {transactions['TransactionDate'].min().date()} -> "
      f"{transactions['TransactionDate'].max().date()}")

# -- 2. CHART 1 — Customer & Account Overview ----------------
print("\n-- Plotting Chart 1: Customer & Account Overview --")
fig, axes = plt.subplots(2, 3, figsize=(16, 9), facecolor='#0a0b14')
fig.suptitle('Customer & Account Overview', fontsize=16, color='white', y=0.98)

for ax in axes.flat:
    ax.set_facecolor('#131520')
    ax.tick_params(colors='#8892b0')
    for spine in ax.spines.values():
        spine.set_edgecolor('#1e2030')

# 2a. Customer type distribution
cust_merge = customers.merge(cust_types, on='CustomerTypeID')
ct = cust_merge['TypeName'].value_counts()
axes[0,0].bar(ct.index, ct.values, color=COLORS[:3])
axes[0,0].set_title('Customer Types', color='white', fontsize=11)
axes[0,0].set_ylabel('Count', color='#8892b0')

# 2b. Account type distribution
acc_merge = accounts.merge(acc_types, on='AccountTypeID')
at = acc_merge['TypeName'].value_counts()
axes[0,1].bar(at.index, at.values, color=COLORS[:5])
axes[0,1].set_title('Account Types', color='white', fontsize=11)
axes[0,1].tick_params(axis='x', rotation=20)

# 2c. Balance distribution (INR)
axes[0,2].hist(accounts['Balance_INR'], bins=30, color='#6366f1', edgecolor='#0a0b14', alpha=0.9)
axes[0,2].set_title('Balance Distribution (Rs.)', color='white', fontsize=11)
axes[0,2].xaxis.set_major_formatter(FuncFormatter(inr_fmt))
axes[0,2].tick_params(axis='x', rotation=15)

# 2d. Transaction type share
tx_merge = transactions.merge(tx_types, on='TransactionTypeID')
tt = tx_merge['TypeName'].value_counts()
axes[1,0].pie(tt.values, labels=tt.index, colors=COLORS[:4],
              autopct='%1.1f%%', textprops={'color':'white', 'fontsize':9})
axes[1,0].set_title('Transaction Types', color='white', fontsize=11)

# 2e. Monthly transaction volume
transactions['YearMonth'] = transactions['TransactionDate'].dt.to_period('M')
monthly = transactions.groupby('YearMonth')['Amount_INR'].sum().reset_index()
monthly['YearMonth'] = monthly['YearMonth'].astype(str)
recent = monthly.tail(12)
axes[1,1].plot(range(len(recent)), recent['Amount_INR'], color='#10b981',
               linewidth=2, marker='o', markersize=4)
axes[1,1].fill_between(range(len(recent)), recent['Amount_INR'], alpha=0.2, color='#10b981')
axes[1,1].set_xticks(range(len(recent)))
axes[1,1].set_xticklabels(recent['YearMonth'].str[-5:], rotation=45, fontsize=8)
axes[1,1].set_title('Monthly Volume (Last 12M)', color='white', fontsize=11)
axes[1,1].yaxis.set_major_formatter(FuncFormatter(inr_fmt))

# 2f. Loan status distribution
ls_merge = loans.merge(loan_stat, on='LoanStatusID')
ls = ls_merge['StatusName'].value_counts()
axes[1,2].bar(ls.index, ls.values, color=[COLORS[1], COLORS[0], COLORS[3]])
axes[1,2].set_title('Loan Status', color='white', fontsize=11)

plt.tight_layout()
chart1_path = os.path.join(CHART_DIR, 'eda_overview.png')
plt.savefig(chart1_path, dpi=120, bbox_inches='tight', facecolor='#0a0b14')
plt.close()
print(f"  Saved: {chart1_path}")

# -- 3. CHART 2 — Correlation & Risk Analysis ----------------
print("-- Plotting Chart 2: Loan Risk Analysis --")
fig, axes = plt.subplots(1, 3, figsize=(16, 5), facecolor='#0a0b14')
fig.suptitle('Loan Risk Analysis', fontsize=16, color='white')

for ax in axes:
    ax.set_facecolor('#131520')
    ax.tick_params(colors='#8892b0')
    for spine in ax.spines.values():
        spine.set_edgecolor('#1e2030')

# 3a. Interest rate by loan status
for i, (name, grp) in enumerate(ls_merge.groupby('StatusName')):
    axes[0].hist(grp['InterestRate'] * 100, bins=15, alpha=0.7,
                 label=name, color=COLORS[i], edgecolor='#0a0b14')
axes[0].set_title('Interest Rate by Loan Status', color='white', fontsize=11)
axes[0].set_xlabel('Interest Rate (%)', color='#8892b0')
axes[0].legend(fontsize=9)

# 3b. Principal amount distribution
axes[1].hist(loans['PrincipalAmount_INR'] / 1e5, bins=20,
             color='#f59e0b', edgecolor='#0a0b14', alpha=0.9)
axes[1].set_title('Loan Principal (Rs. Lakhs)', color='white', fontsize=11)
axes[1].set_xlabel('Amount (Rs. Lakhs)', color='#8892b0')

# 3c. Loan-to-Balance Ratio
valid = loans['LoanToBalanceRatio'].dropna()
valid = valid[valid < valid.quantile(0.95)]
axes[2].hist(valid, bins=20, color='#ef4444', edgecolor='#0a0b14', alpha=0.9)
axes[2].set_title('Loan-to-Balance Ratio', color='white', fontsize=11)
axes[2].set_xlabel('Ratio', color='#8892b0')

plt.tight_layout()
chart2_path = os.path.join(CHART_DIR, 'eda_loan_risk.png')
plt.savefig(chart2_path, dpi=120, bbox_inches='tight', facecolor='#0a0b14')
plt.close()
print(f"  Saved: {chart2_path}")

# -- 4. CHART 3 — Transaction Patterns --------------------─
print("-- Plotting Chart 3: Transaction Patterns --")
fig, axes = plt.subplots(1, 3, figsize=(16, 5), facecolor='#0a0b14')
fig.suptitle('Transaction Patterns', fontsize=16, color='white')

for ax in axes:
    ax.set_facecolor('#131520')
    ax.tick_params(colors='#8892b0')
    for spine in ax.spines.values():
        spine.set_edgecolor('#1e2030')

# Extract hour of day
transactions['Hour'] = pd.to_datetime(transactions['TransactionDate']).dt.hour

# 4a. Transaction volume by hour
hourly = transactions.groupby('Hour')['Amount_INR'].sum()
axes[0].bar(hourly.index, hourly.values, color='#6366f1', edgecolor='#0a0b14', alpha=0.9)
axes[0].set_title('Volume by Hour of Day', color='white', fontsize=11)
axes[0].set_xlabel('Hour', color='#8892b0')
axes[0].yaxis.set_major_formatter(FuncFormatter(inr_fmt))

# 4b. Transaction count by day of week
transactions['DayOfWeek'] = pd.to_datetime(transactions['TransactionDate']).dt.day_name()
dow_order = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']
dow = transactions.groupby('DayOfWeek')['TransactionID'].count().reindex(dow_order)
axes[1].bar(range(7), dow.values, color='#8b5cf6', edgecolor='#0a0b14', alpha=0.9)
axes[1].set_xticks(range(7))
axes[1].set_xticklabels(['Mon','Tue','Wed','Thu','Fri','Sat','Sun'])
axes[1].set_title('Transactions by Day of Week', color='white', fontsize=11)

# 4c. Top 10 branches by volume
branch_vol = transactions.groupby('BranchID')['Amount_INR'].sum().nlargest(10)
axes[2].barh([f'Br {b}' for b in branch_vol.index], branch_vol.values / 1e7,
             color=COLORS[:10], edgecolor='#0a0b14', alpha=0.9)
axes[2].set_title('Top 10 Branches (Rs. Cr)', color='white', fontsize=11)
axes[2].set_xlabel('Volume (Rs. Crores)', color='#8892b0')

plt.tight_layout()
chart3_path = os.path.join(CHART_DIR, 'eda_transactions.png')
plt.savefig(chart3_path, dpi=120, bbox_inches='tight', facecolor='#0a0b14')
plt.close()
print(f"  Saved: {chart3_path}")

# -- 5. Key Insights ----------------------------------------
print()
print("=" * 60)
print("KEY EDA INSIGHTS")
print("=" * 60)
top_hour = transactions.groupby('Hour')['Amount_INR'].sum().idxmax()
top_type = tx_merge.groupby('TypeName')['Amount_INR'].sum().idxmax()
print(f"  Peak transaction hour    : {top_hour}:00")
print(f"  Highest volume type      : {top_type}")
print(f"  Overdue loan rate        : {loans['IsOverdue'].mean()*100:.1f}%")
print(f"  Avg txn freq (90d/acct)  : {accounts.get('TxnFrequency_90d', pd.Series([0])).mean():.1f} txns")
print()
print("  Charts saved to:", CHART_DIR)
print("  Next step -> Run 03_ml_models.py")
